# Package index

## Read first

1. `README.md`
2. `briefs/safety_boundary_and_non_goals.md`
3. `briefs/IntelligenceFlow_tech_brief.md`
4. `evidence/evidence_register.md`
5. `LLM_LOAD_ORDER.md`

## Agent task lanes

| Lane | Start here | Expected output |
|---|---|---|
| Framework inventory | `playbooks/01_inventory_and_extraction.md` | Per-build framework paths, UUIDs, sizes, version strings, extracted DSC paths. |
| Static analysis | `playbooks/02_static_binary_analysis.md` | Dependency graph, symbol/string clusters, ObjC/Swift metadata, pseudo-header notes. |
| Capability/service map | `playbooks/03_entitlements_services_logs.md` | Entitlement matrix, Mach/XPC names, launchd jobs, log predicates. |
| Public-surface trials | `playbooks/04_app_intents_shortcuts_pcc_trials.md` | Controlled trial records across Foundation Models, Shortcuts, Siri/App Intents, Spotlight, PCC. |
| Claim triage | `playbooks/05_agent_claim_triage.md` | Claim cards with evidence class, confidence, reproduction status, counterevidence. |

## Machine-readable files

| File | Format | Use |
|---|---|---|
| `llm_index.jsonl` | JSONL | Chunk map for retrieval agents. |
| `evidence/claim_cards.jsonl` | JSONL | Seed claims and verification tasks. |
| `data/macos26_25C56_probe_summary.json` | JSON | Local macOS 26.2 build 25C56 evidence summary. |
| `evidence/framework_family_seed.yaml` | YAML | Framework names and hypothesized roles. |
| `evidence/entitlement_surface_seed.yaml` | YAML | Entitlement/service names to search locally. |
| `sources/sources.json` | JSON | Source registry. |
| `schemas/*.schema.json` | JSON Schema | Validate local observations/manifests. |

## Project headers

| File | Use |
|---|---|
| `headers/IntelligenceFlowPresence.h` | Non-calling dyld/Objective-C presence probes for project diagnostics. |
| `headers/README.md` | Header validation baseline and generated-header cautions. |
