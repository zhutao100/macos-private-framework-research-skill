# IntelligenceFlow Headers

## Ready-To-Use

- `IntelligenceFlowPresence.h`: dlsym and Objective-C runtime declarations for non-calling presence probes across the nine `IntelligenceFlow*` framework images. Validated on macOS 26.2 build 25C56 with `scripts/verify_intelligenceflow_presence_header.zsh`.

The header intentionally avoids callable private signatures. It is suitable for project diagnostics that need to confirm framework-family availability, version symbols, and representative class/protocol registration without linking against the frameworks.

## Generated Headers

Full `ipsw class-dump` headers were generated locally from the macOS 26.2 build 25C56 arm64e dyld shared cache. They are not included here. The generated set contained 293 header files, produced 408 raw-`id` linter warnings, and failed a direct clang syntax check because Swift metadata names are not Objective-C C type names. Keep those outputs in disposable workspaces and promote only declarations that pass `macos-private-framework-research/scripts/objc_signature_linter.py --compile`.
