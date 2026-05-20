# On-Device Exploration Plan

## Phase A: environment capture

Run:

```sh
mkdir -p out/$(hostname -s)
tools/collect_skylight_inventory.zsh out/$(hostname -s)
```

Expected outputs:

- OS/hardware metadata;
- SIP status;
- dyld cache path list;
- SkyLight bundle metadata;
- best-effort exported-symbol inventory;
- optional SkyLight unified logs only when `SKYLIGHT_COLLECT_LOGS=1` is set.

## Phase B: symbol presence probe

Run:

```sh
swift tools/dlopen_probe_symbols.swift > out/$(hostname -s)/dlsym_probe.txt
```

This script only checks whether known symbol names resolve. It does not call the resolved function pointers.

## Phase C: source-reference extraction

Against a local source tree:

```sh
python3 tools/extract_symbol_refs.py /path/to/source > out/source-symbol-refs.json
```

Use this for third-party projects and local experiments. Do not treat source references as ABI truth.

## Phase D: cross-build diff

```sh
python3 tools/diff_symbol_manifests.py out/mac15.json out/mac26.json
```

Focus on symbols that appear/disappear or move between prefixes.

## Phase E: report

Copy `templates/report_template.md` and fill all evidence fields. Each conclusion should cite a local output file or public source.
