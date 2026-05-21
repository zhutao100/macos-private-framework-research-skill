# Tooling catalog

| Tool | Role | Notes |
|---|---|---|
| `find`, `stat`, `file`, `shasum` | Baseline inventory | Built into macOS. |
| `otool` | Mach-O dependencies/load commands | Use `-L`, `-l`, `-Iv`, `-ov` as needed. |
| `vtool` | Build/toolchain metadata | Useful for SDK/build metadata. |
| `dwarfdump --uuid` | UUID capture | Key for cross-build comparison. |
| `nm` | Symbol extraction | Exported symbol inventory; not complete for stripped binaries. |
| `strings` | String search | Use as hints, never behavior proof. |
| `swift-demangle` | Swift symbol readability | Pipe Swift-looking names. |
| `codesign -d --entitlements :-` | Entitlement extraction | Works for code-signed binaries/appexes/daemons. |
| `plutil` | Parse plists/entitlements | Use `-p` and `-convert json`. |
| `launchctl print` | launchd/service map | User/system domains. |
| `log stream`, `log show` | Unified-log observation | Use explicit predicates and time windows. |
| `dyld-shared-cache-extractor` | Local DSC extraction | Required for many Big Sur+ analysis paths. |
| `ipsw` | Mach-O, DSC, entitlement, ObjC/Swift dump workflows | Strong all-purpose Apple OS research tool. |
| `macos-private-framework-research/scripts/framework_macho_manifest.py` | Agent-sized framework-family manifest | Summarizes dyld-cache skeletons, extracted binaries, dependency counts, symbols, focused strings, and optional cache evidence. |
| `macos-private-framework-research/scripts/collect_code_entitlements.py` | Agent-sized entitlement summaries | Prefer before loading raw entitlement plists from broad candidate sets. |
| `dylibtree` | Dependency graph | Useful for recursive linkage maps. |
| Hopper/Ghidra/IDA | Decompilation and metadata navigation | Record tool version and database settings. |
| ANTLR/linter harness | Pseudo-header validation | Part of MOTIF-style type-inference workflow. |

## Tool version capture

Always capture:

```zsh
sw_vers
uname -a
xcodebuild -version 2>/dev/null || true
xcrun --find otool 2>/dev/null || command -v otool
for tool in otool vtool dwarfdump nm strings codesign plutil launchctl log ipsw dyld-shared-cache-extractor dylibtree; do
  printf '%-32s %s\n' "$tool" "$(command -v "$tool" 2>/dev/null || echo missing)"
done
printf '%-32s %s\n' "xcrun swift-demangle" "$(xcrun -f swift-demangle 2>/dev/null || echo missing)"
```
