# SkyLight.framework Technical Brief

## Executive model

`SkyLight.framework` is the private macOS client-side ABI around WindowServer/CoreGraphics Services/SLS. It is not a supported application GUI framework. It sits below AppKit/SwiftUI/CoreAnimation-adjacent public APIs and above WindowServer's compositing, display, Space, input-routing, and capture machinery.

A useful mental model:

```text
AppKit / SwiftUI / CoreAnimation / Accessibility / ScreenCaptureKit
        ↓
CoreGraphics Services / SkyLight private client ABI
        ↓
WindowServer IPC boundary
        ↓
compositing, windows, Spaces, displays, input routing, capture, IOSurface/GPU integration
```

## Why it matters for overlays and computer-use agents

| Need | Public API path | What SkyLight appears to add | Research posture |
|---|---|---|---|
| Cross-app window geometry | Accessibility, `CGWindowListCopyWindowInfo` | WindowServer-level geometry/order/tag state | Use AX first; verify SLS only when AX is insufficient. |
| Spaces topology | Limited public surface | Managed display/Space graph and window membership | High-value research surface; version-gate heavily. |
| System-level overlays | AppKit `NSWindow.Level` within documented limits | Higher/private Space levels and special WindowServer placement | Lab-only unless isolated behind private backend and fallbacks. |
| Window capture | ScreenCaptureKit, CGWindow APIs | Historical access to minimized/off-Space window images | Prefer ScreenCaptureKit and explicit Screen Recording consent. |
| Background computer-use | AX actions, public `CGEvent.postToPid` | Private per-pid event/focus paths in community projects | Security-sensitive; avoid operational bypass recipes. |

## Symbol naming

| Prefix | Practical meaning |
|---|---|
| `CGS*` | Older CoreGraphics Services names; often still present or aliased. |
| `SLS*` | SkyLight Services names; common for windows, displays, Spaces, transactions, capture. |
| `SLPS*` / `_SLPS*` | Process/focus/event-routing related private names. |
| `SLEvent*` / `SLSEvent*` | Private event object/authentication/routing names. |

## Major functional surfaces

### 1. Connection and identity

Typical names: `SLSMainConnectionID`, `SLSNewConnection`, `SLSConnectionGetPID`, `SLSGetConnectionPSN`.

Research questions:

- Which symbols are exported on the target OS build?
- Are aliases (`CGSMainConnectionID` vs `SLSMainConnectionID`) both present?
- Which callers inside Apple binaries use the connection ID as an opaque handle?

### 2. Windows

Typical names: `SLSGetWindowBounds`, `SLSMoveWindow`, `SLSOrderWindow`, `SLSSetWindowLevel`, `SLSSetWindowTags`, `SLSWindowIterator*`.

Research questions:

- What can public AX/CGWindow APIs already provide?
- Which window state requires SLS-only visibility?
- Does Stage Manager/fullscreen alter behavior across macOS 15 and 26?

### 3. Spaces and displays

Typical names: `SLSCopyManagedDisplays`, `SLSCopyManagedDisplaySpaces`, `SLSCopySpacesForWindows`, `SLSMoveWindowsToManagedSpace`, `SLSSpaceGetType`, `SLSSpaceSetAbsoluteLevel`.

Research questions:

- How does the managed Space graph differ with single-display, multi-display, Stage Manager, and fullscreen apps?
- Which symbols drifted around macOS Sonoma 14.5+ compatibility changes?
- Can all needed observation be performed without mutating Space membership?

### 4. Capture

Typical names: `SLSHWCaptureWindowList`, historical `CGSHWCaptureWindowList`, capture-stream names.

Research questions:

- Which capture needs are satisfied by ScreenCaptureKit?
- What TCC Screen Recording prompts appear for supported APIs?
- Are private capture names present but entitlement-gated or behaviorally inert?

### 5. Events and focus

Typical names: `SLPSPostEventRecordTo`, `_SLPSGetFrontProcess`, `SLEventPostToPid`, event-authentication class names.

Research questions:

- Which public AX action paths avoid event synthesis entirely?
- Which public `CGEvent` paths are sufficient for non-browser apps?
- Which private paths are referenced by community projects, and what privacy/focus invariants do they target?

This package does not provide operational private event-injection recipes.

### 6. Transactions

Typical names: `SLSTransactionCreate`, `SLSTransactionCommit`, `SLSTransactionOrderWindow`, `SLSTransactionSetWindowAlpha`.

Research questions:

- Are transaction names exported on target builds?
- Are they used by Apple binaries for batched window mutations?
- Can behavior be inferred statically without invoking mutation APIs?

## Modern macOS constraints

- Private frameworks have no public headers and no compatibility guarantee.
- Much of the system library surface is packaged through the dyld shared cache/Cryptex path on modern macOS.
- On macOS 15.7.2 build 24G325, the SkyLight framework bundle also exists without a versioned binary on the filesystem; `dlopen` succeeds through the dyld shared cache. This matches the packaging pattern observed on macOS 26.2 build 25C56.
- On macOS 26.2 build 25C56, the SkyLight framework bundle exists on disk but its `Versions/A/SkyLight` binary is absent from the filesystem; the install name is present in the arm64e dyld cache. Use dyld-cache-aware tools instead of treating the framework symlink as a normal Mach-O file.
- `headers/SkyLightReadOnly.h` contains only read-only dlsym signatures validated on macOS 15.7.2 build 24G325 and macOS 26.2 build 25C56. Keep mutation, capture, and event-routing symbols as name-only until independently validated on the target build.
- On macOS 26.2 build 25C56, Hopper shows several public SLS read-only wrappers using a bridged window-management operation path when enabled, with fallback calls to lower-level WindowServer client routines. Treat those wrappers as the stable call boundary for project probes; do not promote the bridged classes themselves into project APIs without separate validation.
- RuntimeViewer is useful as an independent Objective-C runtime metadata source: for selected SkyLight classes it adds ivar offsets and IMP addresses that `ipsw class-dump` omits.
- Objective-C class names such as `SLSEventAuthenticationMessage` must be checked with runtime class lookup or metadata dumps, not `dlsym("ClassName")`.
- SIP protects system locations and Apple-preinstalled apps; research should not require modifying system files.
- TCC/privacy prompts remain part of the supported capture/automation model.
- App Store distribution expects public APIs, so SkyLight-backed functionality should be isolated to non-App-Store/private builds or optional private backends.

## Engineering posture

Recommended architecture:

```text
Public backend
  AppKit / AX / ScreenCaptureKit / CGWindowList / public CGEvent

Private research backend
  dlopen/dlsym presence probe
  per-build symbol manifest
  capability checks
  crash-safe wrappers if experiments are allowed
  public fallback path

Test matrix
  macOS 14.x / 15.x / 26.x
  Apple Silicon + Intel when relevant
  single/multi-display
  Stage Manager on/off
  fullscreen Spaces
  external display hotplug
```

Avoid:

- compile-time hard-linking to private frameworks;
- unconditional private calls on launch;
- global struct-layout assumptions;
- SIP/AMFI/TCC bypass as a dependency;
- Apple-process injection as a product mechanism;
- no fallback when a symbol disappears.
