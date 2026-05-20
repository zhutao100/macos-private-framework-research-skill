#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

SYMBOL_RE = re.compile(
    r"\b(?:SLS[A-Za-z0-9_]*|SLPS[A-Za-z0-9_]*|_SLPS[A-Za-z0-9_]*|"
    r"CGS[A-Za-z0-9_]*|SLEvent[A-Za-z0-9_]*|SLSEvent[A-Za-z0-9_]*|"
    r"AX[A-Za-z0-9_]*|_AX[A-Za-z0-9_]*|CGEvent[A-Za-z0-9_]*)\b"
)
TEXT_SUFFIXES = {".swift", ".m", ".mm", ".h", ".c", ".cc", ".cpp", ".rs", ".md", ".mdx", ".txt"}


def iter_files(root: Path):
    if root.is_file():
        yield root
        return
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
            yield path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract SkyLight-adjacent symbol-name references from source/text trees."
    )
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()

    records: dict[str, dict[str, object]] = {}
    for root in args.paths:
        base = root if root.is_dir() else root.parent
        for path in iter_files(root):
            try:
                text = path.read_text(errors="ignore")
            except OSError:
                continue
            rel = path.relative_to(base).as_posix() if path.is_relative_to(base) else str(path)
            for match in SYMBOL_RE.finditer(text):
                sym = match.group(0)
                rec = records.setdefault(sym, {"symbol": sym, "count": 0, "source_paths": set()})
                rec["count"] = int(rec["count"]) + 1
                rec["source_paths"].add(rel)  # type: ignore[union-attr]

    output = {
        "schema_version": 1,
        "symbols": [
            {"symbol": sym, "count": rec["count"], "source_paths": sorted(rec["source_paths"])}
            for sym, rec in sorted(records.items())
        ],
    }
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
