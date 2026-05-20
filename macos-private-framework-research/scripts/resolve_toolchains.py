#!/usr/bin/env python3
"""Check optional toolchains and report configured installation sources."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = SKILL_DIR / "agents" / "tool-installation.yaml"


@dataclass(frozen=True)
class ToolProbe:
    command: tuple[str, ...] = ()
    app_paths: tuple[Path, ...] = ()


@dataclass
class ToolResolution:
    name: str
    available: bool
    evidence: list[str]
    source: dict[str, str]
    install_attempted: bool = False
    install_returncode: int | None = None


TOOL_PROBES: dict[str, ToolProbe] = {
    "ipsw": ToolProbe(command=("ipsw",)),
    "dyld-shared-cache-extractor": ToolProbe(command=("dyld-shared-cache-extractor",)),
    "RuntimeViewer": ToolProbe(app_paths=(Path("/Applications/RuntimeViewer.app"),)),
    "RuntimeBrowser": ToolProbe(app_paths=(Path("/Applications/RuntimeBrowser.app"),)),
    "Hopper": ToolProbe(app_paths=(Path("/Applications/Hopper Disassembler.app"),)),
    "hopper": ToolProbe(command=("hopper",)),
    "HopperMCPServer": ToolProbe(command=("HopperMCPServer",)),
}


ALIASES = {
    "dsc": "dyld-shared-cache-extractor",
    "dyld-shared-cache": "dyld-shared-cache-extractor",
    "ipsw class-dump": "ipsw",
    "ipsw-class-dump": "ipsw",
    "RunTimeBrowser": "RuntimeBrowser",
    "runtimebrowser": "RuntimeBrowser",
    "runtimeviewer": "RuntimeViewer",
    "hopper-disassembler": "Hopper",
}


def parse_scalar(value: str) -> str:
    value = value.strip()
    if not value:
        return ""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def load_tool_sources(path: Path) -> dict[str, dict[str, str]]:
    """Parse the skill's simple top-level mapping YAML without extra dependencies."""
    sources: dict[str, dict[str, str]] = {}
    current_name: str | None = None
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if not raw_line.startswith(" "):
            if not raw_line.endswith(":"):
                raise ValueError(f"{path}:{line_number}: expected top-level key ending with ':'")
            current_name = raw_line[:-1].strip()
            if not current_name:
                raise ValueError(f"{path}:{line_number}: empty top-level key")
            sources[current_name] = {}
            continue
        if current_name is None:
            raise ValueError(f"{path}:{line_number}: nested key before top-level key")
        if not raw_line.startswith("  ") or raw_line.startswith("   "):
            raise ValueError(f"{path}:{line_number}: expected two-space indentation")
        nested = raw_line.strip()
        if ":" not in nested:
            raise ValueError(f"{path}:{line_number}: expected nested key/value pair")
        key, value = nested.split(":", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"{path}:{line_number}: empty nested key")
        sources[current_name][key] = parse_scalar(value)
    return sources


def canonical_name(name: str, sources: dict[str, dict[str, str]]) -> str:
    if name in sources:
        return name
    if name in ALIASES:
        return ALIASES[name]
    for source_name in sources:
        if source_name.lower() == name.lower():
            return source_name
    return name


def probe_tool(name: str) -> tuple[bool, list[str]]:
    probe = TOOL_PROBES.get(name, ToolProbe(command=(name,)))
    evidence: list[str] = []
    available = False
    if probe.command:
        executable = probe.command[0]
        resolved = shutil.which(executable)
        if resolved:
            available = True
            evidence.append(resolved)
        else:
            evidence.append(f"{executable}: not found in PATH")
    for app_path in probe.app_paths:
        if app_path.exists():
            available = True
            evidence.append(str(app_path))
        else:
            evidence.append(f"{app_path}: not found")
    return available, evidence


def resolve_tools(
    sources: dict[str, dict[str, str]],
    names: list[str],
    run_install: bool,
) -> list[ToolResolution]:
    requested = [canonical_name(name, sources) for name in names] if names else list(sources)
    unknown = [name for name in requested if name not in sources]
    if unknown:
        known = ", ".join(sorted(sources))
        raise ValueError(f"unknown toolchain(s): {', '.join(unknown)}; known: {known}")

    results: list[ToolResolution] = []
    for name in requested:
        available, evidence = probe_tool(name)
        source = sources[name]
        result = ToolResolution(
            name=name,
            available=available,
            evidence=evidence,
            source=source,
        )
        if run_install and not available and source.get("command"):
            command = source["command"]
            result.install_attempted = True
            proc = subprocess.run(command, shell=True, check=False)
            result.install_returncode = proc.returncode
            available, evidence = probe_tool(name)
            result.available = available
            result.evidence = evidence
        results.append(result)
    return results


def display_source_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(SKILL_DIR))
    except ValueError:
        return str(path)


def render_markdown(source_path: Path, results: list[ToolResolution]) -> str:
    lines: list[str] = [
        "# Optional Toolchain Resolution",
        "",
        f"- Source: `{display_source_path(source_path)}`",
        "",
        "| Toolchain | Available | Evidence | Resolution |",
        "|---|---:|---|---|",
    ]
    notes: list[tuple[str, str]] = []
    for result in results:
        source = result.source
        resolution_parts: list[str] = []
        if source.get("command"):
            resolution_parts.append(f"`{source['command']}`")
        if source.get("url"):
            resolution_parts.append(f"<{source['url']}>")
        if source.get("note"):
            notes.append((result.name, source["note"]))
        if result.install_attempted:
            resolution_parts.append(f"install_returncode=`{result.install_returncode}`")
        evidence = "<br>".join(f"`{item}`" for item in result.evidence)
        resolution = "<br>".join(resolution_parts)
        lines.append(f"| `{result.name}` | {result.available} | {evidence} | {resolution} |")
    if notes:
        lines.extend(["", "## Notes", ""])
        for name, note in notes:
            lines.append(f"- `{name}`: {note}")
    return "\n".join(lines) + "\n"


def results_to_json(source_path: Path, results: list[ToolResolution]) -> dict[str, Any]:
    return {
        "source": display_source_path(source_path),
        "toolchains": [asdict(result) for result in results],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "toolchains",
        nargs="*",
        help="Toolchain names to check. Defaults to all entries in agents/tool-installation.yaml.",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE,
        help="Tool installation source file. Defaults to the skill's agents/tool-installation.yaml.",
    )
    parser.add_argument("--json-output", type=Path, help="Write complete JSON results.")
    parser.add_argument(
        "--run-install",
        action="store_true",
        help="Run configured install commands for missing selected toolchains.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when any selected toolchain remains unavailable.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        sources = load_tool_sources(args.source)
        results = resolve_tools(sources, args.toolchains, run_install=args.run_install)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}")
        return 2

    print(render_markdown(args.source, results), end="")

    if args.json_output:
        args.json_output.write_text(
            json.dumps(results_to_json(args.source, results), indent=2, sort_keys=True),
            encoding="utf-8",
        )

    if args.strict and any(not result.available for result in results):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
