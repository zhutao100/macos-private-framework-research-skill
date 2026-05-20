#!/usr/bin/env python3
"""Inventory a macOS host for private-framework research."""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

DEFAULT_DYLD_DIRS = [
    Path("/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld"),
    Path("/System/Library/dyld"),
]

TOOL_NAMES = [
    "file",
    "otool",
    "nm",
    "strings",
    "lipo",
    "codesign",
    "plutil",
    "xcrun",
    "lldb",
    "clang",
    "xcrun swift-demangle",
    "ipsw",
    "ipsw class-dump",
    "dyld-shared-cache-extractor",
    "hopper",
    "HopperMCPServer",
]

APP_CANDIDATES = {
    "Hopper": [Path("/Applications/Hopper Disassembler.app")],
    "RuntimeViewer": [Path("/Applications/RuntimeViewer.app"),],
    "RuntimeBrowser": [Path("/Applications/RuntimeBrowser.app")],
}

BUNDLED_TOOL_CANDIDATES = {
    "HopperMCPServer": [
        Path("/Applications/Hopper Disassembler.app/Contents/MacOS/HopperMCPServer"),
    ],
}


@dataclass(frozen=True)
class CommandResult:
    command: list[str]
    returncode: int | None
    stdout: str
    stderr: str


def run_command(command: list[str], timeout: int = 8) -> CommandResult:
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


def command_stdout(command: list[str], timeout: int = 8) -> str:
    return run_command(command, timeout=timeout).stdout


def count_dirs(path: Path, pattern: str) -> int | None:
    if not path.exists():
        return None
    try:
        return sum(1 for _ in path.glob(pattern))
    except OSError:
        return None


def discover_dyld_caches(extra_dirs: list[Path]) -> list[dict[str, Any]]:
    dirs = [*DEFAULT_DYLD_DIRS, *extra_dirs]
    seen: set[Path] = set()
    caches: list[dict[str, Any]] = []
    for directory in dirs:
        if directory in seen:
            continue
        seen.add(directory)
        if not directory.exists():
            continue
        for cache in sorted(directory.glob("dyld_shared_cache_*")):
            if not cache.is_file():
                continue
            try:
                stat = cache.stat()
            except OSError:
                continue
            caches.append(
                {
                    "path": str(cache),
                    "name": cache.name,
                    "architecture": dyld_cache_architecture(cache.name),
                    "kind": dyld_cache_kind(cache.name),
                    "size_bytes": stat.st_size,
                    "mtime": stat.st_mtime,
                }
            )
    return caches


def dyld_cache_architecture(name: str) -> str:
    prefix = "dyld_shared_cache_"
    if not name.startswith(prefix):
        return ""
    arch = name.removeprefix(prefix).split(".", 1)[0]
    return arch


def dyld_cache_kind(name: str) -> str:
    if name.endswith(".map"):
        return "map"
    if name.endswith(".atlas"):
        return "atlas"
    suffix = name.removeprefix(f"dyld_shared_cache_{dyld_cache_architecture(name)}")
    if re.match(r"^\.\d+$", suffix):
        return "subcache"
    if suffix == "":
        return "primary"
    return "other"


def tool_command(name: str) -> list[str]:
    if name == "xcrun swift-demangle":
        return ["xcrun", "swift-demangle"]
    if name == "ipsw class-dump":
        return ["ipsw", "class-dump"]
    return [name]


def resolve_tool_path(name: str, command: list[str]) -> str | None:
    path = shutil.which(command[0])
    if path:
        return path
    for candidate in BUNDLED_TOOL_CANDIDATES.get(name, []):
        if candidate.exists() and candidate.is_file():
            return str(candidate)
    return None


def tool_info(name: str) -> dict[str, Any]:
    command = tool_command(name)
    path = resolve_tool_path(name, command)
    info: dict[str, Any] = {
        "name": name,
        "command": command,
        "path": path,
        "available": path is not None,
    }
    if not path:
        return info

    version_commands = {
        "ipsw": [name, "version"],
        "dyld-shared-cache-extractor": [name, "--help"],
        "ipsw class-dump": [*command, "--help"],
        "hopper": [name, "--help"],
        "clang": [name, "--version"],
        "lldb": [name, "--version"],
        "xcrun": [name, "--version"],
        "xcrun swift-demangle": [*command, "--version"],
    }
    cmd = version_commands.get(name)
    if cmd:
        result = run_command(cmd, timeout=4)
        text = result.stdout or result.stderr
        info["version_hint"] = "\n".join(text.splitlines()[:3])
    return info


def app_info() -> list[dict[str, Any]]:
    apps: list[dict[str, Any]] = []
    for name, candidates in APP_CANDIDATES.items():
        found = [str(path) for path in candidates if path.exists()]
        apps.append({"name": name, "found_paths": found, "available": bool(found)})
    return apps


def build_inventory(extra_dyld_dirs: list[Path]) -> dict[str, Any]:
    sw_vers = run_command(["sw_vers"])
    csrutil = run_command(["csrutil", "status"])
    csrutil_ar = run_command(["csrutil", "authenticated-root", "status"])
    xcode_select = run_command(["xcode-select", "-p"])
    xcodebuild = run_command(["xcodebuild", "-version"])

    private_fw = Path("/System/Library/PrivateFrameworks")
    public_fw = Path("/System/Library/Frameworks")

    return {
        "host": {
            "platform_system": platform.system(),
            "platform_release": platform.release(),
            "machine": platform.machine(),
            "uname": platform.uname()._asdict(),
            "sw_vers": asdict(sw_vers),
            "environment": {
                "DEVELOPER_DIR": os.environ.get("DEVELOPER_DIR"),
                "SDKROOT": os.environ.get("SDKROOT"),
            },
        },
        "security_status": {
            "csrutil_status": asdict(csrutil),
            "csrutil_authenticated_root": asdict(csrutil_ar),
        },
        "xcode": {
            "xcode_select": asdict(xcode_select),
            "xcodebuild_version": asdict(xcodebuild),
        },
        "dyld_caches": discover_dyld_caches(extra_dyld_dirs),
        "framework_dirs": {
            "private_frameworks_path": str(private_fw),
            "private_framework_count": count_dirs(private_fw, "*.framework"),
            "public_frameworks_path": str(public_fw),
            "public_framework_count": count_dirs(public_fw, "*.framework"),
        },
        "tools": [tool_info(name) for name in TOOL_NAMES],
        "apps": app_info(),
    }


def human_size(size: int | None) -> str:
    if size is None:
        return ""
    value = float(size)
    for unit in ["B", "KiB", "MiB", "GiB"]:
        if value < 1024 or unit == "GiB":
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{size} B"


def primary_cache(caches: list[dict[str, Any]], machine: str) -> dict[str, Any] | None:
    preferred_arches = ["arm64e", "arm64"] if machine == "arm64" else ["x86_64h", "x86_64"]
    for arch in preferred_arches:
        for cache in caches:
            if cache.get("kind") == "primary" and cache.get("architecture") == arch:
                return cache
    for cache in caches:
        if cache.get("kind") == "primary":
            return cache
    return caches[0] if caches else None


def visible_cache_rows(
    caches: list[dict[str, Any]], selected_cache: dict[str, Any] | None, limit: int
) -> list[dict[str, Any]]:
    if limit <= 0:
        return caches
    rows: list[dict[str, Any]] = []
    if selected_cache:
        rows.append(selected_cache)
    for cache in caches:
        if selected_cache and cache["path"] == selected_cache["path"]:
            continue
        rows.append(cache)
        if len(rows) >= limit:
            break
    return rows


def render_markdown(data: dict[str, Any], cache_markdown_limit: int = 16) -> str:
    host = data["host"]
    caches = data["dyld_caches"]
    selected_cache = primary_cache(caches, host["machine"])
    cache_rows = visible_cache_rows(caches, selected_cache, cache_markdown_limit)
    lines: list[str] = []
    lines.append("# macOS Private Framework Research Inventory")
    lines.append("")
    lines.append("## Host")
    lines.append("")
    lines.append(f"- Platform: `{host['platform_system']} {host['platform_release']}`")
    lines.append(f"- Machine: `{host['machine']}`")
    if selected_cache:
        lines.append(f"- Suggested dyld cache: `{selected_cache['path']}`")
    sw = host["sw_vers"]
    if sw["stdout"]:
        lines.append("- `sw_vers`:")
        lines.append("  ```text")
        lines.extend(f"  {line}" for line in sw["stdout"].splitlines())
        lines.append("  ```")
    lines.append("")
    lines.append("## Xcode / CLT")
    lines.append("")
    for key, title in [("xcode_select", "xcode-select"), ("xcodebuild_version", "xcodebuild")]:
        result = data["xcode"][key]
        lines.append(f"- {title}: `{result['stdout'] or result['stderr'] or 'not available'}`")
    lines.append("")
    lines.append("## Security Status")
    lines.append("")
    for key, title in [
        ("csrutil_status", "SIP"),
        ("csrutil_authenticated_root", "Authenticated root"),
    ]:
        result = data["security_status"][key]
        lines.append(f"- {title}: `{result['stdout'] or result['stderr'] or 'not available'}`")
    lines.append("")
    lines.append("## Dyld Shared Caches")
    lines.append("")
    if caches:
        primary_count = sum(1 for cache in caches if cache.get("kind") == "primary")
        subcache_count = sum(1 for cache in caches if cache.get("kind") == "subcache")
        map_count = sum(1 for cache in caches if cache.get("kind") == "map")
        atlas_count = sum(1 for cache in caches if cache.get("kind") == "atlas")
        other_count = len(caches) - primary_count - subcache_count - map_count - atlas_count
        lines.append(
            f"Found `{len(caches)}` cache-related files: primary=`{primary_count}`, subcache=`{subcache_count}`, map=`{map_count}`, atlas=`{atlas_count}`, other=`{other_count}`."
        )
        if len(cache_rows) < len(caches):
            lines.append(
                f"Markdown shows `{len(cache_rows)}` cache rows; JSON contains all cache records."
            )
        lines.append("")
        lines.append("| Cache | Arch | Kind | Size | Path |")
        lines.append("|---|---|---|---:|---|")
        for cache in cache_rows:
            lines.append(
                f"| `{cache['name']}` | `{cache['architecture']}` | `{cache['kind']}` | {human_size(cache['size_bytes'])} | `{cache['path']}` |"
            )
    else:
        lines.append("No dyld shared cache files found in standard locations.")
    lines.append("")
    lines.append("## Framework Directories")
    lines.append("")
    fw = data["framework_dirs"]
    lines.append(
        f"- Private frameworks: `{fw['private_frameworks_path']}` count=`{fw['private_framework_count']}`"
    )
    lines.append(
        f"- Public frameworks: `{fw['public_frameworks_path']}` count=`{fw['public_framework_count']}`"
    )
    lines.append("")
    lines.append("## Tools")
    lines.append("")
    lines.append("| Tool | Available | Path | Version hint |")
    lines.append("|---|---:|---|---|")
    for tool in data["tools"]:
        version = (tool.get("version_hint") or "").replace("\n", "<br>")
        lines.append(
            f"| `{tool['name']}` | {tool['available']} | `{tool.get('path') or ''}` | {version} |"
        )
    lines.append("")
    lines.append("## Apps")
    lines.append("")
    lines.append("| App | Available | Paths |")
    lines.append("|---|---:|---|")
    for app in data["apps"]:
        paths = "<br>".join(f"`{p}`" for p in app["found_paths"])
        lines.append(f"| {app['name']} | {app['available']} | {paths} |")
    lines.append("")
    lines.append("## Suggested Next Commands")
    lines.append("")
    cache_path = (
        selected_cache["path"]
        if selected_cache
        else (
            caches[0]["path"]
            if caches
            else "/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld/dyld_shared_cache_arm64e"
        )
    )
    lines.append("```bash")
    lines.append(f"ipsw dyld info {json.dumps(cache_path)}")
    lines.append(
        "scripts/discover_private_frameworks.py --output /tmp/client-private-frameworks.md /path/to/Client.app"
    )
    lines.append(
        "scripts/extract_dyld_framework.sh --framework FrameworkName --output-dir /tmp/macos-private-frameworks"
    )
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--extra-dyld-dir",
        action="append",
        default=[],
        type=Path,
        help="Additional directory to scan for dyld_shared_cache_* files.",
    )
    parser.add_argument("--output", type=Path, help="Markdown output path. Defaults to stdout.")
    parser.add_argument("--json-output", type=Path, help="JSON output path.")
    parser.add_argument(
        "--cache-markdown-limit",
        type=int,
        default=16,
        help="Maximum dyld cache rows in Markdown. Use 0 for all rows; JSON always contains all.",
    )
    args = parser.parse_args()

    data = build_inventory(args.extra_dyld_dir)
    markdown = render_markdown(data, cache_markdown_limit=args.cache_markdown_limit)

    if args.output:
        args.output.write_text(markdown, encoding="utf-8")
    else:
        print(markdown)

    if args.json_output:
        args.json_output.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
