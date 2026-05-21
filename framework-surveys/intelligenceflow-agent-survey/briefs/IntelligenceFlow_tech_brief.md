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

## Local build findings

### macOS 15.7.2 build 24G325

Build-specific static evidence confirms the family predates macOS 26:

- The arm64e dyld shared cache contains all nine `IntelligenceFlow*` images at version `218.5.0.0.0`.
- The filesystem framework bundles are dyld-cache skeletons; the framework binary symlinks do not resolve to standalone files until extracted or loaded by dyld.
- Extracted Mach-O sizes range from 120568 bytes (`IntelligenceFlowAppIntentsPreviewToolSupport`) to 10010168 bytes (`IntelligenceFlowPlannerSupport`).
- `IntelligenceFlowRuntime.framework` contains `intelligenceflowd` and `IntelligenceFlowDiagnostics.appex` outside the shared cache.
- `IntelligenceFlowContextRuntime.framework` contains `intelligencecontextd` outside the shared cache.
- `launchctl print gui/$UID` shows `com.apple.intelligenceflowd`, `com.apple.intelligencecontextd`, and Mach/XPC labels for `context`, `contextIntelligence`, `internal`, `orchestrator`, `querydecoration`, `snippet-streaming`, `toolbox`, `transcript-entity-querying`, and `uiContext`.
- `intelligenceflowd` carries `com.apple.intelligenceflow.context`, `com.apple.intelligenceflow.querydecoration`, `com.apple.intelligenceflow.uiContext`, Biome read/write streams, and model-manager access.
- `intelligencecontextd` carries IntelligencePlatform use-case/view entitlements, Biome streams including `Siri.Orchestration.RequestContext`, and model-manager access.
- `IntelligenceFlowDiagnostics.appex` carries `com.apple.intelligenceflow.context` and read-only Biome streams `Sage.Transcript` and `IntelligenceFlow.Transcript.Datastream`.
- `IntelligenceFlowPlannerRuntime.framework` links AppIntents, CoreSpotlight, AssistantServices, Biome, GenerativeFunctions/GenerativeModels, IntelligencePlatform, Siri, Spotlight, and Trial frameworks. Its resources include `Metadata.generativefunctions`, `PlanResolutionModel.mlmodelc`, query-decorator namespace descriptors, response-generation validation/preference plists, and risk metadata.
- `IntelligenceFlowPlannerSupport.framework` includes `ToolBoxAllowList.plist`, `ToolPromptOverride.json`, `ToolRetrievalContextAllowList.plist`, `ToolUtterancesOverride.json`, and a sentencepiece model. On build 24G325, `ToolBoxAllowList.plist` contains 101 global entries and 27 local entries; `FlowToolHiddenList.plist` and `SiriXPrivilegedToolManifest.json` were not present in this build.
- Generated Objective-C headers are useful as metadata, not drop-in project headers. The 24G325 pass produced 284 class-dump headers, 333 raw-`id` linter warnings, and a direct clang syntax failure due Swift metadata names. Use `headers/IntelligenceFlowPresence.h` for project presence checks; keep full generated headers local until individual declarations pass compiler/linter validation.

### macOS 26.2 build 25C56

Build-specific static evidence on 25C56 strengthens the same model:

- The arm64e dyld shared cache contains all nine `IntelligenceFlow*` images at version `3505.5.1.0.0`.
- The filesystem framework bundles are mostly dyld-cache skeletons; the framework binary symlinks do not resolve to standalone files until extracted or loaded by dyld.
- `IntelligenceFlowRuntime.framework` contains `intelligenceflowd` and `IntelligenceFlowDiagnostics.appex` outside the shared cache.
- `IntelligenceFlowContextRuntime.framework` contains `intelligencecontextd` outside the shared cache.
- `launchctl print gui/$UID` shows `com.apple.intelligenceflowd`, `com.apple.intelligencecontextd`, and Mach/XPC labels for `context`, `contextIntelligence`, `internal`, `orchestrator`, `querydecoration`, `snippet-streaming`, `toolbox`, `transcript-entity-querying`, and `uiContext`.
- `intelligenceflowd` carries `com.apple.intelligenceflow.context`, `com.apple.intelligenceflow.querydecoration`, `com.apple.intelligenceflow.uiContext`, Biome read/write streams, and model-manager access.
- `intelligencecontextd` carries IntelligencePlatform use-case/view entitlements, Biome streams including `Siri.Orchestration.RequestContext`, and model-manager access.
- `IntelligenceFlowDiagnostics.appex` carries `com.apple.intelligenceflow.context` and read-only Biome streams `Sage.Transcript`, `IntelligenceFlow.Transcript.Datastream`, and `IntelligenceEngine.Interaction.Donation`.
- `IntelligenceFlowPlannerRuntime.framework` links AppIntents, CoreSpotlight, AssistantServices, Biome, GenerativeFunctions/GenerativeModels, IntelligencePlatform, Siri, Spotlight, and Trial frameworks. Its resources include `Metadata.generativefunctions`, `PlanResolutionModel.mlmodelc`, and response-generation validation/preference plists.
- `IntelligenceFlowPlannerSupport.framework` includes tool resources such as `ToolBoxAllowList.plist`, `FlowToolHiddenList.plist`, `SiriXPrivilegedToolManifest.json`, prompt/utterance overrides, and a sentencepiece model. On build 25C56, `ToolBoxAllowList.plist` contains 343 global entries and 0 local entries.

Generated Objective-C headers are useful as metadata, not drop-in project headers. The 25C56 pass produced 293 class-dump headers, 408 raw-`id` linter warnings, and a direct clang syntax failure due Swift metadata names. Use `headers/IntelligenceFlowPresence.h` for project presence checks; keep full generated headers local until individual declarations pass compiler/linter validation.

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
