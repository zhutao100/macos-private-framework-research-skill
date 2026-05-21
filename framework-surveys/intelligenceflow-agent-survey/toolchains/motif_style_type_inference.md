# MOTIF-style type inference workflow

This is a local pseudo-header workflow for Objective-C/Swift-heavy private frameworks. Generated outputs should stay local.

## Inputs

- Extracted framework binary from the local dyld shared cache.
- Objective-C class/method metadata.
- Swift symbol names and demangled output.
- Selector strings, method type encodings if present, and call-site disassembly.
- Consumer binaries that call into the framework.

## Tools

- `ipsw class-dump` / `ipsw swift-dump` when available.
- `otool -ov`, `otool -Iv`, `nm`, `strings`, `swift-demangle`.
- Hopper/Ghidra/IDA for call-site context.
- Parser/linter for pseudo-header validation.

## Agent loop

```text
selector → arity check → class/protocol context → call-site context
         → candidate signature → parse/lint → compile harness
         → claim card → counterevidence search → confidence update
```

## Linter constraints

| Constraint | Reason |
|---|---|
| Objective-C selector colon count equals argument count | Basic signature validity. |
| Return and argument object classes exist or are marked unresolved | Avoid invented types. |
| Type encodings, when present, must be respected | Runtime metadata beats model guesses. |
| Consumer call sites must be consistent with inferred arity and object usage | Prevent overfitting from names alone. |
| Header must parse in a synthetic harness | Basic syntactic validity. |

## Output policy

Store generated pseudo-headers under `~/iflow-lab/pseudo_headers.local/`. In this package or shared reports, include only:

- Hashes.
- Build IDs.
- Counts.
- High-level class/category names.
- Claim cards and evidence references.
