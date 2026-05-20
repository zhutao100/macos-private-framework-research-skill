# SkyLight Build Report

## Target

| Field | Value |
|---|---|
| Host alias |  |
| macOS version/build |  |
| Architecture |  |
| Hardware |  |
| SIP status |  |
| Dyld cache path/hash |  |
| Xcode/CLT version |  |
| Date |  |

## Commands run

```sh
# Paste exact commands here.
```

## Outputs

| Artifact | Purpose | Notes |
|---|---|---|
| `SUMMARY.md` | compact inventory summary |  |
| `SUMMARY.json` | machine-readable compact inventory summary |  |
| `sw_vers.txt` | OS version |  |
| `dyld_shared_caches.txt` | cache paths/sizes and optional hashes |  |
| `skylight_symbol_prefix_counts.tsv` | compact symbol-prefix counts |  |
| `skylight_nm_global.txt` | exported names if available |  |
| `dlsym_probe.tsv` | C-symbol and Objective-C-class presence |  |
| `dlsym_probe.json` | machine-readable probe output |  |
| `readonly_header_probe.json` | `SkyLightReadOnly.h` compile/call validation |  |

## Symbol findings

| Name | Kind | Category | Evidence | Confidence | Notes |
|---|---|---|---|---|---|
|  | c_symbol / objc_class |  |  | C0-C4 |  |

## Public API fallback map

| Desired behavior | Public path | Private hypothesis | Decision |
|---|---|---|---|
|  |  |  |  |

## Risks and constraints

- Distribution:
- Permissions/TCC:
- SIP/AMFI:
- GUI-session stability:
- OS drift:

## Open questions

1.
2.
3.
