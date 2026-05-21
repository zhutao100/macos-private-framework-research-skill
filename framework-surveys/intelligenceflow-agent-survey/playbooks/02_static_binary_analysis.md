# Playbook 02: static binary analysis

## Objective

Map dependencies, exported/imported symbols, string clusters, Swift/Objective-C metadata, and likely consumer relationships.

## Dependency scan

```zsh
for fw in ~/iflow-lab/dsc-extracted/IntelligenceFlow* \
          ~/iflow-lab/dsc-extracted/System/Library/PrivateFrameworks/IntelligenceFlow*.framework/Versions/A/*; do
  [[ -f "$fw" ]] || continue
  echo "## $fw"
  otool -L "$fw" 2>/dev/null || true
done | tee ~/iflow-lab/manifests/dependencies.txt
```

Focus dependency searches on:

```text
FoundationModels
AppIntents
Siri
Assistant
Shortcuts
Spotlight
Biome
IntelligencePlatform
IntelligenceFlow
```

## String scan

```zsh
scripts/scan_intelligenceflow_strings.zsh \
  ~/iflow-lab/dsc-extracted \
  ~/iflow-lab/manifests/intelligenceflow_strings.txt
```

## Symbol and metadata extraction

```zsh
for fw in ~/iflow-lab/dsc-extracted/IntelligenceFlow* \
          ~/iflow-lab/dsc-extracted/System/Library/PrivateFrameworks/IntelligenceFlow*.framework/Versions/A/*; do
  [[ -f "$fw" ]] || continue
  base=$(basename "$fw")
  nm -m "$fw" 2>/dev/null > "$HOME/iflow-lab/manifests/${base}.nm.txt" || true
  otool -ov "$fw" 2>/dev/null > "$HOME/iflow-lab/manifests/${base}.objc.txt" || true
  strings -a "$fw" | xcrun swift-demangle 2>/dev/null > "$HOME/iflow-lab/manifests/${base}.swift_demangled.txt" || true
done
```

## Header generation and validation

```zsh
DSC=/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld/dyld_shared_cache_arm64e
mkdir -p ~/iflow-lab/headers
for fw in IntelligenceFlow IntelligenceFlowAppIntentsPreviewToolSupport IntelligenceFlowContext IntelligenceFlowContextRuntime IntelligenceFlowFeedbackDataCollector IntelligenceFlowPlannerRuntime IntelligenceFlowPlannerSupport IntelligenceFlowRuntime IntelligenceFlowShared; do
  ipsw class-dump "$DSC" "/System/Library/PrivateFrameworks/$fw.framework/Versions/A/$fw" \
    --headers --output "$HOME/iflow-lab/headers/$fw" || true
done

../../macos-private-framework-research/scripts/objc_header_triage.py \
  --headers ~/iflow-lab/headers \
  --output ~/iflow-lab/manifests/intelligenceflow_header_triage.md \
  --json-output ~/iflow-lab/manifests/intelligenceflow_header_triage.json

../../macos-private-framework-research/scripts/objc_signature_linter.py \
  --headers ~/iflow-lab/headers \
  --output ~/iflow-lab/manifests/intelligenceflow_header_lint.md \
  --json-output ~/iflow-lab/manifests/intelligenceflow_header_lint.json \
  --compile
```

On macOS 26.2 build 25C56, the full generated headers are not project-ready as a set: Swift metadata names break direct clang syntax validation. Use `headers/IntelligenceFlowPresence.h` for project presence checks and harden callable signatures one declaration at a time.

## Analysis fields

For each binary, record:

- UUID and size.
- Direct dependencies.
- Exported symbols and count.
- Objective-C class/protocol/category names.
- Swift demangled type/function clusters.
- Strings grouped by subsystem, service, logging category, entitlement, Biome stream, planner/tool/app-intent terminology.
- Candidate consumers and call sites.

## Interpretation discipline

- Strings are discovery leads, not behavior proof.
- Pseudo-headers are local generated artifacts, not Apple headers.
- Cross-check every role inference with at least one of: consumer linkage, entitlement, launchd service, or runtime log correlation.
