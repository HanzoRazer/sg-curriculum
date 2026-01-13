#!/usr/bin/env python3
import argparse, re, sys
from pathlib import Path

BLOCKED = [
  r"\bgcode\b", r"\btoolpath\b", r"\brmos\b", r"\bfixture\b",
  r"\bfeedrate\b", r"\bspindle\b", r"\bcam\b"
]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=".")
    a = ap.parse_args()
    repo = Path(a.repo_root).resolve()
    contracts = repo/"contracts"
    if not contracts.exists():
        print("[no-toolbox-terms] PASS")
        return 0
    pats = [re.compile(p, re.IGNORECASE) for p in BLOCKED]
    bad=[]
    for fp in contracts.rglob("*"):
        if fp.is_file() and fp.suffix in {".json",".md",".txt"}:
            txt = fp.read_text(encoding="utf-8", errors="replace")
            for p in pats:
                if p.search(txt):
                    bad.append(f"{fp.as_posix()} matched {p.pattern}")
                    break
    if bad:
        print(f"[no-toolbox-terms] FAIL ({len(bad)})", file=sys.stderr)
        for b in bad:
            print("  - "+b, file=sys.stderr)
        return 1
    print("[no-toolbox-terms] PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
