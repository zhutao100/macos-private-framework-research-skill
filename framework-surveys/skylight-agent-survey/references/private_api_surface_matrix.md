# Private API Surface Matrix

| Surface | Candidate symbol families | Public alternative | Typical reason people reach for SkyLight | Risk |
|---|---|---|---|---|
| Connection identity | `SLSMainConnectionID`, `SLSNewConnection`, `SLSConnectionGetPID` | Usually none needed; process APIs, `NSRunningApplication` | WindowServer handle needed by many SLS calls | ABI drift; opaque handles. |
| Window geometry | `SLSGetWindowBounds`, `SLSMoveWindow`, `SLSOrderWindow` | AX move/resize; `CGWindowListCopyWindowInfo` | Cross-app manipulation and exact server-side state | Can perturb user session. |
| Window levels/tags | `SLSSetWindowLevel`, `SLSSetWindowTags`, `SLSClearWindowTags` | `NSWindow.Level` for own windows | Special overlays, sticky windows, private ordering | High distribution risk. |
| Spaces/displays | `SLSCopyManagedDisplaySpaces`, `SLSCopySpacesForWindows`, `SLSCopyWindowsWithOptionsAndTags`, `SLSSpaceGetType`, `SLSMoveWindowsToManagedSpace` | Very limited public APIs | Mission Control/Space graph; off-Space window membership | Fragile across releases. |
| Capture | `SLSHWCaptureWindowList`, `CGSHWCaptureWindowList` | ScreenCaptureKit; CGWindow APIs | Minimized/off-Space capture behavior | Privacy/TCC-sensitive. |
| Events/focus | `SLPSPostEventRecordTo`, `SLEventPostToPid`, event-auth classes | AX actions; public `CGEvent` | Background drive without cursor/focus movement | Security-sensitive; excluded operationally. |
| Transactions | `SLSTransaction*` | Public AppKit/CoreAnimation transactions for own app | Batched WindowServer mutations | Layout/signature unknown. |
