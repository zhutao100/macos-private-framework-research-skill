# Public API Alternatives

| Task | Preferred public path | Notes |
|---|---|---|
| Own app windows | AppKit/SwiftUI/`NSWindow` | Do not use SkyLight for normal app windows. |
| Cross-app move/resize | Accessibility `AXUIElement` | Requires Accessibility consent; deterministic for many standard apps. |
| Window enumeration | `CGWindowListCopyWindowInfo`, AX | Good first pass; Space/off-screen/minimized semantics differ by API. |
| Screen/window capture | ScreenCaptureKit | Supported modern capture path; privacy model applies. |
| Element actions | AX actions (`AXPress`, value writes where supported) | Avoids event synthesis entirely. |
| Keyboard/mouse synthesis | Public `CGEvent` APIs | Respect limitations; keep user consent/focus implications explicit. |
| App/process state | `NSWorkspace`, `NSRunningApplication`, `Process` APIs | Prefer over private process-service calls where sufficient. |
| Automation | AppleScript, Shortcuts, AX, app-specific scripting dictionaries | Use app-native surfaces before private WindowServer calls. |
