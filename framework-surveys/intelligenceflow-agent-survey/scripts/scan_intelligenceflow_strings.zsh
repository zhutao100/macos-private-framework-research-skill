#!/bin/zsh
set -euo pipefail

ROOT=${1:-"$HOME/iflow-lab/dsc-extracted/System/Library/PrivateFrameworks"}
OUT=${2:-"$HOME/iflow-lab/manifests/intelligenceflow_strings.txt"}
mkdir -p "$(dirname "$OUT")"

PATTERN='com\.apple\.intelligenceflow|intelligenceflow|intelligencecontext|orchestrator|planner|context|transcript|biome|tool|appintent|foundationmodels|privatecloudcompute|shortcut|spotlight|assistant|siri'

: > "$OUT"
for fw in "$ROOT"/IntelligenceFlow*.framework; do
  [[ -d "$fw" ]] || continue
  bin="$fw/$(basename "$fw" .framework)"
  [[ -f "$bin" ]] || bin="$fw/Versions/A/$(basename "$fw" .framework)"
  [[ -f "$bin" ]] || continue
  {
    echo "## $bin"
    strings -a "$bin" 2>/dev/null | grep -E -i "$PATTERN" | sort -u || true
    echo
  } >> "$OUT"
done

echo "$OUT"
