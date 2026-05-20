# Project Notes: Cua Driver

Source tree inspected locally from `cua.tar.gz`.

## Project profile

Cua is a broad computer-use-agent infrastructure project. The macOS driver material is relevant because it maps the agent problem into public Accessibility, ScreenCaptureKit/vision capture, and SkyLight-assisted background interaction surfaces.

## Relevant source paths

The following paths contain SkyLight, AX, CGEvent, ScreenCaptureKit, or WindowServer references:

```text
blog/inside-macos-window-internals.md
docs/content/docs/cua-driver/guide/getting-started/faq.mdx
docs/content/docs/cua-driver/guide/getting-started/installation.mdx
docs/content/docs/cua-driver/guide/getting-started/introduction.mdx
docs/content/docs/cua-driver/guide/getting-started/process-model.mdx
docs/content/docs/cua-driver/guide/getting-started/quickstart.mdx
docs/content/docs/cua-driver/guide/getting-started/swift-integration.mdx
docs/content/docs/cua-driver/reference/limits.mdx
docs/content/docs/cua-driver/reference/mcp-tools.mdx
libs/cua-driver-rs/PARITY.md
libs/cua-driver-rs/Skills/cua-driver-rs/LINUX.md
libs/cua-driver-rs/Skills/cua-driver-rs/README.md
libs/cua-driver-rs/Skills/cua-driver-rs/SKILL.md
libs/cua-driver-rs/Skills/cua-driver-rs/TESTS.md
libs/cua-driver-rs/Skills/cua-driver-rs/WEB_APPS.md
libs/cua-driver-rs/crates/platform-macos/src/ax/bindings.rs
libs/cua-driver-rs/crates/platform-macos/src/ax/cache.rs
libs/cua-driver-rs/crates/platform-macos/src/ax/tree.rs
libs/cua-driver-rs/crates/platform-macos/src/input/ax_actions.rs
libs/cua-driver-rs/crates/platform-macos/src/input/keyboard.rs
libs/cua-driver-rs/crates/platform-macos/src/input/mod.rs
libs/cua-driver-rs/crates/platform-macos/src/input/mouse.rs
libs/cua-driver-rs/crates/platform-macos/src/input/skylight.rs
libs/cua-driver-rs/crates/platform-macos/src/lib.rs
libs/cua-driver-rs/crates/platform-macos/src/permissions/status.rs
libs/cua-driver-rs/crates/platform-macos/src/tools/click.rs
libs/cua-driver-rs/crates/platform-macos/src/tools/double_click.rs
libs/cua-driver-rs/crates/platform-macos/src/tools/drag.rs
libs/cua-driver-rs/crates/platform-macos/src/tools/get_cursor_position.rs
libs/cua-driver-rs/crates/platform-macos/src/tools/hotkey.rs
libs/cua-driver-rs/crates/platform-macos/src/tools/launch_app.rs
libs/cua-driver-rs/crates/platform-macos/src/tools/list_windows.rs
libs/cua-driver-rs/crates/platform-macos/src/tools/press_key.rs
libs/cua-driver-rs/crates/platform-macos/src/tools/right_click.rs
libs/cua-driver-rs/crates/platform-macos/src/tools/scroll.rs
libs/cua-driver-rs/crates/platform-macos/src/tools/set_value.rs
libs/cua-driver-rs/crates/platform-macos/src/tools/type_text.rs
libs/cua-driver-rs/crates/platform-macos/src/tools/type_text_chars.rs
libs/cua-driver-rs/crates/platform-macos/src/windows.rs
libs/cua-driver-rs/crates/platform-windows/examples/list_windows_parity.rs
libs/cua-driver-rs/crates/platform-windows/examples/type_text_parity.rs
libs/cua-driver-rs/crates/platform-windows/src/tools/impl_.rs
libs/cua-driver-rs/crates/platform-windows/src/tools/stubs.rs
libs/cua-driver/Skills/cua-driver/README.md
libs/cua-driver/Skills/cua-driver/SKILL.md
libs/cua-driver/Skills/cua-driver/TESTS.md
libs/cua-driver/Skills/cua-driver/WEB_APPS.md
libs/cua-driver/Sources/CuaDriverCLI/DiagnoseCommand.swift
libs/cua-driver/Sources/CuaDriverCLI/DoctorCommand.swift
libs/cua-driver/Sources/CuaDriverCore/AppState/AppState.swift
libs/cua-driver/Sources/CuaDriverCore/Capture/WindowCapture.swift
libs/cua-driver/Sources/CuaDriverCore/Cursor/AgentCursor.swift
libs/cua-driver/Sources/CuaDriverCore/Focus/AXEnablementAssertion.swift
libs/cua-driver/Sources/CuaDriverCore/Focus/FocusGuard.swift
libs/cua-driver/Sources/CuaDriverCore/Focus/SyntheticAppFocusEnforcer.swift
libs/cua-driver/Sources/CuaDriverCore/Focus/SystemFocusStealPreventer.swift
libs/cua-driver/Sources/CuaDriverCore/Input/AXInput.swift
libs/cua-driver/Sources/CuaDriverCore/Input/CursorControl.swift
libs/cua-driver/Sources/CuaDriverCore/Input/FocusWithoutRaise.swift
libs/cua-driver/Sources/CuaDriverCore/Input/KeyboardInput.swift
libs/cua-driver/Sources/CuaDriverCore/Input/MouseInput.swift
libs/cua-driver/Sources/CuaDriverCore/Input/SkyLightEventPost.swift
libs/cua-driver/Sources/CuaDriverCore/Permissions/Permissions.swift
libs/cua-driver/Sources/CuaDriverCore/Recording/VideoRecorder.swift
libs/cua-driver/Sources/CuaDriverCore/Windows/SpaceMigrator.swift
libs/cua-driver/Sources/CuaDriverCore/Windows/WindowCoordinateSpace.swift
libs/cua-driver/Sources/CuaDriverCore/Windows/WindowEnumerator.swift
libs/cua-driver/Sources/CuaDriverServer/Tools/ClickTool.swift
libs/cua-driver/Sources/CuaDriverServer/Tools/DoubleClickTool.swift
libs/cua-driver/Sources/CuaDriverServer/Tools/GetWindowStateTool.swift
libs/cua-driver/Sources/CuaDriverServer/Tools/HotkeyTool.swift
libs/cua-driver/Sources/CuaDriverServer/Tools/LaunchAppTool.swift
libs/cua-driver/Sources/CuaDriverServer/Tools/ListWindowsTool.swift
libs/cua-driver/Sources/CuaDriverServer/Tools/MoveCursorTool.swift
libs/cua-driver/Sources/CuaDriverServer/Tools/PressKeyTool.swift
libs/cua-driver/Sources/CuaDriverServer/Tools/RightClickTool.swift
libs/cua-driver/Sources/CuaDriverServer/Tools/ScreenshotTool.swift
libs/cua-driver/Sources/CuaDriverServer/Tools/ScrollTool.swift
libs/cua-driver/Sources/CuaDriverServer/Tools/SetValueTool.swift
libs/cua-driver/Sources/CuaDriverServer/Tools/TypeTextTool.swift
libs/lume/src/VNC/VNCService.swift
```

## Observed surface categories

| Category | Examples observed in source/docs | Research value |
|---|---|---|
| Public AX dispatch | `AXUIElement`, AX tree/cache/action tools | Preferred route for deterministic element-indexed actions. |
| Public/per-pid CGEvent | `CGEvent` keyboard/mouse helpers | Baseline for non-HID event synthesis experiments. |
| Private SkyLight events | `SLEvent*`, `SLSEvent*` names in source/comments | Security-sensitive background event routing surface; this package only inventories names. |
| Focus/foreground preservation | `SLPS*`, `_SLPS*` names and focus-guard files | Useful to reason about no-foreground-change invariants. |
| Capture | Screen/window capture files and docs | Useful to compare AX-only, vision-only, and combined SOM modalities. |

## Research value

Cua provides a modern agent-oriented map of the problem:

- how to keep user foreground/cursor/Space stable;
- when AX is enough;
- where browser/custom-drawn surfaces break public event assumptions;
- why capture mode, signing identity, and permissions affect agent loops.

## Package boundary

This package does not reproduce Cua's operational private event recipes. It indexes the relevant files and symbol names so an authorized researcher can decide what to inspect in a controlled lab.
