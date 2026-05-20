# SkyLight Agent Survey Package

Date: 2026-05-20

This package is an LLM-agent-oriented survey and on-device exploration kit for `SkyLight.framework`, the private macOS client-side interface around WindowServer/CoreGraphics Services/SLS.

It is designed for progressive loading:

1. Start with `INDEX.md` and `AGENTS.md`.
2. Read `briefs/SkyLight_tech_brief.md` for the framework model.
3. Use `references/symbol_clusters.md` and `data/seed_symbol_manifest.json` as hypotheses.
4. Run only the read-only tools under `tools/` on a disposable or lab macOS machine.
5. Record results into `templates/report_template.md`.

## Safety boundary

This package intentionally excludes operational SIP/AMFI/TCC bypass procedures, Apple-process injection recipes, exploit chains, privilege-escalation steps, and code that invokes private event-injection routines. It includes safe, read-only inventory tools and methodology for legitimate reverse-engineering, compatibility research, and defensive assessment.

## Contents

```text
AGENTS.md
INDEX.md
briefs/
references/
references/project_notes/
data/
headers/
tools/
templates/
seed/
```

## Most useful entry points

| File | Purpose |
|---|---|
| `briefs/SkyLight_tech_brief.md` | Technical overview of SkyLight surfaces and modern macOS constraints. |
| `briefs/agent_research_methodology.md` | Work plan for LLM-assisted, versioned on-device exploration. |
| `briefs/security_boundaries.md` | What is in-scope and out-of-scope for safe research. |
| `references/symbol_clusters.md` | Symbol families and investigation questions. |
| `references/project_notes/cua_driver_notes.md` | How Cua maps to the background computer-use problem space. |
| `references/project_notes/skylightwindow_notes.md` | How SkyLightWindow maps to system-level overlay/Space experiments. |
| `tools/collect_skylight_inventory.zsh` | Read-only host inventory and symbol collection. |
| `tools/dlopen_probe_symbols.swift` | Read-only `dlopen`/`dlsym` presence probe; it does not call private symbols. |
| `data/seed_symbol_manifest.json` | Machine-readable symbol-name observations from seed source trees. |
```
