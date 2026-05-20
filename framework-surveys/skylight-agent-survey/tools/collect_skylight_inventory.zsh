#!/bin/zsh
set -euo pipefail
setopt NULL_GLOB

out_dir=${1:-"skylight-inventory-$(date -u +%Y%m%dT%H%M%SZ)"}
mkdir -p "$out_dir"

run() {
    local name=$1
    shift
    {
        printf '$'
        local arg
        for arg in "$@"; do
            printf ' %q' "$arg"
        done
        printf '\n\n'
        "$@"
    } >"$out_dir/$name" 2>&1 || true
}

printf 'SkyLight inventory created at %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >"$out_dir/README.txt"

run sw_vers.txt sw_vers
run uname.txt uname -a
run arch.txt arch
run csrutil_status.txt csrutil status
run xcodebuild_version.txt xcodebuild -version
run clang_version.txt clang --version

skylight_bundle='/System/Library/PrivateFrameworks/SkyLight.framework'
skylight_bin_a='/System/Library/PrivateFrameworks/SkyLight.framework/Versions/A/SkyLight'
skylight_bin_short='/System/Library/PrivateFrameworks/SkyLight.framework/SkyLight'
windowserver_bin='/System/Library/PrivateFrameworks/SkyLight.framework/Resources/WindowServer'

cache_candidates=(
    /System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld/dyld_shared_cache_*(.)
    /System/Library/dyld/dyld_shared_cache_*(.)
)
primary_cache=''
for cache in "${cache_candidates[@]}"; do
    case "$(basename "$cache")" in
        *.map | *.atlas | *.[0-9][0-9]) continue ;;
    esac
    primary_cache="$cache"
    break
done

{
    printf 'bundle=%s\n' "$skylight_bundle"
    /bin/ls -leO@ "$skylight_bundle" 2>&1 || true
    printf '\nVersions/A/SkyLight:\n'
    /bin/ls -leO@ "$skylight_bin_a" 2>&1 || true
    printf '\nSkyLight symlink path:\n'
    /bin/ls -leO@ "$skylight_bin_short" 2>&1 || true
    printf '\nResolved SkyLight binary path:\n'
    if [[ -e "$skylight_bin_short" ]]; then
        printf 'exists\n'
    else
        printf 'not present on filesystem; likely dyld-cache resident on this build\n'
    fi
    printf '\nWindowServer resource:\n'
    /bin/ls -leO@ "$windowserver_bin" 2>&1 || true
} >"$out_dir/skylight_paths.txt"

run skylight_file.txt file "$skylight_bin_short"
run skylight_otool_L.txt otool -L "$skylight_bin_short"
run skylight_codesign.txt codesign -dv --verbose=4 "$skylight_bin_short"
run windowserver_file.txt file "$windowserver_bin"
run windowserver_codesign.txt codesign -dv --verbose=4 "$windowserver_bin"

# Best-effort export/name inventory. Filesystem commands can fail when the framework binary is
# cache-resident; the compact ipsw path below is preferred when available.
run skylight_nm_global.txt nm -gjU "$skylight_bin_short"
run skylight_dyldinfo_exports.txt dyldinfo -exports "$skylight_bin_short"
run skylight_strings_sls.txt sh -c "strings -a '$skylight_bin_short' | grep -E '^(SLS|CGS|SLPS|SLEvent|SLSEvent|_SLPS)' | sort -u"

if [[ -n "$primary_cache" && -f "${primary_cache}.map" ]]; then
    run skylight_cache_map_refs.txt grep -n '/System/Library/PrivateFrameworks/SkyLight.framework' "${primary_cache}.map"
else
    printf 'Skipped: no primary dyld cache map was found.\n' >"$out_dir/skylight_cache_map_refs.txt"
fi

if [[ -n "$primary_cache" && -x "$(command -v ipsw 2>/dev/null || true)" ]]; then
    run skylight_ipsw_symbol_names.txt sh -c \
        'ipsw dyld macho "$1" SkyLight --symbols | awk -F "\t" '"'"'NF >= 2 { sym=$2; sub(/^_/, "", sym); if (sym ~ /^(SLS|CGS|SLPS|_SLPS|SLEvent|SLSEvent)/) print sym }'"'"' | sort -u' \
        sh "$primary_cache"
else
    printf 'Skipped: ipsw or primary dyld cache was not available.\n' >"$out_dir/skylight_ipsw_symbol_names.txt"
fi

awk '
BEGIN {
    order[1] = "CGS"
    order[2] = "SLS"
    order[3] = "SLPS"
    order[4] = "_SLPS"
    order[5] = "SLEvent"
    order[6] = "SLSEvent"
}
/^SLSEvent/ { count["SLSEvent"]++; next }
/^SLEvent/ { count["SLEvent"]++; next }
/^_SLPS/ { count["_SLPS"]++; next }
/^SLPS/ { count["SLPS"]++; next }
/^SLS/ { count["SLS"]++; next }
/^CGS/ { count["CGS"]++; next }
END {
    print "prefix\tcount"
    for (i = 1; i <= 6; i++) {
        print order[i] "\t" count[order[i]] + 0
    }
}
' "$out_dir/skylight_ipsw_symbol_names.txt" >"$out_dir/skylight_symbol_prefix_counts.tsv"

{
    printf 'primary_cache=%s\n\n' "$primary_cache"
    for cache in "${cache_candidates[@]}"; do
        [[ -e "$cache" ]] || continue
        printf '%s\n' "$cache"
        file "$cache" 2>/dev/null || true
        if [[ "${SKYLIGHT_HASH_CACHES:-0}" == "1" ]]; then
            shasum -a 256 "$cache" 2>/dev/null || true
        else
            printf 'sha256: skipped (set SKYLIGHT_HASH_CACHES=1)\n'
        fi
        printf '\n'
    done
} >"$out_dir/dyld_shared_caches.txt"

symbol_count=$(
    awk '!/^Skipped:/ && NF { count++ } END { print count + 0 }' \
        "$out_dir/skylight_ipsw_symbol_names.txt"
)

created_utc="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
product_version="$(sw_vers -productVersion 2>/dev/null || true)"
build_version="$(sw_vers -buildVersion 2>/dev/null || true)"
darwin_version="$(uname -r 2>/dev/null || true)"
arch_name="$(arch 2>/dev/null || true)"
framework_binary_present=0
if [[ -e "$skylight_bin_a" ]]; then
    framework_binary_present=1
fi

{
    printf '# SkyLight Inventory Summary\n\n'
    printf '- Created UTC: `%s`\n' "$created_utc"
    printf '- Product: `%s %s`\n' "$product_version" "$build_version"
    printf '- Darwin: `%s`\n' "$darwin_version"
    printf '- Architecture: `%s`\n' "$arch_name"
    printf '- Primary dyld cache: `%s`\n' "${primary_cache:-not found}"
    if [[ "$framework_binary_present" -eq 1 ]]; then
        printf '- Framework binary on filesystem: `present`\n'
    else
        printf '- Framework binary on filesystem: `absent; dyld-cache resident`\n'
    fi
    printf '- WindowServer resource: `%s`\n' "$windowserver_bin"
    printf '- SkyLight symbol names collected: `%s`\n' "$symbol_count"
    printf '\n## Symbol Prefix Counts\n\n'
    printf '| Prefix | Count |\n'
    printf '|---|---:|\n'
    awk 'NR > 1 { printf "| `%s` | %d |\n", $1, $2 }' \
        "$out_dir/skylight_symbol_prefix_counts.tsv"
    printf '\nSee `skylight_ipsw_symbol_names.txt` for the full symbol-name list and `dyld_shared_caches.txt` for cache details.\n'
} >"$out_dir/SUMMARY.md"

if command -v python3 >/dev/null 2>&1; then
    SKYLIGHT_CREATED_UTC="$created_utc" \
    SKYLIGHT_PRODUCT_VERSION="$product_version" \
    SKYLIGHT_BUILD_VERSION="$build_version" \
    SKYLIGHT_DARWIN_VERSION="$darwin_version" \
    SKYLIGHT_ARCH="$arch_name" \
    SKYLIGHT_PRIMARY_CACHE="${primary_cache:-}" \
    SKYLIGHT_BINARY_PRESENT="$framework_binary_present" \
    SKYLIGHT_WINDOWSERVER="$windowserver_bin" \
    SKYLIGHT_SYMBOL_COUNT="$symbol_count" \
    python3 - "$out_dir/skylight_symbol_prefix_counts.tsv" "$out_dir/SUMMARY.json" <<'PY'
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

counts_path = Path(sys.argv[1])
output_path = Path(sys.argv[2])

prefix_counts: dict[str, int] = {}
for line in counts_path.read_text().splitlines()[1:]:
    if not line.strip():
        continue
    prefix, count = line.split("\t", 1)
    prefix_counts[prefix] = int(count)

summary = {
    "schema_version": 1,
    "created_utc": os.environ["SKYLIGHT_CREATED_UTC"],
    "product_version": os.environ["SKYLIGHT_PRODUCT_VERSION"],
    "build_version": os.environ["SKYLIGHT_BUILD_VERSION"],
    "darwin_version": os.environ["SKYLIGHT_DARWIN_VERSION"],
    "architecture": os.environ["SKYLIGHT_ARCH"],
    "primary_dyld_cache": os.environ["SKYLIGHT_PRIMARY_CACHE"] or None,
    "framework_binary_on_filesystem": os.environ["SKYLIGHT_BINARY_PRESENT"] == "1",
    "windowserver_resource": os.environ["SKYLIGHT_WINDOWSERVER"],
    "symbol_count": int(os.environ["SKYLIGHT_SYMBOL_COUNT"]),
    "prefix_counts": prefix_counts,
    "outputs": {
        "markdown_summary": "SUMMARY.md",
        "symbol_names": "skylight_ipsw_symbol_names.txt",
        "dyld_caches": "dyld_shared_caches.txt",
    },
}
output_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
PY
else
    printf '{"schema_version":1,"status":"skipped","reason":"python3 unavailable"}\n' >"$out_dir/SUMMARY.json"
fi

if [[ "${SKYLIGHT_COLLECT_LOGS:-0}" == "1" ]]; then
    run skylight_unified_log_last_1h.txt log show --last 1h --style compact --predicate 'subsystem == "com.apple.SkyLight" OR process == "WindowServer"'
else
    printf 'Skipped. Set SKYLIGHT_COLLECT_LOGS=1 to collect recent SkyLight/WindowServer logs.\n' >"$out_dir/skylight_unified_log_last_1h.txt"
fi

printf 'Done: %s\n' "$out_dir"
