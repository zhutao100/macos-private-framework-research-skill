#!/bin/zsh
set -euo pipefail
setopt NULL_GLOB

ROOT=${1:-"$HOME/iflow-lab/dsc-extracted/System/Library/PrivateFrameworks"}
OUT=${2:-"$HOME/iflow-lab/manifests/intelligenceflow_strings.txt"}
MAX_LINES_PER_BINARY=${MAX_LINES_PER_BINARY:-120}
mkdir -p "$(dirname "$OUT")"

PATTERN='com\.apple\.intelligenceflow|intelligenceflow|intelligencecontext|orchestrator|planner|context|transcript|biome|tool|appintent|foundationmodels|privatecloudcompute|shortcut|spotlight|assistant|siri'

: > "$OUT"
for candidate in "$ROOT"/IntelligenceFlow* "$ROOT"/System/Library/PrivateFrameworks/IntelligenceFlow*.framework; do
  [[ -e "$candidate" ]] || continue
  if [[ -f "$candidate" ]]; then
    bin="$candidate"
  else
    bin="$candidate/$(basename "$candidate" .framework)"
    [[ -f "$bin" ]] || bin="$candidate/Versions/A/$(basename "$candidate" .framework)"
  fi
  [[ -f "$bin" ]] || continue
  {
    echo "## $bin"
    strings -a "$bin" 2>/dev/null | grep -E -i "$PATTERN" | sort -u | sed -n "1,${MAX_LINES_PER_BINARY}p" || true
    echo
  } >> "$OUT"
done

echo "$OUT"
