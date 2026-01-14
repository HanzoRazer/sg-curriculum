#!/usr/bin/env python3
import argparse, json, os, re, subprocess, sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

HEX64_RE = re.compile(r"^[0-9a-f]{64}$")

@dataclass
class Violation:
    code: str
    message: str

def run_git(args: List[str], cwd: Path) -> str:
    p = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip() or p.stdout.strip())
    return p.stdout

def changed_files(repo_root: Path, base_ref: str) -> List[str]:
    out = run_git(["diff","--name-only",f"{base_ref}...HEAD"], cwd=repo_root)
    return [x.strip() for x in out.splitlines() if x.strip()]

def read_contracts_version(repo_root: Path) -> Tuple[bool,str]:
    fp = repo_root/"contracts"/"CONTRACTS_VERSION.json"
    if not fp.exists():
        return (False,"")
    data = json.loads(fp.read_text(encoding="utf-8"))
    return (bool(data.get("public_released", False)), str(data.get("tag","") or ""))

def is_schema(p: str) -> bool:
    return p.startswith("contracts/") and p.endswith(".schema.json")

def is_sha(p: str) -> bool:
    return p.startswith("contracts/") and p.endswith(".schema.sha256")

def stem(p: str) -> str:
    name = Path(p).name
    return name.replace(".schema.json","").replace(".schema.sha256","")

def is_v1(p: str) -> bool:
    return bool(re.search(r"_v1\.schema\.(json|sha256)$", p))

def check_sha_format(repo_root: Path) -> List[Violation]:
    v=[]
    for fp in (repo_root/"contracts").glob("*.schema.sha256"):
        raw = fp.read_text(encoding="utf-8").strip()
        if not HEX64_RE.match(raw):
            v.append(Violation("SHA256_FORMAT", f"{fp.as_posix()} must be 64 lowercase hex only"))
    return v

def _extract_added_lines(diff: str) -> str:
    """Extract only added lines from unified diff (no +++ headers)."""
    return "\n".join(
        ln[1:]
        for ln in diff.splitlines()
        if ln.startswith("+") and not ln.startswith("+++ ")
    )

def _stem_mentioned(text: str, stem: str) -> bool:
    """Token-safe match: stem must appear as whole word (not partial)."""
    pat = re.compile(rf"(?<![A-Za-z0-9_]){re.escape(stem)}(?![A-Za-z0-9_])")
    return pat.search(text) is not None

def check_changelog(
    repo_root: Path, changed: List[str], base_ref: str, debug: bool = False
) -> List[Violation]:
    contract_changes = [p for p in changed if is_schema(p) or is_sha(p)]
    if not contract_changes:
        return []
    if "contracts/CHANGELOG.md" not in changed:
        return [Violation("CHANGELOG_REQUIRED","Contract schema/hash changed but contracts/CHANGELOG.md was not updated.")]

    diff = run_git(
        ["diff", f"{base_ref}...HEAD", "--", "contracts/CHANGELOG.md"],
        cwd=repo_root,
    )
    added_only = _extract_added_lines(diff)

    if debug:
        print(
            "\n[contracts-gov][debug] CHANGELOG added lines scanned:\n"
            + (added_only or "<no added lines>"),
            file=sys.stderr,
        )

    stems = sorted({stem(p) for p in contract_changes})
    missing = [s for s in stems if not _stem_mentioned(added_only, s)]

    if missing:
        # Always print scanned content on failure (developer UX)
        if not debug:
            print(
                "\n[contracts-gov][debug] CHANGELOG added lines scanned:\n"
                + (added_only or "<no added lines>"),
                file=sys.stderr,
            )
        return [Violation(
            "CHANGELOG_MISSING_MENTIONS",
            "contracts/CHANGELOG.md added lines must mention each changed contract: " + ", ".join(missing),
        )]
    return []

def check_immutability(repo_root: Path, changed: List[str]) -> List[Violation]:
    public, tag = read_contracts_version(repo_root)
    if not public:
        return []
    touched = [p for p in changed if (is_schema(p) or is_sha(p)) and is_v1(p)]
    if touched:
        return [Violation("V1_IMMUTABLE", f"public_released=true (tag={tag or '<none>'}); v1 immutable: "+", ".join(sorted(touched)))]
    return []

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--base-ref", default="origin/main")
    # Debug defaults: enabled locally, disabled in CI (CI=true)
    default_debug = "CI" not in os.environ
    ap.add_argument(
        "--debug",
        action="store_true",
        default=default_debug,
        help="Print debug information (auto-enabled locally, off in CI unless explicitly set).",
    )
    a = ap.parse_args()
    repo = Path(a.repo_root).resolve()
    try:
        ch = changed_files(repo, a.base_ref)
        violations = []
        violations += check_sha_format(repo)
        violations += check_changelog(repo, ch, a.base_ref, debug=a.debug)
        violations += check_immutability(repo, ch)
    except Exception as e:
        print("[contracts-gov] ERROR:", e, file=sys.stderr)
        return 2
    if not violations:
        print("[contracts-gov] PASS")
        return 0
    print(f"[contracts-gov] FAIL ({len(violations)})", file=sys.stderr)
    for v in violations:
        print(f"  - [{v.code}] {v.message}", file=sys.stderr)
    return 1

if __name__ == "__main__":
    raise SystemExit(main())
