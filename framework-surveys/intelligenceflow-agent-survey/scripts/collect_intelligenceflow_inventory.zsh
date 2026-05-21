#!/bin/zsh
set -euo pipefail

OUT=${1:-"$HOME/iflow-lab/inventory"}
mkdir -p "$OUT"

{
  echo "# collected_at_utc"
  date -u
  echo "# sw_vers"
  sw_vers
  echo "# uname"
  uname -a
  echo "# arch"
  arch
  echo "# tools"
  for tool in find stat file shasum otool vtool dwarfdump nm strings swift-demangle codesign plutil launchctl log ipsw dyld-shared-cache-extractor dylibtree; do
    printf '%-32s %s\n' "$tool" "$(command -v "$tool" 2>/dev/null || echo missing)"
  done
} | tee "$OUT/system.txt"

find /System/Library/PrivateFrameworks \
  -maxdepth 1 \
  -name 'IntelligenceFlow*' \
  -print 2>/dev/null | sort | tee "$OUT/framework_paths.txt"

find /System/Library /usr/libexec /System/Applications /Applications \
  \( -iname '*intelligence*' -o -iname '*siri*' -o -iname '*shortcut*' -o -iname '*biome*' -o -iname '*foundation*model*' \) \
  -print 2>/dev/null | sort | tee "$OUT/candidates.txt"

while IFS= read -r p; do
  [[ -e "$p" ]] || continue
  echo "## $p"
  stat -f 'path=%N size=%z mode=%Sp modified=%Sm' "$p" 2>/dev/null || true
  file "$p" 2>/dev/null || true
  [[ -f "$p" ]] && shasum -a 256 "$p" 2>/dev/null || true
done < "$OUT/framework_paths.txt" > "$OUT/framework_stat_hash.txt"
