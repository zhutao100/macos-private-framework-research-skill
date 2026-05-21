# Agent prompt: static analysis lane

You are analyzing local artifacts from a macOS build. Do not infer behavior from names alone.

Inputs to load:

1. `briefs/IntelligenceFlow_tech_brief.md`
2. `evidence/framework_family_seed.yaml`
3. Local `intelligenceflow_macho_manifest.json`
4. Local string scans and dependency scans

Tasks:

1. Produce a dependency graph for every `IntelligenceFlow*` binary.
2. Cluster strings into service names, entitlements, logs, planner/tool terms, App Intents terms, Biome/transcript terms, Foundation Models terms.
3. Identify candidate consumers.
4. Create claim cards for only evidence-backed claims.
5. List top 10 next local checks.

Output format:

- `dependency_graph.md`
- `string_clusters.md`
- `candidate_consumers.md`
- `claim_cards.local.jsonl`
