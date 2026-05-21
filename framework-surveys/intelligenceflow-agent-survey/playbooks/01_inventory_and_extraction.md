# Playbook 01: inventory and extraction

## Objective

Build a reproducible, per-build inventory of `IntelligenceFlow*` frameworks and extracted dyld-cache artifacts.

## Step 1: baseline system metadata

```zsh
mkdir -p ~/iflow-lab/inventory
{
  date -u
  sw_vers
  uname -a
  arch
} | tee ~/iflow-lab/inventory/system.txt
```

## Step 2: direct filesystem inventory

```zsh
find /System/Library/PrivateFrameworks   -maxdepth 1   -name 'IntelligenceFlow*'   -print | sort | tee ~/iflow-lab/inventory/framework_paths.txt
```

## Step 3: candidate process/service files

```zsh
find /System/Library /usr/libexec /System/Applications /Applications   \( -iname '*intelligence*' -o -iname '*siri*' -o -iname '*shortcut*' \)   -print 2>/dev/null | sort | tee ~/iflow-lab/inventory/candidates.txt
```

## Step 4: dyld shared-cache extraction

Default Apple silicon DSC path:

```zsh
DSC=/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld/dyld_shared_cache_arm64e
OUT=~/iflow-lab/dsc-extracted
mkdir -p "$OUT"
dyld-shared-cache-extractor "$DSC" "$OUT"
```

Then collect extracted paths:

```zsh
find "$OUT/System/Library/PrivateFrameworks"   -maxdepth 1   -name 'IntelligenceFlow*'   -print | sort | tee ~/iflow-lab/inventory/extracted_framework_paths.txt
```

## Step 5: manifest

```zsh
scripts/build_macho_manifest.py   "$OUT/System/Library/PrivateFrameworks"/IntelligenceFlow*.framework   > ~/iflow-lab/manifests/intelligenceflow_macho_manifest.json
```

## Expected outputs

- `system.txt`
- `framework_paths.txt`
- `candidates.txt`
- `extracted_framework_paths.txt`
- `intelligenceflow_macho_manifest.json`
