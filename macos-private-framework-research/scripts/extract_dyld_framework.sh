#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<'USAGE'
Usage: extract_dyld_framework.sh --framework NAME [options]

Extract a named private framework from the active macOS dyld shared cache into a disposable output directory.

Required:
  --framework NAME        Framework basename, for example DiskManagement or CoreSuggestionsInternals.

Options:
  --cache PATH            Dyld shared cache path. Defaults to the first standard cache matching host arch.
  --output-dir DIR        Destination directory. Default: /tmp/macos-private-frameworks.
  --tool auto|ipsw|dsc    Extraction tool. Default: auto.
  --force                 Pass force flags where supported and permit reuse of the output directory.
  --keep-full-extract     Do not delete non-target files after a full dyld-shared-cache-extractor run.
  -h, --help              Show this help.

Notes:
  - This script writes only to --output-dir.
  - It does not modify dyld caches, system frameworks, installed apps, or code signatures.
  - ipsw is preferred because it can extract a single dylib/framework and enrich symbols.
USAGE
}

framework=""
cache=""
output_dir="/tmp/macos-private-frameworks"
tool="auto"
force=0
keep_full_extract=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --framework)
            framework="${2:-}"
            shift 2
            ;;
        --cache)
            cache="${2:-}"
            shift 2
            ;;
        --output-dir)
            output_dir="${2:-}"
            shift 2
            ;;
        --tool)
            tool="${2:-}"
            shift 2
            ;;
        --force)
            force=1
            shift
            ;;
        --keep-full-extract)
            keep_full_extract=1
            shift
            ;;
        -h | --help)
            usage
            exit 0
            ;;
        *)
            echo "error: unknown argument: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
done

if [[ -z "$framework" ]]; then
    echo "error: --framework is required" >&2
    usage >&2
    exit 2
fi

case "$tool" in
    auto | ipsw | dsc) ;;
    *)
        echo "error: --tool must be auto, ipsw, or dsc" >&2
        exit 2
        ;;
esac

find_default_cache() {
    local arch
    arch="$(uname -m 2>/dev/null || true)"
    local base_dirs=(
        "/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld"
        "/System/Library/dyld"
    )
    local names=()
    if [[ "$arch" == "arm64" ]]; then
        names=("dyld_shared_cache_arm64e" "dyld_shared_cache_arm64")
    else
        names=("dyld_shared_cache_x86_64h" "dyld_shared_cache_x86_64")
    fi
    local dir name candidate
    for dir in "${base_dirs[@]}"; do
        for name in "${names[@]}"; do
            candidate="$dir/$name"
            if [[ -f "$candidate" ]]; then
                printf '%s\n' "$candidate"
                return 0
            fi
        done
    done
    for dir in "${base_dirs[@]}"; do
        if [[ -d "$dir" ]]; then
            find "$dir" -maxdepth 1 -type f -name 'dyld_shared_cache_*' | sort | head -n 1
            return 0
        fi
    done
    return 1
}

if [[ -z "$cache" ]]; then
    cache="$(find_default_cache || true)"
fi

if [[ -z "$cache" || ! -f "$cache" ]]; then
    echo "error: dyld shared cache not found. Provide --cache PATH." >&2
    exit 1
fi

if [[ "$tool" == "auto" ]]; then
    if command -v ipsw >/dev/null 2>&1; then
        tool="ipsw"
    elif command -v dyld-shared-cache-extractor >/dev/null 2>&1; then
        tool="dsc"
    else
        echo "error: neither ipsw nor dyld-shared-cache-extractor is available in PATH" >&2
        exit 1
    fi
fi

mkdir -p "$output_dir"

find_target_outputs() {
    local root="$1"
    find "$root" -type f \( \
        -path "*/System/Library/PrivateFrameworks/${framework}.framework/*/${framework}" -o \
        -path "*/System/Library/PrivateFrameworks/${framework}.framework/${framework}" -o \
        -path "*/${framework}.framework/*/${framework}" -o \
        -path "*/${framework}.framework/${framework}" \
        \) 2>/dev/null | sort
}

extract_with_ipsw() {
    local args=(dyld extract "$cache" "$framework" -o "$output_dir")
    if [[ "$force" -eq 1 ]]; then
        args+=(--force)
    fi

    echo "+ ipsw ${args[*]} --objc --stubs" >&2
    if ipsw "${args[@]}" --objc --stubs; then
        return 0
    fi

    echo "warning: ipsw extraction with --objc --stubs failed; retrying without enrichment flags" >&2
    echo "+ ipsw ${args[*]}" >&2
    ipsw "${args[@]}"
}

extract_with_dsc() {
    if ! command -v dyld-shared-cache-extractor >/dev/null 2>&1; then
        echo "error: dyld-shared-cache-extractor not found" >&2
        exit 1
    fi
    echo "+ dyld-shared-cache-extractor $cache $output_dir" >&2
    dyld-shared-cache-extractor "$cache" "$output_dir"

    if [[ "$keep_full_extract" -eq 0 ]]; then
        cat >&2 <<'NOTE'
notice: dyld-shared-cache-extractor performs broad extraction. Non-target files were left in place because safe automatic pruning cannot be guaranteed for every tool version.
NOTE
    fi
}

case "$tool" in
    ipsw)
        if ! command -v ipsw >/dev/null 2>&1; then
            echo "error: ipsw not found" >&2
            exit 1
        fi
        extract_with_ipsw
        ;;
    dsc)
        extract_with_dsc
        ;;
esac

outputs=()
while IFS= read -r extracted_path; do
    outputs+=("$extracted_path")
done < <(find_target_outputs "$output_dir")

cat <<REPORT
Extraction complete
Framework: $framework
Cache: $cache
Tool: $tool
Output directory: $output_dir
REPORT

if [[ "${#outputs[@]}" -gt 0 ]]; then
    echo "Target files:"
    printf '  %s\n' "${outputs[@]}"
else
    cat <<'REPORT'
Target files: none found by expected framework path patterns.

Next checks:
  - Verify the framework name and dyld cache architecture.
  - Inspect the output directory for relocated paths.
  - Try ipsw class-dump directly against the cache if extraction succeeded but no standalone path was found.
REPORT
    exit 1
fi
