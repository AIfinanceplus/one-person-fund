from __future__ import annotations

import argparse
import json

from backend.orchestration.demo import run_demo
from backend.orchestration.persistent import run_persistent_demo


def main() -> None:
    parser = argparse.ArgumentParser(description="Rates Fund OS command line")
    parser.add_argument("command", choices=("demo", "persistent-demo"), nargs="?", default="demo")
    parser.add_argument("--db", default="data/runtime/rates-fund.sqlite3")
    args = parser.parse_args()
    if args.command == "demo":
        print(json.dumps(run_demo(), indent=2, default=str))
    elif args.command == "persistent-demo":
        from pathlib import Path
        Path(args.db).parent.mkdir(parents=True, exist_ok=True)
        print(json.dumps(run_persistent_demo(args.db), indent=2, default=str))


if __name__ == "__main__":
    main()
