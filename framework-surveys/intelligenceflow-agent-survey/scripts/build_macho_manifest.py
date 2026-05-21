#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Iterable


def run(cmd: list[str]) -> str:
    try:
        proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
    except FileNotFoundError:
        return ""
    return (proc.stdout or proc.stderr).strip()


def candidate_binaries(paths: Iterable[Path]) -> list[Path]:
    out: list[Path] = []
    for path in paths:
        if path.is_file():
            out.append(path)
            continue
        if path.is_dir() and path.suffix == '.framework':
            name = path.stem
            direct = path / name
            versioned = path / 'Versions' / 'A' / name
            for candidate in (direct, versioned):
                if candidate.is_file():
                    out.append(candidate)
                    break
    return sorted(set(out))


def manifest_for(path: Path) -> dict[str, object]:
    st = path.stat()
    sha = run(['shasum', '-a', '256', str(path)])
    return {
        'path': str(path),
        'name': path.name,
        'size': st.st_size,
        'mtime': int(st.st_mtime),
        'sha256': sha.split()[0] if sha else '',
        'file': run(['file', str(path)]),
        'uuid': run(['dwarfdump', '--uuid', str(path)]),
        'dependencies': run(['otool', '-L', str(path)]).splitlines(),
        'load_commands_brief': run(['otool', '-l', str(path)]).splitlines()[:400],
        'build': run(['vtool', '-show-build', str(path)]).splitlines(),
        'defined_external_symbols': run(['nm', '-demangle', '-defined-only', '-extern-only', str(path)]).splitlines()[:1000],
    }


def main() -> int:
    if len(sys.argv) < 2:
        print('usage: build_macho_manifest.py <framework-or-binary> [...]', file=sys.stderr)
        return 2
    paths = [Path(arg).expanduser() for arg in sys.argv[1:]]
    bins = candidate_binaries(paths)
    result = {
        'schema_version': 1,
        'generated_by': 'build_macho_manifest.py',
        'inputs': [str(p) for p in paths],
        'binaries': [manifest_for(p) for p in bins],
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
