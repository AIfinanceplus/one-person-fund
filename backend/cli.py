from __future__ import annotations

import argparse
import json

from backend.orchestration.demo import run_demo


def main() -> None:
    parser = argparse.ArgumentParser(description="Rates Fund OS command line")
    parser.add_argument("command", choices=("demo",), nargs="?", default="demo")
    args = parser.parse_args()
    if args.command == "demo":
        print(json.dumps(run_demo(), indent=2, default=str))


if __name__ == "__main__":
    main()
