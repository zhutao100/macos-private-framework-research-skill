#!/usr/bin/env python3
"""Lint reconstructed Objective-C headers and optionally run clang syntax validation."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

METHOD_START_RE = re.compile(r"^\s*[+-]\s*\(")
METHOD_RE = re.compile(r"^\s*([+-])\s*\(([^)]*)\)\s*(.*?)\s*;\s*$")
IDENTIFIER_RE = re.compile(r"[A-Za-z_][\w$]*\Z")
INTERFACE_OR_PROTOCOL_RE = re.compile(r"^\s*@(interface|protocol)\s+([A-Za-z_][\w$]*)")


@dataclass(frozen=True)
class Diagnostic:
    severity: str
    code: str
    file: str
    line: int
    message: str
    declaration: str = ""


@dataclass(frozen=True)
class CommandResult:
    command: list[str]
    returncode: int | None
    stdout: str
    stderr: str


def run_command(command: list[str], timeout: int = 60) -> CommandResult:
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


def iter_header_files(headers: Path) -> list[Path]:
    if headers.is_file():
        return [headers]
    return sorted(path for path in headers.rglob("*.h") if path.is_file())


def collapse_method_lines(text: str) -> list[tuple[int, str, bool]]:
    result: list[tuple[int, str, bool]] = []
    current: list[str] = []
    start_line = 0
    in_method = False
    for line_no, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if not in_method and METHOD_START_RE.match(stripped):
            in_method = True
            start_line = line_no
            current = [stripped]
            if stripped.endswith(";"):
                result.append((start_line, " ".join(current), True))
                in_method = False
            continue
        if in_method:
            current.append(stripped)
            if stripped.endswith(";"):
                result.append((start_line, " ".join(current), True))
                in_method = False
    if in_method and current:
        result.append((start_line, " ".join(current), False))
    return result


def selector_labels_from_body(body: str) -> list[str]:
    labels: list[str] = []
    paren_depth = 0
    brace_depth = 0
    for index, char in enumerate(body):
        if char == "(":
            paren_depth += 1
        elif char == ")" and paren_depth:
            paren_depth -= 1
        elif char == "{":
            brace_depth += 1
        elif char == "}" and brace_depth:
            brace_depth -= 1
        elif char == ":" and paren_depth == 0 and brace_depth == 0:
            end = index
            while end > 0 and body[end - 1].isspace():
                end -= 1
            start = end
            while start > 0 and (body[start - 1].isalnum() or body[start - 1] in "_$"):
                start -= 1
            label = body[start:end]
            if IDENTIFIER_RE.match(label):
                labels.append(label)
    return labels


def selector_from_body(body: str) -> str:
    labels = selector_labels_from_body(body)
    if labels:
        return "".join(f"{label}:" for label in labels)
    return re.split(r"\s+", body.strip(), maxsplit=1)[0].strip(";")


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


def lint_type(
    type_text: str, file: str, line: int, declaration: str, role: str
) -> list[Diagnostic]:
    t = normalize_type(type_text)
    diagnostics: list[Diagnostic] = []
    if re.search(r"\bstruct\s*\{", t):
        diagnostics.append(
            Diagnostic(
                "error",
                "anonymous-struct",
                file,
                line,
                f"{role} uses inline anonymous struct; recover a named typedef/layout",
                declaration,
            )
        )
    if re.search(r"(^|[\s(<,])\?(?:[\s>),]|$)", t):
        diagnostics.append(
            Diagnostic(
                "error",
                "unknown-type-marker",
                file,
                line,
                f"{role} contains unknown type marker `?`",
                declaration,
            )
        )
    if "void *" in t or "void*" in t:
        diagnostics.append(
            Diagnostic(
                "warning",
                "void-pointer",
                file,
                line,
                f"{role} is a void pointer; document pointee semantics or evidence gap",
                declaration,
            )
        )
    if t == "id" or t == "__kindof id":
        diagnostics.append(
            Diagnostic(
                "warning",
                "raw-id",
                file,
                line,
                f"{role} is raw id; recover class/protocol bound where possible",
                declaration,
            )
        )
    if (
        re.search(
            r"\b(NSArray|NSMutableArray|NSDictionary|NSMutableDictionary|NSSet|NSMutableSet)\s*\*",
            t,
        )
        and "<" not in t
    ):
        diagnostics.append(
            Diagnostic(
                "warning",
                "raw-collection",
                file,
                line,
                f"{role} is a raw collection; recover lightweight generic type",
                declaration,
            )
        )
    if "^" in t and "void (^)(" not in t and "(^" not in t:
        diagnostics.append(
            Diagnostic(
                "warning",
                "block-shape",
                file,
                line,
                f"{role} contains block marker; verify block return and parameter shape",
                declaration,
            )
        )
    return diagnostics


def lint_header(path: Path, root: Path) -> list[Diagnostic]:
    rel = str(path.relative_to(root) if root.is_dir() else path.name)
    text = path.read_text(encoding="utf-8", errors="replace")
    diagnostics: list[Diagnostic] = []

    if text.count("@interface") + text.count("@protocol") > 0 and text.count("@end") == 0:
        diagnostics.append(
            Diagnostic(
                "error",
                "missing-end",
                rel,
                1,
                "header declares interface/protocol but no @end was found",
            )
        )

    for line_no, declaration, complete in collapse_method_lines(text):
        if not complete:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "unterminated-method",
                    rel,
                    line_no,
                    "method declaration is not terminated by semicolon",
                    declaration,
                )
            )
            continue
        match = METHOD_RE.match(declaration)
        if not match:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "malformed-method",
                    rel,
                    line_no,
                    "method declaration does not match Objective-C method syntax",
                    declaration,
                )
            )
            continue
        _, return_type, body = match.groups()
        selector = selector_from_body(body)
        colon_count = selector.count(":")
        param_types = extract_parameter_types(body)
        if colon_count != len(param_types):
            diagnostics.append(
                Diagnostic(
                    "error",
                    "selector-arity-mismatch",
                    rel,
                    line_no,
                    f"selector `{selector}` has {colon_count} labels but {len(param_types)} parameter type groups",
                    declaration,
                )
            )
        if "..." in declaration:
            diagnostics.append(
                Diagnostic(
                    "warning",
                    "variadic",
                    rel,
                    line_no,
                    "variadic declaration requires exact caller evidence",
                    declaration,
                )
            )
        diagnostics.extend(lint_type(return_type, rel, line_no, declaration, "return type"))
        for index, param_type in enumerate(param_types, start=1):
            diagnostics.extend(
                lint_type(param_type, rel, line_no, declaration, f"parameter {index}")
            )
    return diagnostics


def sdk_path() -> str | None:
    result = run_command(["xcrun", "--sdk", "macosx", "--show-sdk-path"], timeout=10)
    if result.returncode == 0 and result.stdout:
        return result.stdout.splitlines()[0]
    return None


def compile_headers(headers: Path, extra_include: list[Path]) -> CommandResult:
    clang = shutil.which("clang") or shutil.which("cc")
    if not clang:
        return CommandResult(["clang"], None, "", "clang not found")
    header_files = iter_header_files(headers)
    with tempfile.TemporaryDirectory(prefix="objc-header-lint-") as tmp:
        tmp_path = Path(tmp)
        wrapper = Path(tmp) / "validate_headers.m"
        lines = [
            "#import <Foundation/Foundation.h>",
            "#import <CoreFoundation/CoreFoundation.h>",
            "#import <CoreGraphics/CoreGraphics.h>",
            "#import <QuartzCore/QuartzCore.h>",
            "#import <Metal/Metal.h>",
            "#import <IOSurface/IOSurface.h>",
        ]
        for header in header_files:
            escaped = str(header.resolve()).replace('"', '\\"')
            lines.append(f'#import "{escaped}"')
        lines.append("int main(void) { return 0; }")
        wrapper.write_text("\n".join(lines), encoding="utf-8")
        command = [
            clang,
            "-x",
            "objective-c",
            "-fsyntax-only",
            "-fmodules",
            f"-fmodules-cache-path={tmp_path / 'module-cache'}",
            "-ferror-limit=12",
            "-Wno-objc-root-class",
            "-Wno-unknown-pragmas",
            "-Wno-nullability-completeness",
        ]
        resolved_sdk = sdk_path()
        if resolved_sdk:
            command.extend(["-isysroot", resolved_sdk])
        for include in extra_include:
            command.extend(["-I", str(include)])
        if headers.is_dir():
            command.extend(["-I", str(headers.resolve())])
        command.append(str(wrapper))
        return run_command(command, timeout=90)


def abbreviate(text: str, max_chars: int) -> str:
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    if max_chars <= 3:
        return "." * max_chars
    return f"{text[: max_chars - 3]}..."


def abbreviate_lines(text: str, max_chars: int, max_line_chars: int) -> str:
    line_limited = "\n".join(
        abbreviate(line, max_line_chars) if max_line_chars > 0 else line
        for line in text.splitlines()
    )
    return abbreviate(line_limited, max_chars)


def render_markdown(
    headers: Path,
    diagnostics: list[Diagnostic],
    compile_result: CommandResult | None,
    diagnostic_limit: int = 200,
    max_message_chars: int = 220,
    max_compile_output_chars: int = 6000,
    max_compile_line_chars: int = 500,
) -> str:
    counts: dict[str, int] = {"error": 0, "warning": 0, "info": 0}
    for diagnostic in diagnostics:
        counts[diagnostic.severity] = counts.get(diagnostic.severity, 0) + 1
    compile_failed = bool(compile_result is not None and compile_result.returncode not in (0, None))
    lines: list[str] = [
        "# Objective-C Signature Lint",
        "",
        f"Headers: `{headers}`",
        f"Structural errors: `{counts.get('error', 0)}`",
        f"Warnings: `{counts.get('warning', 0)}`",
        f"Clang syntax check: `{'failed' if compile_failed else 'passed' if compile_result is not None else 'not run'}`",
        f"Total blocking issues: `{counts.get('error', 0) + (1 if compile_failed else 0)}`",
        f"Rendered diagnostics: `{min(len(diagnostics), diagnostic_limit) if diagnostic_limit > 0 else len(diagnostics)}`",
        "",
    ]
    if diagnostics:
        lines.extend(["| Severity | Code | Location | Message |", "|---|---|---|---|"])
        visible_diagnostics = (
            diagnostics[:diagnostic_limit]
            if diagnostic_limit and diagnostic_limit > 0
            else diagnostics
        )
        for diagnostic in visible_diagnostics:
            lines.append(
                f"| {diagnostic.severity} | `{diagnostic.code}` | `{diagnostic.file}:{diagnostic.line}` | {abbreviate(diagnostic.message, max_message_chars)} |"
            )
        if len(visible_diagnostics) < len(diagnostics):
            lines.append("")
            lines.append(
                f"Markdown is limited to the first `{len(visible_diagnostics)}` diagnostics. JSON contains all `{len(diagnostics)}` diagnostics."
            )
        lines.append("")
    else:
        lines.append("No structural diagnostics from built-in checks.")
        lines.append("")
    if compile_result is not None:
        lines.append("## Clang Syntax Check")
        lines.append("")
        lines.append(f"- Return code: `{compile_result.returncode}`")
        lines.append(f"- Command: `{' '.join(compile_result.command)}`")
        text = compile_result.stdout or compile_result.stderr
        if text:
            rendered_text = abbreviate_lines(text, max_compile_output_chars, max_compile_line_chars)
            lines.append("```text")
            lines.append(rendered_text)
            lines.append("```")
            if rendered_text != text:
                lines.append(
                    "Clang output abbreviated in Markdown; JSON contains the complete output."
                )
        else:
            lines.append("No clang output.")
        lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "Treat `error` diagnostics as blocking for inferred-signature acceptance. Treat `warning` diagnostics as explicit evidence gaps unless disassembly, caller behavior, or runtime metadata supports the remaining ambiguity."
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--headers", required=True, type=Path, help="Header file or directory.")
    parser.add_argument("--output", type=Path, help="Markdown report path. Defaults to stdout.")
    parser.add_argument("--json-output", type=Path, help="JSON report path.")
    parser.add_argument(
        "--compile",
        action="store_true",
        help="Run clang -fsyntax-only against a generated wrapper.",
    )
    parser.add_argument(
        "--include",
        action="append",
        type=Path,
        default=[],
        help="Extra include path for clang. Can be repeated.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=200,
        help="Limit diagnostics rendered in Markdown. Use 0 for all diagnostics. JSON always contains all diagnostics.",
    )
    parser.add_argument(
        "--max-message-chars",
        type=int,
        default=220,
        help="Maximum characters for each diagnostic message in Markdown.",
    )
    parser.add_argument(
        "--max-compile-output-chars",
        type=int,
        default=6000,
        help="Maximum clang output characters in Markdown; JSON remains complete.",
    )
    parser.add_argument(
        "--max-compile-line-chars",
        type=int,
        default=500,
        help="Maximum characters for each clang output line in Markdown; JSON remains complete.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.headers.exists():
        raise SystemExit(f"headers path not found: {args.headers}")
    root = args.headers if args.headers.is_dir() else args.headers.parent
    diagnostics: list[Diagnostic] = []
    for header in iter_header_files(args.headers):
        diagnostics.extend(lint_header(header, root))
    compile_result = compile_headers(args.headers, args.include) if args.compile else None
    markdown = render_markdown(
        args.headers,
        diagnostics,
        compile_result,
        diagnostic_limit=args.limit,
        max_message_chars=args.max_message_chars,
        max_compile_output_chars=args.max_compile_output_chars,
        max_compile_line_chars=args.max_compile_line_chars,
    )
    data: dict[str, Any] = {
        "schema_version": "1.0",
        "headers": str(args.headers),
        "diagnostics": [asdict(item) for item in diagnostics],
        "compile": asdict(compile_result) if compile_result else None,
        "summary": {
            "errors": sum(1 for item in diagnostics if item.severity == "error")
            + (1 if compile_result and compile_result.returncode not in (0, None) else 0),
            "warnings": sum(1 for item in diagnostics if item.severity == "warning"),
        },
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(markdown, encoding="utf-8")
    else:
        print(markdown)
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
