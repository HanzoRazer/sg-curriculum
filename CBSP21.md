# CBSP21 — Complete Boundary-Safe Processing Protocol

**Scope:** sg-curriculum repository  
**Policy Classification:** AI Governance / Quality Control  
**Version:** 1.0  
**Effective Date:** 2026-01-20  
**Owner:** sg-curriculum maintainers  
**Review Cycle:** Annual  

---

## Related Governance Documents

This policy complements and references:

| Document | Purpose |
|----------|---------|
| [.github/copilot-instructions.md](.github/copilot-instructions.md) | AI agent coding guidance, domain boundaries |
| [docs/CURRICULUM_GOVERNANCE_v1.md](docs/CURRICULUM_GOVERNANCE_v1.md) | Contract versioning, change process |
| [docs/COACH_TRACE_POLICY_v1.md](docs/COACH_TRACE_POLICY_v1.md) | LLM trace storage policy |
| [docs/DATA_RETENTION_POLICY_v1.md](docs/DATA_RETENTION_POLICY_v1.md) | Data lifecycle rules |
| [contracts/CHANGELOG.md](contracts/CHANGELOG.md) | Schema change history |

---

## 1. Purpose

CBSP21 defines the **minimum completeness standard** for any AI system or human contributor scanning, reviewing, or modifying sg-curriculum. Its goal is to eliminate *partial-capture errors, hallucinated fill-ins, and scoping drift* by ensuring **≥95% of the source content** is processed before generating outputs.

This policy prevents:
- Misinterpretation caused by partial document review
- Hallucinated or fabricated code/content
- Incomplete refactors that break dependent code
- Patches declared "redundant" when they contain meaningful changes

---

## 2. Core Principle

> **Do not reason from partial inputs.**  
> **Do not generate, modify, or implement code until ≥95% of the relevant source has been fully scanned and verified.**

---

## 3. Scope

CBSP21 applies when:
- AI agents scan, review, summarize, refactor, or generate code
- Human contributors submit PRs modifying governed areas
- Automated systems process curriculum content

### 3.1 Governed Areas in sg-curriculum

| Area | Path | Description |
|------|------|-------------|
| Coaching Engine | `src/sg_coach/` | Evaluation engine, domain models |
| Groove Layer | `src/sg_groove/` | Accompaniment adaptation system |
| Runtime | `runtime/` | CLI runtime, database, identity |
| Contracts | `contracts/` | JSON schemas (immutable after release) |
| Tests | `tests/` | Test suite |
| Fixtures | `fixtures/` | Test vectors and expected outputs |
| CI Scripts | `scripts/ci/` | Governance enforcement |

---

## 4. Coverage Requirement

### 4.1 Required Minimum

The system/contributor must:
- Attempt to process **100% of the provided content**
- Confirm **no less than 95% actual coverage** before proceeding

### 4.2 Prohibited Actions

The system/contributor must NOT:
- Generate conclusions from excerpts
- Fill in gaps based on probability or inference
- Treat missing sections as irrelevant
- Execute or produce runnable code from partial extracts
- Declare patches "redundant" without proof
- Guess missing content
- Act on incomplete scans

---

## 5. Verification Procedure

### 5.1 Unit Enumeration

All relevant units must be identified:
- Files in scope
- Functions/classes modified
- Contracts referenced

### 5.2 Coverage Measurement

```
coverage = scanned_bytes / total_bytes
```

### 5.3 Coverage Confirmation

Output may proceed **only if**:

```
coverage >= 0.95
```

### 5.4 Audit Logging

Systems must log one of:

```
CBSP21 Coverage Confirmed: 97.3%
CBSP21 Coverage Failure: 83.4% — Output Halted
```

---

## 6. Mandatory Stop Conditions

The system MUST **immediately stop and request clarification** when:

- Content appears truncated
- Code blocks are incomplete
- A file reference is listed but content not present
- A fence marker ``` is opened but not closed
- Coverage cannot reach ≥95%
- Missing dependency content

**Failure to meet coverage = NO OUTPUT.**

The only allowed response is a request for the missing content.

---

## 7. Safety & Boundary Rules

1. **Never invent missing code or text**
2. **Never assume omitted content is irrelevant**
3. **Never merge partial fragments into runnable logic**
4. **Never treat commentary-embedded code as authoritative unless structured**
5. **Respect domain boundaries** — sg-curriculum does NOT own CAM/toolpaths/G-code/RMOS (see copilot-instructions.md)

---

## 8. Structured Input Format

### 8.1 Preferred Input Structure

To reduce scan ambiguity, prefer:
- Full file contents
- Unified diffs
- Fenced blocks with declared paths:

```
FILE: src/sg_coach/models.py
<full content>
```

### 8.2 Patch Packet Format

When submitting code changes, use this structure:

```
FILE: path/to/file.py
```python
# Full file content or complete diff
def example():
    pass
```
```

**Requirements:**
- At least one `FILE: ` header per packet
- Balanced triple-backtick fences
- No `...` placeholders inside code fences

### 8.3 Immutable Ground Truth

The `cbsp21/full_source/` directory (when present) represents **authoritative, immutable content**:

- **MUST NOT** be modified by AI systems
- Only human-controlled processes may update it
- All coverage calculations treat it as read-only

---

## 9. Output Timing

Output may only be produced **after ALL of the following are true:**

- Coverage ≥ 95%
- No unresolved missing content
- No unclosed code blocks
- No skipped embedded code regions
- All STOP CONDITIONS cleared

---

## 10. Integrity Guarantees

CBSP21 ensures:

- Deterministic processing
- No accidental truncation
- No hallucinated code fill-ins
- Stable reproducibility
- Clear safety boundaries

---

## 11. Audit Statement Format

When output is produced, include:

```
CBSP21 Coverage: 98.2% — All completeness conditions satisfied.
```

If coverage is below threshold:

```
CBSP21 Coverage: 83.5% — Output prohibited. Please provide remaining content.
```

---

## 12. Compliance & Enforcement

Failure to comply with this policy may result in:

- PR rejection by CI gates
- Output rejection by AI systems
- Required re-scan with complete content

---

## 13. Roles & Responsibilities

| Role | Responsibility |
|------|----------------|
| **Maintainers** | Ensure CI gates are configured |
| **Contributors** | Include patch manifests for code changes |
| **AI Agents** | Verify coverage before generating output |
| **CI System** | Enforce coverage and manifest requirements |

---

## 14. Exceptions

Exceptions require:
- Documented justification in PR description
- Explicit maintainer approval
- Entry in `.cbsp21/exemptions.json` if recurring

---

## 15. Reusable Guardrail Instruction

Paste this where AI agents need the directive:

> **Scan the provided {document | file | folder | path} completely in accordance with protocol `CBSP21.md`. You must process no less than 95% of the total informational content before producing conclusions, summaries, or transformations. If any portion of the source cannot be scanned, stop and request clarification rather than assuming or inferring missing content.**

---

## 16. Implementation Scripts

### 16.1 Coverage Check Script

**Path:** `scripts/cbsp21/cbsp21_coverage_check.py`

```python
#!/usr/bin/env python
"""
CBSP21 Coverage Check for sg-curriculum

Usage:
    python scripts/cbsp21/cbsp21_coverage_check.py \
        --full-path cbsp21/full_source \
        --scanned-path cbsp21/scanned_source \
        --threshold 0.95
"""

import argparse
from pathlib import Path


def total_bytes_in_dir(root: Path) -> int:
    """Sum bytes of all regular files under a directory (recursive)."""
    return sum(
        f.stat().st_size
        for f in root.rglob("*")
        if f.is_file()
    )


def compute_bytes(path: Path) -> int:
    """Return total bytes for a file or a directory."""
    if path.is_file():
        return path.stat().st_size
    if path.is_dir():
        return total_bytes_in_dir(path)
    raise ValueError(f"Path not found: {path}")


def main() -> int:
    ap = argparse.ArgumentParser(description="CBSP21 Coverage Check")
    ap.add_argument("--full-path", required=True)
    ap.add_argument("--scanned-path", required=True)
    ap.add_argument("--threshold", type=float, default=0.95)
    args = ap.parse_args()

    full = Path(args.full_path)
    scanned = Path(args.scanned_path)

    if not full.exists():
        raise SystemExit(f"Full path does not exist: {full}")
    if not scanned.exists():
        raise SystemExit(f"Scanned path does not exist: {scanned}")

    if full.is_file() != scanned.is_file():
        raise SystemExit("CBSP21 ERROR: full-path and scanned-path must both be files or both be directories.")

    full_bytes = compute_bytes(full)
    scanned_bytes = compute_bytes(scanned)

    if not full_bytes:
        raise SystemExit("CBSP21 ERROR: full source appears empty.")

    coverage = scanned_bytes / full_bytes
    percent = coverage * 100

    print(f"CBSP21 Coverage: {percent:.2f}%")
    print(f"  full_bytes   = {full_bytes}")
    print(f"  scanned_bytes= {scanned_bytes}")
    print(f"  threshold    = {args.threshold * 100:.2f}%")

    if coverage < args.threshold:
        print("CBSP21 FAIL: Coverage below threshold. Output prohibited.")
        return 1

    print("CBSP21 PASS: Coverage requirement satisfied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

### 16.2 Coverage with Audit Log

**Path:** `scripts/cbsp21/cbsp21_coverage_with_audit.py`

```python
#!/usr/bin/env python
"""
CBSP21 Coverage & Audit Logger for sg-curriculum

Usage:
    python scripts/cbsp21/cbsp21_coverage_with_audit.py \
        --full cbsp21/full_source \
        --scanned cbsp21/scanned_source \
        --threshold 0.95 \
        --log logs/cbsp21_audit.jsonl
"""

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


def total_bytes_in_dir(root: Path) -> int:
    return sum(f.stat().st_size for f in root.rglob("*") if f.is_file())


def compute_bytes(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    if path.is_dir():
        return total_bytes_in_dir(path)
    raise ValueError(f"Path not found: {path}")


def audit_record(
    *,
    full: Path,
    scanned: Path,
    full_bytes: int,
    scanned_bytes: int,
    coverage: float,
    threshold: float,
    status: str,
) -> Dict[str, Any]:
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "policy": "CBSP21",
        "repo": "sg-curriculum",
        "full_path": str(full),
        "scanned_path": str(scanned),
        "full_bytes": full_bytes,
        "scanned_bytes": scanned_bytes,
        "coverage_ratio": coverage,
        "repo_coverage_percent": round(coverage * 100, 2),
        "threshold": threshold,
        "status": status,
        "ci": {
            "github_run_id": os.getenv("GITHUB_RUN_ID"),
            "github_sha": os.getenv("GITHUB_SHA"),
            "github_ref": os.getenv("GITHUB_REF"),
        },
    }


def append_jsonl(path: Path, rec: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", required=True)
    ap.add_argument("--scanned", required=True)
    ap.add_argument("--threshold", type=float, default=0.95)
    ap.add_argument("--log", required=True)
    args = ap.parse_args()

    full = Path(args.full)
    scanned = Path(args.scanned)
    log = Path(args.log)

    if not full.exists():
        print(f"CBSP21 FAIL: full path missing: {full}")
        rec = audit_record(full=full, scanned=scanned, full_bytes=0, scanned_bytes=0,
                           coverage=0.0, threshold=args.threshold, status="fail")
        append_jsonl(log, rec)
        return 1

    if not scanned.exists():
        print(f"CBSP21 FAIL: scanned path missing: {scanned}")
        rec = audit_record(full=full, scanned=scanned, full_bytes=compute_bytes(full), scanned_bytes=0,
                           coverage=0.0, threshold=args.threshold, status="fail")
        append_jsonl(log, rec)
        return 1

    if full.is_file() != scanned.is_file():
        print("CBSP21 FAIL: full and scanned must both be files or both be directories.")
        return 1

    full_bytes = compute_bytes(full)
    scanned_bytes = compute_bytes(scanned)

    if not full_bytes:
        print("CBSP21 FAIL: full source empty.")
        return 1

    coverage = scanned_bytes / full_bytes
    percent = coverage * 100

    print(f"CBSP21 Coverage: {percent:.2f}% (threshold {args.threshold * 100:.2f}%)")

    status = "pass" if coverage >= args.threshold else "fail"
    rec = audit_record(
        full=full, scanned=scanned,
        full_bytes=full_bytes, scanned_bytes=scanned_bytes,
        coverage=coverage, threshold=args.threshold, status=status,
    )
    append_jsonl(log, rec)

    if status == "fail":
        print("CBSP21 FAIL: Coverage below threshold. Output prohibited.")
        return 1

    print("CBSP21 PASS: Coverage requirement satisfied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

### 16.3 Patch Packet Format Validator

**Path:** `scripts/cbsp21/check_patch_packet_format.py`

```python
#!/usr/bin/env python
"""
CBSP21 Patch Packet Format Validator for sg-curriculum

Validates that patch packets are structured and safe to scan:
- Must include at least one line starting with "FILE: "
- Code fences (```) must be balanced
- Disallow "..." placeholder inside code fences

Usage:
    python scripts/cbsp21/check_patch_packet_format.py --glob "cbsp21/patch_packets/**/*.*"
"""

import argparse
import glob
from pathlib import Path


def balanced_fences(text: str) -> bool:
    return text.count("```") % 2 == 0


def has_file_headers(text: str) -> bool:
    return any(line.startswith("FILE: ") for line in text.splitlines())


def has_ellipsis_inside_code_fence(text: str) -> bool:
    in_fence = False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence and line.strip() == "...":
            return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--glob", required=True, help="Glob of packet files to validate.")
    ap.add_argument("--disallow-ellipsis-in-code", action="store_true", default=True)
    args = ap.parse_args()

    files = [Path(p) for p in glob.glob(args.glob, recursive=True)]
    files = [p for p in files if p.is_file()]

    if not files:
        print("CBSP21 Patch Packet: no files matched; skipping.")
        return 0

    failed = False

    for path in files:
        txt = path.read_text(encoding="utf-8", errors="ignore")

        if not has_file_headers(txt):
            print(f"CBSP21 PATCH FAIL: Missing FILE headers in {path}")
            failed = True

        if not balanced_fences(txt):
            print(f"CBSP21 PATCH FAIL: Unbalanced ``` fences in {path}")
            failed = True

        if args.disallow_ellipsis_in_code and has_ellipsis_inside_code_fence(txt):
            print(f"CBSP21 PATCH FAIL: Found '...' placeholder inside code fence in {path}")
            failed = True

    if failed:
        return 1

    print("CBSP21 Patch Packet: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

---

## 17. PR Gate Script

**Path:** `scripts/ci/check_cbsp21_gate.py`

```python
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
            capture_output=True, text=True, check=True
        )
        return [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
    except subprocess.CalledProcessError:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1"],
            capture_output=True, text=True, check=True
        )
        return [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]


def is_governed_file(path: str) -> bool:
    """Check if file is in a governed area."""
    return any(path.startswith(gp) for gp in GOVERNED_PATHS)


def is_code_file(path: str) -> bool:
    """Check if file is a code file."""
    code_exts = {".py", ".json", ".yaml", ".yml", ".sh", ".ps1"}
    return Path(path).suffix.lower() in code_exts


def main() -> int:
    min_coverage = float(os.getenv("CBSP21_MIN_COVERAGE", "0.95"))
    manifest_path = Path(os.getenv("CBSP21_MANIFEST_PATH", ".cbsp21/patch_input.json"))

    changed_files = get_changed_files()
    governed_code_files = [f for f in changed_files if is_governed_file(f) and is_code_file(f)]

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

    overall = manifest.get("overall_file_context_coverage", 100)
    print(f"\n✅ CBSP21 GATE PASS: All governed files declared with sufficient coverage.")
    print(f"   Overall file context coverage: {overall}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

---

## 18. CI Workflows

### 18.1 Coverage Gate Workflow

**Path:** `.github/workflows/cbsp21_coverage_gate.yml`

```yaml
name: CBSP21 Coverage Gate

on:
  pull_request:
    paths:
      - "cbsp21/**"
      - "scripts/cbsp21/**"
  push:
    branches: [main]
    paths:
      - "cbsp21/**"
      - "scripts/cbsp21/**"

jobs:
  cbsp21-coverage:
    runs-on: ubuntu-latest

    env:
      CBSP21_THRESHOLD: "0.95"

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: CBSP21 Coverage + Audit
        run: |
          python scripts/cbsp21/cbsp21_coverage_with_audit.py \
            --full cbsp21/full_source \
            --scanned cbsp21/scanned_source \
            --threshold $CBSP21_THRESHOLD \
            --log logs/cbsp21_audit.jsonl

      - name: Upload audit log
        uses: actions/upload-artifact@v4
        with:
          name: cbsp21_audit
          path: logs/cbsp21_audit.jsonl
```

### 18.2 PR Gate Workflow

**Path:** `.github/workflows/cbsp21_pr_gate.yml`

```yaml
name: CBSP21 PR Gate

on:
  pull_request:
    paths:
      - "src/**"
      - "runtime/**"
      - "contracts/**"
      - "tests/**"
      - "fixtures/**"
      - "scripts/ci/**"

jobs:
  cbsp21-pr-gate:
    runs-on: ubuntu-latest

    env:
      CBSP21_MIN_COVERAGE: "0.95"
      CBSP21_MANIFEST_PATH: ".cbsp21/patch_input.json"

    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: CBSP21 PR Gate Check
        run: python scripts/ci/check_cbsp21_gate.py
```

### 18.3 Patch Packet Format Workflow

**Path:** `.github/workflows/cbsp21_patch_format.yml`

```yaml
name: CBSP21 Patch Packet Format

on:
  pull_request:
    paths:
      - "cbsp21/patch_packets/**"

jobs:
  cbsp21-patch-format:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Validate patch packets
        run: |
          python scripts/cbsp21/check_patch_packet_format.py \
            --glob "cbsp21/patch_packets/**/*.*" \
            --disallow-ellipsis-in-code
```

---

## 19. Patch Input Manifest

### 19.1 Location

Every non-trivial change MUST include a manifest at:

```
.cbsp21/patch_input.json
```

### 19.2 Required Fields (v1)

```json
{
  "schema_version": "cbsp21_patch_input_v1",
  "patch_id": "GROOVE_V0_IMPL",
  "title": "Implement Groove Layer v0",
  "intent": "Add accompaniment adaptation engine with window evaluation and control output.",
  "change_type": "code",
  "behavior_change": "compatible",
  "risk_level": "medium",
  "scope": {
    "paths_in_scope": ["src/sg_groove/", "tests/", "fixtures/groove_v0/"],
    "files_expected_to_change": [
      "src/sg_groove/models.py",
      "src/sg_groove/window_eval.py",
      "src/sg_groove/groove_layer.py",
      "tests/test_groove_v0.py"
    ]
  },
  "diff_range": {
    "base": "origin/main",
    "head": "HEAD"
  },
  "changed_files_count": 4,
  "changed_files_exact": [
    "src/sg_groove/models.py",
    "src/sg_groove/window_eval.py",
    "src/sg_groove/groove_layer.py",
    "tests/test_groove_v0.py"
  ],
  "changed_files": [
    {
      "path": "src/sg_groove/models.py",
      "action": "add",
      "scanned_sources": ["docs/groove_layer_spec.md", "contracts/groove_layer_control_v0.schema.json"],
      "file_context_coverage_percent": 100.0
    }
  ],
  "diff_articulation": {
    "what_changed": [
      "Added PerformanceEvent dataclass for event input",
      "Added EngineContext for tempo/time-signature context",
      "Added WindowStats for per-window statistics",
      "Added GrooveState for latent state tracking",
      "Added compute_window_stats() for evidence extraction",
      "Added GrooveLayer class with update_window() method"
    ],
    "why_not_redundant": "No prior implementation existed. This is net-new code implementing the v0 spec."
  },
  "verification": {
    "commands_run": ["pytest tests/test_groove_v0.py -v"]
  },
  "overall_file_context_coverage": 100.0
}
```

### 19.3 Example Template

**Path:** `.cbsp21/patch_input.json.example`

```json
{
  "schema_version": "cbsp21_patch_input_v1",
  "patch_id": "EXAMPLE_PATCH",
  "title": "Short descriptive title",
  "intent": "1-3 sentences explaining what this change accomplishes.",
  "change_type": "code|docs|ci|mixed",
  "behavior_change": "none|compatible|breaking",
  "risk_level": "low|medium|high",
  "scope": {
    "paths_in_scope": ["src/sg_coach/"],
    "files_expected_to_change": ["src/sg_coach/models.py"]
  },
  "diff_range": {
    "base": "origin/main",
    "head": "HEAD"
  },
  "changed_files_count": 1,
  "changed_files_exact": ["src/sg_coach/models.py"],
  "changed_files": [
    {
      "path": "src/sg_coach/models.py",
      "action": "modify",
      "scanned_sources": ["src/sg_coach/coach_policy.py", "tests/test_coach_policy.py"],
      "file_context_coverage_percent": 97.0
    }
  ],
  "diff_articulation": {
    "what_changed": ["Added new field X to SessionRecord"],
    "why_not_redundant": "Field X is required for feature Y, no existing field serves this purpose."
  },
  "verification": {
    "commands_run": ["pytest tests/test_coach_policy.py -v"]
  },
  "overall_file_context_coverage": 97.0,
  "notes": "Optional additional context."
}
```

---

## 20. Diff Review Gate

### 20.1 When Required

| Risk Level | Trigger | Requirement |
|------------|---------|-------------|
| **Low** | Pure additions (new files) | No diff review required |
| **Medium** | Modifications to existing functions | Show diff, confirm |
| **High** | Changes to guards, control flow, thresholds | Show diff + explain impact |

### 20.2 Redundancy Check Protocol

Before declaring a patch "REDUNDANT", verify:

1. **Keyword scan**: Function/variable names exist
2. **Functional equivalence**: Behavior matches, not just presence
3. **Coverage analysis**: Feature is complete, no gaps

### 20.3 Pre-Commit Checklist for Behavior Changes

```markdown
## Pre-Commit Review

- [ ] Diff shown (not just described)
- [ ] Behavior change explained
- [ ] Impact on existing workflows documented
- [ ] Approval received

If guard/restriction added:
- [ ] Existing functionality preserved OR explicitly deprecated
- [ ] Fallback behavior documented
```

---

## 21. Exemptions

### 21.1 Exempt Patterns

Add to `.cbsp21/exemptions.json`:

```json
{
  "exempt_patterns": [
    "docs/**",
    "*.md",
    "**/__pycache__/**"
  ]
}
```

### 21.2 Emergency Hotfixes

Emergency hotfixes may skip manifest but require:
- Post-merge audit within 24 hours
- Entry in `.cbsp21/incident_log.json`

---

## 22. Repo Layout

```
sg-curriculum/
├── .cbsp21/
│   ├── patch_input.json          # Current PR manifest
│   ├── patch_input.json.example  # Template
│   ├── exemptions.json           # Exempt patterns
│   └── incident_log.json         # Post-hoc audits
├── cbsp21/
│   ├── full_source/              # Immutable ground truth
│   ├── scanned_source/           # Scanned representation
│   └── patch_packets/            # Structured FILE: packets
├── logs/
│   └── cbsp21_audit.jsonl        # Audit log
└── scripts/
    └── cbsp21/
        ├── cbsp21_coverage_check.py
        ├── cbsp21_coverage_with_audit.py
        └── check_patch_packet_format.py
```

---

## 23. Revision History

| Rev | Date | Notes |
|-----|------|-------|
| 1.0 | 2026-01-20 | Initial release for sg-curriculum. Tailored from CBSP21 general policy. Removed ToolBox-specific references. Added governed areas specific to this repo. Integrated with existing governance documents. |

---

**End of CBSP21 for sg-curriculum**
