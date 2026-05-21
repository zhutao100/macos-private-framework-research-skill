#!/bin/zsh
set -euo pipefail

SECONDS_TO_RUN=${1:-120}
OUT=${2:-"$HOME/iflow-lab/logs/intelligenceflow_${SECONDS_TO_RUN}s.log"}
mkdir -p "$(dirname "$OUT")"

PREDICATE='subsystem CONTAINS[c] "intelligence" OR process CONTAINS[c] "intelligence" OR eventMessage CONTAINS[c] "IntelligenceFlow" OR eventMessage CONTAINS[c] "FoundationModels" OR eventMessage CONTAINS[c] "AppIntent" OR eventMessage CONTAINS[c] "PrivateCloudCompute" OR eventMessage CONTAINS[c] "Shortcuts" OR eventMessage CONTAINS[c] "Spotlight" OR eventMessage CONTAINS[c] "Siri"'

{
  echo "# started_at_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "# timeout_seconds=$SECONDS_TO_RUN"
  echo "# predicate=$PREDICATE"
} > "$OUT"

log stream --style compact --timeout "$SECONDS_TO_RUN" --predicate "$PREDICATE" >> "$OUT"

echo "$OUT"
