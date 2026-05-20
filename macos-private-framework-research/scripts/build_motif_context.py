#!/usr/bin/env python3
"""Build an LLM-ready context bundle for one Objective-C signature candidate."""

from __future__ import annotations

import argparse
import json
import re
import shutil
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


def run_command(command: list[str], timeout: int = 20) -> CommandResult:
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


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def find_candidate(data: dict[str, Any], candidate_id: int) -> dict[str, Any]:
    for candidate in data.get("candidates", []):
        if int(candidate.get("id", -1)) == candidate_id:
            return candidate
    raise SystemExit(f"candidate id not found: {candidate_id}")


def header_file(headers: Path, candidate: dict[str, Any]) -> Path:
    rel = Path(candidate["file"])
    if headers.is_file():
        return headers
    return headers / rel


def nearby_header_context(
    headers: Path, candidate: dict[str, Any], radius: int = 20
) -> dict[str, Any]:
    path = header_file(headers, candidate)
    if not path.exists():
        return {"path": str(path), "error": "header path not found", "lines": []}
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    line_no = int(candidate.get("line", 1))
    start = max(1, line_no - radius)
    end = min(len(lines), line_no + radius)
    return {
        "path": str(path),
        "start_line": start,
        "end_line": end,
        "lines": [{"line": idx, "text": lines[idx - 1]} for idx in range(start, end + 1)],
    }


def selector_terms(candidate: dict[str, Any]) -> list[str]:
    terms: list[str] = []
    for key in ["selector", "container"]:
        value = str(candidate.get(key, ""))
        if value:
            terms.append(value)
    selector = str(candidate.get("selector", ""))
    terms.extend(part for part in selector.split(":") if part)
    declaration = str(candidate.get("declaration", ""))
    terms.extend(
        part
        for part in re.findall(r"[A-Za-z_][\w$]{3,}", declaration)
        if part not in {"void", "BOOL", "NSInteger", "NSUInteger"}
    )
    deduped: list[str] = []
    seen: set[str] = set()
    for term in terms:
        if term not in seen:
            seen.add(term)
            deduped.append(term)
    return deduped[:24]


def limited_lines(text: str, max_lines: int = 80, max_chars: int = 16000) -> str:
    lines = text.splitlines()[:max_lines]
    joined = "\n".join(lines)
    return joined[:max_chars]


def strings_evidence(binary: Path, terms: list[str], max_matches: int = 80) -> dict[str, Any]:
    if not binary or not binary.exists():
        return {"error": "binary not found", "matches": []}
    strings_cmd = shutil.which("strings")
    if not strings_cmd:
        return {"error": "strings command not found", "matches": []}
    result = run_command([strings_cmd, "-a", str(binary)], timeout=40)
    if result.returncode not in (0, None) and not result.stdout:
        return {"command": asdict(result), "matches": []}
    matches: list[dict[str, str]] = []
    lowered_terms = [(term, term.lower()) for term in terms]
    for line in result.stdout.splitlines():
        lower = line.lower()
        hit_terms = [term for term, lowered in lowered_terms if lowered in lower]
        if hit_terms:
            matches.append({"text": line[:500], "terms": hit_terms})
            if len(matches) >= max_matches:
                break
    return {"command": asdict(result), "matches": matches}


def symbol_evidence(binary: Path, terms: list[str], max_matches: int = 120) -> dict[str, Any]:
    if not binary or not binary.exists():
        return {"error": "binary not found", "matches": []}
    nm_cmd = shutil.which("nm")
    if not nm_cmd:
        return {"error": "nm command not found", "matches": []}
    result = run_command([nm_cmd, "-m", str(binary)], timeout=40)
    if result.returncode not in (0, None) and not result.stdout:
        return {"command": asdict(result), "matches": []}
    matches: list[dict[str, str]] = []
    lowered_terms = [(term, term.lower()) for term in terms]
    for line in result.stdout.splitlines():
        lower = line.lower()
        hit_terms = [term for term, lowered in lowered_terms if lowered in lower]
        if hit_terms:
            matches.append({"text": line[:500], "terms": hit_terms})
            if len(matches) >= max_matches:
                break
    return {"command": asdict(result), "matches": matches}


def binary_metadata(binary: Path | None) -> dict[str, Any]:
    if binary is None:
        return {}
    metadata: dict[str, Any] = {"path": str(binary), "exists": binary.exists()}
    if not binary.exists():
        return metadata
    metadata["file"] = asdict(run_command(["file", str(binary)], timeout=8))
    metadata["otool_L"] = asdict(run_command(["otool", "-L", str(binary)], timeout=20))
    metadata["dwarfdump_uuid"] = asdict(
        run_command(["dwarfdump", "--uuid", str(binary)], timeout=15)
    )
    return metadata


def client_evidence(paths: list[Path], terms: list[str]) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    for path in paths:
        item: dict[str, Any] = {"path": str(path), "exists": path.exists()}
        if path.exists():
            item["file"] = asdict(run_command(["file", str(path)], timeout=8))
            item["otool_L"] = asdict(run_command(["otool", "-L", str(path)], timeout=20))
            item["strings"] = strings_evidence(path, terms, max_matches=40)
        evidence.append(item)
    return evidence


def prompt_text(context: dict[str, Any]) -> str:
    candidate = context["candidate"]
    lines: list[str] = []
    lines.append("# MOTIF-Style Objective-C Signature Inference Task")
    lines.append("")
    lines.append(
        "Infer the most likely precise Objective-C signature for the candidate declaration. Preserve selector spelling and method arity. Return uncertainty explicitly when evidence is insufficient."
    )
    lines.append("")
    lines.append("## Candidate")
    lines.append("")
    lines.append(f"- ID: `{candidate['id']}`")
    lines.append(
        f"- Container: `{candidate.get('container_kind', 'unknown')} {candidate.get('container', 'unknown')}`"
    )
    lines.append(f"- Selector: `{candidate.get('selector', '')}`")
    lines.append(f"- Current declaration: `{candidate.get('declaration', '')}`")
    lines.append(f"- Return type: `{candidate.get('return_type', '')}`")
    lines.append(f"- Parameter types: `{', '.join(candidate.get('parameter_types', []))}`")
    lines.append("")
    lines.append("## Nearby Header Context")
    lines.append("")
    lines.append("```objc")
    for line in context["header_context"].get("lines", []):
        prefix = ">" if line["line"] == candidate.get("line") else " "
        lines.append(f"{prefix}{line['line']:5d}: {line['text']}")
    lines.append("```")
    lines.append("")
    if binary := context.get("binary"):
        lines.append("## Binary Metadata")
        lines.append("")
        lines.append(f"- Binary: `{binary.get('path', '')}`")
        file_text = (
            binary.get("file", {}).get("stdout") or binary.get("file", {}).get("stderr") or ""
        )
        if file_text:
            lines.append(f"- file: `{file_text}`")
        uuid_text = binary.get("dwarfdump_uuid", {}).get("stdout") or ""
        if uuid_text:
            lines.append("- UUID:")
            lines.append("  ```text")
            lines.extend(f"  {line}" for line in uuid_text.splitlines()[:6])
            lines.append("  ```")
        lines.append("")
    for section_name, key in [("Symbol Matches", "symbols"), ("String Matches", "strings")]:
        data = context.get(key, {})
        matches = data.get("matches", [])
        if matches:
            lines.append(f"## {section_name}")
            lines.append("")
            lines.append("```text")
            for match in matches[:40]:
                lines.append(match["text"])
            lines.append("```")
            lines.append("")
    if context.get("client_evidence"):
        lines.append("## Client Evidence")
        lines.append("")
        for item in context["client_evidence"]:
            lines.append(f"### `{item['path']}`")
            file_text = (
                item.get("file", {}).get("stdout") or item.get("file", {}).get("stderr") or ""
            )
            if file_text:
                lines.append(f"- file: `{file_text}`")
            string_matches = item.get("strings", {}).get("matches", [])
            if string_matches:
                lines.append("- Matching strings:")
                for match in string_matches[:12]:
                    lines.append(f"  - `{match['text']}`")
            lines.append("")
    lines.append("## Required Output")
    lines.append("")
    lines.append(
        "Return JSON with `candidate_id`, `proposed_declaration`, `changed_parts`, `evidence`, `validation_plan`, `confidence`, and `open_questions`."
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--candidate-json", required=True, type=Path, help="JSON output from objc_header_triage.py."
    )
    parser.add_argument("--candidate-id", required=True, type=int, help="Candidate ID to package.")
    parser.add_argument("--headers", required=True, type=Path, help="Header root used for triage.")
    parser.add_argument("--binary", type=Path, help="Extracted framework Mach-O binary.")
    parser.add_argument(
        "--client",
        action="append",
        type=Path,
        default=[],
        help="Optional client Mach-O path. Can be repeated.",
    )
    parser.add_argument("--output", required=True, type=Path, help="Context JSON output path.")
    parser.add_argument("--prompt-output", type=Path, help="Markdown prompt output path.")
    parser.add_argument(
        "--context-radius", type=int, default=20, help="Header context lines around candidate."
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    data = read_json(args.candidate_json)
    candidate = find_candidate(data, args.candidate_id)
    terms = selector_terms(candidate)
    context: dict[str, Any] = {
        "schema_version": "1.0",
        "candidate_source": str(args.candidate_json),
        "candidate": candidate,
        "search_terms": terms,
        "header_context": nearby_header_context(
            args.headers, candidate, radius=args.context_radius
        ),
        "binary": binary_metadata(args.binary) if args.binary else None,
        "symbols": symbol_evidence(args.binary, terms) if args.binary else {"matches": []},
        "strings": strings_evidence(args.binary, terms) if args.binary else {"matches": []},
        "client_evidence": client_evidence(args.client, terms) if args.client else [],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(context, indent=2, sort_keys=True), encoding="utf-8")
    if args.prompt_output:
        args.prompt_output.parent.mkdir(parents=True, exist_ok=True)
        args.prompt_output.write_text(prompt_text(context), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
