#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    data = json.loads(path.read_text())
    return data


def manifest_shape(data: Any) -> str:
    if isinstance(data, dict):
        if isinstance(data.get("symbols"), list):
            return "symbols"
        if isinstance(data.get("records"), list):
            return "records"
    if isinstance(data, list):
        return "list"
    return "unknown"


def load_symbols(path: Path, *, status: str | None) -> tuple[set[str], str]:
    data = load_json(path)
    shape = manifest_shape(data)
    symbols: set[str] = set()

    if isinstance(data, dict) and isinstance(data.get("symbols"), list):
        for item in data["symbols"]:
            if isinstance(item, str):
                symbols.add(item)
            elif isinstance(item, dict) and "symbol" in item:
                symbols.add(str(item["symbol"]))

    if isinstance(data, dict) and isinstance(data.get("records"), list):
        for item in data["records"]:
            if not isinstance(item, dict) or "name" not in item:
                continue
            if status and str(item.get("status", "")) != status:
                continue
            symbols.add(str(item["name"]))

    if isinstance(data, list):
        for item in data:
            if isinstance(item, str):
                symbols.add(item)
            elif isinstance(item, dict):
                if "symbol" in item:
                    symbols.add(str(item["symbol"]))
                elif "name" in item and (not status or str(item.get("status", "")) == status):
                    symbols.add(str(item["name"]))

    return symbols, shape


def cap(values: list[str], limit: int) -> tuple[list[str], int]:
    if limit <= 0 or len(values) <= limit:
        return values, 0
    return values[:limit], len(values) - limit


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Diff two private-framework symbol manifests or dlopen probe summaries. "
            "Inputs may be strings, {symbol: ...} entries, {name/status: ...} records, "
            "or dictionaries containing symbols[]/records[]."
        )
    )
    parser.add_argument("old", type=Path)
    parser.add_argument("new", type=Path)
    parser.add_argument(
        "--status",
        default=None,
        help="For probe-summary records, include only records with this status, for example 'present'.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum added/removed names rendered in stdout. Use 0 for complete lists.",
    )
    args = parser.parse_args()

    old, old_shape = load_symbols(args.old, status=args.status)
    new, new_shape = load_symbols(args.new, status=args.status)
    added = sorted(new - old)
    removed = sorted(old - new)
    rendered_added, added_omitted = cap(added, args.limit)
    rendered_removed, removed_omitted = cap(removed, args.limit)

    report = {
        "old": str(args.old),
        "new": str(args.new),
        "old_shape": old_shape,
        "new_shape": new_shape,
        "status_filter": args.status,
        "added": rendered_added,
        "added_count": len(added),
        "added_omitted": added_omitted,
        "removed": rendered_removed,
        "removed_count": len(removed),
        "removed_omitted": removed_omitted,
        "common_count": len(old & new),
        "old_count": len(old),
        "new_count": len(new),
    }
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
