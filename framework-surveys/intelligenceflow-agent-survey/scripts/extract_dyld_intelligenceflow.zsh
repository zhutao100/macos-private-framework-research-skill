#!/bin/zsh
set -euo pipefail

OUT=${1:-"$HOME/iflow-lab/dsc-extracted"}
DSC=${2:-"/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld/dyld_shared_cache_arm64e"}

if [[ ! -f "$DSC" ]]; then
  echo "dyld shared cache not found: $DSC" >&2
  exit 1
fi

mkdir -p "$OUT"

frameworks=(
  IntelligenceFlow
  IntelligenceFlowAppIntentsPreviewToolSupport
  IntelligenceFlowContext
  IntelligenceFlowContextRuntime
  IntelligenceFlowFeedbackDataCollector
  IntelligenceFlowPlannerRuntime
  IntelligenceFlowPlannerSupport
  IntelligenceFlowRuntime
  IntelligenceFlowShared
)

if command -v ipsw >/dev/null 2>&1; then
  for fw in "${frameworks[@]}"; do
    log="$OUT/${fw}.extract.log"
    if ! ipsw dyld extract "$DSC" "$fw" -o "$OUT" --force >"$log" 2>&1; then
      cat "$log" >&2
      exit 1
    fi
  done
elif command -v dyld-shared-cache-extractor >/dev/null 2>&1; then
  dyld-shared-cache-extractor "$DSC" "$OUT"
else
  echo "ipsw or dyld-shared-cache-extractor is required" >&2
  exit 1
fi

{
  for fw in "${frameworks[@]}"; do
    if [[ -f "$OUT/$fw" ]]; then
      printf '%s\n' "$OUT/$fw"
    fi
    if [[ -f "$OUT/System/Library/PrivateFrameworks/$fw.framework/Versions/A/$fw" ]]; then
      printf '%s\n' "$OUT/System/Library/PrivateFrameworks/$fw.framework/Versions/A/$fw"
    fi
    if [[ -f "$OUT/System/Library/PrivateFrameworks/$fw.framework/$fw" ]]; then
      printf '%s\n' "$OUT/System/Library/PrivateFrameworks/$fw.framework/$fw"
    fi
  done
} | sort -u | tee "$OUT/intelligenceflow_extracted_paths.txt"
