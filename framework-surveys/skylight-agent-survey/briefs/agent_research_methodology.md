# LLM-Agent Methodology for macOS Private Framework Research

## Goal

Recover a build-specific, evidence-backed understanding of `SkyLight.framework` sufficient to guide overlay/computer-use engineering decisions without crossing into unsafe bypass or exploitation work.

## Core principles

| Principle | Rationale |
|---|---|
| Build-specific evidence | Private ABI drift is normal; never merge facts across OS builds without labels. |
| Observation before mutation | WindowServer state changes can disrupt the GUI session. |
| Public fallback first | Most production use cases should degrade to public APIs. |
| Symbol names are hypotheses | `dlsym` presence is not a callable signature. |
| Keep artifacts machine-readable | JSON manifests allow cross-build diffing and agent ingestion. |

## Recommended workflow

### Stage 0: target registration

Record:

- `sw_vers`
- `uname -a`
- `sysctl -n machdep.cpu.brand_string`
- `csrutil status`
- architecture and hardware class
- dyld shared cache paths and SHA-256 hashes, if practical
- Xcode/CommandLineTools version

### Stage 1: static inventory

Use read-only tools:

- `otool -L` for linked private frameworks in binaries under study.
- `nm`, `dyldinfo`, `strings`, Hopper, Ghidra, or dyld-cache-aware tooling for symbol/name inventory.
- RuntimeBrowser/class-dump-like tools for Objective-C metadata where available.
- Third-party declarations from yabai/Hammerspoon/Cua/SkyLightWindow as signposts, not headers.

### Stage 2: source cross-reference

For every candidate symbol:

- record where it appears;
- classify the surface area;
- mark whether it is used for observation, mutation, capture, or event routing;
- identify public API fallback;
- assign confidence C0-C4.

### Stage 3: build diffing

Diff manifests across:

- macOS 14.x, 15.x, 26.x;
- Intel vs Apple Silicon where relevant;
- minor updates with WindowServer CVEs or graphics changes.

### Stage 4: benign runtime observation

Allowed by this package:

- `dlopen`/`dlsym` presence checks;
- unified-log queries scoped to `com.apple.SkyLight`/WindowServer;
- public API experiments with AX/ScreenCaptureKit/CGWindowList;
- non-mutating Space/window enumeration where the implementation is already trusted in a lab.

Excluded by this package:

- bypassing SIP/AMFI/TCC;
- injecting into Dock/Finder/WindowServer/other Apple processes;
- invoking private event-injection paths;
- exploit development or crash-triggering fuzzing against WindowServer.

### Stage 5: engineering decision

For each desired product feature, produce:

- public implementation path;
- private implementation hypothesis;
- OS build compatibility table;
- failure mode and fallback;
- consent/permission implications;
- App Store/notarization constraints;
- test cases for Spaces, displays, fullscreen, Stage Manager, and login/lock states.
