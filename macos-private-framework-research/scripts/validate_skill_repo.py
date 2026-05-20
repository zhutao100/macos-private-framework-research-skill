#!/usr/bin/env python3
"""Validate a Codex/Open Agent Skills repository layout."""

from __future__ import annotations

import argparse
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
IGNORED_REPO_NAMES = {".DS_Store", "__pycache__"}


@dataclass
class Finding:
    severity: str
    path: str
    message: str


def parse_frontmatter(skill_md: Path) -> dict[str, str]:
    text = skill_md.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    fields: dict[str, str] = {}
    for raw_line in match.group(1).splitlines():
        if not raw_line.strip() or raw_line.startswith(" "):
            continue
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        fields[key.strip()] = value.strip().strip('"')
    return fields


def run_syntax(command: list[str]) -> tuple[int | None, str]:
    try:
        proc = subprocess.run(
            command,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=30,
        )
        return proc.returncode, (proc.stdout + proc.stderr).strip()
    except FileNotFoundError:
        return None, "command not found"
    except subprocess.TimeoutExpired:
        return None, "timeout"


def validate_skill(skill_dir: Path, repo_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        findings.append(Finding("error", str(skill_dir.relative_to(repo_root)), "missing SKILL.md"))
        return findings
    fields = parse_frontmatter(skill_md)
    name = fields.get("name", "")
    description = fields.get("description", "")
    if not name:
        findings.append(
            Finding("error", str(skill_md.relative_to(repo_root)), "missing frontmatter name")
        )
    elif name != skill_dir.name:
        findings.append(
            Finding(
                "error",
                str(skill_md.relative_to(repo_root)),
                f"frontmatter name `{name}` does not match directory `{skill_dir.name}`",
            )
        )
    elif not NAME_RE.match(name):
        findings.append(
            Finding(
                "error",
                str(skill_md.relative_to(repo_root)),
                "name must be lowercase letters, digits, and hyphens",
            )
        )
    if not description:
        findings.append(
            Finding(
                "error", str(skill_md.relative_to(repo_root)), "missing frontmatter description"
            )
        )
    elif len(description) > 1024:
        findings.append(
            Finding(
                "warning",
                str(skill_md.relative_to(repo_root)),
                "description is longer than 1024 characters",
            )
        )

    text = skill_md.read_text(encoding="utf-8")
    for directory_name in ["scripts", "references", "assets"]:
        directory = skill_dir / directory_name
        if not directory.exists():
            continue
        for child in sorted(
            path
            for path in directory.iterdir()
            if path.is_file() and path.name not in IGNORED_REPO_NAMES
        ):
            rel = child.relative_to(skill_dir)
            if child.name not in text and str(rel) not in text:
                findings.append(
                    Finding("warning", str(rel), "file is not referenced from SKILL.md")
                )
            if directory_name == "scripts":
                first_line = child.read_text(encoding="utf-8", errors="replace").splitlines()[:1]
                if not first_line or not first_line[0].startswith("#!"):
                    findings.append(Finding("error", str(rel), "script missing shebang"))
                if not child.stat().st_mode & 0o111:
                    findings.append(Finding("error", str(rel), "script is not executable"))
                if child.suffix == ".py":
                    rc, output = run_syntax(["python3", "-m", "py_compile", str(child)])
                    if rc not in (0, None):
                        findings.append(
                            Finding("error", str(rel), f"python syntax failed: {output[:500]}")
                        )
                    elif rc is None:
                        findings.append(
                            Finding("warning", str(rel), f"python syntax not checked: {output}")
                        )
                elif child.suffix == ".sh":
                    rc, output = run_syntax(["bash", "-n", str(child)])
                    if rc not in (0, None):
                        findings.append(
                            Finding("error", str(rel), f"bash syntax failed: {output[:500]}")
                        )
                    elif rc is None:
                        findings.append(
                            Finding("warning", str(rel), f"bash syntax not checked: {output}")
                        )
                elif child.suffix == ".swift":
                    rc, output = run_syntax(["swiftc", "-parse", str(child)])
                    if rc not in (0, None):
                        findings.append(
                            Finding("error", str(rel), f"swift syntax failed: {output[:500]}")
                        )
                    elif rc is None:
                        findings.append(
                            Finding("warning", str(rel), f"swift syntax not checked: {output}")
                        )
    return findings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo", type=Path, help="Repository root to validate.")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = args.repo.resolve()
    findings: list[Finding] = []
    for required in ["README.md", "AGENTS.md"]:
        if not (repo / required).exists():
            findings.append(Finding("error", required, "required root file is missing"))
    skill_dirs = sorted(
        path for path in repo.iterdir() if path.is_dir() and not path.name.startswith(".")
    )
    skill_dirs = [path for path in skill_dirs if (path / "SKILL.md").exists()]
    if not skill_dirs:
        findings.append(Finding("error", str(repo), "no skill directory with SKILL.md found"))
    for skill_dir in skill_dirs:
        findings.extend(validate_skill(skill_dir, repo))

    for finding in findings:
        print(f"{finding.severity}: {finding.path}: {finding.message}")

    error_count = sum(1 for finding in findings if finding.severity == "error")
    warning_count = sum(1 for finding in findings if finding.severity == "warning")
    print(f"validated {len(skill_dirs)} skill(s); errors={error_count}; warnings={warning_count}")
    if error_count or (args.strict and warning_count):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
