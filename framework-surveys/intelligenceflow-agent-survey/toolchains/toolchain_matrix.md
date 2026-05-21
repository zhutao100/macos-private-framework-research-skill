# Toolchain matrix

| Research question | Minimum toolchain | Stronger toolchain | Output artifact |
|---|---|---|---|
| Does the framework exist on this build? | `find`, `stat`, `file` | DSC extraction + `ipsw dyld` | `framework_inventory.json` |
| Which frameworks does it link against? | `otool -L` | `dylibtree`, `dyldinfo`, Ghidra graph | `dependency_graph.md/json` |
| What services/labels does it mention? | `strings`, `grep` | string clustering + call-site disassembly | `string_clusters.md/json` |
| Which binaries have relevant entitlements? | `codesign`, `plutil` | `ipsw ent`, full filesystem candidate scan | `entitlement_matrix.json` |
| Which launchd jobs/services exist? | `launchctl print` | launchd plist scan + log correlation | `service_map.md/json` |
| Do public Apple Intelligence actions trigger it? | `log stream`, privacy report | controlled trials + repeated runs | `trial_records/*.yaml` |
| What are likely Objective-C method types? | class dump + `otool` | MOTIF-style LLM+tool+linter loop | `pseudo_headers.local/` + claim cards |
