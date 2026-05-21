#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
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
        elif path.is_dir():
            for candidate in sorted(path.glob('IntelligenceFlow*')):
                if candidate.is_file() and candidate.suffix in ('', '.dylib'):
                    out.append(candidate)
                elif candidate.is_dir() and candidate.suffix == '.framework':
                    out.extend(candidate_binaries([candidate]))
    return sorted(set(out))


def limited_lines(text: str, limit: int) -> dict[str, object]:
    lines = text.splitlines()
    if limit < 0:
        rendered = lines
    else:
        rendered = lines[:limit]
    return {
        'lines': rendered,
        'total_count': len(lines),
        'rendered_count': len(rendered),
        'truncated': limit >= 0 and len(lines) > limit,
    }


def otool_dependency_text(text: str) -> str:
    lines = text.splitlines()
    if lines and lines[0].endswith(':'):
        lines = lines[1:]
    return '\n'.join(lines)


def manifest_for(path: Path, args: argparse.Namespace) -> dict[str, object]:
    st = path.stat()
    sha = run(['shasum', '-a', '256', str(path)])
    dependencies = run(['otool', '-L', str(path)])
    load_commands = run(['otool', '-l', str(path)]) if args.include_load_commands else ""
    symbols = run(['nm', '-gjU', str(path)])
    strings = ""
    if args.string_pattern:
        strings = run(['/bin/sh', '-c', 'strings -a "$1" | grep -E -i "$2" | sort -u', 'sh', str(path), args.string_pattern])
    return {
        'path': str(path),
        'name': path.name,
        'size': st.st_size,
        'mtime': int(st.st_mtime),
        'sha256': sha.split()[0] if sha else '',
        'file': run(['file', str(path)]),
        'uuid': run(['dwarfdump', '--uuid', str(path)]),
        'dependencies': limited_lines(otool_dependency_text(dependencies), args.dependency_limit),
        'load_commands_brief': limited_lines(load_commands, args.load_command_limit),
        'build': run(['vtool', '-show-build', str(path)]).splitlines(),
        'defined_external_symbols': limited_lines(symbols, args.symbol_limit),
        'focused_strings': limited_lines(strings, args.string_limit),
    }


def write_markdown(result: dict[str, object], output: Path) -> None:
    lines = [
        '# IntelligenceFlow Mach-O Manifest',
        '',
        f"Inputs: `{len(result['inputs'])}`",
        f"Binaries: `{len(result['binaries'])}`",
        '',
        '| Binary | Size | UUID | Deps | Symbols |',
        '|---|---:|---|---:|---:|',
    ]
    for binary in result['binaries']:
        uuid_text = str(binary.get('uuid', '')).replace('\n', ' ')
        uuid_parts = uuid_text.split()
        uuid = uuid_parts[1] if len(uuid_parts) > 1 and uuid_parts[0] == 'UUID:' else uuid_text
        deps = binary.get('dependencies', {})
        symbols = binary.get('defined_external_symbols', {})
        lines.append(
            f"| `{binary['name']}` | {binary['size']} | `{uuid}` | "
            f"{deps.get('total_count', 0)} | {symbols.get('total_count', 0)} |"
        )
    lines.append('')
    lines.append('JSON output contains capped dependency, load-command, symbol, and focused-string details with truncation flags.')
    output.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main() -> int:
    parser = argparse.ArgumentParser(description='Build a capped Mach-O manifest for IntelligenceFlow binaries.')
    parser.add_argument('paths', nargs='+', help='Framework directories, flat extracted binaries, or directories containing either.')
    parser.add_argument('--output', type=Path, help='Write JSON to this path instead of stdout.')
    parser.add_argument('--markdown-output', type=Path, help='Write a compact Markdown summary.')
    parser.add_argument('--dependency-limit', type=int, default=120)
    parser.add_argument('--symbol-limit', type=int, default=300)
    parser.add_argument('--load-command-limit', type=int, default=0)
    parser.add_argument('--string-limit', type=int, default=120)
    parser.add_argument('--string-pattern', default='intelligenceflow|intelligencecontext|orchestrator|planner|context|transcript|biome|tool|appintent|foundationmodels|privatecloudcompute|shortcut|spotlight|assistant|siri')
    parser.add_argument('--include-load-commands', action='store_true')
    args = parser.parse_args()

    paths = [Path(arg).expanduser() for arg in args.paths]
    bins = candidate_binaries(paths)
    result = {
        'schema_version': 1,
        'generated_by': 'build_macho_manifest.py',
        'inputs': [str(p) for p in paths],
        'binaries': [manifest_for(p, args) for p in bins],
    }
    if args.markdown_output:
        write_markdown(result, args.markdown_output)
    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        args.output.write_text(text + '\n', encoding='utf-8')
    else:
        print(text)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
