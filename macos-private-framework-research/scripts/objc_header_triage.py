#!/usr/bin/env python3
"""Rank underspecified Objective-C declarations in reconstructed headers."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

INTERFACE_RE = re.compile(r"^\s*@interface\s+([A-Za-z_][\w$]*)\b")
PROTOCOL_RE = re.compile(r"^\s*@protocol\s+([A-Za-z_][\w$]*)\b")
CATEGORY_RE = re.compile(r"^\s*@interface\s+([A-Za-z_][\w$]*)\s*\(([^)]*)\)")
METHOD_RE = re.compile(r"^\s*([+-])\s*\(([^)]*)\)\s*(.*?)\s*;\s*$")
LABEL_RE = re.compile(r"([A-Za-z_][\w$]*)\s*:")

SEVERE_PATTERNS = [
    (
        "anonymous-struct",
        re.compile(r"\bstruct\s*\{"),
        "inline anonymous struct requires a named typedef or recovered layout",
    ),
    (
        "function-pointer",
        re.compile(r"\(\s*\*\s*\)"),
        "function pointer type needs exact signature",
    ),
    (
        "unknown-objc-encoding",
        re.compile(r"(^|[\s(<,])\?(?:[\s>),]|$)"),
        "unknown type encoding marker",
    ),
]

AMBIGUOUS_TYPE_PATTERNS = [
    ("raw-id", re.compile(r"^(?:id|__kindof\s+id)$"), "raw id lacks class/protocol constraint"),
    ("void-pointer", re.compile(r"\bvoid\s*\*"), "void pointer lacks pointee semantics"),
    (
        "raw-collection",
        re.compile(
            r"\b(NSArray|NSMutableArray|NSDictionary|NSMutableDictionary|NSSet|NSMutableSet)\s*\*"
        ),
        "collection lacks lightweight generic type",
    ),
    (
        "cf-type",
        re.compile(r"\bCF[A-Za-z0-9_]+Ref\b"),
        "CoreFoundation reference may need ownership/bridging context",
    ),
    ("block", re.compile(r"\^"), "block type often needs parameter and return recovery"),
    (
        "sel",
        re.compile(r"^SEL$"),
        "selector argument should be cross-checked against caller behavior",
    ),
]

XPC_SELECTOR_RE = re.compile(r"\b(xpc|XPC|connection|listener|remote|reply|completion|handler)\b")
DELEGATE_SELECTOR_RE = re.compile(r"\b(delegate|Delegate|dataSource|DataSource)\b")


@dataclass
class Candidate:
    id: int
    file: str
    line: int
    container_kind: str
    container: str
    method_kind: str
    selector: str
    declaration: str
    return_type: str
    parameter_types: list[str]
    score: int
    reasons: list[dict[str, str]] = field(default_factory=list)
    context_hint: str = ""


def read_header_lines(path: Path) -> list[tuple[int, str]]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    return list(enumerate(text.splitlines(), start=1))


def iter_header_files(headers: Path) -> list[Path]:
    if headers.is_file():
        return [headers]
    return sorted(path for path in headers.rglob("*.h") if path.is_file())


def collapse_method_lines(lines: list[tuple[int, str]]) -> list[tuple[int, str]]:
    result: list[tuple[int, str]] = []
    current: list[str] = []
    start_line = 0
    in_method = False
    for line_no, raw in lines:
        stripped = raw.strip()
        if not in_method and re.match(r"^[+-]\s*\(", stripped):
            in_method = True
            start_line = line_no
            current = [stripped]
            if stripped.endswith(";"):
                result.append((start_line, " ".join(current)))
                in_method = False
            continue
        if in_method:
            current.append(stripped)
            if stripped.endswith(";"):
                result.append((start_line, " ".join(current)))
                in_method = False
    return result


def container_at_line(lines: list[tuple[int, str]], target_line: int) -> tuple[str, str]:
    kind = "unknown"
    name = "unknown"
    for line_no, line in lines:
        if line_no > target_line:
            break
        if match := CATEGORY_RE.match(line):
            kind = "category"
            name = f"{match.group(1)}({match.group(2)})"
            continue
        if match := INTERFACE_RE.match(line):
            kind = "class"
            name = match.group(1)
            continue
        if match := PROTOCOL_RE.match(line):
            kind = "protocol"
            name = match.group(1)
            continue
        if line.strip() == "@end":
            kind = "unknown"
            name = "unknown"
    return kind, name


def selector_from_method_body(body: str) -> str:
    labels = LABEL_RE.findall(body)
    if labels:
        return "".join(f"{label}:" for label in labels)
    token = re.split(r"\s+", body.strip(), maxsplit=1)[0]
    return token.strip(";")


def normalize_type(type_text: str) -> str:
    return re.sub(r"\s+", " ", type_text.strip())


def extract_parameter_types(method_body: str) -> list[str]:
    """Extract Objective-C parameter type groups, preserving nested block parentheses."""
    types: list[str] = []
    index = 0
    while index < len(method_body):
        colon = method_body.find(":", index)
        if colon == -1:
            break
        cursor = colon + 1
        while cursor < len(method_body) and method_body[cursor].isspace():
            cursor += 1
        if cursor >= len(method_body) or method_body[cursor] != "(":
            index = cursor + 1
            continue
        depth = 0
        start = cursor + 1
        cursor += 1
        while cursor < len(method_body):
            char = method_body[cursor]
            if char == "(":
                depth += 1
            elif char == ")":
                if depth == 0:
                    types.append(normalize_type(method_body[start:cursor]))
                    cursor += 1
                    break
                depth -= 1
            cursor += 1
        index = cursor
    return types


def reasons_for_type(type_text: str) -> list[dict[str, str]]:
    reasons: list[dict[str, str]] = []
    normalized = normalize_type(type_text)
    for code, pattern, message in SEVERE_PATTERNS:
        if pattern.search(normalized):
            reasons.append({"code": code, "message": message, "type": normalized})
    for code, pattern, message in AMBIGUOUS_TYPE_PATTERNS:
        if pattern.search(normalized):
            if code == "raw-collection" and "<" in normalized:
                continue
            reasons.append({"code": code, "message": message, "type": normalized})
    if normalized.startswith("NSError **") or normalized == "NSError **":
        reasons.append(
            {
                "code": "nserror-out",
                "message": "NSError out parameter needs caller-side success/failure semantics",
                "type": normalized,
            }
        )
    return reasons


def score_reasons(reasons: list[dict[str, str]], selector: str, container: str) -> tuple[int, str]:
    weights = {
        "anonymous-struct": 9,
        "function-pointer": 8,
        "unknown-objc-encoding": 8,
        "void-pointer": 7,
        "block": 6,
        "raw-id": 5,
        "raw-collection": 4,
        "cf-type": 4,
        "nserror-out": 3,
        "sel": 3,
        "xpc-selector": 5,
        "delegate-selector": 3,
    }
    score = sum(weights.get(reason["code"], 1) for reason in reasons)
    hints: list[str] = []
    if XPC_SELECTOR_RE.search(selector) or XPC_SELECTOR_RE.search(container):
        reasons.append(
            {
                "code": "xpc-selector",
                "message": "selector/container suggests XPC or callback boundary",
                "type": "selector",
            }
        )
        score += weights["xpc-selector"]
        hints.append("XPC/callback boundary")
    if DELEGATE_SELECTOR_RE.search(selector):
        reasons.append(
            {
                "code": "delegate-selector",
                "message": "selector suggests delegate/data-source contract",
                "type": "selector",
            }
        )
        score += weights["delegate-selector"]
        hints.append("delegate contract")
    if any(reason["code"] in {"anonymous-struct", "void-pointer", "block"} for reason in reasons):
        hints.append("requires disassembly/client-use evidence")
    if any(reason["code"] == "raw-id" for reason in reasons):
        hints.append("recover class/protocol/generic constraint")
    return score, "; ".join(dict.fromkeys(hints))


def analyze_header(header: Path, root: Path) -> list[Candidate]:
    lines = read_header_lines(header)
    candidates: list[Candidate] = []
    for line_no, declaration in collapse_method_lines(lines):
        match = METHOD_RE.match(declaration)
        if not match:
            continue
        method_kind, return_type, body = match.groups()
        return_type = normalize_type(return_type)
        parameter_types = extract_parameter_types(body)
        selector = selector_from_method_body(body)
        reasons = reasons_for_type(return_type)
        for param in parameter_types:
            reasons.extend(reasons_for_type(param))
        if not reasons and len(parameter_types) == 0:
            continue
        container_kind, container = container_at_line(lines, line_no)
        score, hint = score_reasons(reasons, selector, container)
        if score == 0:
            continue
        rel = header.relative_to(root) if root.is_dir() else header.name
        candidates.append(
            Candidate(
                id=0,
                file=str(rel),
                line=line_no,
                container_kind=container_kind,
                container=container,
                method_kind=method_kind,
                selector=selector,
                declaration=declaration,
                return_type=return_type,
                parameter_types=parameter_types,
                score=score,
                reasons=reasons,
                context_hint=hint,
            )
        )
    return candidates


def build_candidates(headers: Path) -> list[Candidate]:
    root = headers if headers.is_dir() else headers.parent
    candidates: list[Candidate] = []
    for header in iter_header_files(headers):
        candidates.extend(analyze_header(header, root))
    candidates.sort(key=lambda item: (-item.score, item.file, item.line))
    for index, candidate in enumerate(candidates, start=1):
        candidate.id = index
    return candidates


def render_markdown(headers: Path, candidates: list[Candidate]) -> str:
    lines: list[str] = [
        "# Objective-C Header Triage",
        "",
        f"Headers: `{headers}`",
        f"Candidates: `{len(candidates)}`",
        "",
    ]
    if not candidates:
        lines.append(
            "No underspecified Objective-C declarations matched the built-in triage rules."
        )
        return "\n".join(lines)

    lines.extend(
        [
            "| ID | Score | Container | Selector | Location | Primary reasons |",
            "|---:|---:|---|---|---|---|",
        ]
    )
    for candidate in candidates:
        reason_codes = ", ".join(dict.fromkeys(reason["code"] for reason in candidate.reasons))
        lines.append(
            f"| {candidate.id} | {candidate.score} | `{candidate.container}` | `{candidate.selector}` | `{candidate.file}:{candidate.line}` | {reason_codes} |"
        )
    lines.append("")
    lines.append("## Candidate Details")
    lines.append("")
    for candidate in candidates:
        lines.append(f"### {candidate.id}. `{candidate.container} {candidate.selector}`")
        lines.append("")
        lines.append(f"- Location: `{candidate.file}:{candidate.line}`")
        lines.append(f"- Score: `{candidate.score}`")
        if candidate.context_hint:
            lines.append(f"- Context hint: {candidate.context_hint}")
        lines.append("- Declaration:")
        lines.append("  ```objc")
        lines.append(f"  {candidate.declaration}")
        lines.append("  ```")
        lines.append("- Reasons:")
        for reason in candidate.reasons:
            lines.append(f"  - `{reason['code']}` on `{reason['type']}`: {reason['message']}")
        lines.append("")
    return "\n".join(lines)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--headers", required=True, type=Path, help="Header file or directory of .h files."
    )
    parser.add_argument("--output", type=Path, help="Markdown report path. Defaults to stdout.")
    parser.add_argument("--json-output", type=Path, help="JSON candidate output path.")
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Limit rendered candidates in Markdown; JSON always contains all candidates.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.headers.exists():
        raise SystemExit(f"headers path not found: {args.headers}")
    candidates = build_candidates(args.headers)
    visible_candidates = candidates[: args.limit] if args.limit and args.limit > 0 else candidates
    markdown = render_markdown(args.headers, visible_candidates)
    data: dict[str, Any] = {
        "schema_version": "1.0",
        "headers": str(args.headers),
        "candidate_count": len(candidates),
        "candidates": [asdict(candidate) for candidate in candidates],
    }
    if args.output:
        write_text(args.output, markdown)
    else:
        print(markdown)
    if args.json_output:
        write_text(args.json_output, json.dumps(data, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
