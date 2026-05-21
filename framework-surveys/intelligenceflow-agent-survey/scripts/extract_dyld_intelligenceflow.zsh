#!/bin/zsh
set -euo pipefail

OUT=${1:-"$HOME/iflow-lab/dsc-extracted"}
DSC=${2:-"/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld/dyld_shared_cache_arm64e"}

if ! command -v dyld-shared-cache-extractor >/dev/null 2>&1; then
  echo "dyld-shared-cache-extractor not found in PATH" >&2
  exit 1
fi

if [[ ! -f "$DSC" ]]; then
  echo "dyld shared cache not found: $DSC" >&2
  exit 1
fi

mkdir -p "$OUT"
dyld-shared-cache-extractor "$DSC" "$OUT"

find "$OUT/System/Library/PrivateFrameworks" \
  -maxdepth 1 \
  -name 'IntelligenceFlow*' \
  -print 2>/dev/null | sort | tee "$OUT/intelligenceflow_extracted_paths.txt"
