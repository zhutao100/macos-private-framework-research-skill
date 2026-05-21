# Evidence register

## Public Apple architecture

| Source | What it supports | Evidence grade | Notes |
|---|---|---:|---|
| Apple Intelligence developer page | Apple Intelligence app integration through App Intents and direct model access through Foundation Models | A | Public architecture, not private internals. |
| WWDC25 Foundation Models session | On-device model API; guided generation; tool calling; stateful sessions; transcripts | A | Strong anchor for public model layer. |
| WWDC24 Bring your app to Siri | App Intents/SiriKit/Assistant Schemas as public action surface | A | Strong anchor for Siri/App Intents bridge from the public side. |
| WWDC25 Shortcuts/Spotlight with App Intents | Shortcuts Use Model and Spotlight/App Intents on Mac | A | Useful controlled-probe surface. |
| Apple Support: Apple Intelligence privacy on Mac | PCC request reporting and privacy-report export | A | Useful external correlation signal. |
| apple/security-pcc | PCC security/privacy repository | A | PCC context only; not local `IntelligenceFlow` internals. |

## Private framework existence and activity

| Source | What it supports | Evidence grade | Notes |
|---|---|---:|---|
| Local macOS 15.7.2 build 24G325 dyld cache | All nine `IntelligenceFlow*` images exist at version `218.5.0.0.0` with UUIDs and extracted Mach-O sizes | A for this build | See `data/macos15_24G325_probe_summary.json`. |
| Local macOS 15.7.2 build 24G325 launchd/services | `intelligenceflowd`, `intelligencecontextd`, and `com.apple.intelligenceflow.*` service labels are registered in the GUI domain | A for this build | Runtime behavior still requires controlled trial correlation. |
| Local macOS 15.7.2 build 24G325 entitlements | Context, query decoration, UI context, Biome transcript/telemetry streams, IntelligencePlatform, and model-manager gates on local binaries | A for this build | Applies to named binaries only. |
| Local macOS 15.7.2 build 24G325 header validation | Class-dump generated metadata is not directly project-ready; `IntelligenceFlowPresence.h` validates non-calling presence checks | A for this build | Full generated headers need per-declaration hardening. |
| Local macOS 26.2 build 25C56 dyld cache | All nine `IntelligenceFlow*` images exist at version `3505.5.1.0.0` with UUIDs and extracted Mach-O sizes | A for this build | See `data/macos26_25C56_probe_summary.json`. |
| Local macOS 26.2 build 25C56 launchd/services | `intelligenceflowd`, `intelligencecontextd`, and `com.apple.intelligenceflow.*` service labels are registered in the GUI domain | A for this build | Runtime behavior still requires controlled trial correlation. |
| Local macOS 26.2 build 25C56 entitlements | Context, query decoration, UI context, Biome transcript/telemetry streams, IntelligencePlatform, and model-manager gates on local binaries | A for this build | Applies to named binaries only. |
| Local macOS 26.2 build 25C56 header validation | Class-dump generated metadata is not directly project-ready; `IntelligenceFlowPresence.h` validates non-calling presence checks | A for this build | Full generated headers need per-declaration hardening. |
| The Apple Wiki PrivateFrameworks list | Names of `IntelligenceFlow*` frameworks under `/System/Library/PrivateFrameworks` | C | Unofficial index; good for discovery, not role claims. |
| blacktop/ipsw-diffs `IntelligenceFlow.md` | Path, version, UUID/function/string counts across 26.2 beta diff | C | Cross-OS shared-cache signal; reproduce locally for macOS. |
| blacktop/ipsw-diffs `IntelligenceFlowRuntime.md` | Runtime binary exists and changes across build diff | C | Activity signal. |
| blacktop/ipsw-diffs `IntelligenceFlowPlannerSupport.md` | Large planner-support binary exists and changes across build diff | C | Role inference is name-based until local analysis. |

## Entitlement and service hints

| Source | What it supports | Evidence grade | Notes |
|---|---|---:|---|
| NewOSXBook `IntelligenceFlowDiagnostics` entitlements | `com.apple.intelligenceflow.context`; Biome read-only streams `Sage.Transcript`, `IntelligenceFlow.Transcript.Datastream`; Mach lookup `com.apple.intelligenceflow.context` | C | iOS record; narrow claim only. |
| Public entitlement catalogs / diffs | `orchestrator`, `context`, `orchestrator.features`, Mach lookup names | C | Treat as labels to search locally. |

## Methodology and tooling

| Source | What it supports | Evidence grade | Notes |
|---|---|---:|---|
| MOTIF paper | LLM-agent type inference workflow for macOS private frameworks | A for methodology | Does not directly describe `IntelligenceFlow`. |
| ipsw docs | Mach-O/DSC/entitlement tooling | A for tool capability | Use exact versions in lab logs. |
| dyld-shared-cache-extractor | DSC extraction | A for tool capability | Local extraction only. |
| RuntimeBrowser / class-dump header archives | Header-style inspection approach | B/C | Generated headers are pseudo-headers, not Apple documentation. |

## Seed research snapshot

The task-provided `source_materials/research_IntelligenceFlow_frameworks.md` is used as a seed synthesis. Treat it as a useful starting model, not primary evidence. Promote only claims that are independently supported by primary documentation or local reproduction.
