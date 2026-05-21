# IntelligenceFlow technical brief

## Executive model

The most defensible current model is:

```text
User/system request
  → Siri, Writing Tools, Shortcuts, Spotlight, app surfaces
  → App Intents / Assistant Schemas / indexed entities / semantic context
  → private orchestration, context, and planning layer
     likely involving IntelligenceFlow*, intelligencecontextd, intelligenceflowd-like services, and related daemons
  → model execution
     on-device Foundation Models and/or Private Cloud Compute
  → tool execution / app action / generated response
```

`IntelligenceFlow*` should be treated as a private orchestration/context/planning substrate adjacent to, not equivalent to, Apple’s public `FoundationModels.framework` and `AppIntents.framework` surfaces.

## Evidence grade summary

| Evidence class | Supports | Confidence |
|---|---|---:|
| Apple Developer / Apple Support / Apple ML docs | Public architecture: Foundation Models, App Intents, Shortcuts Use Model, PCC privacy report | High |
| Private-framework filesystem indexes | Existence of `IntelligenceFlow*` framework names | High for names, lower for roles |
| Shared-cache diffs | Binary presence, version churn, approximate function/symbol/string counts | Medium |
| Entitlement catalogs | Capability gates and Mach lookup labels around context/orchestrator/transcript streams | Medium |
| Community notes | Daemon topology, IPC hypotheses, security research leads | Low to medium until reproduced locally |
| Local reproduction | Build-specific fact | Highest; required before strong claims |

## Framework family seed

| Component | Observed name/source | Working hypothesis | Confidence |
|---|---|---|---:|
| `IntelligenceFlow.framework` | Private-framework index, shared-cache diffs | Core shared pipeline/orchestration types | Medium |
| `IntelligenceFlowRuntime.framework` | Private-framework index, shared-cache diffs | Runtime support for live flow execution | Medium |
| `IntelligenceFlowContext.framework` | Private-framework index, entitlement names | Context-access capability boundary | Medium |
| `IntelligenceFlowContextRuntime.framework` | Private-framework index, shared-cache diffs | Runtime support for context queries/services | Low-medium |
| `IntelligenceFlowPlannerRuntime.framework` | Private-framework index, shared-cache diffs | Planner/multi-step runtime | Medium |
| `IntelligenceFlowPlannerSupport.framework` | Private-framework index, large shared-cache diff | Shared planner support library | Medium |
| `IntelligenceFlowShared.framework` | Private-framework index, shared-cache diffs | Shared data types/utilities | Medium |
| `IntelligenceFlowFeedbackDataCollector.framework` | Private-framework index | Feedback/diagnostics collection | Medium by name, low on internals |
| `IntelligenceFlowAppIntentsPreviewToolSupport.framework` | Private-framework index | Internal support for App Intents tool preview/testing | Medium by name, low on internals |

## Public architecture anchor points

- Apple documents Apple Intelligence as spanning iPhone, iPad, Mac, Apple Vision Pro, and Apple Watch, with app integration through App Intents and direct model access through Foundation Models.
- Foundation Models is the sanctioned public on-device model interface. It supports guided generation, tool calling, stateful sessions, transcript state, and app-defined tools.
- App Intents and Assistant Schemas are the public action/entity exposure layer for Siri, Shortcuts, Spotlight, and related system surfaces.
- Shortcuts’ Use Model action exposes on-device, PCC, and extension-model routing at the automation layer.
- Apple Intelligence privacy reports provide a public side channel for PCC request correlation on Mac.

## Private architecture hypotheses

| Hypothesis | Evidence to seek locally | Reject if |
|---|---|---|
| `IntelligenceFlow*` mediates context/planning for Siri or Shortcuts | Logs, linkage, entitlements, service names, App Intents trials | No logs/linkage/service references under controlled trials |
| `IntelligenceFlowContext*` is the context gate | Entitlements, Mach lookup labels, Biome strings, context log predicates | Only name appears; no service/entitlement/log correlation |
| `IntelligenceFlowPlanner*` hosts multi-step/tool planner support | Dependencies on AppIntents/FoundationModels/Siri/Biome; planner strings; controlled App Intents trials | Static strings absent and no runtime correlation |
| `IntelligenceFlowAppIntentsPreviewToolSupport` bridges tool-preview metadata | Linkage to AppIntents/Shortcuts/testing services | Only unused artifact; no consumers found |
| Transcript streams exist for diagnostics | Entitlements and Biome stream labels on local diagnostics binaries | No local binary/entitlement/string support |

## Claims to avoid before local reproduction

- `IntelligenceFlow.framework` is the single universal router for all Apple Intelligence requests.
- `intelligenceflowd` always orchestrates Siri, Writing Tools, Shortcuts, Spotlight, and Foundation Models.
- Biome stores all Apple Intelligence transcripts.
- Private APIs are stable enough for third-party production software.
- iOS shared-cache diffs exactly describe macOS internals.
- Framework names fully reveal runtime responsibilities.

## High-value local verification outputs

1. Build manifest: `sw_vers`, hardware, OS build, architecture, Apple Intelligence feature state.
2. Framework inventory: paths, UUIDs, sizes, versions, linkage, load commands.
3. Dependency graph: `IntelligenceFlow*` ↔ AppIntents/FoundationModels/Siri/Biome/Spotlight/Shortcuts.
4. Capability graph: entitlements, Mach services, launchd jobs, sandbox profiles if visible.
5. Runtime correlation: logs under controlled Foundation Models, Shortcuts, Siri/App Intents, Spotlight, PCC trials.
6. Claim cards: every assertion has evidence, reproduction status, counterevidence, and confidence.
