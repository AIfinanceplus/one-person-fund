from __future__ import annotations

import argparse
import json

from backend.orchestration.demo import run_demo
from backend.orchestration.full_run import run_full_demo
from backend.orchestration.modes import run_paper, run_replay
from backend.orchestration.persistent import run_persistent_demo


def main() -> None:
    parser = argparse.ArgumentParser(description="Rates Fund OS command line")
    parser.add_argument("command", choices=("demo", "full-demo", "persistent-demo", "replay", "paper"), nargs="?", default="demo")
    parser.add_argument("--db", default="data/runtime/rates-fund.sqlite3")
    parser.add_argument("--fixture", default="data/fixtures/curve_demo.json")
    parser.add_argument("--snapshot", default=None)
    args = parser.parse_args()
    if args.command == "demo":
        print(json.dumps(run_demo(), indent=2, default=str))
    elif args.command == "full-demo":
        print(json.dumps(run_full_demo(), indent=2, default=str))
    elif args.command == "persistent-demo":
        from pathlib import Path
        Path(args.db).parent.mkdir(parents=True, exist_ok=True)
        print(json.dumps(run_persistent_demo(args.db), indent=2, default=str))
    elif args.command == "replay":
        print(json.dumps(run_replay(args.fixture), indent=2, default=str))
    elif args.command == "paper":
        if not args.snapshot:
            parser.error("paper requires --snapshot PATH with confirmed market data")
        print(json.dumps(run_paper(args.snapshot), indent=2, default=str))


if __name__ == "__main__":
    main()
