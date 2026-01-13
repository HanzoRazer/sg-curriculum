from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

from .config import RuntimeConfig
from .engine import init_runtime, compute_assignment, ingest_session


def main() -> None:
    ap = argparse.ArgumentParser(prog="sgc")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init", help="Initialize local runtime (db + device identity).")

    ap_asg = sub.add_parser("next", help="Generate next assignment for learner slot.")
    ap_asg.add_argument("--slot", type=int, default=1)

    ap_ing = sub.add_parser("ingest-session", help="Ingest a session JSON from stdin or file.")
    ap_ing.add_argument("--slot", type=int, default=1)
    ap_ing.add_argument("--file", type=str, default="")

    args = ap.parse_args()
    cfg = RuntimeConfig.load()

    if args.cmd == "init":
        out = init_runtime(cfg)
        print(json.dumps(out, indent=2))
        return

    if args.cmd == "next":
        out = compute_assignment(cfg, learner_slot=args.slot)
        print(json.dumps(out, indent=2))
        return

    if args.cmd == "ingest-session":
        if args.file:
            payload = json.loads(Path(args.file).read_text(encoding="utf-8"))
        else:
            payload = json.loads(sys.stdin.read())
        out = ingest_session(cfg, payload, learner_slot=args.slot)
        print(json.dumps(out, indent=2))
        return


if __name__ == "__main__":
    main()
