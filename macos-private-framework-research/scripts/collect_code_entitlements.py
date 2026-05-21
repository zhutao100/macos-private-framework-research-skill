#!/usr/bin/env python3
"""Collect and summarize code-signing entitlements for apps, bundles, and binaries."""

from __future__ import annotations

import argparse
import json
import os
import plistlib
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CommandResult:
    command: list[str]
    returncode: int | None
    stdout: str
    stderr: str


def run_command(command: list[str], timeout: int = 15) -> CommandResult:
    try:
        proc = subprocess.run(
            command,
            text=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=timeout,
        )
        return CommandResult(
            command=command,
            returncode=proc.returncode,
            stdout=proc.stdout.decode(errors="replace"),
            stderr=proc.stderr.decode(errors="replace"),
        )
    except FileNotFoundError:
        return CommandResult(command, None, "", "command not found")
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return CommandResult(command, None, stdout, f"timeout: {stderr}".strip())


def redact_path(path: str, redact_home: bool) -> str:
    if not redact_home:
        return path
    home = os.path.expanduser("~")
    if path == home:
        return "~"
    if path.startswith(home + "/"):
        return "~" + path[len(home):]
    return path


def load_paths(args: argparse.Namespace) -> list[Path]:
    values = [Path(value).expanduser() for value in args.targets]
    for paths_file in args.paths_file:
        for raw_line in paths_file.expanduser().read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw_line.split("#", 1)[0].strip()
            if line:
                values.append(Path(line).expanduser())
    seen: set[str] = set()
    out: list[Path] = []
    for path in values:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        out.append(path)
    return out


def value_preview(value: Any, max_chars: int) -> str:
    if isinstance(value, (str, int, float, bool)) or value is None:
        text = str(value)
    else:
        text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    text = text.replace("\n", "\\n")
    return text if len(text) <= max_chars else text[: max_chars - 3] + "..."


def focus_hits(value: Any, regex: re.Pattern[str] | None, max_value_chars: int) -> list[dict[str, str]]:
    if regex is None:
        return []
    hits: list[dict[str, str]] = []

    def walk(node: Any, path: str) -> None:
        if isinstance(node, dict):
            for key, child in node.items():
                child_path = f"{path}.{key}" if path else str(key)
                key_matched = regex.search(str(key)) is not None
                if key_matched:
                    hits.append({"path": child_path, "match": str(key), "value": value_preview(child, max_value_chars)})
                if not key_matched and not isinstance(child, (dict, list)) and regex.search(str(child)):
                    hits.append({"path": child_path, "match": value_preview(child, max_value_chars), "value": value_preview(child, max_value_chars)})
                walk(child, child_path)
        elif isinstance(node, list):
            for index, child in enumerate(node):
                child_path = f"{path}[{index}]"
                if not isinstance(child, (dict, list)) and regex.search(str(child)):
                    hits.append({"path": child_path, "match": value_preview(child, max_value_chars), "value": value_preview(child, max_value_chars)})
                walk(child, child_path)

    walk(value, "")
    deduped: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for hit in hits:
        key = (hit["path"], hit["match"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(hit)
    return deduped


def parse_entitlements(text: str) -> tuple[dict[str, Any], str]:
    stripped = text.strip()
    if not stripped:
        return {}, "empty"
    try:
        parsed = plistlib.loads(stripped.encode())
    except Exception as exc:
        return {}, f"parse_error: {exc}"
    if not isinstance(parsed, dict):
        return {}, f"unexpected plist root: {type(parsed).__name__}"
    return parsed, "parsed"


def collect_one(path: Path, args: argparse.Namespace, regex: re.Pattern[str] | None) -> dict[str, Any]:
    exists = path.exists()
    display_path = redact_path(str(path), args.redact_home)
    record: dict[str, Any] = {
        "path": display_path,
        "exists": exists,
    }
    if not exists:
        record["status"] = "missing"
        return record
    result = run_command(["codesign", "-d", "--entitlements", ":-", str(path)], timeout=args.timeout)
    record["codesign"] = asdict(result)
    record["codesign"]["command"] = ["codesign", "-d", "--entitlements", ":-", display_path]
    if result.returncode is None:
        record["status"] = "tool_missing"
        return record
    if result.returncode != 0 and not result.stdout.strip():
        record["status"] = "codesign_failed"
        return record
    entitlements, parse_status = parse_entitlements(result.stdout)
    record["parse_status"] = parse_status
    record["entitlement_count"] = len(entitlements)
    record["entitlement_keys"] = sorted(entitlements)
    if entitlements:
        record["status"] = "entitlements"
        record["entitlements"] = entitlements
        record["focus_hits"] = focus_hits(entitlements, regex, args.max_value_chars)
    else:
        record["status"] = "no_entitlements" if parse_status == "empty" else "parse_error"
        record["raw_preview"] = value_preview(result.stdout or result.stderr, args.max_value_chars)
        record["focus_hits"] = []
    return record


def render_markdown(report: dict[str, Any], limit: int, max_hit_rows: int) -> str:
    records = report["records"]
    visible = records if limit <= 0 else records[:limit]
    lines: list[str] = [
        "# Code Entitlement Collection",
        "",
        f"Inputs: `{report['summary']['inputs']}`",
        f"Records in report: `{report['summary']['records']}`",
        f"Existing targets: `{report['summary']['existing']}`",
        f"Targets with entitlements: `{report['summary']['with_entitlements']}`",
        f"Targets with focus hits: `{report['summary']['with_focus_hits']}`",
        "",
    ]
    if len(visible) < len(records):
        lines.append(f"Markdown shows `{len(visible)}` of `{len(records)}` records; JSON contains all records.")
        lines.append("")
    lines.extend([
        "| Target | Status | Keys | Focus hits |",
        "|---|---|---:|---:|",
    ])
    for record in visible:
        lines.append(
            f"| `{record['path']}` | `{record.get('status', '')}` | "
            f"{record.get('entitlement_count', 0)} | {len(record.get('focus_hits', []))} |"
        )
    if any(record.get("focus_hits") for record in visible):
        lines.append("")
        lines.append("## Focus Hits")
        lines.append("")
        for record in visible:
            hits = record.get("focus_hits", [])
            if not hits:
                continue
            lines.append(f"### `{record['path']}`")
            for hit in hits[:max_hit_rows]:
                value = hit["value"].replace("`", "'")
                lines.append(f"- `{hit['path']}` = `{value}`")
            if len(hits) > max_hit_rows:
                lines.append(f"- ... {len(hits) - max_hit_rows} more in JSON")
            lines.append("")
    return "\n".join(lines)


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    try:
        regex = re.compile(args.focus_pattern, re.IGNORECASE) if args.focus_pattern else None
    except re.error as exc:
        raise SystemExit(f"invalid --focus-pattern: {exc}") from exc
    paths = load_paths(args)
    all_records = [collect_one(path, args, regex) for path in paths]
    records = all_records
    if args.only_matching:
        records = [record for record in records if record.get("focus_hits")]
    return {
        "schema_version": 1,
        "focus_pattern": args.focus_pattern,
        "summary": {
            "inputs": len(paths),
            "processed": len(all_records),
            "records": len(records),
            "existing": sum(1 for record in all_records if record.get("exists")),
            "with_entitlements": sum(1 for record in all_records if record.get("status") == "entitlements"),
            "with_focus_hits": sum(1 for record in all_records if record.get("focus_hits")),
        },
        "records": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("targets", nargs="*", help="Apps, bundles, XPC services, appex bundles, or binaries.")
    parser.add_argument("--paths-file", action="append", default=[], type=Path, help="Newline-delimited target paths.")
    parser.add_argument("--focus-pattern", default="", help="Regex used to highlight entitlement keys and values.")
    parser.add_argument("--only-matching", action="store_true", help="Keep only records with focus-pattern hits.")
    parser.add_argument("--output", type=Path, help="Markdown output path. Defaults to stdout.")
    parser.add_argument("--json-output", type=Path, help="JSON output path.")
    parser.add_argument("--limit", type=int, default=60, help="Maximum records rendered in Markdown. Use 0 for all.")
    parser.add_argument("--max-hit-rows", type=int, default=20, help="Maximum focus-hit rows per target in Markdown.")
    parser.add_argument("--max-value-chars", type=int, default=240, help="Maximum rendered value length.")
    parser.add_argument("--timeout", type=int, default=15, help="codesign timeout per target in seconds.")
    parser.add_argument("--no-redact-home", dest="redact_home", action="store_false", help="Do not redact $HOME in output paths.")
    parser.set_defaults(redact_home=True)
    args = parser.parse_args()

    if not args.targets and not args.paths_file:
        parser.error("provide at least one target or --paths-file")

    report = build_report(args)
    markdown = render_markdown(report, args.limit, args.max_hit_rows)
    if args.output:
        args.output.write_text(markdown + "\n", encoding="utf-8")
    else:
        print(markdown)
    if args.json_output:
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
