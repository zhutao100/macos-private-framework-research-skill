# SkyLight.framework research brief — May 2026

## Executive takeaways

| Topic | Current assessment |
|----|----|
| Best mental model | `SkyLight.framework` is the private client-side ABI around macOS WindowServer/CoreGraphics Services/SLS. It is not a normal app GUI framework. |
| Why it matters | It exposes window, display, Space, capture, event-routing, and WindowServer transaction capabilities that public APIs intentionally restrict. |
| Why it is fragile | No public headers, dyld shared cache packaging, SIP/read-only system volume, private entitlements, TCC/privacy boundaries, and OS-build-specific symbol drift. |
| Who uses it | Window managers, window switchers, automation/agent drivers, UI overlay experiments, and security researchers. |
| Production posture | Treat as private SPI. Use public APIs first, isolate private calls behind feature gates, version-probe at runtime, and design graceful degradation. |
| Security posture | The WindowServer/SkyLight boundary remains a live attack surface; Apple continued patching WindowServer issues in 2025–2026 security updates. |

## 1. What SkyLight is

`SkyLight.framework` is best understood as the private framework that exposes much of the client-side interface to WindowServer and related CoreGraphics Services machinery. WindowServer is the long-lived per-login graphical server responsible for window management, compositing, display coordination, and input routing. Eclectic Light’s 2025 WindowServer explainer describes it as the “master compositor” that remains active from login until shutdown, positions windows into a layered display image, manages Spaces and multiple displays, captures/extracts screen content, and routes mouse/keyboard events to owning apps. It also notes that WindowServer logging often appears under the `com.apple.SkyLight` subsystem. ([The Eclectic Light Company](https://eclecticlight.co/2025/12/13/explainer-windowserver-2/ "Explainer: WindowServer – The Eclectic Light Company"))

Historically, Apple’s public documentation and third-party commentary referred to the compositor as Quartz Compositor/Core Graphics. The implementation boundary shifted: older macOS versions exposed WindowServer components under SkyLight’s private framework bundle, and modern macOS increasingly packages system libraries through the dyld shared cache rather than as ordinary standalone dylibs in framework directories. That matters for research because the framework path can exist while the actual binary code lives in the dyld shared cache. ([The Eclectic Light Company](https://eclecticlight.co/2020/06/08/windowserver-display-compositor-and-input-event-router/ "WindowServer: display compositor and input event router – The Eclectic Light Company"))

A more accurate layering model is:

``` text
AppKit / SwiftUI / CoreAnimation / Accessibility / ScreenCaptureKit
        ↓
CoreGraphics Services / SkyLight private client ABI
        ↓
WindowServer IPC boundary
        ↓
compositing, Spaces, displays, input dispatch, capture, IOSurface/CA/GPU integration
```

The seed survey’s broad framing is directionally correct, but “higher-level frameworks translate down to SkyLight” is too linear. Modern macOS graphics and UI routing also involve CoreAnimation, IOSurface, TCC, ScreenCaptureKit, Accessibility, Metal/Quartz, and other daemon/service boundaries.

## 2. Naming: `CGS`, `SLS`, `SLPS`, and why symbols look inconsistent

SkyLight research literature and open-source consumers use several symbol families:

| Prefix | Typical meaning in practice | Examples seen in open-source declarations |
|----|----|----|
| `CGS*` | Older CoreGraphics Services naming; many APIs predate the SkyLight rename or coexist as aliases/wrappers. | `CGSManagedDisplaySetCurrentSpace`, `CGSCaptureWindowsContentsToRectWithOptions` |
| `SLS*` | SkyLight Services naming; common for windows, displays, Spaces, transactions, capture. | `SLSGetWindowBounds`, `SLSCopyManagedDisplaySpaces`, `SLSMoveWindowsToManagedSpace`, `SLSHWCaptureWindowList` |
| `SLPS*` | SkyLight Process Services-style naming, often around process/event interaction. | `SLPSPostEventRecordTo` |
| `_SLPS*` | Private/underscored variants. | `_SLPSGetFrontProcess` |

Open-source projects such as yabai and Hammerspoon expose large private declaration sets for these symbols, including connection management, window geometry, window ordering, window levels/tags, managed displays, Spaces, process-to-Space assignment, event posting, transaction APIs, and hardware capture. These declarations are useful as research signposts, not stable headers. ([GitHub](https://github.com/koekeishiya/yabai/blob/master/src/misc/extern.h "yabai/src/misc/extern.h at master · asmvik/yabai · GitHub"))

## 3. Functional surface area

### 3.1 Connections and process/window identity

Commonly observed APIs include:

``` c
SLSMainConnectionID
SLSNewConnection
SLSRegisterConnectionNotifyProc
SLSConnectionGetPID
_SLPSGetFrontProcess
SLSFindWindowAndOwner
```

These are used to obtain or reason about a WindowServer connection, map windows to owners, and identify foreground process/window state. Public alternatives exist for some of this through `NSWorkspace`, `CGWindowListCopyWindowInfo`, and Accessibility, but public APIs usually stop short of privileged mutation or off-Space operations.

### 3.2 Window geometry, ordering, levels, tags

Common symbol families include:

``` c
SLSGetWindowBounds
SLSMoveWindow
SLSOrderWindow
SLSSetWindowLevel
SLSGetWindowLevel
SLSSetWindowTags
SLSClearWindowTags
SLSWindowIterator*
```

These support operations that public APIs either restrict to the calling app’s own windows or expose only indirectly through Accessibility. For a tiling window manager, this is why SkyLight remains attractive: Accessibility can move/resize many windows, but it does not offer full-fidelity Space, level, tag, ordering, and WindowServer transaction semantics.

### 3.3 Spaces, displays, and Mission Control state

This is one of SkyLight’s highest-value surfaces for window managers and automation tools:

``` c
SLSCopyManagedDisplays
SLSCopyManagedDisplaySpaces
SLSManagedDisplayGetCurrentSpace
SLSCopySpacesForWindows
SLSMoveWindowsToManagedSpace
SLSProcessAssignToSpace
SLSSpaceGetType
SLSSpaceCopyName
```

Hammerspoon’s `hs.spaces` module, for example, calls private SLS APIs such as `SLSCopyManagedDisplaySpaces`, `SLSCopyWindowsWithOptionsAndTags`, and `SLSCopySpacesForWindows` to inspect Space/window state that public macOS APIs do not fully expose. ([GitHub](https://github.com/Hammerspoon/hammerspoon/blob/master/extensions/spaces/libspaces.m "hammerspoon/extensions/spaces/libspaces.m at master · Hammerspoon/hammerspoon · GitHub"))

### 3.4 Capture and thumbnails

Window switchers and automation tools care about capture because public capture APIs have permission and visibility constraints. Historically, projects used private APIs such as:

``` c
CGSHWCaptureWindowList
SLSHWCaptureWindowList
CGSCaptureWindowsContentsToRectWithOptions
SLSHWCaptureStreamCreateWithWindow
```

AltTab has documented use of private capture functions for window images, with comments indicating tradeoffs versus public `CGWindowListCreateImage`, including speed and support for minimized or other-Space windows. More recent public APIs such as ScreenCaptureKit offer a supported path for high-performance capture, but with TCC Screen Recording permission and Apple-defined behavior. ([GitHub](https://github.com/lwouis/alt-tab-macos/issues/122?utm_source=chatgpt.com "Display video of the windows instead of static screenshots"))

### 3.5 Event routing and background interaction

Private event APIs include symbols such as:

``` c
SLPSPostEventRecordTo
SLEventPostToPid
```

This area is security-sensitive. Public alternatives include Accessibility actions, `CGEventPost`, and `CGEvent.postToPid`, but public paths generally preserve stronger user-consent and focus semantics. Current automation projects such as Cua describe using public `CGEvent.postToPid` for background keyboard delivery and SkyLight-based paths for pixel/click routing without stealing focus, while still treating macOS parity and implementation details as active development areas. ([cua.ai](https://cua.ai/docs/cua-driver/guide/getting-started/introduction "What is Cua Driver? | Cua"))

### 3.6 Transactions

Some declaration sets expose transaction APIs:

``` c
SLSTransactionCreate
SLSTransactionCommit
SLSTransactionOrderWindow
SLSTransactionSetWindowLevel
SLSTransactionSetWindowAlpha
```

These suggest a batched mutation model against WindowServer state. For research, transactions are useful because they expose how Apple groups visual/window mutations internally. For product code, they are high-risk because structure layouts, ordering semantics, and privilege checks are private.

## 4. Why open-source tools keep touching SkyLight

| Use case | Why public APIs are insufficient | Representative projects/signals |
|----|----|----|
| Tiling window managers | Need cross-app window movement, Space membership, display/Space topology, window ordering, and sometimes focus semantics. | yabai declares broad SLS/SLPS APIs for windows, Spaces, displays, ordering, and events. ([GitHub](https://github.com/koekeishiya/yabai/blob/master/src/misc/extern.h "yabai/src/misc/extern.h at master · asmvik/yabai · GitHub")) |
| Spaces scripting | Mission Control/Spaces is not comprehensively exposed as a public API. | Hammerspoon uses private SLS calls for display Space lists and window-to-Space queries. ([GitHub](https://github.com/Hammerspoon/hammerspoon/blob/master/extensions/spaces/libspaces.m "hammerspoon/extensions/spaces/libspaces.m at master · Hammerspoon/hammerspoon · GitHub")) |
| Window switchers | Need fast thumbnails, minimized-window capture, other-Space visibility, and stable window metadata. | AltTab historically used private capture APIs and documents public/private capture tradeoffs. ([GitHub](https://github.com/lwouis/alt-tab-macos/issues/122?utm_source=chatgpt.com "Display video of the windows instead of static screenshots")) |
| System-level overlays | Need window levels and Spaces above normal app windows, sometimes across full-screen/lock-screen contexts. | SkyLightWindow advertises use of private SkyLight APIs for views above all other windows and high system-level Spaces. ([GitHub](https://github.com/Lakr233/SkyLightWindow "GitHub - Lakr233/SkyLightWindow: Display your UI on lock screen. · GitHub")) |
| Computer-use agents | Need background interaction without stealing focus or changing active Space. | Cua’s docs describe non-focus-stealing app driving and SkyLight-assisted event delivery paths. ([cua.ai](https://cua.ai/docs/cua-driver/guide/getting-started/introduction "What is Cua Driver? | Cua")) |

The common pattern is not “SkyLight is faster.” The more precise pattern is: SkyLight exposes state and mutation points that Apple intentionally does not commit to as public API.

## 5. Hardening and distribution constraints

### 5.1 No public contract

Apple documents public frameworks; private frameworks are undocumented and may change without notice. Jviotti’s private-framework survey notes that macOS ships a large number of private frameworks used by system services or public-framework dependencies, but these are not documented as public developer interfaces. ([Juan Cruz Viotti](https://www.jviotti.com/2023/11/20/exploring-macos-private-frameworks.html "Exploring macOS private frameworks"))

### 5.2 dyld shared cache changed inspection workflow

Since Big Sur, many built-in libraries are cached in the dyld shared cache, commonly under Preboot/Cryptex paths, so inspecting `/System/Library/PrivateFrameworks/SkyLight.framework` as a normal bundle is insufficient. Research workflows generally need dyld shared cache extraction or tools that understand the cache directly, such as Hopper, Ghidra workflows, Apple tooling, or `dyld-shared-cache-extractor`. ([Juan Cruz Viotti](https://www.jviotti.com/2023/11/20/exploring-macos-private-frameworks.html "Exploring macOS private frameworks"))

### 5.3 SIP and sealed system volume

System Integrity Protection restricts even root from modifying protected parts of macOS. That makes “patch SkyLight in place” the wrong default mental model on modern macOS. Practical research should happen in disposable VMs or lab machines, and production tooling should avoid mutating system components. ([Apple Support](https://support.apple.com/en-us/102149?utm_source=chatgpt.com "About System Integrity Protection on your Mac"))

### 5.4 App Store incompatibility

Mac App Store review policy requires apps to use public APIs and run on currently shipping OS versions. A dependency on private SkyLight APIs is therefore not compatible with normal App Store distribution. ([Apple Developer](https://developer.apple.com/app-store/review/guidelines/ "App Review Guidelines - Apple Developer"))

### 5.5 TCC and privacy boundaries

For screen capture, Apple’s supported model is explicit Screen Recording consent; ScreenCaptureKit is the modern high-performance public capture framework and participates in that privacy model. Private SkyLight capture paths should not be treated as a stable or approved way to avoid user consent. ([Apple Developer](https://developer.apple.com/documentation/screencapturekit/?utm_source=chatgpt.com "ScreenCaptureKit | Apple Developer Documentation"))

### 5.6 Private entitlements and privileged WindowServer modes

Community discussions identify private entitlements such as `com.apple.private.skylight.universal-owner` as relevant to privileged WindowServer capabilities. Entitlement databases and issue threads show that such entitlements exist in Apple-signed components, but they are not available to third-party developers through normal signing. Some community threads discuss process injection or privileged helper strategies; those are not appropriate production techniques and should be treated as security-sensitive research territory, not operational guidance. ([GitHub](https://github.com/koekeishiya/yabai/issues/2593?utm_source=chatgpt.com "Use Private Entitlement Instead of Sideloading into Dock ..."))

## 6. Security relevance

WindowServer has historically been a valuable exploit target because many sandboxed processes need to interact with it. Older security research described WindowServer’s broad IPC exposure and demonstrated sandbox escape/privilege escalation chains, including a Pwn2Own 2018 Safari sandbox escape involving a WindowServer memory-corruption vulnerability. ([keenlab.tencent.com](https://keenlab.tencent.com/en/2016/07/22/WindowServer-The-privilege-chameleon-on-macOS-Part-1/?utm_source=chatgpt.com "WindowServer: The privilege chameleon on macOS (Part 1)"))

This remains relevant, not just historical. Apple’s 2025–2026 security updates continued to include WindowServer fixes. Examples include a macOS Sequoia 15.4 WindowServer type-confusion issue causing unexpected app termination, a macOS Sequoia 15.7 WindowServer issue where an app could trick a user into copying sensitive data to the pasteboard, and a macOS Sequoia 15.7.4 WindowServer issue where an app could cause unexpected system termination or corrupt process memory. ([Apple Support](https://support.apple.com/en-us/122373 "About the security content of macOS Sequoia 15.4 - Apple Support"))

The defensible conclusion: SkyLight/WindowServer is not merely a convenience API surface. It is a high-value trust boundary, and modern Apple hardening reflects that.

## 7. Research methodology that holds up on modern macOS

A practical, reproducible SkyLight research workflow should be versioned and build-specific.

| Step | Purpose | Recommended practice |
|----|----|----|
| 1\. Fix target matrix | Avoid mixing symbols across OS builds. | Record macOS marketing version, build number, architecture, dyld cache path/hash, and hardware class. |
| 2\. Build symbol inventory | Find exported/private names. | Use `nm`, `strings`, `dyldinfo`, Hopper/Ghidra, and dyld shared cache extraction. |
| 3\. Compare public consumers | Infer stable-ish clusters. | Cross-reference yabai, Hammerspoon, AltTab, Cua, NUIKit/CGSInternal, and similar projects. |
| 4\. Classify symbols by surface | Avoid random API poking. | Group by connection, window, Space, display, capture, event, transaction, notification. |
| 5\. Version-diff releases | Identify drift. | Diff symbol presence and callsites across 14.x, 15.x, 26.x where available. |
| 6\. Observe runtime behavior | Validate hypotheses. | Use logs, Instruments, sample/spindump, and benign observation. WindowServer/SkyLight logging often appears under `com.apple.SkyLight`. |
| 7\. Gate experiments | Avoid destabilizing daily machines. | Use a disposable VM/lab host. Avoid SIP/AMFI changes on a primary machine. |
| 8\. Encapsulate private calls | Make failure modes explicit. | Use runtime symbol resolution, version checks, capability probes, and public fallbacks. |

The 2026 MOTIF paper is relevant here because it systematizes LLM-assisted type inference for stripped private macOS frameworks. The important contribution is not that it makes private APIs “safe,” but that it improves recovery of function signatures from undocumented binaries compared with baseline static tooling. ([arXiv](https://arxiv.org/abs/2601.01673?utm_source=chatgpt.com "Exposing Hidden Interfaces: LLM-Guided Type Inference for Reverse Engineering macOS Private Frameworks"))

## 8. Public API alternatives and when SkyLight is usually unnecessary

| Task | Supported public API path | What SkyLight adds | Recommendation |
|----|----|----|----|
| Move/resize visible app windows | Accessibility `AXUIElement` | Potentially richer ordering, Space, and cross-Space control | Use AX first; SkyLight only for non-App-Store power tools. |
| Manage own app windows | AppKit/SwiftUI/`NSWindow` | None needed for normal apps | Do not use SkyLight. |
| Inspect windows | `CGWindowListCopyWindowInfo`, AX | More internal metadata, other-Space behavior, tags/levels | Use public APIs unless exact Space/window-server state is required. |
| Capture screen/windows | ScreenCaptureKit, `CGWindowListCreateImage` where still suitable | Minimized/off-Space/private capture behavior | Use ScreenCaptureKit; accept TCC. |
| Drive UI automation | Accessibility, AppleScript where applicable, `CGEventPost` | Background/non-focus event delivery | Use AX actions and public event APIs; private event injection is brittle and security-sensitive. |
| Spaces introspection | Very limited public support | Managed display Space graph, current Space, window membership | SkyLight is often the only route; isolate heavily. |
| Always-on-top/system overlays | `NSWindow.Level` within documented limits | Higher/private system levels and special Spaces | Avoid for production except controlled internal tools. |

## 9. Corrections to the seed survey

| Seed claim | Refined assessment |
|----|----|
| “SkyLight communicates directly with the WindowServer binary embedded inside it.” | Historically reasonable for some macOS versions, but modern macOS packaging is more dyld-cache/Cryptex-oriented. Treat physical framework paths as version-specific. |
| “AppKit/UIKit/CoreAnimation translate layout instructions down to SkyLight.” | Too simple. AppKit/CoreAnimation/CoreGraphics/IOSurface/WindowServer interact through several layers; SkyLight is one major private client boundary, not the sole lowering target. |
| “Display compositing is managed through SkyLight.” | WindowServer is the compositor. SkyLight is a private interface into that world; compositing also involves CoreAnimation, graphics drivers, IOSurface, Metal/Quartz, and display services. |
| “Private entitlements can be bypassed by disabling AMFI or injecting into Dock.” | Community research discusses privileged paths, but those are not distributable or safe operational recommendations. The useful conclusion is entitlement-gating and non-portability. |
| “WindowServer crash logs involving SkyLight usually mean logout/freeze/reset.” | Often plausible: WindowServer failure can freeze display/input or force session disruption, but diagnosis requires the actual crash log, panic log, and surrounding unified logs. Eclectic Light notes recurrent WindowServer failure can freeze/panic and should be reported. ([The Eclectic Light Company](https://eclecticlight.co/2025/12/13/explainer-windowserver-2/ "Explainer: WindowServer – The Eclectic Light Company")) |

## 10. Practical guidance for a serious SkyLight project

### Use this architecture

``` text
Public backend
  AppKit / AX / ScreenCaptureKit / CGWindowList / CGEvent

Private backend
  SkyLight runtime loader
  symbol table by OS build
  capability probes
  crash-safe wrappers
  feature flags
  telemetry/logging
  public fallback path

Test matrix
  macOS 14.x / 15.x / 26.x
  Intel if relevant
  Apple Silicon
  single-display / multi-display
  Stage Manager on/off
  fullscreen Spaces
  external display hotplug
```

### Avoid this architecture

``` text
compile-time hard link to SkyLight
global assumptions about struct layout
unconditional private API call on launch
no public fallback
no OS-build gate
requires SIP/AMFI changes
requires injecting into Apple processes
```

### Minimum engineering controls

| Control | Reason |
|----|----|
| Runtime `dlsym`/weak loading | Prevents hard launch failure when a symbol disappears. |
| Per-build symbol manifest | Makes ABI drift visible. |
| Capability probing | Avoids assuming one macOS minor release behaves like another. |
| Crash containment | WindowServer-adjacent bugs can log out or freeze the GUI session. |
| Feature flags | Allows remote/local disable when Apple changes internals. |
| Public fallback | Keeps app usable under App Store/notarized/private-API-hostile environments. |
| VM-based testing | Reduces risk from graphical session resets and malformed calls. |

## Bottom line

SkyLight is the private macOS WindowServer client interface, with broad reach over windows, Spaces, displays, capture, event routing, and transactions. Its importance comes from the gap between what Apple exposes publicly and what serious window managers, automation systems, and researchers need to observe or mutate. Its risk comes from the same property: it sits on a hardened, undocumented, security-sensitive boundary.

For product work, the correct default is **public API first, SkyLight only as an isolated non-App-Store/private backend with runtime probes and graceful degradation**. For research, the correct default is **versioned dyld-cache analysis in a disposable macOS environment, with community declarations treated as hypotheses rather than headers**.
