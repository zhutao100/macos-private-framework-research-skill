# Public Web Sources

Retrieved/checked for this package on 2026-05-20.

| Source | URL | Why it matters |
|---|---|---|
| MOTIF paper | https://arxiv.org/abs/2601.01673 | LLM-assisted private-framework type inference methodology; emphasizes tool-augmented metadata extraction, binary inspection, constraint checking, and compilable header recovery. |
| J. Viotti private-framework survey | https://www.jviotti.com/2023/11/20/exploring-macos-private-frameworks.html | Practical approaches: `otool`, RuntimeBrowser, Hopper, dyld shared cache extraction, `dylibtree`. Notes modern dyld shared cache/Cryptex packaging. |
| Eclectic Light WindowServer explainer | https://eclecticlight.co/2025/12/13/explainer-windowserver-2/ | Current high-level model of WindowServer as compositor/input/event-routing service; notes SkyLight logging context. |
| Eclectic Light 2020 WindowServer article | https://eclecticlight.co/2020/06/08/windowserver-display-compositor-and-input-event-router/ | Historical compositor/input-router explanation. |
| Apple SIP support | https://support.apple.com/en-us/102149 | SIP protects `/System`, `/usr`, `/bin`, `/sbin`, `/var`, and Apple-preinstalled apps; root is restricted. |
| Apple App Review Guidelines | https://developer.apple.com/app-store/review/guidelines/ | Guideline 2.5.1 requires public APIs for App Store apps. |
| Apple ScreenCaptureKit docs | https://developer.apple.com/documentation/screencapturekit/ | Supported high-performance capture framework. |
| WWDC22 Meet ScreenCaptureKit | https://developer.apple.com/videos/play/wwdc2022/10156/ | ScreenCaptureKit performance/privacy framing. |
| Apple macOS Tahoe 26.3 security content | https://support.apple.com/en-us/126348 | Shows WindowServer remained in 2026 Apple security advisories. |
| Apple macOS Sequoia 15.7.4 security content | https://support.apple.com/en-us/126349 | Shows WindowServer memory/cache fixes in 2026 updates. |
| yabai `extern.h` | https://raw.githubusercontent.com/koekeishiya/yabai/refs/heads/master/src/misc/extern.h | Large community declaration set for SLS/CGS/SLPS windows, Spaces, displays, transactions, capture, focus. |
| Hammerspoon `hs.spaces` implementation | https://raw.githubusercontent.com/Hammerspoon/hammerspoon/refs/heads/master/extensions/spaces/libspaces.m | Concrete use of private Spaces APIs for managed display spaces, window-to-Space queries, and Space moves. |
| Cua Driver docs | https://cua.ai/docs/cua-driver/guide/getting-started/introduction | Computer-use driver framing: no foreground change, AX/vision modalities, SkyLight-assisted private paths. |
| Cua repository | https://github.com/trycua/cua | Source reference for macOS driver implementation and docs. |
| SkyLightWindow repository | https://github.com/Lakr233/SkyLightWindow | Compact overlay/Space-level project using private SkyLight APIs. |
