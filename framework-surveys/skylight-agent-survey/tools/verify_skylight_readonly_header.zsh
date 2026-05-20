#!/bin/zsh
set -euo pipefail

usage() {
    cat <<'USAGE'
Usage: verify_skylight_readonly_header.zsh [output.json]

Compile and run the SkyLightReadOnly.h non-mutating prototype probe.
The probe writes JSON to stdout or to output.json when provided.
JSON includes dlsym/dladdr symbol-resolution records and non-mutating call results.
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    usage
    exit 0
fi

script_dir=${0:A:h}
survey_dir=${script_dir:h}
output=${1:-}
tmp_dir=$(mktemp -d "${TMPDIR:-/tmp}/skylight-readonly-verify.XXXXXX")
trap 'rm -rf "$tmp_dir"' EXIT

clang_bin=$(xcrun -f clang 2>/dev/null || command -v clang)
sdk_path=$(xcrun --sdk macosx --show-sdk-path 2>/dev/null || true)

compile_cmd=(
    "$clang_bin"
    -fobjc-arc
    -fmodules
    -Werror=implicit-function-declaration
    -I "$survey_dir/headers"
)
if [[ -n "$sdk_path" ]]; then
    compile_cmd+=(-isysroot "$sdk_path")
fi
compile_cmd+=(
    -framework Foundation
    -framework CoreGraphics
    "$script_dir/verify_skylight_readonly_header.m"
    -o "$tmp_dir/verify_skylight_readonly_header"
)

"${compile_cmd[@]}"

if [[ -n "$output" ]]; then
    "$tmp_dir/verify_skylight_readonly_header" >"$output"
else
    "$tmp_dir/verify_skylight_readonly_header"
fi
