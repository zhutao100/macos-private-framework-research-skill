# Agent Operating Guide

## Objective

Produce build-specific, verifiable research notes for `SkyLight.framework` without destabilizing the host or crossing macOS privacy/security boundaries.

## Rules

- Prefer public APIs first: AppKit/SwiftUI, Accessibility, ScreenCaptureKit, `CGWindowListCopyWindowInfo`, and public `CGEvent` paths.
- Treat private SLS/CGS/SLPS symbols as hypotheses until verified on the target OS build.
- Do not disable SIP, bypass AMFI, edit TCC databases, inject into Apple processes, patch system binaries, or attach to protected Apple daemons as part of this package's workflows.
- Use a disposable VM or lab Mac for any observation that could perturb WindowServer state.
- Keep all outputs build-specific: record `sw_vers`, `uname -a`, architecture, dyld shared cache path/hash, SIP status, and tool versions.
- Never convert a symbol-name observation into a callable signature without independent static + runtime validation.

## Work loop

1. Inventory target: run `tools/collect_skylight_inventory.zsh out/<target-id>`.
2. Symbol presence: run `swift tools/dlopen_probe_symbols.swift > out/<target-id>/dlsym_probe.txt`.
3. Normalize: parse outputs into JSON using `tools/extract_symbol_refs.py` where applicable.
4. Compare: use `tools/diff_symbol_manifests.py old.json new.json` across OS builds.
5. Analyze: map symbols into `references/symbol_clusters.md` categories.
6. Report: fill `templates/report_template.md` with exact commands, outputs, and confidence level.

## Confidence levels

| Level | Meaning |
|---|---|
| C0 | Name found only in third-party source/commentary. |
| C1 | Name present in local strings/symbol table on target build. |
| C2 | Name has static callsite evidence or type metadata. |
| C3 | Signature validated by non-destructive dlsym/prototype tests. |
| C4 | Behavior validated by benign on-device experiment with rollback plan. |

## Preferred output shape

Write concise Markdown plus JSON manifests. Avoid long prose dumps. Link every claim to a command output, source path, or public URL.
