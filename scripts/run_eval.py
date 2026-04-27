"""Run functional test suite (task_suite.yaml). Stub — see VisClick_Detailed_Plan.md Part I."""
from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--suite", type=Path, default=Path("tests/task_suite.yaml"))
    args = ap.parse_args()
    if not args.suite.exists():
        print(f"Create {args.suite} first. Stub exit.")
        return
    print("Stub: run_eval — wire to visclick.bot and log Pass/Fail.")


if __name__ == "__main__":
    main()
