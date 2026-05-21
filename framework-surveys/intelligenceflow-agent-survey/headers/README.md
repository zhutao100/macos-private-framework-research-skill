# IntelligenceFlow Headers

## Ready-To-Use

- `IntelligenceFlowPresence.h`: dlsym and Objective-C runtime declarations for non-calling presence probes across the nine `IntelligenceFlow*` framework images. Validated on macOS 15.7.2 build 24G325 and macOS 26.2 build 25C56 with `scripts/verify_intelligenceflow_presence_header.zsh`.

The header intentionally avoids callable private signatures. It is suitable for project diagnostics that need to confirm framework-family availability, version symbols, and representative class/protocol registration without linking against the frameworks.

## Generated Headers

Full `ipsw class-dump` headers were generated locally from macOS 15.7.2 build 24G325 and macOS 26.2 build 25C56 arm64e dyld shared caches. They are not included here. The 24G325 generated set contained 284 header files, produced 333 raw-`id` linter warnings, and failed a direct clang syntax check because Swift metadata names are not Objective-C C type names. The 25C56 generated set contained 293 header files and 408 raw-`id` linter warnings with the same direct clang limitation. Keep those outputs in disposable workspaces and promote only declarations that pass `macos-private-framework-research/scripts/objc_signature_linter.py --compile`.
