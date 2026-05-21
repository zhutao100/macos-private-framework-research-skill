# Public Apple architecture notes

## Foundation Models

`FoundationModels.framework` is Apple’s public on-device model framework. It is the correct starting point for developer-facing generation, structured output, tool calling, sessions, and transcript inspection.

Research implication: do not assume private `IntelligenceFlow*` calls are required for app-level model features. Use Foundation Models examples as controlled probes, and observe whether private `IntelligenceFlow*` logs or dependencies appear.

## App Intents, Siri, Shortcuts, Spotlight

Apple positions App Intents as the public way to expose app actions/entities across Siri, Shortcuts, Spotlight, widgets, and Apple Intelligence-adjacent surfaces. Assistant Schemas standardize domains/actions for Siri integration.

Research implication: App Intents trials provide a stable public action/tool surface. They are a better probe than private API invocation.

## Private Cloud Compute

PCC is Apple’s documented remote execution tier for complex Apple Intelligence requests. On Mac, Apple Intelligence privacy reports can expose recent PCC request activity.

Research implication: for each controlled trial, capture whether the request stayed on-device, used PCC, or used an extension model. Use the privacy report as an external correlation artifact.
