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
        *.map|*.atlas|*.[0-9][0-9]) continue ;;
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
        'ipsw dyld macho "$1" SkyLight --symbols | awk -F "\t" '"'"'NF >= 2 { sym=$2; sub(/^_/, "", sym); if (sym ~ /^(SLS|CGS|SLPS|SLEvent|SLSEvent)/) print sym }'"'"' | sort -u' \
        sh "$primary_cache"
else
    printf 'Skipped: ipsw or primary dyld cache was not available.\n' >"$out_dir/skylight_ipsw_symbol_names.txt"
fi

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

if [[ "${SKYLIGHT_COLLECT_LOGS:-0}" == "1" ]]; then
    run skylight_unified_log_last_1h.txt log show --last 1h --style compact --predicate 'subsystem == "com.apple.SkyLight" OR process == "WindowServer"'
else
    printf 'Skipped. Set SKYLIGHT_COLLECT_LOGS=1 to collect recent SkyLight/WindowServer logs.\n' >"$out_dir/skylight_unified_log_last_1h.txt"
fi

printf 'Done: %s\n' "$out_dir"
