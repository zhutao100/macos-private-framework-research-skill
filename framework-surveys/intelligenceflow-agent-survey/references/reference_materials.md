# Existing reference materials

## Primary Apple sources

- Apple Intelligence developer page: public integration overview.
- WWDC25 Foundation Models sessions: on-device model API, tool calling, guided generation, stateful sessions.
- WWDC24 Siri/App Intents session: App Intents, SiriKit, Assistant Schemas, semantic search, on-screen context.
- WWDC25 Shortcuts/Spotlight session: Use Model action and App Intents on Mac.
- Apple Support privacy pages: PCC routing and Apple Intelligence privacy reports.
- apple/security-pcc: PCC source components for security/privacy verification.

## Private-framework discovery references

- The Apple Wiki `/System/Library/PrivateFrameworks`: framework-name discovery index.
- blacktop/ipsw-diffs: shared-cache diff artifacts for paths, UUIDs, version churn, function/symbol/string counts.
- NewOSXBook entitlement database: entitlement and Mach lookup discovery hints.

## Header/pseudo-header references

No generated private headers are included. `headers/IntelligenceFlowPresence.h` is a project-authored presence header that uses `dlopen`, `dlsym`, and Objective-C runtime lookup without declaring callable private APIs. For local pseudo-header work, use:

- `ipsw class-dump` / `ipsw swift-dump` where applicable.
- `class-dump`, `RuntimeBrowser`, or Ghidra/IDA/Hopper metadata views.
- Local outputs only; store provenance and build IDs with every pseudo-header.
- `macos-private-framework-research/scripts/objc_signature_linter.py --compile` before promoting a declaration into project code.

## Usage recipes included here

- `playbooks/01_inventory_and_extraction.md`: inventory and DSC extraction.
- `playbooks/02_static_binary_analysis.md`: dependency, metadata, strings, ObjC/Swift inspection.
- `playbooks/03_entitlements_services_logs.md`: entitlements, Mach/XPC labels, launchd, logs.
- `playbooks/04_app_intents_shortcuts_pcc_trials.md`: controlled public-surface experiments.
