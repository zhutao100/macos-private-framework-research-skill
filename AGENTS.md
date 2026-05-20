# Agent Development Notes

This repository contains one installable skill: `macos-private-framework-research`.

Use the inventory → dependency discovery → dyld extraction → header reconstruction → candidate triage → type-inference context → linter feedback → report loop as the default. Keep claims grounded in commands, file paths, tool versions, and the exact macOS build being analyzed.

## Standards

Maintain compatibility with Codex CLI skills and the Open Agent Skills layout:

- Root repository: `README.md`, `AGENTS.md`, and one or more skill directories.
- Skill directory name must match `SKILL.md` frontmatter `name`.
- `SKILL.md` must include `name` and `description`; keep it concise and use references for detail.
- Put deterministic tooling in `scripts/`.
- Put reusable templates and config snippets in `assets/`.
- Put focused, conditionally loaded documentation in `references/`.
- Keep file references one level deep from `SKILL.md`.
- Keep bundled `references/`, `scripts/`, and `assets/` files reachable from the skill instructions or used scripts.

## Development Workflow

After changing scripts, metadata, assets, or references, run:

```bash
macos-private-framework-research/scripts/validate_skill_repo.py .
python3 -m py_compile macos-private-framework-research/scripts/*.py
bash -n macos-private-framework-research/scripts/*.sh
bash -n framework-surveys/skylight-agent-survey/tools/*.zsh
python3 -m py_compile framework-surveys/skylight-agent-survey/tools/*.py
```

On a macOS host, also run:

```bash
macos-private-framework-research/scripts/macos_private_framework_inventory.py \
  --output /tmp/macos-pf-inventory.md \
  --json-output /tmp/macos-pf-inventory.json
macos-private-framework-research/scripts/discover_private_frameworks.py \
  --output /tmp/finder-private-frameworks.md \
  --json-output /tmp/finder-private-frameworks.json \
  /System/Library/CoreServices/Finder.app
```

## Research Boundaries

- Keep scripts read-only by default. Scripts may write reports, extracted copies, and generated context files only to explicit output paths.
- Treat decompiler output, LLM-inferred types, and runtime dumps as hypotheses until corroborated by static metadata, disassembly, client usage, or compiler/linter checks.
- Use local disposable workspaces for all extraction and validation. Do not modify `/System`, `/Library`, installed apps, or dyld caches.

## Reference Checkouts

The `reference-checkout/` directory contains source repositories of the tools and skills used in this research; refer to them when you need to understand how a tool works.

- `MxIris-Reverse-Engineering/RuntimeViewer`
- `nst/RuntimeBrowser`
- `nygard/class-dump`
- `blacktop/ipsw`
- `keith/dyld-shared-cache-extractor`
- `zhutao100/hopper-disassembler-skill`
