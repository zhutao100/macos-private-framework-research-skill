# Index

## Briefs

- `briefs/SkyLight_tech_brief.md` — current technical model of SkyLight.
- `briefs/agent_research_methodology.md` — LLM-agent workflow for private-framework research.
- `briefs/on_device_exploration_plan.md` — staged tasks for lab-machine exploration.

## References

- `references/public_web_sources.md` — public sources used in the survey.
- `references/symbol_clusters.md` — SLS/CGS/SLPS/AX/CGEvent symbol families.
- `references/private_api_surface_matrix.md` — surfaces, public alternatives, and risk.
- `references/project_notes/cua_driver_notes.md` — Cua-related findings.
- `references/project_notes/skylightwindow_notes.md` — SkyLightWindow-related findings.
- `references/build_observations/macos15_24G325.md` — verified host findings for macOS 15.7.2 build 24G325.
- `references/public_api_alternatives.md` — supported API fallback map.
- `references/build_observations/macos26_25C56.md` — verified host findings for macOS 26.2 build 25C56.

## Data

- `data/seed_symbol_manifest.json` — extracted symbol-name observations.
- `data/macos15_24G325_probe_summary.json` — compact symbol/class/header-call probe for macOS 15.7.2 build 24G325.
- `data/macos26_25C56_probe_summary.json` — compact symbol/class and read-only header-call probe for macOS 26.2 build 25C56.
- `data/source_index.json` — structured source list and why each source matters.

## Headers

- `headers/README.md` — header scope and validation notes.
- `headers/SkyLightReadOnly.h` — dlsym-based read-only signatures validated on macOS 15.7.2 build 24G325.
- `headers/skylight_symbol_names.h` — symbol-name constants for read-only probes. No function signatures.

## Tools

- `tools/collect_skylight_inventory.zsh` — read-only host inventory.
- `tools/dlopen_probe_symbols.swift` — read-only C-symbol and Objective-C-class presence probe.
- `tools/verify_skylight_readonly_header.zsh` — compile and run the `SkyLightReadOnly.h` non-mutating call probe.
- `tools/extract_symbol_refs.py` — parse symbol-name references from local text/source trees.
- `tools/diff_symbol_manifests.py` — compare manifests across OS builds.

## Templates

- `templates/report_template.md` — final report format.
- `templates/agent_task_cards.md` — task cards for LLM agents.
