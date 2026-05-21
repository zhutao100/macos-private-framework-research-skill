#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) < 2:
        print('usage: normalize_observations.py <observation-yaml-or-text> [...]', file=sys.stderr)
        return 2
    rows: list[dict[str, object]] = []
    for arg in sys.argv[1:]:
        p = Path(arg).expanduser()
        rows.append({
            'path': str(p),
            'exists': p.exists(),
            'size': p.stat().st_size if p.exists() else None,
            'suffix': p.suffix,
            'text_preview': p.read_text(errors='replace')[:2000] if p.exists() and p.is_file() else '',
        })
    print(json.dumps({'schema_version': 1, 'observations': rows}, indent=2, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
