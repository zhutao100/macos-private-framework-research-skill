# Project Notes: SkyLightWindow

Source tree inspected locally from `SkyLightWindow.tar.gz`.

## Project profile

SkyLightWindow is a compact Swift package for system-level overlays. Its README describes it as using private SkyLight APIs to display views above other windows, including fullscreen contexts.

## Relevant files

```text
.gitignore
Example/MoveToSky.xcodeproj/project.pbxproj
Example/MoveToSky.xcodeproj/project.xcworkspace/contents.xcworkspacedata
Example/MoveToSky.xcworkspace/contents.xcworkspacedata
Example/MoveToSky/Assets.xcassets/AccentColor.colorset/Contents.json
Example/MoveToSky/Assets.xcassets/AppIcon.appiconset/Contents.json
Example/MoveToSky/Assets.xcassets/Contents.json
Example/MoveToSky/ContentView.swift
Example/MoveToSky/MoveToSky.entitlements
Example/MoveToSky/MoveToSkyApp.swift
LICENSE
Package.swift
README.md
Sources/SkyLightWindow/SkyLightOperator.swift
Sources/SkyLightWindow/SwiftUI+MoveToSky.swift
Sources/SkyLightWindow/SwiftUI+WindowReader.swift
Sources/SkyLightWindow/TopmostWindow.swift
Sources/SkyLightWindow/TopmostWindowController.swift
```

## Observed SkyLight surface

The central implementation file is `Sources/SkyLightWindow/SkyLightOperator.swift`.

Observed symbol-name families:

- connection: `SLSMainConnectionID`
- Space creation/visibility: `SLSSpaceCreate`, `SLSShowSpaces`
- private Space level: `SLSSpaceSetAbsoluteLevel`
- window-to-Space movement: `SLSSpaceAddWindowsAndRemoveFromSpaces`

## Research value

This project is useful as a minimal overlay/Space-level case study:

- It isolates the overlay problem to a small number of Space APIs.
- It demonstrates why system-level overlays reach beyond public `NSWindow.Level`.
- It gives a small symbol set to verify across OS builds.

## Caveats

- Treat the README's distribution/App Store claims as project claims requiring independent verification.
- The code path mutates WindowServer Space state; do not run experiments on a daily-driver host.
- Convert any experiment into capability probes and public fallbacks before product use.
