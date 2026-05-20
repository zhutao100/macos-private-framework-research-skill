# Research Synthesis: LLM-Assisted macOS Private Framework Analysis

## Working Model

Modern macOS private framework analysis is no longer just `class-dump` plus manual browsing. A reliable agent workflow combines:

1. **Client-driven discovery**: inspect apps, daemons, XPC services, helpers, entitlements, and launch plists to identify which private frameworks are actually used.
2. **Static binary preparation**: locate the relevant dyld shared cache slice, extract the framework if needed, and generate baseline Objective-C/Swift interfaces.
3. **Metadata-aware triage**: find declarations where runtime metadata is structurally useful but semantically incomplete: `id`, `void *`, raw collections, anonymous structs, blocks, protocols, and cross-framework typedefs.
4. **Tool-augmented inference**: fuse selector semantics, neighboring headers, public SDK conventions, caller behavior, symbol/string evidence, decompiler output, and disassembly.
5. **Linter/compile feedback**: validate each inferred signature and feed diagnostics back into the next inference step.
6. **Evidence report**: preserve uncertainty and cite exact commands, paths, OS build, tool versions, and validation results.

The key design decision is to let the LLM propose candidate types, but require tools and static constraints to reject hallucinated or incompatible signatures.

## Lessons from MOTIF-Style Research

The MOTIF paper frames private-framework reconstruction as a two-stage loop:

- **Stage I: static preparation** extracts partial metadata, baseline headers, and symbol maps.
- **Stage II: constraint-guided inference** packages method strings, symbols, tool definitions, and metadata into a tool-using agent loop. Candidate signatures are then validated by a semantic source-level linter and refined with diagnostics.

Adopt the following operational consequences:

- Never ask the model to infer from selector names alone when binary evidence or client usage exists.
- Always preserve the original selector spelling and arity.
- Use neighboring class declarations and properties as high-value context.
- Treat blocks, protocol-qualified `id<...>`, generic collections, CoreFoundation bridging types, and structs as the high-leverage recovery targets.
- Keep a terminating action: after a bounded number of refinements, emit either a validated signature or an explicit evidence gap.
- Prefer local model/tool loops for sensitive binaries; avoid sending proprietary binaries, private traces, or unreleased OS data to remote services unless policy permits it.

## Toolchain Findings

### RuntimeBrowser

RuntimeBrowser is a classic Objective-C runtime browser. It enumerates classes currently loaded into the ObjC runtime, dynamically loads modules, lists methods, and formats output as header-like declarations. It remains useful for live runtime enumeration and quick ObjC header export, but it is inherently runtime-loaded and ObjC-specific:

- It can miss code that is not loaded.
- It cannot expose pure C/C++ surfaces.
- It cannot fully recover Swift metadata.
- Its type fidelity is limited by ObjC runtime encodings and decoder heuristics.

Use it as a quick runtime metadata source, not as the sole source of truth.

### RuntimeViewer

RuntimeViewer is a modern RuntimeBrowser alternative with Objective-C and Swift interface extraction, Mach-O parsing, interface transformers, export workflows, and MCP integration on modern macOS. It is especially useful when Swift metadata matters or when an LLM client can query a RuntimeViewer MCP bridge.

Use it for:

- Swift type/enum layout and member/vtable offset context.
- Rich Objective-C interface output with addresses and transformer settings.
- LLM-facing runtime inspection through MCP when configured.

Avoid relying on RuntimeViewer injection features unless the user explicitly authorizes dynamic inspection in a safe test environment. Prefer static Mach-O loading and interface export first.

### Hopper Disassembler Skill

The Hopper skill provides deterministic binary inventory, bounded Hopper snapshots, evidence search, Hopper MCP probing, address mapping, and universal Mach-O workspace scripts. For this skill, use it as a companion capability when you need:

- Focused disassembly or pseudocode.
- Xrefs from selectors, strings, or symbols.
- Address/file-offset mapping.
- Reusable Hopper `.hop` databases.
- Evidence-backed binary reports.

Do not use decompiler pseudocode as final proof; corroborate it with assembly, imports, xrefs, strings, or compiler validation.

### `ipsw`

`ipsw` is currently one of the most useful CLI tools for Apple OS research. It supports dyld shared cache parsing, extraction, Objective-C/Swift class dumping, symbols, stubs, and analysis-friendly extraction flags. Prefer it for repeatable command-line extraction and baseline headers when installed.

### `dyld-shared-cache-extractor`

`dyld-shared-cache-extractor` uses Xcode's `dsc_extractor.bundle`, making it resilient to new or beta dyld cache formats when the selected Xcode matches the OS. Use it when `ipsw` fails due to cache format drift or when a beta Xcode is required.

## Recommended Evidence Matrix

For each inferred signature, try to fill at least four columns:

| Evidence type | Example | Confidence contribution |
|---|---|---|
| Runtime encoding | `@?`, `@"NSString"`, `^{...}` | Confirms broad type shape |
| Selector semantics | `initWithURL:options:error:` | Suggests argument names/types |
| Neighbor declarations | properties, ivars, superclass/protocols | Constrains class and typedef choices |
| Public SDK analogues | Foundation/AppKit idioms | Suggests conventional concrete types |
| Client usage | caller passes `NSString *`, `NSDictionary *`, block | Strong concrete type evidence |
| Disassembly/pseudocode | `objc_msgSend` to `count`, `UTF8String`, block invoke | Confirms usage behavior |
| Compiler/linter | syntax and semantic diagnostics | Rejects invalid forms |
| Dynamic observation | safe LLDB/RuntimeViewer run | Useful but optional; higher operational cost |

## Common Failure Modes

| Failure mode | Symptom | Mitigation |
|---|---|---|
| Header hallucination | model invents classes or typedefs | require HdrScan/Header context or public SDK proof |
| Selector mutation | labels changed to fit guessed types | hard-fail in linter; selectors are evidence |
| Over-specific generics | `NSDictionary<NSString *, Foo *> *` without evidence | downgrade to `NSDictionary *` or mark inferred |
| Anonymous structs | `struct { double x; double y; }` in method signature | map to known typedef (`CGPoint`, `CGRect`, `NSRange`) only with evidence |
| Missing blocks | `id` used where caller invokes block | inspect block invoke signature and call sites |
| Swift elision | ObjC-only dumps miss Swift interfaces | use RuntimeViewer, Swift demangle, and Swift metadata tools |
| Cache format drift | extractor fails on new macOS | switch selected Xcode, use `dyld-shared-cache-extractor`, or Hopper cache loader |

## Deliverable Standard

A good agent report should include:

- Objective: framework, version, and research question.
- Environment: macOS version/build, architecture, Xcode, dyld cache path, tool versions.
- Discovery: client binaries and private frameworks with `otool -L` evidence.
- Extraction/header generation: exact commands and output paths.
- Candidate table: original method, reasons for underspecification, evidence gathered.
- Inference table: proposed signature, confidence, validation status, remaining uncertainty.
- Reproducibility: commands, artifacts, and bounded assumptions.
- Scope: clear statement that no private binaries/headers are redistributed.
