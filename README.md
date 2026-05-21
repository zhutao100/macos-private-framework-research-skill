# macOS Private Framework Research Skill

Installable agent skill repository for researching modern macOS private frameworks with a repeatable, evidence-backed workflow.

## Skill

`macos-private-framework-research` helps agents discover private-framework dependencies, extract dyld shared cache images, reconstruct Objective-C/Swift interfaces, triage underspecified signatures, and run an LLM-assisted type-inference loop with static validation.

Primary entrypoint:

```text
macos-private-framework-research/SKILL.md
```

## Clone

Reference checkouts are optional source signposts. Avoid initializing them from `git clone --recurse-submodules --shallow-submodules`: Git runs recursive submodule checkout with `--no-single-branch`, which makes high-ref repositories fetch every branch/tag tip at depth 1.

Use a two-step checkout when reference sources are needed:

```bash
git clone -o zhutao100 https://github.com/zhutao100/macos-private-framework-research-skill.git
cd macos-private-framework-research-skill
git submodule update --init --recursive --depth 1 --single-branch --jobs 4
```

`reference-checkout/hammerspoon` is opt-in because the recursive clone path is especially large. Initialize it only when needed:

```bash
git submodule update --init --depth 1 --single-branch --checkout -- reference-checkout/hammerspoon
```

## Install

User-scoped install for Codex CLI and other Open Agent Skills-compatible clients:

```bash
macos-private-framework-research/scripts/install_codex_skill.sh --replace
```

Repository-scoped install:

```bash
macos-private-framework-research/scripts/install_codex_skill.sh --scope repo --replace
```

Manual install:

```bash
mkdir -p "$HOME/.agents/skills"
cp -R macos-private-framework-research "$HOME/.agents/skills/"
```

## Common Commands

Inventory host, dyld cache, and tools:

```bash
macos-private-framework-research/scripts/macos_private_framework_inventory.py \
  --output /tmp/macos-pf-inventory.md \
  --json-output /tmp/macos-pf-inventory.json
```

Resolve optional non-built-in toolchains only when a workflow needs them:

```bash
macos-private-framework-research/scripts/resolve_toolchains.py ipsw dyld-shared-cache-extractor
```

Discover private-framework usage by a system app or client binary:

```bash
macos-private-framework-research/scripts/discover_private_frameworks.py \
  --output /tmp/disk-utility-private-frameworks.md \
  --json-output /tmp/disk-utility-private-frameworks.json \
  "/System/Applications/Utilities/Disk Utility.app"
```

Extract a framework from the dyld shared cache:

```bash
macos-private-framework-research/scripts/extract_dyld_framework.sh \
  --framework DiskManagement \
  --output-dir /tmp/macos-private-frameworks
```

Use `--enrich-objc-stubs` only when extraction-time enrichment is needed; run `ipsw class-dump` separately for bounded header output.

Build a capped framework manifest before loading raw dependency, symbol, or string dumps:

```bash
macos-private-framework-research/scripts/framework_macho_manifest.py \
  --framework DiskManagement \
  --json-output /tmp/DiskManagement.manifest.json \
  --markdown-output /tmp/DiskManagement.manifest.md
```

Probe candidate C symbols and Objective-C classes without calling them:

```bash
macos-private-framework-research/scripts/dlopen_symbol_probe.swift \
  --image /System/Library/PrivateFrameworks/DiskManagement.framework/DiskManagement \
  --symbol CandidateFunction \
  --class CandidateClass \
  --json
```

Triage reconstructed headers for underspecified method signatures:

```bash
macos-private-framework-research/scripts/objc_header_triage.py \
  --headers /tmp/DiskManagement.headers \
  --output /tmp/DiskManagement.candidates.md \
  --json-output /tmp/DiskManagement.candidates.json
```

Markdown reports are bounded by default for agent ingestion; JSON outputs remain complete.

Build an LLM-ready MOTIF-style inference context for one candidate:

```bash
macos-private-framework-research/scripts/build_motif_context.py \
  --candidate-json /tmp/DiskManagement.candidates.json \
  --candidate-id 1 \
  --headers /tmp/DiskManagement.headers \
  --binary /tmp/macos-private-frameworks/System/Library/PrivateFrameworks/DiskManagement.framework/Versions/A/DiskManagement \
  --output /tmp/DiskManagement.candidate-1.context.json \
  --prompt-output /tmp/DiskManagement.candidate-1.prompt.md
```

Lint candidate reconstructed headers before treating them as evidence:

```bash
macos-private-framework-research/scripts/objc_signature_linter.py \
  --headers /tmp/DiskManagement.inferred.headers \
  --output /tmp/DiskManagement.lint.md \
  --json-output /tmp/DiskManagement.lint.json \
  --compile
```

## Validation

Portable validation that does not require macOS-specific tools:

```bash
macos-private-framework-research/scripts/validate_skill_repo.py .
macos-private-framework-research/scripts/resolve_toolchains.py --json-output /tmp/macos-pf-toolchains.json \
  >/tmp/macos-pf-toolchains.md
macos-private-framework-research/scripts/framework_macho_manifest.py --framework IntelligenceFlow \
  --json-output /tmp/macos-pf-framework-manifest.json \
  --markdown-output /tmp/macos-pf-framework-manifest.md
python3 -m py_compile macos-private-framework-research/scripts/*.py
bash -n macos-private-framework-research/scripts/*.sh
macos-private-framework-research/scripts/dlopen_symbol_probe.swift --help >/tmp/macos-pf-dlopen-help.txt
zsh -n framework-surveys/intelligenceflow-agent-survey/scripts/*.zsh
python3 -m py_compile framework-surveys/intelligenceflow-agent-survey/scripts/*.py
zsh -n framework-surveys/skylight-agent-survey/tools/*.zsh
python3 -m py_compile framework-surveys/skylight-agent-survey/tools/*.py
```

On a macOS host, also run the inventory script, a small app/binary discovery pass, and survey header verifiers when touching the survey packages.

```bash
framework-surveys/intelligenceflow-agent-survey/scripts/verify_intelligenceflow_presence_header.zsh \
  /tmp/intelligenceflow-presence-verify.json
swift framework-surveys/skylight-agent-survey/tools/dlopen_probe_symbols.swift --json \
  >/tmp/skylight-dlsym-probe.json
framework-surveys/skylight-agent-survey/tools/verify_skylight_readonly_header.zsh \
  /tmp/skylight-readonly-verify.json
```
