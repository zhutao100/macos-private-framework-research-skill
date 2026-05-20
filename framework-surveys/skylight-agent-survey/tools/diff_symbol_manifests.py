#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_symbols(path: Path) -> set[str]:
    data = json.loads(path.read_text())
    items = data.get("symbols", [])
    return {str(item["symbol"]) for item in items if "symbol" in item}


def main() -> None:
    parser = argparse.ArgumentParser(description="Diff two SkyLight symbol manifests.")
    parser.add_argument("old", type=Path)
    parser.add_argument("new", type=Path)
    args = parser.parse_args()

    old = load_symbols(args.old)
    new = load_symbols(args.new)

    report = {
        "old": str(args.old),
        "new": str(args.new),
        "added": sorted(new - old),
        "removed": sorted(old - new),
        "common_count": len(old & new),
        "old_count": len(old),
        "new_count": len(new),
    }
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
