# Tooling Workflows

## 1. Host Inventory

Start every investigation with:

```bash
scripts/macos_private_framework_inventory.py \
  --output /tmp/macos-pf-inventory.md \
  --json-output /tmp/macos-pf-inventory.json
```

Check:

- `sw_vers` product/build.
- `uname -m` architecture.
- dyld cache candidates in `/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld/` and `/System/Library/dyld/`.
- Xcode/CLT path and version.
- `csrutil status` and `csrutil authenticated-root status` for research notes only; do not ask to disable protections.
- availability of `ipsw`, `dyld-shared-cache-extractor`, `class-dump`, Hopper, RuntimeViewer, RuntimeBrowser, LLDB, and LLVM tools.

### Optional Toolchain Resolution

Do not install every optional toolchain up front. When a selected workflow needs a missing non-built-in tool, check the configured source first:

```bash
scripts/resolve_toolchains.py ipsw dyld-shared-cache-extractor
scripts/resolve_toolchains.py RuntimeViewer RuntimeBrowser Hopper HopperMCPServer
```

The resolver reads `agents/tool-installation.yaml`, checks commands and application bundles, and reports install commands, URLs, and notes. Use `--run-install` only for a specific missing toolchain required by the current task, then rerun the resolver or inventory and record the observed version/source in the report.

## 2. Client-Driven Discovery

Given a client app:

```bash
scripts/discover_private_frameworks.py \
  --output /tmp/client-private-frameworks.md \
  --json-output /tmp/client-private-frameworks.json \
  "/System/Applications/Utilities/Disk Utility.app"
```

The script resolves the main executable using `Info.plist`, walks common embedded component locations, and runs `otool -L` on Mach-O files. It groups `/System/Library/PrivateFrameworks/*.framework` references by framework and target binary.

Manual fallback:

```bash
APP="/System/Applications/Utilities/Disk Utility.app"
EXE="$APP/Contents/MacOS/Disk Utility"
otool -L "$EXE" | grep PrivateFrameworks
plutil -p "$APP/Contents/Info.plist"
codesign -d --entitlements :- "$APP" 2>/dev/null || true
```

For daemons and agents, inspect:

```bash
plutil -p /System/Library/LaunchDaemons/com.example.plist
plutil -p /System/Library/LaunchAgents/com.example.plist
```

Use entitlement and Mach service names as routing hints, not proof of API behavior.

## 3. Dyld Shared Cache Extraction

Preferred single-framework path:

```bash
scripts/extract_dyld_framework.sh \
  --framework DiskManagement \
  --output-dir /tmp/macos-private-frameworks
```

`ipsw` can also emit ObjC/stub enrichment during extraction, but that can be expensive on large or new caches. Start with the plain extraction above, then opt in only when needed:

```bash
scripts/extract_dyld_framework.sh \
  --framework DiskManagement \
  --output-dir /tmp/macos-private-frameworks \
  --enrich-objc-stubs
```

Manual `ipsw` examples:

```bash
CACHE=/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld/dyld_shared_cache_arm64e
ipsw dyld info "$CACHE"
ipsw dyld extract "$CACHE" DiskManagement -o /tmp/macos-private-frameworks --force
ipsw dyld extract "$CACHE" DiskManagement -o /tmp/macos-private-frameworks --objc --stubs --force
ipsw dyld macho "$CACHE" DiskManagement --objc --symbols --strings
ipsw class-dump "$CACHE" DiskManagement --headers --output /tmp/DiskManagement.headers
```

If `--objc`/`--stubs` flags fail or stall on an older/newer `ipsw`, retry without them and use `ipsw class-dump` plus `ipsw dyld macho --symbols --strings` as separate, more bounded steps.

For cache-resident frameworks, run `ipsw class-dump` against the dyld cache path first. A flat file produced by `ipsw dyld extract` can be useful for Mach-O load-command inspection while still failing Objective-C metadata address mapping during class-dump on newer caches.

Manual `dyld-shared-cache-extractor` examples:

```bash
CACHE=/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld/dyld_shared_cache_arm64e
dyld-shared-cache-extractor "$CACHE" /tmp/macos-private-frameworks
DEVELOPER_DIR=/Applications/Xcode-beta.app \
  dyld-shared-cache-extractor "$CACHE" /tmp/macos-private-frameworks
```

This extracts many cache entries. Locate the target afterward:

```bash
find /tmp/macos-private-frameworks -type f -path '*System/Library/PrivateFrameworks/DiskManagement.framework/*'
```

## 4. Header Reconstruction

Try multiple independent header/interface sources when fidelity matters:

| Source | Strength | Weakness |
|---|---|---|
| `ipsw class-dump` | repeatable CLI, dyld-aware | ObjC-centric; types can remain generic |
| RuntimeViewer | ObjC + Swift; rich interface export; MCP | requires app/tool availability; injection features require care |
| RuntimeBrowser | classic live ObjC runtime browse/export | only loaded ObjC runtime state; old macOS UI assumptions |
| Hopper export | good for focused GUI disassembly and ObjC headers | GUI/tool license; header export still metadata-limited |
| `class-dump` | simple standalone ObjC dump | often weaker on modern dyld cache/extracted binaries |

Keep each output in a separate directory and compare:

```bash
mkdir -p /tmp/FrameworkName.headers/{ipsw,runtimeviewer,hopper}
diff -ru /tmp/FrameworkName.headers/ipsw /tmp/FrameworkName.headers/runtimeviewer | less
```

## 5. Runtime Presence Probe

Before treating a name as callable or using it as class metadata, run a read-only presence probe:

```bash
scripts/dlopen_symbol_probe.swift \
  --image /System/Library/PrivateFrameworks/FrameworkName.framework/FrameworkName \
  --symbol CandidateFunction \
  --class CandidateClass \
  --json > /tmp/FrameworkName.probe.json
```

Use repeated `--image` arguments for framework-path fallbacks and repeated `--symbol`/`--class` arguments for a short candidate set. For larger lists, use newline-delimited files:

```bash
scripts/dlopen_symbol_probe.swift \
  --image /System/Library/PrivateFrameworks/FrameworkName.framework/FrameworkName \
  --symbol-file /tmp/FrameworkName.symbols.txt \
  --class-file /tmp/FrameworkName.classes.txt \
  --json
```

The probe records host build metadata, the loaded path, `dlsym` status, `NSClassFromString` status, and `dladdr` image/symbol resolution for present C symbols. It does not call resolved function pointers or instantiate classes. Treat `present` as name evidence only; signatures still require static metadata, caller evidence, and linter/compile validation.

Use `scripts/diff_symbol_manifests.py --status present old.json new.json` to compare two probe JSON files or symbol manifests across builds.

## 6. Hopper Companion Workflow

When the Hopper skill is installed, use it for binary evidence:

```bash
hopper-disassembler-analysis/scripts/inspect_macho_targets.py \
  --include-deps \
  --output /tmp/framework.inventory.md \
  /tmp/macos-private-frameworks/.../FrameworkName

hopper-disassembler-analysis/scripts/run_hopper_export.sh \
  --include-pseudocode \
  --procedure-pattern 'SelectorOrClassName|0xADDRESS' \
  --max-procedures 20 \
  --max-basic-blocks 32 \
  --summary-output /tmp/framework.hopper.md \
  --output /tmp/framework.hopper.json \
  /tmp/macos-private-frameworks/.../FrameworkName
```

Search the snapshot before reopening Hopper:

```bash
hopper-disassembler-analysis/scripts/hopper_evidence_search.py \
  --ignore-case \
  /tmp/framework.hopper.json \
  'selectorName|ClassName|UniqueString'
```

## 7. RuntimeViewer Workflow

Use RuntimeViewer when Swift metadata or an MCP bridge can improve the agent loop.

Static-first procedure:

1. Open the extracted framework or dyld-cache entry in RuntimeViewer.
2. Export Objective-C and Swift interfaces to `/tmp/FrameworkName.runtimeviewer/`.
3. Enable rich options when the goal is LLM inference: ivar offsets, method IMP addresses, property accessor addresses, Swift type layout, enum layout, vtable/PWT offsets, and member addresses.
4. Feed the export into `objc_header_triage.py` for Objective-C candidates and keep Swift interface output as reference context.

MCP procedure:

1. Start RuntimeViewer and verify the MCP bridge status.
2. Copy the app-provided MCP config into the LLM client's MCP config.
3. Use read-only runtime inspection calls first.
4. Avoid process injection unless explicitly authorized and necessary.

Use `assets/runtimeviewer-mcp-config.example.json` only as a placeholder; RuntimeViewer should provide the authoritative config.

## 8. RuntimeBrowser Workflow

RuntimeBrowser remains useful for fast ObjC runtime browsing:

1. Build/open RuntimeBrowser on the target macOS host.
2. Load the desired framework if it is not already loaded.
3. Export header-like output for classes/protocols.
4. Compare against static dumps.

Do not rely on RuntimeBrowser for Swift-only types, pure C/C++ APIs, or unloaded framework surfaces.

## 9. Built-In Tool Fallbacks

```bash
file /path/to/binary
lipo -info /path/to/binary
otool -L /path/to/binary
otool -l /path/to/binary
nm -m /path/to/binary | head
strings -a /path/to/binary | grep -i 'selector-or-keyword'
xcrun llvm-objdump --macho --syms /path/to/binary | head
xcrun swift-demangle '$s...'
```

For symbols and strings, keep output bounded. Large raw dumps are less useful to agents than compact evidence snippets tied to one candidate.

## 10. Cache-Resident Framework Paths

On modern macOS, a framework bundle can exist on disk while the Mach-O image is cache-resident. In that case, `file`, `nm`, `dyldinfo`, or `strings` on `/System/Library/PrivateFrameworks/Name.framework/Name` may fail even though `dlopen` succeeds.

Check the cache map and switch to cache-aware tools:

```bash
CACHE=/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld/dyld_shared_cache_arm64e
grep '/System/Library/PrivateFrameworks/Name.framework' "$CACHE.map"
ipsw dyld macho "$CACHE" Name --symbols
ipsw class-dump "$CACHE" Name --headers --output /tmp/Name.headers
```
