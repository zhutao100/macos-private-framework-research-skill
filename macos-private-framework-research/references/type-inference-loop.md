# Type-Inference Loop

## Goal

Recover more precise Objective-C method signatures for private framework APIs without inventing unsupported types. This loop is designed for LLM agents that can call tools, inspect headers, and run validators.

## Inputs

Minimum useful input bundle:

```json
{
  "framework": "FrameworkName",
  "binary": "/tmp/.../FrameworkName",
  "headers_root": "/tmp/FrameworkName.headers",
  "candidate": {
    "id": 1,
    "class_or_protocol": "ClassName",
    "method": "- (id)foo:(id)arg options:(id)arg2;",
    "selector": "foo:options:",
    "reasons": ["id return", "raw Objective-C object argument"]
  },
  "evidence": {
    "nearby_header_context": "...",
    "symbols": ["..."],
    "strings": ["..."],
    "client_usage": ["..."],
    "disassembly_notes": ["..."]
  }
}
```

Use `scripts/build_motif_context.py` to assemble this bundle.

## Step 1: Classify the Unknowns

For each candidate method, mark positions:

| Position | Common unknown | Evidence needed |
|---|---|---|
| Return | `id`, `void *`, `@` | caller sends messages to return value; naming convention; property pairing |
| Object arg | `id`, raw collection | selector label, caller object class, property/ivar context |
| Delegate arg | `id` | protocol declarations, `respondsToSelector:`, delegate naming |
| Collection arg | `NSArray *`, `NSDictionary *` | element access, enumerated object messages, key/value selectors |
| Block arg | `id` or `@?` | block invoke signature, captured use, completion naming |
| Struct arg | anonymous/raw struct | public typedef shape; field use; bridge to CoreGraphics/Foundation |
| Pointer arg | `void *`, `char *`, `CFTypeRef` | dereference pattern, CoreFoundation calls, memory management calls |

## Step 2: Collect Evidence in Priority Order

1. **Original method encoding**: preserve the broad runtime shape.
2. **Exact selector**: selector labels are not editable.
3. **Class context**: superclass, protocols, properties, ivars, categories.
4. **Neighbor methods**: paired getter/setter, `initWith...`, completion variants.
5. **Public SDK analogues**: Foundation/AppKit conventions and typedefs.
6. **Client usage**: caller allocations, literals, message sends, or Swift bridged calls.
7. **Disassembly/pseudocode**: pointer/scalar behavior, message sends on args, return paths.
8. **Compile/lint diagnostics**: reject invalid syntax and unresolvable typedefs.

## Step 3: Propose a Candidate Signature

Rules:

- Keep `+`/`-`, selector labels, colons, and arity identical.
- Prefer known SDK types over invented private types unless that private type exists in the header set.
- Prefer `id<Protocol>` only when protocol evidence exists.
- Prefer collection generics only when evidence supports element/key/value types.
- Prefer `NSError **` only when selector semantics and call-site conventions support out-error behavior.
- Preserve nullability only if a source already contains nullability or there is strong evidence; otherwise omit it.
- Do not add method attributes unless found in headers or required to compile.

## Step 4: Validate

Run:

```bash
scripts/objc_signature_linter.py \
  --headers /tmp/FrameworkName.inferred.headers \
  --output /tmp/FrameworkName.lint.md \
  --json-output /tmp/FrameworkName.lint.json \
  --compile
```

Hard failures:

- Syntax errors.
- Selector label/arity mismatch.
- Inline anonymous structs in method signatures.
- Unknown private class used without a header or forward declaration.
- Block syntax that does not compile.
- Method declaration split or malformed after editing.

Soft failures:

- Raw `id` remains.
- Raw `void *` remains.
- Ungeneric `NSArray`, `NSDictionary`, `NSSet` remains.
- `NSDictionary<NSString *, id> *` or similarly weak generics.
- `NSObject *` where a more specific class appears likely but unproven.

## Step 5: Feed Diagnostics Back

For each linter issue:

1. Quote the failing declaration.
2. State the failed constraint.
3. Identify the needed evidence.
4. Query the tool or reference that can answer it.
5. Revise only the affected type position.

Keep iterations bounded. After three failed revisions, emit a partial result with uncertainty.

## Step 6: Confidence Labels

Use stable labels in reports:

| Label | Meaning |
|---|---|
| `validated` | compiles/lints and has at least two independent evidence sources |
| `likely` | strong semantic + one structural evidence source; no compiler failures |
| `plausible` | selector/public-SDK convention only; still useful but marked uncertain |
| `unknown` | insufficient evidence; keep original generic type |
| `rejected` | failed hard constraint or contradicted by evidence |

## Example Mini-Loop

Original:

```objc
- (id)displayNameForItem:(id)arg1 options:(id)arg2;
```

Evidence:

- Selector labels: `displayName`, `Item`, `options`.
- Neighbor property: `@property (retain) NSArray *items;`.
- Caller sends `UTF8String` to return value.
- Caller passes `NSDictionary` literal as second arg.

Candidate:

```objc
- (NSString *)displayNameForItem:(id)item options:(NSDictionary *)options;
```

Validation result:

- Selector unchanged.
- Syntax compiles.
- Return is supported by caller behavior.
- First arg remains `id` because item concrete class is not proven.

Report confidence: `likely` for return and options, `unknown` for item.

## Prompt Pattern

Use `assets/type-inference-prompt-template.md` for LLM calls. The prompt should require:

- Original declaration.
- Output as JSON only.
- A per-type-position evidence table.
- A confidence label.
- No selector mutation.
- A fallback to original type when evidence is insufficient.
