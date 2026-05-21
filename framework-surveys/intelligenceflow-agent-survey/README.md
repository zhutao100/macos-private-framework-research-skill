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
| `briefs/safety_boundary_and_non_goals.md` | What this package intentionally excludes and safe substitutes. |
| `evidence/` | Evidence register, framework inventory seeds, entitlement seeds, claim cards. |
| `references/` | Source annotations, public Apple architecture notes, tooling catalog. |
| `toolchains/` | Lab setup, toolchain matrix, MOTIF-style type-inference workflow. |
| `playbooks/` | On-device collection and verification playbooks. |
| `scripts/` | Local-only collectors for framework inventory, strings, entitlements, logs, and Mach-O manifests. |
| `templates/` | Observation records, claim cards, lab runbook, agent prompts. |
| `schemas/` | JSON schemas for manifests and observations. |
| `source_materials/` | Seed research snapshot supplied with the task. |

## Scope boundaries

No Apple private binaries, private headers, entitlement-bearing Apple executables, or generated private headers are redistributed here. The scripts only collect metadata from a researcher-controlled macOS machine and write local outputs.

This package also excludes actionable SIP/AMFI/TCC bypass steps, exploit chains, and Apple-process injection recipes. It replaces those with observable control-plane mapping: entitlements, Mach/XPC service names, launchd jobs, dyld/shared-cache metadata, unified logs, App Intents trials, and Apple Intelligence privacy reports.

## Suggested first run

```zsh
cd intelligenceflow_survey_package_2026-05-21
mkdir -p ~/iflow-lab
scripts/collect_intelligenceflow_inventory.zsh ~/iflow-lab/inventory
scripts/collect_entitlements.zsh ~/iflow-lab/inventory/candidates.txt ~/iflow-lab/entitlements
scripts/observe_unified_logs.zsh 120 ~/iflow-lab/logs/intelligenceflow_120s.log
```

Use `templates/lab_runbook.md` to record OS build, hardware, feature state, prompts, privacy-report state, and artifacts.
