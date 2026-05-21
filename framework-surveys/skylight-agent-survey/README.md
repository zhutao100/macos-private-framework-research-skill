# SkyLight Agent Survey Package

Date: 2026-05-20

This package is an LLM-agent-oriented survey and on-device exploration kit for `SkyLight.framework`, the private macOS client-side interface around WindowServer/CoreGraphics Services/SLS.

It is designed for progressive loading:

1. Start with `INDEX.md` and `AGENTS.md`.
2. Read `briefs/SkyLight_tech_brief.md` for the framework model.
3. Use `references/symbol_clusters.md` and `data/seed_symbol_manifest.json` as hypotheses.
4. Run only the read-only tools under `tools/` on a disposable or lab macOS machine.
5. Record results into `templates/report_template.md`.

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
| `references/symbol_clusters.md` | Symbol families and investigation questions. |
| `references/project_notes/cua_driver_notes.md` | How Cua maps to the background computer-use problem space. |
| `references/project_notes/skylightwindow_notes.md` | How SkyLightWindow maps to system-level overlay/Space experiments. |
| `tools/collect_skylight_inventory.zsh` | Read-only host inventory and symbol collection; writes compact `SUMMARY.md` and `SUMMARY.json`. |
| `references/build_observations/macos15_24G325.md` | Verified packaging, extraction, header, probe, and read-only declaration findings from macOS 15.7.2 build 24G325. |
| `references/build_observations/macos26_25C56.md` | Verified packaging, extraction, header, probe, and read-only declaration findings from macOS 26.2 build 25C56. |
| `tools/dlopen_probe_symbols.swift` | Read-only `dlopen`/`dlsym`/`NSClassFromString` presence probe; it does not call private symbols. |
| `tools/verify_skylight_readonly_header.zsh` | Compiles `headers/SkyLightReadOnly.h` and runs non-mutating prototype calls. |
| `headers/SkyLightReadOnly.h` | Project-ready dlsym declarations for read-only connection/display/Space/window observation. |
| `data/seed_symbol_manifest.json` | Machine-readable symbol-name observations from seed source trees. |
```
