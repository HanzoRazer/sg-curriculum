#!/usr/bin/env python3
"""
CBSP21 PR Gate for sg-curriculum

Validates that PRs touching governed areas have a valid patch_input.json manifest
with sufficient coverage declarations.

Env:
  CBSP21_MIN_COVERAGE     default 0.95
  CBSP21_MANIFEST_PATH    default .cbsp21/patch_input.json

Usage:
  python scripts/ci/check_cbsp21_gate.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Set


# Governed areas in sg-curriculum
GOVERNED_PATHS = {
    "src/sg_coach/",
    "src/sg_groove/",
    "runtime/",
    "contracts/",
    "tests/",
    "fixtures/",
    "scripts/ci/",
}


def get_changed_files() -> List[str]:
    """Get files changed in this PR (vs origin/main)."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "origin/main...HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
    except subprocess.CalledProcessError:
        # Fallback: compare to HEAD~1
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD~1"],
                capture_output=True,
                text=True,
                check=True,
            )
            return [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
        except subprocess.CalledProcessError:
            return []


def is_governed_file(path: str) -> bool:
    """Check if file is in a governed area."""
    return any(path.startswith(gp) for gp in GOVERNED_PATHS)


def is_code_file(path: str) -> bool:
    """Check if file is a code file (not just docs)."""
    code_exts = {".py", ".json", ".yaml", ".yml", ".sh", ".ps1"}
    return Path(path).suffix.lower() in code_exts


def load_exemptions() -> Set[str]:
    """Load exempt patterns from .cbsp21/exemptions.json if it exists."""
    exemptions_path = Path(".cbsp21/exemptions.json")
    if not exemptions_path.exists():
        return set()
    try:
        data = json.loads(exemptions_path.read_text(encoding="utf-8"))
        return set(data.get("exempt_patterns", []))
    except (json.JSONDecodeError, OSError):
        return set()


def is_exempt(path: str, exempt_patterns: Set[str]) -> bool:
    """Check if path matches any exempt pattern."""
    from fnmatch import fnmatch

    for pattern in exempt_patterns:
        if fnmatch(path, pattern):
            return True
    return False


def main() -> int:
    min_coverage = float(os.getenv("CBSP21_MIN_COVERAGE", "0.95"))
    manifest_path = Path(os.getenv("CBSP21_MANIFEST_PATH", ".cbsp21/patch_input.json"))
    exempt_patterns = load_exemptions()

    changed_files = get_changed_files()
    governed_code_files = [
        f
        for f in changed_files
        if is_governed_file(f) and is_code_file(f) and not is_exempt(f, exempt_patterns)
    ]

    if not governed_code_files:
        print("CBSP21 GATE: No governed code files changed - skipping manifest check.")
        return 0

    print(f"CBSP21 GATE: {len(governed_code_files)} governed code file(s) changed:")
    for f in governed_code_files:
        print(f"  - {f}")

    if not manifest_path.exists():
        print(f"\n❌ CBSP21 GATE FAIL: Missing manifest at {manifest_path}")
        print("   PRs changing governed areas must include a patch_input.json manifest.")
        print("   See .cbsp21/patch_input.json.example for template.")
        return 1

    try:
        manifest: Dict[str, Any] = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        print(f"❌ CBSP21 GATE FAIL: Invalid manifest: {e}")
        return 1

    # Check required fields
    required_fields = ["schema_version", "patch_id", "title", "intent", "change_type"]
    missing_fields = [f for f in required_fields if f not in manifest]
    if missing_fields:
        print(f"❌ CBSP21 GATE FAIL: Missing required fields: {missing_fields}")
        return 1

    # Check schema version
    if manifest.get("schema_version") != "cbsp21_patch_input_v1":
        print(f"❌ CBSP21 GATE FAIL: Invalid schema_version. Expected 'cbsp21_patch_input_v1'")
        return 1

    # Check that all governed code files are declared in manifest
    declared_paths = {cf["path"] for cf in manifest.get("changed_files", [])}
    missing = [f for f in governed_code_files if f not in declared_paths]

    if missing:
        print(f"\n❌ CBSP21 GATE FAIL: Changed files not declared in manifest:")
        for m in missing:
            print(f"  - {m}")
        return 1

    # Check coverage per file
    violations: List[str] = []
    for cf in manifest.get("changed_files", []):
        path = cf.get("path", "")
        cov = cf.get("file_context_coverage_percent", 0)
        if cov is None:
            cov = 0
        cov_ratio = cov / 100.0 if cov > 1 else cov

        if path in governed_code_files and cov_ratio < min_coverage:
            violations.append(f"{path}: {cov_ratio*100:.1f}% < {min_coverage*100:.1f}%")

    if violations:
        print(f"\n❌ CBSP21 GATE FAIL: Coverage below threshold ({min_coverage*100:.0f}%):")
        for v in violations:
            print(f"  - {v}")
        return 1

    # Check diff_articulation for non-trivial changes
    behavior_change = manifest.get("behavior_change", "none")
    if behavior_change != "none":
        diff_art = manifest.get("diff_articulation", {})
        why_not_redundant = diff_art.get("why_not_redundant", "")
        if not why_not_redundant or len(why_not_redundant) < 10:
            print(
                f"\n❌ CBSP21 GATE FAIL: behavior_change='{behavior_change}' requires "
                f"diff_articulation.why_not_redundant explanation"
            )
            return 1

    overall = manifest.get("overall_file_context_coverage", 100)
    print(f"\n✅ CBSP21 GATE PASS: All governed files declared with sufficient coverage.")
    print(f"   Overall file context coverage: {overall}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
