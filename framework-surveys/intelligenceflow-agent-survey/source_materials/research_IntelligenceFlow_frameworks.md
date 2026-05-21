# IntelligenceFlow private-framework research snapshot

*As of 2026-05-21*

## Bottom line

The private-framework evidence comes from filesystem/private-framework indexes, shared-cache diffs, entitlement catalogs, and community reverse-engineering notes.

The most defensible model is:

``` text
User / system request
  → Siri, Writing Tools, Shortcuts, Spotlight, app surfaces
  → App Intents / Assistant Schemas / semantic entities
  → private orchestration/context/planner layer
     likely involving IntelligenceFlow*, intelligenceflowd, related daemons
  → model execution
     on-device Foundation Models daemon and/or Private Cloud Compute
  → tool execution / app actions / generated response
```

Apple’s public materials confirm the outer architecture: Apple Intelligence exposes system-wide features and app integration through App Intents and models; the Foundation Models framework gives developers access to the on-device model powering Apple Intelligence; Private Cloud Compute handles more complex requests under Apple’s privacy/security model. ([Apple Developer](https://developer.apple.com/apple-intelligence/ "Apple Intelligence - Apple Developer"))

---

## Evidence grading

| Evidence class | What it supports | Confidence |
|----|----|---:|
| Apple Developer / Apple ML Research / Apple Support | Public architecture: Foundation Models, App Intents, Shortcuts, PCC, privacy report, guided generation, tool calling | High |
| Private-framework filesystem lists | Existence of `IntelligenceFlow*` framework family under `/System/Library/PrivateFrameworks` | High |
| Shared-cache / IPSW diffs | Binary presence, dependency churn, approximate size/function-symbol-string counts across OS builds | Medium |
| Entitlement catalogs | Capability gates such as `com.apple.intelligenceflow.context`, `orchestrator`, Mach service names, transcript-querying permissions | Medium |
| Community security research notes | Possible daemon topology, IPC flow, prompt-injection surfaces, tool-dispatch path | Low-to-medium until locally reproduced |

The Apple Wiki’s private-framework list includes `IntelligenceFlow`, `IntelligenceFlowRuntime`, `IntelligenceFlowContext`, `IntelligenceFlowContextRuntime`, `IntelligenceFlowPlannerRuntime`, `IntelligenceFlowPlannerSupport`, `IntelligenceFlowFeedbackDataCollector`, `IntelligenceFlowAppIntentsPreviewToolSupport`, and `IntelligenceFlowShared`, but the site itself frames private-framework descriptions as unofficial and potentially incorrect. ([The Apple Wiki](https://theapplewiki.com/wiki/Filesystem%3A/System/Library/PrivateFrameworks "Filesystem:/System/Library/PrivateFrameworks - The Apple Wiki"))

---

## Public architecture Apple does document

### 1. Foundation Models is the public on-device model API

Apple’s 2025 Foundation Models materials say the framework exposes the on-device LLM that powers Apple Intelligence, runs locally and offline, and supports structured generation, tool calling, stateful sessions, streaming, and adapters. Apple’s technical report describes a roughly 3B-parameter on-device model, an OS daemon for constrained/speculative decoding, the `Tool` protocol for parallel/serial tool calls, and `LanguageModelSession` for stateful generation with KV-cache reuse. ([Apple Developer](https://developer.apple.com/videos/play/wwdc2025/286/ "Meet the Foundation Models framework - WWDC25 - Videos - Apple Developer"))

That matters because `IntelligenceFlow` is probably **not** the public model API. It is more plausibly a private orchestration/context/planning layer behind Apple Intelligence surfaces, while `FoundationModels.framework` is the supported developer entry point.

### 2. App Intents are the public action/tool surface

Apple positions App Intents as the mechanism for exposing app actions and entities to Siri, Spotlight, Shortcuts, widgets, Control Center, Visual Intelligence, and Apple Intelligence. WWDC24’s Siri/App Intents session explicitly ties Apple Intelligence to app actions, on-screen awareness, semantic search, Assistant Schemas, and indexed entities. ([Apple Developer](https://developer.apple.com/videos/play/wwdc2024/10133/ "Bring your app to Siri - WWDC24 - Videos - Apple Developer"))

WWDC25 expands the same pattern: Shortcuts on Mac can use App Intents and the “Use Model” action; Spotlight and Mac automation can invoke app entities/actions; model execution can be on-device, via Private Cloud Compute, or via ChatGPT when selected. ([Apple Developer](https://developer.apple.com/videos/play/wwdc2025/260/ "Develop for Shortcuts and Spotlight with App Intents - WWDC25 - Videos - Apple Developer"))

### 3. Private Cloud Compute is the documented remote execution tier

Apple’s privacy documentation says Apple Intelligence tries to process requests on device, sends only relevant request data to PCC for more complex work, and does not store or make that data accessible to Apple. It also exposes Apple Intelligence privacy reporting on Mac. ([Apple](https://www.apple.com/legal/privacy/data/en/intelligence-engine/ "Legal - Apple Intelligence & Privacy- Apple"))

Apple’s PCC security repository is intended to let researchers inspect components implementing PCC security/privacy mechanisms. That is useful context, but it is about PCC, not direct documentation of local `IntelligenceFlow` internals. ([GitHub](https://github.com/apple/security-pcc "GitHub - apple/security-pcc: Private Cloud Compute (PCC) · GitHub"))

---

## Private-framework family inventory

| Component | Existence evidence | Likely role | Confidence on role |
|----|----|----|---:|
| `IntelligenceFlow.framework` | Listed in private-framework indexes and shared-cache diffs | Core shared pipeline / orchestration types | Medium |
| `IntelligenceFlowRuntime.framework` | Listed; shared-cache diffs show dependency relationship with `IntelligenceFlow` and `IntelligenceFlowContext` | Runtime support for live flow execution, likely daemon-facing | Medium |
| `IntelligenceFlowContext.framework` | Listed; entitlement catalogs mention `com.apple.intelligenceflow.context` | Context-access capability boundary | Medium |
| `IntelligenceFlowContextRuntime.framework` | Listed; shared-cache diffs show standalone runtime binary | Runtime support for context queries / context services | Low-to-medium |
| `IntelligenceFlowPlannerRuntime.framework` | Listed; large binary in shared-cache diffs | Planner / multi-step execution runtime | Medium |
| `IntelligenceFlowPlannerSupport.framework` | Listed; very large support binary in diffs | Shared planner support library | Medium |
| `IntelligenceFlowShared.framework` | Listed in framework indexes and diffs | Shared data types/utilities across the family | Medium |
| `IntelligenceFlowFeedbackDataCollector.framework` | Listed and present in diffs | Feedback / diagnostics collection | Medium by name, low on internals |
| `IntelligenceFlowAppIntentsPreviewToolSupport.framework` | Listed and present in diffs | Developer/internal support for App Intents preview tooling | Medium by name, low on internals |

Shared-cache diffs from `blacktop/ipsw-diffs` show these binaries with paths under `/System/Library/PrivateFrameworks/…` and nontrivial function/symbol/string counts. For example, one 26.2 beta diff reports `IntelligenceFlow.framework` at version `3505.5.1.0.0` with ~18.6k functions, `IntelligenceFlowRuntime` with ~13.1k functions, and `IntelligenceFlowPlannerRuntime` with ~22.6k functions. `IntelligenceFlowPlannerSupport` is even larger, with ~36.4k functions in one diff. These are not macOS source documents, but they are strong binary-existence signals across Apple OS shared-cache builds. ([GitHub](https://raw.githubusercontent.com/blacktop/ipsw-diffs/main/26_2_23C5027f__vs_26_2_23C5033h/DYLIBS/IntelligenceFlow.md "raw.githubusercontent.com"))

The smaller members also appear in diffs: `IntelligenceFlowContext`, `IntelligenceFlowContextRuntime`, `IntelligenceFlowAppIntentsPreviewToolSupport`, `IntelligenceFlowFeedbackDataCollector`, and `IntelligenceFlowShared`. ([GitHub](https://raw.githubusercontent.com/blacktop/ipsw-diffs/main/26_2_23C5027f__vs_26_2_23C5033h/DYLIBS/IntelligenceFlowContext.md "raw.githubusercontent.com"))

---

## Likely internal architecture

### 1. Context layer

The strongest signal for a context boundary is the entitlement family. macOS entitlement catalogs for macOS 26 beta builds list binaries with entitlements such as:

| Entitlement | Likely meaning |
|----|----|
| `com.apple.intelligenceflow.context` | Access to IntelligenceFlow context service/data |
| `com.apple.intelligenceflow.orchestrator` | Permission to participate in orchestration |
| `com.apple.intelligenceflow.transcript-entity-querying` | Query access over transcript/entity data |
| `com.apple.intelligenceflow.orchestrator.features` | Feature-gated orchestrator capabilities |

Code-signing entitlement databases and Apple OS entitlement dumps also show Mach lookup names such as `com.apple.intelligenceflow.orchestrator` and `com.apple.intelligenceflow.context`. That suggests the architecture is capability-gated and XPC/Mach-service mediated rather than a loose in-process library call graph. ([codecolor.ist](https://codecolor.ist/entdb/os/find?key=com.apple.intelligenceflow.context&os=mac%2F26.0_25A5346a&utm_source=chatgpt.com "Entitlement Database"))

A NewOSXBook entitlement entry for `IntelligenceFlowDiagnostics` shows read-only private Biome permissions for `Sage.Transcript` and `IntelligenceFlow.Transcript.Datastream`. This supports the narrow claim that at least diagnostics tooling can read IntelligenceFlow/Sage transcript streams. It does **not** prove that every Apple Intelligence request is persisted as readable transcript data. ([newosxbook.com](https://newosxbook.com/ent.php?exec=IntelligenceFlowDiagnostics&osVer=iOS18&utm_source=chatgpt.com "J's Entitlement DataBase"))

### 2. Planner/tool layer

Apple’s public Foundation Models report confirms that Apple’s public on-device model stack supports tool calling, including structurally constrained tool calls, serial/parallel tool-call graphs, guided generation, and stateful sessions. ([arXiv](https://arxiv.org/html/2507.13575v1 "Apple Intelligence Foundation Language Models"))

Given the names `IntelligenceFlowPlannerRuntime` and `IntelligenceFlowPlannerSupport`, it is plausible that the private framework family contains internal planning/orchestration machinery for Apple Intelligence features. However, the exact planner API, graph representation, and daemon split are not publicly documented. The correct phrasing is:

> `IntelligenceFlowPlanner*` is consistent with a private planner runtime used by Apple Intelligence orchestration, but its concrete class/function contracts require local binary analysis.

### 3. App Intents bridge

Apple’s public story is clear: App Intents expose app-specific actions/entities; Assistant Schemas define standardized domains; Siri/Apple Intelligence can use them to take actions in apps. ([Apple Developer](https://developer.apple.com/videos/play/wwdc2024/10133/ "Bring your app to Siri - WWDC24 - Videos - Apple Developer"))

The private framework `IntelligenceFlowAppIntentsPreviewToolSupport` is therefore likely an internal support component for previewing/testing App Intents as tools, but the name alone should not be overread. The bridge from “model wants tool call” to “App Intent action executes” is likely mediated by private services plus public App Intents metadata.

### 4. Daemon topology

Public Apple docs do not document that daemon. Community reverse-engineering notes describe a broader Apple Intelligence IPC path involving `assistantd`, `intelligenceflowd`, `intelligencecontextd`, model-management services, App Intents discovery, and shortcut execution. Those notes are useful leads, not sufficient evidence for a final map without reproducing them on a target macOS build. ([GitHub](https://raw.githubusercontent.com/dmaynor/apple-vuln-research/main/RESEARCH_STATE.md "raw.githubusercontent.com"))

A cautious working model:

``` text
assistant / Siri / Shortcuts / Spotlight surface
  ↕ XPC / Mach services
private orchestration daemon(s)
  ↕ entitlements: context, orchestrator, transcript/entity querying
IntelligenceFlowRuntime / ContextRuntime / PlannerRuntime
  ↕ App Intents metadata + Assistant Schemas + indexed entities
tool execution / app actions
  ↕ model daemon / on-device model / PCC path
response or action result
```

---

## What has changed recently

### Foundation Models made part of the stack public

Earlier Apple Intelligence reverse engineering had to infer model invocation indirectly. With the Foundation Models framework, Apple now exposes a sanctioned local model API with structured output, tool calls, sessions, streaming, and adapters. This reduces the need to touch private `IntelligenceFlow*` APIs for app-level model features. ([Apple Developer](https://developer.apple.com/videos/play/wwdc2025/286/ "Meet the Foundation Models framework - WWDC25 - Videos - Apple Developer"))

Adapters are version-bound to the system model and OS range; Apple documents `.fmadapter` packaging, entitlement requirements, Background Assets distribution, and compatibility constraints. ([Apple Developer](https://developer.apple.com/apple-intelligence/foundation-models-adapter/ "Foundation Models adapter training - Apple Intelligence - Apple Developer"))

### Shortcuts gained explicit model-routing choices

On Mac, Shortcuts’ “Use Model” action can route a shortcut to the on-device model, Private Cloud Compute, or ChatGPT, depending on user configuration and action selection. That gives a public, inspectable automation-level surface over Apple Intelligence without relying on private framework calls. ([Apple Support](https://support.apple.com/guide/mac-help/use-apple-intelligence-in-shortcuts-mchl91750563/mac "Use Apple Intelligence in Shortcuts on Mac - Apple Support"))

### The private framework family is active and versioned

The `IntelligenceFlow*` binaries are not stale artifacts. Shared-cache diffs show version churn and function-count changes across 26.x builds, including `IntelligenceFlow`, `IntelligenceFlowRuntime`, `PlannerRuntime`, and `AppIntentsPreviewToolSupport`. That strongly suggests ongoing development. ([GitHub](https://raw.githubusercontent.com/blacktop/ipsw-diffs/main/26_2_23C5027f__vs_26_2_23C5033h/DYLIBS/IntelligenceFlow.md "raw.githubusercontent.com"))

---

## Claims I would avoid making without local reproduction

| Claim | Status |
|----|----|
| “`IntelligenceFlow.framework` is the single core router for all Apple Intelligence requests” | Plausible, not proven publicly |
| “`intelligenceflowd` always orchestrates Siri, Writing Tools, Shortcuts, Spotlight, and Foundation Models” | Too broad without per-surface tracing |
| “Biome stores all Apple Intelligence transcripts” | Not established; diagnostics entitlements show some transcript-stream access |
| “The private APIs are stable enough to call from third-party software” | False assumption; private APIs are unsupported and unstable |
| “iOS shared-cache diffs exactly describe macOS internals” | Not safe; useful as cross-platform signal only |
| “Framework names reveal complete responsibilities” | Names are strong hints, not contracts |

Apple’s App Store rules and private-framework guidance remain relevant: apps should use documented APIs, and private frameworks can change without notice. ([GitHub](https://github.com/phatblat/macOSPrivateFrameworks "GitHub - phatblat/macOSPrivateFrameworks: ‍♂️ macOS Private Frameworks · GitHub"))

---

## Local verification playbook

For a macOS 15/26 research machine, I would validate in this order.

### 1. Inventory private frameworks

``` zsh
find /System/Library/PrivateFrameworks \
  -maxdepth 1 \
  -name 'IntelligenceFlow*' \
  -print | sort
```

On Big Sur and later, many system libraries are effectively represented through the dyld shared cache rather than normal standalone dylibs. The practical path is to extract from the shared cache before running `otool`, `nm`, `strings`, Hopper, or Ghidra workflows. ([Juan Cruz Viotti](https://www.jviotti.com/2023/11/20/exploring-macos-private-frameworks.html "Exploring macOS private frameworks"))

``` zsh
DSC=/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld/dyld_shared_cache_arm64e
OUT="$HOME/dsc-extracted"

mkdir -p "$OUT"
dyld-shared-cache-extractor "$DSC" "$OUT"

find "$OUT/System/Library/PrivateFrameworks" \
  -maxdepth 1 \
  -name 'IntelligenceFlow*' \
  -print | sort
```

### 2. Compare linkage

``` zsh
FW="$OUT/System/Library/PrivateFrameworks/IntelligenceFlowRuntime.framework/Versions/A/IntelligenceFlowRuntime"

otool -L "$FW"
otool -l "$FW" | rg 'LC_ID_DYLIB|LC_LOAD_DYLIB|name '
```

Focus on dependencies such as:

``` text
IntelligenceFlow.framework
IntelligenceFlowContext.framework
IntelligenceFlowPlanner*.framework
FoundationModels.framework
AppIntents.framework
Biome*.framework
Siri*.framework
```

### 3. Search names, subsystems, and service labels

``` zsh
for fw in "$OUT/System/Library/PrivateFrameworks"/IntelligenceFlow*.framework/Versions/A/*; do
  echo "## $fw"
  strings -a "$fw" \
    | rg -i 'com\.apple\.intelligenceflow|intelligenceflowd|orchestrator|planner|context|transcript|biome|tool|appintent' \
    | sort -u
done
```

### 4. Inspect entitlements on candidate daemons/extensions

``` zsh
codesign -d --entitlements :- /path/to/candidate 2>/dev/null | plutil -p -
```

Search for:

``` text
com.apple.intelligenceflow.context
com.apple.intelligenceflow.orchestrator
com.apple.intelligenceflow.transcript-entity-querying
com.apple.security.exception.mach-lookup.global-name
com.apple.private.biome.*
```

### 5. Inspect launchd registrations

``` zsh
launchctl print system | rg -i 'intelligence|foundation|model|siri|assistant'
launchctl print "gui/$UID" | rg -i 'intelligence|foundation|model|siri|assistant'
```

### 6. Observe unified logs under controlled prompts

``` zsh
log stream --style compact \
  --predicate 'subsystem CONTAINS[c] "intelligence" OR process CONTAINS[c] "intelligence" OR eventMessage CONTAINS[c] "IntelligenceFlow"'
```

Run separate trials for:

| Trial                            | Expected signal                         |
|----------------------------------|-----------------------------------------|
| Foundation Models sample app     | model daemon / session / tool-call logs |
| Siri request with no app action  | assistant + model/context logs          |
| Siri request invoking App Intent | App Intents bridge + orchestration logs |
| Shortcut “Use Model” on-device   | Shortcuts + model path                  |
| Shortcut “Use Model” PCC         | PCC/reporting path                      |
| Spotlight entity action          | App entity / indexed entity path        |

### 7. Correlate with Apple Intelligence privacy report

Apple documents that Mac can expose an Apple Intelligence privacy report for recent requests. Use it as an external consistency check for whether a request stayed on-device, used PCC, or used an extension such as ChatGPT. ([Apple Support](https://support.apple.com/guide/mac-help/apple-intelligence-and-privacy-mchlfc0d4779/mac "Apple Intelligence and privacy on Mac - Apple Support"))

---

## Research agenda for a deeper reverse-engineering pass

| Goal | Method | Output |
|----|----|----|
| Framework inventory by OS build | Extract dyld cache from macOS 15.x, 26.x, future betas | Versioned manifest of binaries, UUIDs, sizes, exported symbols, strings |
| Dependency graph | `otool -L`, `dyldinfo`, Mach-O load commands | Framework-to-framework graph |
| Entitlement map | `codesign` over daemons, appexes, frameworks where applicable | Capability matrix: context/orchestrator/transcript/Biome/Mach |
| XPC/Mach service map | launchd plists, entitlements, strings, runtime logs | Service graph |
| App Intents bridge map | compare public App Intents metadata with IntelligenceFlow logs | Tool-discovery/execution model |
| Context flow | run controlled Siri/Shortcuts/FoundationModels prompts and diff logs | Context service usage per surface |
| PCC boundary | compare privacy report, network/log state, request type | On-device vs PCC routing conditions |
| Prompt-injection surface | controlled App Intent / Shortcut / document-context prompts | Reproducible security notes, not speculation |

---

## Practical conclusion

`IntelligenceFlow*` is best understood as Apple’s **private orchestration/context/planning substrate around Apple Intelligence**, adjacent to the public Foundation Models and App Intents stack. The framework family is real, actively changing, entitlement-gated, and likely daemon-mediated.

For engineering work, the stable public substitutes are:

| Need | Public route |
|----|----|
| On-device generation | `FoundationModels.framework` |
| Structured output | Foundation Models guided generation |
| Model tool use | Foundation Models `Tool` protocol |
| App actions for Siri/Shortcuts/Spotlight | `AppIntents.framework` |
| Standardized Siri domains | Assistant Schemas |
| User automation | Shortcuts “Use Model” |
| Remote/private heavy inference | Private Cloud Compute, where Apple routes eligible requests |

For reverse engineering, the next high-value step is a per-build local map: `IntelligenceFlow*` binaries → entitlements → Mach services → launchd jobs → unified-log events → App Intents/tool execution. That is the point where the architecture moves from plausible naming inference to reproducible system behavior.
