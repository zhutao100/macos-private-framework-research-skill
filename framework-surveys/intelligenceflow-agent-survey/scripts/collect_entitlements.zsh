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
: > "$OUT/intelligenceflow_entitlement_hits.txt"
while IFS= read -r candidate_path; do
  [[ -f "$candidate_path" || -d "$candidate_path" ]] || continue
  digest=$(printf '%s' "$candidate_path" | shasum -a 256 | awk '{print substr($1, 1, 16)}')
  base=$(basename "$candidate_path" | tr -c '[:alnum:]._-' '_')
  safe="${base}_${digest}"
  raw="$OUT/raw/${safe}.plist"
  json="$OUT/json/${safe}.json"
  if codesign -d --entitlements :- "$candidate_path" > "$raw" 2>/dev/null; then
    plutil -convert json -o "$json" "$raw" >/dev/null 2>&1 || rm -f "$json"
    if grep -E -i 'intelligenceflow|intelligenceplatform|biome|mach-lookup|appintents|shortcuts|siri|assistant' "$raw" >/dev/null 2>&1; then
      printf '%s\t%s\n' "$candidate_path" "$json" | tee -a "$OUT/entitlement_index.txt"
      {
        echo "## $candidate_path"
        plutil -p "$raw" 2>/dev/null | grep -E -i 'com\.apple\.intelligenceflow|intelligenceflow|intelligenceplatform|biome|mach-lookup|orchestrator|transcript|modelmanager|shortcut|siri' | sed -n '1,120p' || true
        echo
      } >> "$OUT/intelligenceflow_entitlement_hits.txt"
    fi
  else
    rm -f "$raw"
  fi
done < "$CANDIDATES"

echo "$OUT"
