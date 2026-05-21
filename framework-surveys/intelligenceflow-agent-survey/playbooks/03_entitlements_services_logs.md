# Playbook 03: entitlements, services, logs

## Objective

Map capability gates and runtime service labels without injecting into or modifying Apple processes.

## Entitlement scan

```zsh
../../macos-private-framework-research/scripts/collect_code_entitlements.py \
  --paths-file ~/iflow-lab/inventory/candidates.txt \
  --focus-pattern 'intelligenceflow|intelligenceplatform|biome|mach-lookup|modelmanager|transcript|appintents|shortcuts|siri|assistant' \
  --only-matching \
  --output ~/iflow-lab/entitlements/focused_entitlements.md \
  --json-output ~/iflow-lab/entitlements/focused_entitlements.json
```

Search outputs for:

```text
com.apple.intelligenceflow.context
com.apple.intelligenceflow.querydecoration
com.apple.intelligenceflow.uiContext
com.apple.intelligenceflow.orchestrator
com.apple.intelligenceflow.orchestrator.features
com.apple.intelligenceflow.transcript-entity-querying
com.apple.private.biome.read-only
com.apple.security.exception.mach-lookup.global-name
```

Use `scripts/collect_entitlements.zsh` only when raw per-target plist files are needed. On macOS 15.7.2 build 24G325 and macOS 26.2 build 25C56, local entitlement hits were confirmed on `intelligenceflowd`, `intelligencecontextd`, and `IntelligenceFlowDiagnostics.appex`. See the matching `data/macos*_probe_summary.json` before broadening claims to other builds.

## launchd service map

```zsh
mkdir -p ~/iflow-lab/manifests
launchctl print system 2>/dev/null | grep -Ei 'intelligence|foundation|model|siri|assistant|shortcut|spotlight|biome'   > ~/iflow-lab/manifests/launchctl_system_intelligence.txt || true
launchctl print "gui/$UID" 2>/dev/null | grep -Ei 'intelligence|foundation|model|siri|assistant|shortcut|spotlight|biome'   > ~/iflow-lab/manifests/launchctl_gui_intelligence.txt || true
```

High-signal GUI labels observed on builds 24G325 and 25C56 include `com.apple.intelligenceflowd`, `com.apple.intelligencecontextd`, `com.apple.intelligenceflow.context`, `com.apple.intelligenceflow.orchestrator`, `com.apple.intelligenceflow.querydecoration`, `com.apple.intelligenceflow.toolbox`, `com.apple.intelligenceflow.transcript-entity-querying`, and `com.apple.intelligenceflow.uiContext`.

## Unified logs

Use bounded collection windows:

```zsh
scripts/observe_unified_logs.zsh 180 ~/iflow-lab/logs/intelligenceflow_180s.log
```

Run separate windows for each trial:

| Trial | Probe |
|---|---|
| Idle baseline | No prompt/action. |
| Foundation Models app/sample | Public on-device session and tool call. |
| Shortcuts Use Model on-device | Deterministic text transform. |
| Shortcuts Use Model PCC | Complex request selected for PCC if available. |
| Siri no-app-action | Simple informational request. |
| Siri/App Intents action | Invoke a known app action. |
| Spotlight action | Invoke App Intent from Spotlight. |

## Log predicate seed

```text
subsystem CONTAINS[c] "intelligence" OR
process CONTAINS[c] "intelligence" OR
eventMessage CONTAINS[c] "IntelligenceFlow" OR
eventMessage CONTAINS[c] "AppIntent" OR
eventMessage CONTAINS[c] "FoundationModels" OR
eventMessage CONTAINS[c] "PrivateCloudCompute"
```

## Output discipline

For each run, save:

- Absolute start/end time.
- Trial prompt/action.
- Network state.
- Privacy-report export state.
- Log predicate.
- Log output.
- Negative findings.
