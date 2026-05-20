# Modern macOS Notes: 15, 26, and Future Versions

## Version and Build Discipline

Always record:

```bash
sw_vers
uname -m
xcode-select -p 2>/dev/null || true
xcodebuild -version 2>/dev/null || true
csrutil status 2>/dev/null || true
csrutil authenticated-root status 2>/dev/null || true
```

Private framework contents, dyld cache format, Swift metadata, and generated stubs can change between minor releases and betas. Treat every result as scoped to the exact product version and build.

## Dyld Shared Cache Locations

Modern macOS commonly stores dyld shared caches under:

```text
/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld/dyld_shared_cache_arm64e
/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld/dyld_shared_cache_x86_64h
```

Older or alternate systems may also expose:

```text
/System/Library/dyld/dyld_shared_cache_arm64e
/System/Library/dyld/dyld_shared_cache_x86_64h
/System/Library/dyld/dyld_shared_cache_x86_64
```

Use `scripts/macos_private_framework_inventory.py` instead of hardcoding a single path.

## Architecture Selection

- Apple Silicon system caches are usually `arm64e`.
- Intel systems may use `x86_64h` or `x86_64`.
- Universal client apps can contain multiple slices. Keep architecture-specific conclusions separate.
- arm64e pointer authentication can affect pointer interpretation; prefer tools that understand PAC and dyld slide info.

## Cryptex and Sealed System Volume

Modern macOS places substantial OS content in sealed/read-only system locations and Cryptex paths. Do not attempt to patch or rebuild live dyld caches. Extract into `/tmp` or an explicit research workspace and analyze copies.

Some framework bundles retain resources and signatures on disk while the Mach-O image is only present in the dyld shared cache. Treat a missing `Versions/A/FrameworkName` binary as a packaging fact, not proof that the framework is unavailable. Check the dyld cache map and use cache-aware tools before drawing conclusions.

## macOS 26+ Naming

Apple's 2025 platform naming introduced macOS Tahoe 26. Future annual releases may continue version-number naming while preserving private-framework and dyld-cache mechanics with incremental changes. Avoid version-specific assumptions unless verified on the host.

## Xcode Drift

When dyld extraction fails on a beta/new OS:

1. Check selected Xcode:

   ```bash
   xcode-select -p
   xcodebuild -version
   ```

2. Try the matching beta/newer Xcode:

   ```bash
   DEVELOPER_DIR=/Applications/Xcode-beta.app \
     dyld-shared-cache-extractor "$CACHE" /tmp/macos-private-frameworks
   ```

3. Try `ipsw` if the extractor fails, or Hopper's dyld cache loader for focused inspection.

## Swift and Objective-C Surfaces

Private frameworks can expose a mixture of:

- Objective-C classes, protocols, categories, properties, ivars, and selectors.
- Swift nominal types, extensions, protocols, enums, vtables, protocol witness tables, and reflection metadata.
- C functions, constants, structs, and CoreFoundation-style APIs.
- C++ symbols and templates.
- XPC/Mach service surfaces and entitlement-sensitive flows.

Objective-C header dumps are only one surface. When Swift or C/C++ appears relevant, add RuntimeViewer, Swift demangling, symbol analysis, and disassembly to the evidence bundle.

## Runtime Loading Caveats

Runtime enumeration tools observe what is loaded in a process. Static Mach-O/dyld analysis observes what is present in a binary. Differences are expected:

| Difference | Cause |
|---|---|
| RuntimeBrowser sees fewer classes | framework not loaded, lazy category loading, gated paths |
| Static dump sees classes runtime does not show | code not loaded in current process |
| RuntimeViewer static export differs from runtime view | static metadata vs live runtime realization |
| Hopper header export differs from class dump | different parser heuristics and cache handling |

Use disagreement as a triage signal, not an automatic error.

## Safe Dynamic Analysis

Dynamic analysis can be useful for resolving receivers and concrete types, but it increases risk and operational complexity. Before dynamic analysis:

- Use a VM or sacrificial user account.
- Prefer read-only observation.
- Avoid disabling SIP/TCC or injecting into protected/system processes unless the user has explicitly authorized it and the analysis cannot be done statically.
- Capture only the minimum trace needed for the candidate signature.
