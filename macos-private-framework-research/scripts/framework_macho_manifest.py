#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import plistlib
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Any


def run(cmd: list[str]) -> str:
    try:
        proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
    except FileNotFoundError:
        return ""
    return (proc.stdout or proc.stderr).strip()


def limited_lines(text: str, limit: int) -> dict[str, Any]:
    lines = text.splitlines()
    rendered = lines if limit < 0 else lines[:limit]
    return {
        "lines": rendered,
        "total_count": len(lines),
        "rendered_count": len(rendered),
        "truncated": limit >= 0 and len(lines) > limit,
    }


def otool_dependency_text(text: str) -> str:
    lines = text.splitlines()
    if lines and lines[0].endswith(":"):
        lines = lines[1:]
    return "\n".join(lines)


def default_cache() -> str:
    arch = platform.machine()
    names = ["dyld_shared_cache_arm64e", "dyld_shared_cache_arm64"] if arch == "arm64" else [
        "dyld_shared_cache_x86_64h",
        "dyld_shared_cache_x86_64",
    ]
    roots = [
        Path("/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld"),
        Path("/System/Library/dyld"),
    ]
    for root in roots:
        for name in names:
            candidate = root / name
            if candidate.is_file():
                return str(candidate)
    return ""


def read_plist(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        with path.open("rb") as fh:
            value = plistlib.load(fh)
    except Exception:
        return {}
    return value if isinstance(value, dict) else {}


def framework_binary(path: Path) -> Path | None:
    if path.is_file():
        return path
    if not path.is_dir() or path.suffix != ".framework":
        return None
    name = path.stem
    for candidate in (path / name, path / "Versions" / "A" / name):
        if candidate.is_file():
            return candidate
    return None


def expand_targets(args: argparse.Namespace) -> list[Path]:
    targets = [Path(value).expanduser() for value in args.targets]
    root = Path(args.private_framework_root)
    for framework in args.framework:
        name = framework.removesuffix(".framework")
        targets.append(root / f"{name}.framework")
    expanded: list[Path] = []
    for target in targets:
        if target.is_dir() and target.suffix != ".framework":
            expanded.extend(
                sorted(
                    child for child in target.iterdir()
                    if child.suffix == ".framework" or (child.is_file() and child.suffix in ("", ".dylib"))
                )
            )
        else:
            expanded.append(target)
    return expanded


def load_cache_images(cache: str) -> dict[str, dict[str, Any]]:
    if not cache or not Path(cache).is_file() or not shutil.which("ipsw"):
        return {}
    text = run(["ipsw", "dyld", "info", cache, "--dylibs", "--json"])
    if not text:
        return {}
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return {}
    images: dict[str, dict[str, Any]] = {}
    for image in parsed.get("dylibs", []):
        name = image.get("name")
        if isinstance(name, str):
            images[name] = image
    return images


def dyld_lookup_name(target: Path) -> str:
    if target.suffix == ".framework":
        name = target.stem
        return f"/System/Library/PrivateFrameworks/{name}.framework/Versions/A/{name}"
    if target.is_file() and target.suffix == "":
        name = target.name
        return f"/System/Library/PrivateFrameworks/{name}.framework/Versions/A/{name}"
    return str(target)


def manifest_for_binary(path: Path, args: argparse.Namespace) -> dict[str, Any]:
    stat = path.stat()
    sha = run(["shasum", "-a", "256", str(path)])
    dependencies = run(["otool", "-L", str(path)])
    symbols = run(["nm", "-gjU", str(path)])
    load_commands = run(["otool", "-l", str(path)]) if args.include_load_commands else ""
    strings = ""
    if args.string_pattern:
        strings = run([
            "/bin/sh",
            "-c",
            'strings -a "$1" | grep -E -i "$2" | sort -u',
            "sh",
            str(path),
            args.string_pattern,
        ])
    return {
        "path": str(path),
        "name": path.name,
        "size": stat.st_size,
        "mtime": int(stat.st_mtime),
        "sha256": sha.split()[0] if sha else "",
        "file": run(["file", str(path)]),
        "uuid": run(["dwarfdump", "--uuid", str(path)]),
        "build": run(["vtool", "-show-build", str(path)]).splitlines(),
        "dependencies": limited_lines(otool_dependency_text(dependencies), args.dependency_limit),
        "defined_external_symbols": limited_lines(symbols, args.symbol_limit),
        "focused_strings": limited_lines(strings, args.string_limit),
        "load_commands": limited_lines(load_commands, args.load_command_limit),
    }


def manifest_for_target(target: Path, args: argparse.Namespace, cache_images: dict[str, dict[str, Any]]) -> dict[str, Any]:
    binary = framework_binary(target)
    info: dict[str, Any] = {}
    version: dict[str, Any] = {}
    if target.is_dir() and target.suffix == ".framework":
        info = read_plist(target / "Versions" / "A" / "Resources" / "Info.plist")
        version = read_plist(target / "Versions" / "A" / "Resources" / "version.plist")
    dyld_name = dyld_lookup_name(target)
    entry: dict[str, Any] = {
        "target": str(target),
        "framework_name": target.stem if target.suffix == ".framework" else "",
        "binary_present": binary is not None,
        "dyld_lookup_name": dyld_name,
        "dyld_cache_image": cache_images.get(dyld_name, {}),
        "info_plist": {key: info.get(key) for key in ("CFBundleIdentifier", "CFBundleShortVersionString", "CFBundleVersion") if key in info},
        "version_plist": {key: version.get(key) for key in ("ProjectName", "SourceVersion", "BuildVersion") if key in version},
    }
    if binary:
        entry["binary"] = manifest_for_binary(binary, args)
    return entry


def write_markdown(result: dict[str, Any], output: Path) -> None:
    lines = [
        "# Framework Mach-O Manifest",
        "",
        f"Cache: `{result.get('dyld_cache') or 'not used'}`",
        f"Targets: `{len(result['targets'])}`",
        "",
        "| Target | Binary | Dyld version | UUID | Deps | Symbols |",
        "|---|---:|---|---|---:|---:|",
    ]
    for entry in result["targets"]:
        binary = entry.get("binary", {})
        dyld = entry.get("dyld_cache_image", {})
        deps = binary.get("dependencies", {})
        symbols = binary.get("defined_external_symbols", {})
        uuid_text = str(binary.get("uuid") or dyld.get("uuid", "")).replace("\n", " ")
        uuid_parts = uuid_text.split()
        uuid = uuid_parts[1] if len(uuid_parts) > 1 and uuid_parts[0] == "UUID:" else uuid_text
        name = entry.get("framework_name") or Path(entry["target"]).name
        lines.append(
            f"| `{name}` | `{entry['binary_present']}` | `{dyld.get('version', '')}` | `{uuid}` | "
            f"{deps.get('total_count', 0)} | {symbols.get('total_count', 0)} |"
        )
    lines.append("")
    lines.append("JSON output contains capped arrays with `total_count`, `rendered_count`, and `truncated` metadata.")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a compact manifest for framework bundles and extracted Mach-O files.")
    parser.add_argument("targets", nargs="*", help="Framework bundles, extracted Mach-O files, or directories.")
    parser.add_argument("--framework", action="append", default=[], help="Private framework basename under --private-framework-root.")
    parser.add_argument("--private-framework-root", default="/System/Library/PrivateFrameworks")
    parser.add_argument("--cache", default=default_cache(), help="Dyld shared cache path used to annotate cache-resident framework skeletons.")
    parser.add_argument("--json-output", "--output", dest="json_output", type=Path)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--dependency-limit", type=int, default=120)
    parser.add_argument("--symbol-limit", type=int, default=300)
    parser.add_argument("--string-limit", type=int, default=120)
    parser.add_argument("--load-command-limit", type=int, default=0)
    parser.add_argument("--include-load-commands", action="store_true")
    parser.add_argument("--string-pattern", default="")
    args = parser.parse_args()

    targets = expand_targets(args)
    if not targets:
        parser.error("provide at least one target or --framework")
    cache_images = load_cache_images(args.cache)
    result = {
        "schema_version": 1,
        "generated_by": "framework_macho_manifest.py",
        "dyld_cache": args.cache,
        "targets": [manifest_for_target(target, args, cache_images) for target in targets],
    }
    if args.markdown_output:
        write_markdown(result, args.markdown_output)
    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.json_output:
        args.json_output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
