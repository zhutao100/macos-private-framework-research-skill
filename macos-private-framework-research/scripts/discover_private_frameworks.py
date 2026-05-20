#!/usr/bin/env python3
"""Discover private frameworks linked by macOS app bundles or Mach-O binaries."""

from __future__ import annotations

import argparse
import json
import os
import plistlib
import re
import stat
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

PRIVATE_FRAMEWORK_RE = re.compile(r"(/System/Library/PrivateFrameworks/([^/]+)\.framework/[^\s]*)")
PUBLIC_FRAMEWORK_RE = re.compile(r"(/System/Library/Frameworks/([^/]+)\.framework/[^\s]*)")
DYLIB_RE = re.compile(r"\s+([^\s]+) \(compatibility version")

COMMON_APP_SUBDIRS = [
    "Contents/MacOS",
    "Contents/Frameworks",
    "Contents/PlugIns",
    "Contents/XPCServices",
    "Contents/Library/LoginItems",
    "Contents/Library/LaunchServices",
    "Contents/Helpers",
]


@dataclass
class CommandResult:
    command: list[str]
    returncode: int | None
    stdout: str
    stderr: str


def run_command(command: list[str], timeout: int = 15) -> CommandResult:
    try:
        proc = subprocess.run(
            command,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
        return CommandResult(command, proc.returncode, proc.stdout.strip(), proc.stderr.strip())
    except FileNotFoundError:
        return CommandResult(command, None, "", "command not found")
    except subprocess.TimeoutExpired as exc:
        stdout = (
            exc.stdout.decode(errors="replace")
            if isinstance(exc.stdout, bytes)
            else (exc.stdout or "")
        )
        stderr = (
            exc.stderr.decode(errors="replace")
            if isinstance(exc.stderr, bytes)
            else (exc.stderr or "")
        )
        return CommandResult(command, None, stdout.strip(), f"timeout: {stderr}".strip())


def is_probably_macho(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            magic = handle.read(4)
    except OSError:
        return False
    macho_magics = {
        b"\xfe\xed\xfa\xce",
        b"\xce\xfa\xed\xfe",
        b"\xfe\xed\xfa\xcf",
        b"\xcf\xfa\xed\xfe",
        b"\xca\xfe\xba\xbe",
        b"\xbe\xba\xfe\xca",
        b"\xca\xfe\xba\xbf",
        b"\xbf\xba\xfe\xca",
    }
    return magic in macho_magics


def executable_from_app(app: Path) -> Path | None:
    info_plist = app / "Contents" / "Info.plist"
    if not info_plist.exists():
        return None
    try:
        with info_plist.open("rb") as handle:
            info = plistlib.load(handle)
    except Exception:
        return None
    exe_name = info.get("CFBundleExecutable")
    if not exe_name:
        return None
    exe = app / "Contents" / "MacOS" / exe_name
    return exe if exe.exists() else None


def candidate_macho_paths(root: Path, max_depth: int = 6) -> list[Path]:
    paths: list[Path] = []
    if root.is_file():
        return [root] if is_probably_macho(root) else []
    if root.suffix == ".app":
        main = executable_from_app(root)
        if main:
            paths.append(main)
        for rel in COMMON_APP_SUBDIRS:
            directory = root / rel
            if directory.exists():
                paths.extend(walk_macho_files(directory, root_depth=directory, max_depth=max_depth))
    else:
        paths.extend(walk_macho_files(root, root_depth=root, max_depth=max_depth))
    # Deduplicate while preserving order.
    seen: set[Path] = set()
    deduped: list[Path] = []
    for path in paths:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            deduped.append(path)
    return deduped


def walk_macho_files(directory: Path, root_depth: Path, max_depth: int) -> list[Path]:
    result: list[Path] = []
    if not directory.exists():
        return result
    for current, dirs, files in os.walk(directory):
        current_path = Path(current)
        try:
            rel_depth = len(current_path.relative_to(root_depth).parts)
        except ValueError:
            rel_depth = 0
        if rel_depth > max_depth:
            dirs[:] = []
            continue
        for filename in files:
            path = current_path / filename
            try:
                mode = path.stat().st_mode
            except OSError:
                continue
            if (
                stat.S_ISREG(mode)
                and (mode & stat.S_IXUSR or is_probably_macho(path))
                and is_probably_macho(path)
            ):
                result.append(path)
    return result


def parse_otool_libraries(text: str) -> list[str]:
    libs: list[str] = []
    for line in text.splitlines()[1:]:
        match = DYLIB_RE.match(line)
        if match:
            libs.append(match.group(1))
    return libs


def analyze_binary(path: Path) -> dict[str, Any]:
    file_result = run_command(["file", str(path)], timeout=8)
    otool_result = run_command(["otool", "-L", str(path)], timeout=20)
    libs = parse_otool_libraries(otool_result.stdout) if otool_result.stdout else []
    private_matches: list[dict[str, str]] = []
    public_matches: list[dict[str, str]] = []
    for lib in libs:
        private = PRIVATE_FRAMEWORK_RE.search(lib)
        if private:
            private_matches.append(
                {"framework": private.group(2), "path": private.group(1), "library": lib}
            )
            continue
        public = PUBLIC_FRAMEWORK_RE.search(lib)
        if public:
            public_matches.append(
                {"framework": public.group(2), "path": public.group(1), "library": lib}
            )
    return {
        "path": str(path),
        "file": asdict(file_result),
        "otool_L": asdict(otool_result),
        "libraries": libs,
        "private_frameworks": private_matches,
        "public_frameworks": public_matches,
    }


def collect_entitlements(target: Path) -> dict[str, Any] | None:
    candidate = target
    if target.is_file():
        # codesign accepts binaries too, but app entitlements are often on the bundle.
        candidate = target
    result = run_command(["codesign", "-d", "--entitlements", ":-", str(candidate)], timeout=15)
    if result.returncode is None:
        return None
    return asdict(result)


def summarize_frameworks(analyses: list[dict[str, Any]]) -> dict[str, list[dict[str, str]]]:
    summary: dict[str, list[dict[str, str]]] = {}
    for analysis in analyses:
        binary = analysis["path"]
        for item in analysis["private_frameworks"]:
            summary.setdefault(item["framework"], []).append(
                {"binary": binary, "path": item["path"]}
            )
    return summary


def render_markdown(data: dict[str, Any], binary_detail_limit: int = 40) -> str:
    lines: list[str] = []
    lines.append("# Private Framework Discovery")
    lines.append("")
    lines.append("## Inputs")
    lines.append("")
    for target in data["targets"]:
        lines.append(f"- `{target}`")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    summary = data["private_framework_summary"]
    if summary:
        lines.append("| Framework | Referencing binaries | Framework path examples |")
        lines.append("|---|---:|---|")
        for framework, refs in sorted(summary.items()):
            paths = sorted({ref["path"] for ref in refs})
            lines.append(
                f"| `{framework}` | {len(refs)} | {'<br>'.join(f'`{p}`' for p in paths[:5])} |"
            )
    else:
        lines.append(
            "No linked `/System/Library/PrivateFrameworks/*.framework` dependencies found by `otool -L`."
        )
    lines.append("")
    lines.append("## Binary Evidence")
    lines.append("")
    analyses = data["analyses"]
    visible_analyses = (
        analyses[:binary_detail_limit]
        if binary_detail_limit and binary_detail_limit > 0
        else analyses
    )
    if len(visible_analyses) < len(analyses):
        lines.append(
            f"Markdown shows `{len(visible_analyses)}` of `{len(analyses)}` analyzed binaries. JSON contains all binary evidence."
        )
        lines.append("")
    for analysis in visible_analyses:
        lines.append(f"### `{analysis['path']}`")
        lines.append("")
        file_stdout = analysis["file"]["stdout"] or analysis["file"]["stderr"]
        lines.append(f"- file: `{file_stdout}`")
        if analysis["private_frameworks"]:
            lines.append("- Private frameworks:")
            for item in analysis["private_frameworks"]:
                lines.append(f"  - `{item['framework']}`: `{item['path']}`")
        else:
            lines.append("- Private frameworks: none linked directly")
        if analysis["otool_L"]["returncode"] not in (0, None):
            lines.append(f"- `otool -L` error: `{analysis['otool_L']['stderr']}`")
        lines.append("")
    if data.get("entitlements"):
        lines.append("## Entitlements")
        lines.append("")
        for target, result in data["entitlements"].items():
            lines.append(f"### `{target}`")
            lines.append("```text")
            lines.append(result.get("stdout") or result.get("stderr") or "")
            lines.append("```")
            lines.append("")
    lines.append("## Suggested Next Steps")
    lines.append("")
    if summary:
        first = sorted(summary)[0]
        lines.append("```bash")
        lines.append(
            f"scripts/extract_dyld_framework.sh --framework {first} --output-dir /tmp/macos-private-frameworks"
        )
        lines.append(
            f"ipsw class-dump /System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld/dyld_shared_cache_arm64e {first} --headers --output /tmp/{first}.headers"
        )
        lines.append(
            f"scripts/objc_header_triage.py --headers /tmp/{first}.headers --output /tmp/{first}.candidates.md --json-output /tmp/{first}.candidates.json"
        )
        lines.append("```")
    else:
        lines.append(
            "Inspect indirect dependencies, launch services, entitlements, XPC service names, and strings for private API usage hints."
        )
    lines.append("")
    return "\n".join(lines)


def build_report(targets: list[Path], include_entitlements: bool, max_depth: int) -> dict[str, Any]:
    analyses: list[dict[str, Any]] = []
    entitlements: dict[str, Any] = {}
    for target in targets:
        for binary in candidate_macho_paths(target, max_depth=max_depth):
            analyses.append(analyze_binary(binary))
        if include_entitlements:
            ent = collect_entitlements(target)
            if ent is not None:
                entitlements[str(target)] = ent
    return {
        "targets": [str(target) for target in targets],
        "analyses": analyses,
        "private_framework_summary": summarize_frameworks(analyses),
        "entitlements": entitlements,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "targets", nargs="+", type=Path, help="App bundles, directories, or Mach-O binaries."
    )
    parser.add_argument(
        "--include-entitlements",
        action="store_true",
        help="Run codesign entitlement extraction for each top-level target.",
    )
    parser.add_argument(
        "--max-depth", type=int, default=6, help="Maximum directory depth for component discovery."
    )
    parser.add_argument(
        "--binary-detail-limit",
        type=int,
        default=40,
        help="Maximum analyzed binaries rendered in Markdown. Use 0 for all; JSON always contains all.",
    )
    parser.add_argument("--output", type=Path, help="Markdown output path. Defaults to stdout.")
    parser.add_argument("--json-output", type=Path, help="JSON output path.")
    args = parser.parse_args()

    missing = [str(path) for path in args.targets if not path.exists()]
    if missing:
        parser.error(f"target(s) do not exist: {', '.join(missing)}")

    data = build_report(args.targets, args.include_entitlements, args.max_depth)
    markdown = render_markdown(data, binary_detail_limit=args.binary_detail_limit)
    if args.output:
        args.output.write_text(markdown, encoding="utf-8")
    else:
        print(markdown)
    if args.json_output:
        args.json_output.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
