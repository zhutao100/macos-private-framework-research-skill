#!/bin/zsh
set -euo pipefail

CANDIDATES=${1:-"$HOME/iflow-lab/inventory/candidates.txt"}
OUT=${2:-"$HOME/iflow-lab/entitlements"}
mkdir -p "$OUT/raw" "$OUT/json"

if [[ ! -f "$CANDIDATES" ]]; then
  echo "candidate list not found: $CANDIDATES" >&2
  exit 1
fi

: > "$OUT/entitlement_index.txt"
while IFS= read -r path; do
  [[ -f "$path" || -d "$path" ]] || continue
  safe=$(echo "$path" | sed 's#[/: ]#_#g')
  raw="$OUT/raw/${safe}.plist"
  json="$OUT/json/${safe}.json"
  if codesign -d --entitlements :- "$path" > "$raw" 2>/dev/null; then
    plutil -convert json -o "$json" "$raw" 2>/dev/null || true
    if grep -E -i 'intelligenceflow|intelligenceplatform|biome|mach-lookup|appintents|shortcuts|siri|assistant' "$raw" >/dev/null 2>&1; then
      echo "$path" | tee -a "$OUT/entitlement_index.txt"
    fi
  else
    rm -f "$raw"
  fi
done < "$CANDIDATES"

grep -R -E -i 'com\.apple\.intelligenceflow|intelligenceflow|intelligenceplatform|biome|mach-lookup|orchestrator|transcript' "$OUT/raw" > "$OUT/intelligenceflow_entitlement_hits.txt" 2>/dev/null || true

echo "$OUT"
