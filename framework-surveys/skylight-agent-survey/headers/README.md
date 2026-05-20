# SkyLight Headers

## Ready-To-Use

- `SkyLightReadOnly.h`: dlsym-based C declarations for read-only connection, display, Space, and window observation probes. Validated on macOS 15.7.2 build 24G325 and macOS 26.2 build 25C56 with `tools/verify_skylight_readonly_header.zsh`.
- `skylight_symbol_names.h`: symbol-name and Objective-C class-name constants for presence probes. It intentionally avoids callable signatures.

## Generated Headers

Full `ipsw class-dump` Objective-C headers are build-specific generated artifacts. Keep them in disposable workspaces and validate with `macos-private-framework-research/scripts/objc_signature_linter.py` before promoting any declaration into a project header.
