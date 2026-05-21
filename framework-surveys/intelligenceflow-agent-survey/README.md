# IntelligenceFlow survey package

Generated: 2026-05-21

This package is a technical survey and on-device exploration guide for the macOS `IntelligenceFlow*` private-framework family. It is optimized for LLM-agent ingestion: short indexed documents, explicit evidence grades, JSONL claim cards, shell/Python collectors, and progressive-loading prompts.

## Contents

| Path | Purpose |
|---|---|
| `INDEX.md` | Fast package map and recommended reading order. |
| `LLM_LOAD_ORDER.md` | Progressive context-loading plan for agents. |
| `briefs/IntelligenceFlow_tech_brief.md` | Current technical model, evidence, hypotheses, and claims to avoid. |
| `briefs/agentic_private_framework_research_best_practices.md` | LLM-agent methodology for modern macOS private-framework research. |
| `evidence/` | Evidence register, framework inventory seeds, entitlement seeds, claim cards. |
| `data/` | Build-specific local observation summaries. |
| `headers/` | Project-ready presence header and generated-header validation notes. |
| `references/` | Source annotations, public Apple architecture notes, tooling catalog. |
| `toolchains/` | Lab setup, toolchain matrix, MOTIF-style type-inference workflow. |
| `playbooks/` | On-device collection and verification playbooks. |
| `scripts/` | Local-only collectors for framework inventory, strings, entitlements, logs, and Mach-O manifests. |
| `templates/` | Observation records, claim cards, lab runbook, agent prompts. |
| `schemas/` | JSON schemas for manifests and observations. |
| `source_materials/` | Seed research snapshot supplied with the task. |

## Verified local baselines

- `data/macos15_24G325_probe_summary.json` records a local macOS 15.7.2 build 24G325 pass. The pass confirmed nine `IntelligenceFlow*` dyld-cache images at version `218.5.0.0.0`, found `intelligenceflowd` and `intelligencecontextd` launchd/service evidence, and validated `headers/IntelligenceFlowPresence.h` as a project-ready non-calling presence header.
- `data/macos26_25C56_probe_summary.json` records a local macOS 26.2 build 25C56 pass. The pass confirmed nine `IntelligenceFlow*` dyld-cache images at version `3505.5.1.0.0`, found `intelligenceflowd` and `intelligencecontextd` launchd/service evidence, and validated the same presence header.

## Suggested first run

```zsh
mkdir -p ~/iflow-lab
scripts/collect_intelligenceflow_inventory.zsh ~/iflow-lab/inventory
scripts/extract_dyld_intelligenceflow.zsh ~/iflow-lab/dsc-extracted
scripts/collect_entitlements.zsh ~/iflow-lab/inventory/candidates.txt ~/iflow-lab/entitlements
scripts/observe_unified_logs.zsh 120 ~/iflow-lab/logs/intelligenceflow_120s.log
```

Use `templates/lab_runbook.md` to record OS build, hardware, feature state, prompts, privacy-report state, and artifacts.
