#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<'USAGE'
Usage: install_codex_skill.sh [--scope user|repo|legacy-codex] [--dest DIR] [--replace]

Installs the macos-private-framework-research skill directory.

Scopes:
  user          $HOME/.agents/skills                         (default)
  repo          $PWD/.agents/skills
  legacy-codex  $HOME/.codex/skills

Options:
  --dest DIR    Install into DIR instead of a predefined scope.
  --replace     Remove an existing skill directory before copying.
  -h, --help    Show this help.
USAGE
}

scope="user"
dest=""
replace=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --scope)
            scope="${2:-}"
            shift 2
            ;;
        --dest)
            dest="${2:-}"
            shift 2
            ;;
        --replace)
            replace=1
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

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$(cd "$script_dir/.." && pwd)"
skill_name="$(basename "$skill_dir")"

if [[ -z "$dest" ]]; then
    case "$scope" in
        user) dest="$HOME/.agents/skills" ;;
        repo) dest="$PWD/.agents/skills" ;;
        legacy-codex) dest="$HOME/.codex/skills" ;;
        *)
            echo "error: invalid scope: $scope" >&2
            usage >&2
            exit 2
            ;;
    esac
fi

mkdir -p "$dest"
target="$dest/$skill_name"

if [[ -e "$target" ]]; then
    if [[ "$replace" -eq 1 ]]; then
        rm -rf "$target"
    else
        echo "error: target already exists: $target (use --replace)" >&2
        exit 1
    fi
fi

cp -R "$skill_dir" "$target"

echo "installed $skill_name -> $target"
