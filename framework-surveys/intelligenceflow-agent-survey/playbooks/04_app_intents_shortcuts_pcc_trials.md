# Playbook 04: App Intents, Shortcuts, PCC trials

## Objective

Use public Apple surfaces to trigger relevant behavior and correlate `IntelligenceFlow*` evidence through logs, privacy reports, and local metadata.

## Trial matrix

| Trial ID | Surface | Action | Expected correlation |
|---|---|---|---|
| T001 | Foundation Models sample | On-device prompt with no tool | FoundationModels/model session logs; possible no IntelligenceFlow signal. |
| T002 | Foundation Models sample | Tool-calling prompt | Tool-call logs; check AppIntents/IntelligenceFlow absence/presence. |
| T003 | Shortcuts | Use Model → On-Device | Shortcuts + model logs; no PCC report expected. |
| T004 | Shortcuts | Use Model → PCC | Privacy report entry; PCC-related logs where visible. |
| T005 | Shortcuts | Use Model → Extension Model | Extension-model route, if enabled; separate from PCC. |
| T006 | Siri | Natural language request no app action | Assistant/Siri/model/context signals. |
| T007 | Siri/App Intent | Invoke app action/entity | App Intents, Assistant Schema, tool/action orchestration signals. |
| T008 | Spotlight | Run app action from Spotlight | Spotlight/App Intents action logs. |

## Trial record template

Use `templates/observation_record.yaml` for each run.

## Privacy-report correlation

After PCC-targeted trials:

1. Open System Settings → Privacy & Security → Apple Intelligence Report.
2. Use duration covering the trial window.
3. Export `Apple_Intelligence_Report.json`.
4. Store it under `~/iflow-lab/trials/<trial-id>/`.
5. Record whether it contains entries for the trial window.

## App Intents checklist

For any test app/action:

- Intent identifier.
- Entity type and properties exposed.
- `@Parameter` fields.
- `AppShortcutsProvider` entries.
- Spotlight discoverability.
- Whether action accepts rich text or app entities.
- Whether output can be consumed by Use Model.

## Interpretation

- A public-surface trial can prove correlation, not necessarily internal causation.
- Repeat trials and compare idle baseline logs.
- For each observed private service or framework mention, create a claim card.
