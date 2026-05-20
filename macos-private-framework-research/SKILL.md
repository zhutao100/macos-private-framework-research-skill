---
name: macos-private-framework-research
description: Research modern macOS private frameworks with dyld shared cache extraction, Objective-C/Swift metadata reconstruction, Hopper/RuntimeViewer/RuntimeBrowser/ipsw workflows, and MOTIF-style LLM-guided type inference. Use for authorized macOS 15, macOS 26, and future-version private framework analysis, header reconstruction, signature validation, client dependency tracing, and evidence-backed reports.
license: MIT
compatibility: macOS 15/26+ recommended; Python 3.13+; Xcode Command Line Tools; optional ipsw, dyld-shared-cache-extractor, Hopper, RuntimeViewer, RuntimeBrowser.
metadata:
  version: "1.0.0"
---

# macOS Private Framework Research

Use this skill to investigate macOS private frameworks in a repeatable, evidence-backed way. Default to local read-only analysis, bounded extraction into disposable directories, and iterative signature validation. Treat reconstructed headers and model-inferred types as hypotheses until corroborated.

## Quick Workflow

1. Inventory the host and analysis tools.

   ```bash
   scripts/macos_private_framework_inventory.py \
     --output /tmp/macos-pf-inventory.md \
     --json-output /tmp/macos-pf-inventory.json
   ```

   Record macOS product/build, architecture, dyld cache path, Xcode/CLT version, SIP status, and available tools before interpreting results. Load `references/modern-macos-notes.md` when cache paths, Cryptex paths, or version drift matter.

2. Discover client dependencies and candidate frameworks.

   ```bash
   scripts/discover_private_frameworks.py \
     --output /tmp/client-private-frameworks.md \
     --json-output /tmp/client-private-frameworks.json \
     /path/to/Client.app
   ```

   For `.app` bundles, start from the main executable, then inspect embedded frameworks, XPC services, login items, helpers, and plugins when evidence points there. Use `otool -L` evidence to decide which framework to extract; do not assume a framework is involved because its name sounds related.

3. Extract or open the framework image.

   ```bash
   scripts/extract_dyld_framework.sh \
     --framework FrameworkName \
     --output-dir /tmp/macos-private-frameworks
   ```

   Preferred extraction order: plain `ipsw dyld extract` for a single-framework copy; `ipsw class-dump` for Objective-C headers; `dyld-shared-cache-extractor` when Xcode's `dsc_extractor.bundle` is needed for newer/beta cache formats; Hopper's dyld cache loader for focused GUI/MCP inspection. Use `--enrich-objc-stubs` only when extraction-time ObjC/stub enrichment is necessary and acceptable for the host. Load `references/tooling-workflows.md` for alternatives.

4. Generate baseline interfaces.

   Use the most informative available path:

   ```bash
   # Static Objective-C headers from the shared cache or extracted Mach-O.
   ipsw class-dump /System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld/dyld_shared_cache_arm64e \
     FrameworkName --headers --output /tmp/FrameworkName.headers

   # Or, after extraction:
   ipsw class-dump /tmp/macos-private-frameworks/.../FrameworkName \
     --headers --output /tmp/FrameworkName.headers
   ```

   When available, use RuntimeViewer for Swift + Objective-C interfaces and Hopper for disassembly/pseudocode/xrefs. RuntimeBrowser is useful for live Objective-C runtime enumeration but will miss code that is not loaded and non-ObjC surfaces.

5. Triage underspecified declarations.

   ```bash
   scripts/objc_header_triage.py \
     --headers /tmp/FrameworkName.headers \
     --output /tmp/FrameworkName.candidates.md \
     --json-output /tmp/FrameworkName.candidates.json
   ```

   Markdown output is bounded for agent ingestion by default; JSON still contains all candidates. Prioritize methods involving `id`, `void *`, anonymous structs, raw collections, blocks, protocol-qualified delegates, XPC-facing classes, entitlement-controlled flows, and selectors observed in client binaries.

6. Build a MOTIF-style context bundle for each high-value candidate.

   ```bash
   scripts/build_motif_context.py \
     --candidate-json /tmp/FrameworkName.candidates.json \
     --candidate-id 1 \
     --headers /tmp/FrameworkName.headers \
     --binary /tmp/macos-private-frameworks/.../FrameworkName \
     --output /tmp/FrameworkName.candidate-1.context.json \
     --prompt-output /tmp/FrameworkName.candidate-1.prompt.md
   ```

   The context should include the method string, class/protocol, nearby header context, selector labels, framework metadata, symbol/string evidence, client usage, and any focused Hopper/RuntimeViewer observations. Load `references/type-inference-loop.md` before performing iterative inference.

7. Infer, validate, and refine signatures.

   ```bash
   scripts/objc_signature_linter.py \
     --headers /tmp/FrameworkName.inferred.headers \
     --output /tmp/FrameworkName.lint.md \
     --json-output /tmp/FrameworkName.lint.json \
     --compile
   ```

   Markdown output is bounded for agent ingestion by default; JSON still contains all diagnostics. Iterate until hard errors are resolved or the evidence gap is explicit. Use compiler diagnostics, selector-label preservation, method encodings, caller behavior, decompiler hints, public SDK typedefs, and neighboring declarations as constraints. Never silently change selector spelling or method arity.

8. Report reproducibly.

   Use `assets/framework-research-report-template.md`. Include OS build, dyld cache path, extraction command, target binary UUIDs when available, tools and versions, header-generation path, candidate IDs, inferred signatures, validation results, disassembly/client-use evidence, and unresolved uncertainty.

## Tool Selection

| Need | Prefer | Fallback |
|---|---|---|
| Host/cache/tool inventory | `scripts/macos_private_framework_inventory.py` | manual `sw_vers`, `csrutil status`, `xcodebuild -version` |
| Client framework discovery | `scripts/discover_private_frameworks.py` | `otool -L`, `plutil`, `codesign -d --entitlements :-` |
| Single framework extraction | plain `ipsw dyld extract` via `scripts/extract_dyld_framework.sh` | `dyld-shared-cache-extractor`, Hopper dyld cache loader |
| ObjC baseline headers | `ipsw class-dump`, RuntimeViewer export | RuntimeBrowser, Hopper ObjC header export |
| Swift metadata/interface | RuntimeViewer | Hopper/IDA/Ghidra plus Swift demangling |
| Disassembly/xrefs | Hopper skill/MCP or Hopper GUI | `xcrun llvm-objdump`, LLDB focused disassembly |
| Type inference | MOTIF-style tool + feedback loop | manual constraint table and linter diagnostics |

## Bundled Scripts

- `scripts/install_codex_skill.sh`: Install this skill to user, repo, or legacy Codex skill locations.
- `scripts/macos_private_framework_inventory.py`: Inventory macOS, dyld caches, framework directories, SIP, Xcode, and analysis tools.
- `scripts/discover_private_frameworks.py`: Resolve app/binary targets and list linked private frameworks with supporting evidence.
- `scripts/extract_dyld_framework.sh`: Extract a named framework from the active dyld shared cache using `ipsw` or `dyld-shared-cache-extractor`; use `--enrich-objc-stubs` only when needed.
- `scripts/objc_header_triage.py`: Scan reconstructed headers and rank underspecified Objective-C declarations with bounded Markdown and complete JSON.
- `scripts/build_motif_context.py`: Build complete JSON and bounded Markdown prompt bundles for a single candidate signature.
- `scripts/objc_signature_linter.py`: Validate reconstructed Objective-C headers with structural checks, bounded Markdown, complete JSON, and optional `clang -fsyntax-only`.
- `scripts/validate_skill_repo.py`: Validate this repository layout and script syntax without external dependencies.

## References

Load only what the task needs:

- `references/research-synthesis.md`: Research findings and the rationale for a MOTIF-style agent loop.
- `references/tooling-workflows.md`: Concrete workflows for ipsw, dyld cache extraction, RuntimeViewer, RuntimeBrowser, Hopper, and built-in tools.
- `references/type-inference-loop.md`: Step-by-step type-inference, linter, and evidence fusion procedure.
- `references/modern-macos-notes.md`: macOS 15/26+ path, Cryptex, arm64e, SIP, Swift/ObjC, and future-version cautions.

## Assets

- `assets/framework-research-report-template.md`: Reproducible report template.
- `assets/type-inference-prompt-template.md`: Prompt scaffold for a candidate method signature.
- `assets/motif-context-template.json`: JSON shape for context bundles.
- `assets/signature-candidate-template.json`: JSON shape for inferred signature records.
- `assets/header-compile-wrapper.m`: Minimal Objective-C compile wrapper for validating generated headers.
- `assets/runtimeviewer-mcp-config.example.json`: Example MCP client configuration placeholder for RuntimeViewer.
