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
  echo
  echo "# tools"
  for tool in find stat file shasum otool vtool dwarfdump nm strings swift-demangle codesign plutil launchctl log ipsw dyld-shared-cache-extractor dylibtree; do
    printf '%-32s %s\n' "$tool" "$(command -v "$tool" 2>/dev/null || echo missing)"
  done
} | tee "$OUT/system.txt"

{ find /System/Library/PrivateFrameworks \
  -maxdepth 1 \
  -name 'IntelligenceFlow*' \
  -print 2>/dev/null || true; } | sort -u | tee "$OUT/framework_paths.txt"

candidate_roots=(
  /System/Library
  /usr/libexec
  /System/Applications
  /Applications
)

{
  for root in "${candidate_roots[@]}"; do
    [[ -e "$root" ]] || continue
    find "$root" \
      \( -iname '*intelligence*' -o -iname '*siri*' -o -iname '*shortcut*' -o -iname '*biome*' -o -iname '*foundation*model*' \) \
      -print 2>/dev/null || true
  done
} | grep -Ev '/Xcode\.app/Contents/Developer/Platforms/.*/SDKs/|/Xcode\.app/Contents/Developer/Toolchains/' \
  | sort -u | tee "$OUT/candidates.txt"

{
  echo "# candidate_count"
  wc -l < "$OUT/candidates.txt" | tr -d ' '
  echo "# high_signal_candidates"
  grep -E -i '/(intelligenceflowd|intelligencecontextd|IntelligenceFlowDiagnostics\.appex|assistantd|siriactionsd|siriinferenced|modelmanagerd|modelcatalogd|biomed|BiomeAgent)(/|$)' "$OUT/candidates.txt" || true
} > "$OUT/candidate_summary.txt"

while IFS= read -r p; do
  [[ -e "$p" ]] || continue
  echo "## $p"
  stat -f 'path=%N size=%z mode=%Sp modified=%Sm' "$p" 2>/dev/null || true
  file "$p" 2>/dev/null || true
  info="$p/Versions/A/Resources/Info.plist"
  version="$p/Versions/A/Resources/version.plist"
  base="${p:t:r}"
  binary="$p/$base"
  [[ -f "$info" ]] && plutil -p "$info" 2>/dev/null | grep -E 'CFBundleIdentifier|CFBundleVersion|CFBundleShortVersionString' || true
  [[ -f "$version" ]] && plutil -p "$version" 2>/dev/null | grep -E 'ProjectName|SourceVersion|BuildVersion' || true
  if [[ -e "$binary" ]]; then
    echo "binary_present=true"
    file "$binary" 2>/dev/null || true
    shasum -a 256 "$binary" 2>/dev/null || true
  else
    echo "binary_present=false"
    echo "dyld_cache_resident_hint=true"
  fi
done < "$OUT/framework_paths.txt" > "$OUT/framework_stat_hash.txt"
