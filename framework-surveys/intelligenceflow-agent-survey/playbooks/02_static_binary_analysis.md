# Playbook 02: static binary analysis

## Objective

Map dependencies, exported/imported symbols, string clusters, Swift/Objective-C metadata, and likely consumer relationships.

## Dependency scan

```zsh
for fw in ~/iflow-lab/dsc-extracted/System/Library/PrivateFrameworks/IntelligenceFlow*.framework/*; do
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
  ~/iflow-lab/dsc-extracted/System/Library/PrivateFrameworks \
  ~/iflow-lab/manifests/intelligenceflow_strings.txt
```

## Symbol and metadata extraction

```zsh
for fw in ~/iflow-lab/dsc-extracted/System/Library/PrivateFrameworks/IntelligenceFlow*.framework/*; do
  [[ -f "$fw" ]] || continue
  base=$(basename "$fw")
  nm -m "$fw" 2>/dev/null > "$HOME/iflow-lab/manifests/${base}.nm.txt" || true
  otool -ov "$fw" 2>/dev/null > "$HOME/iflow-lab/manifests/${base}.objc.txt" || true
  strings -a "$fw" | swift-demangle 2>/dev/null > "$HOME/iflow-lab/manifests/${base}.swift_demangled.txt" || true
done
```

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
