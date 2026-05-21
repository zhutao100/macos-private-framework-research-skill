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
scripts/collect_intelligenceflow_inventory.zsh ~/iflow-lab/inventory
```

On macOS 26.2 build 25C56 the framework bundles exist as dyld-cache skeletons: the framework directories and Info/version plists are present, but the main framework binary symlinks do not resolve to standalone files.

## Step 3: candidate process/service files

```zsh
sed -n '1,120p' ~/iflow-lab/inventory/candidate_summary.txt
```

## Step 4: dyld shared-cache extraction

Default Apple silicon DSC path:

```zsh
DSC=/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld/dyld_shared_cache_arm64e
OUT=~/iflow-lab/dsc-extracted
scripts/extract_dyld_intelligenceflow.zsh "$OUT" "$DSC"
```

The script prefers single-image `ipsw dyld extract`, which writes flat files such as `~/iflow-lab/dsc-extracted/IntelligenceFlow`. It falls back to broad `dyld-shared-cache-extractor` output when `ipsw` is unavailable.

```zsh
cat "$OUT/intelligenceflow_extracted_paths.txt"
```

## Step 5: manifest

```zsh
mkdir -p ~/iflow-lab/manifests
scripts/build_macho_manifest.py \
  --output ~/iflow-lab/manifests/intelligenceflow_macho_manifest.json \
  --markdown-output ~/iflow-lab/manifests/intelligenceflow_macho_manifest.md \
  "$OUT"
```

## Expected outputs

- `system.txt`
- `framework_paths.txt`
- `candidates.txt`
- `extracted_framework_paths.txt`
- `intelligenceflow_macho_manifest.json`
