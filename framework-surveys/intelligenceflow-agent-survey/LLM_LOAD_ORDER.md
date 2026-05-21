# LLM load order

Use this order to avoid overloading context with low-signal material.

## Level 0: Orient

Load:

- `README.md`
- `INDEX.md`

Stop when the agent can state the package boundaries and task lanes.

## Level 1: Build the current model

Load:

- `briefs/IntelligenceFlow_tech_brief.md`
- `evidence/evidence_register.md`
- `data/macos15_24G325_probe_summary.json` when build 24G325 evidence is relevant
- `data/macos26_25C56_probe_summary.json` when build 25C56 evidence is relevant
- `references/public_apple_architecture.md`

Stop when the agent can distinguish Apple-documented surfaces from private-framework hypotheses.

## Level 2: Plan local collection

Load:

- `toolchains/toolchain_matrix.md`
- `toolchains/setup_macos_research_lab.md`
- `playbooks/01_inventory_and_extraction.md`
- `playbooks/03_entitlements_services_logs.md`

Stop when the agent has a build-specific collection plan.

## Level 3: Run and normalize observations

Load:

- `scripts/*.zsh`
- `scripts/*.py`
- `templates/observation_record.yaml`
- `schemas/observation.schema.json`

Stop when the agent has locally generated artifacts and observation records.

## Level 4: Type inference and deeper analysis

Load:

- `toolchains/motif_style_type_inference.md`
- `playbooks/02_static_binary_analysis.md`
- `headers/README.md`
- `headers/IntelligenceFlowPresence.h` when project presence checks are needed
- `templates/agent_prompt_type_inference.md`

Stop when each inferred private signature is represented as a claim card with reproducible evidence.

## Level 5: Controlled public-surface experiments

Load:

- `playbooks/04_app_intents_shortcuts_pcc_trials.md`
- `templates/lab_runbook.md`

Stop when trials can be correlated across logs, privacy report, and local artifacts.
