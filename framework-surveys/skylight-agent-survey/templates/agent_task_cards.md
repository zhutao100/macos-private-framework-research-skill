# Agent Task Cards

## T1: Build inventory

Input: target macOS host.

Steps:

1. Run `tools/collect_skylight_inventory.zsh out/<target>`.
2. Run `swift tools/dlopen_probe_symbols.swift > out/<target>/dlsym_probe.tsv`.
3. Run `swift tools/dlopen_probe_symbols.swift --json > out/<target>/dlsym_probe.json`.
4. Record commands and outputs in `templates/report_template.md`.

Done when: OS metadata, dyld cache path, and symbol/class-presence output are saved. Include cache hashes when `SKYLIGHT_HASH_CACHES=1` was used.

## T2: Source cross-reference

Input: source tree for a project that may use SkyLight/private CGS.

Steps:

1. Run `python3 tools/extract_symbol_refs.py <tree> > out/source-symbols.json`.
2. Group symbols into categories from `references/symbol_clusters.md`.
3. Mark public API fallback for each category.

Done when: every candidate symbol has source path, category, and confidence C0.

## T3: Cross-build drift

Input: two or more symbol manifests.

Steps:

1. Normalize each manifest to `{"symbols":[{"symbol":"..."}]}`.
2. Run `tools/diff_symbol_manifests.py old.json new.json`.
3. Highlight added/removed symbols in report.

Done when: drift table is produced and risky disappearing symbols are flagged.

## T4: Overlay feasibility

Input: desired overlay behavior.

Steps:

1. Try public `NSWindow.Level` and collection-behavior options first.
2. Identify whether fullscreen/lock/special Spaces require private Space APIs.
3. Do not run mutating private calls without an explicit lab-only experiment plan.

Done when: feature has public fallback and private-risk statement.

## T5: Computer-use feasibility

Input: target app and action mode.

Steps:

1. Prefer AX element actions.
2. Use vision/capture only with Screen Recording consent.
3. Treat private event-routing/focus symbols as research-only unless separately authorized.

Done when: route is classified as AX, public event, capture, or private/rejected.
