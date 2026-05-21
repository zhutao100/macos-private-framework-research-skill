# Agentic private-framework research best practices

## Operating principles

1. **Build-pin every observation.** Always capture OS version, build number, hardware, architecture, dyld cache UUIDs, tool versions, and feature flags.
2. **Separate discovery from inference.** A string, class name, or entitlement is not a behavior claim. Behavior requires runtime correlation or consumer analysis.
3. **Prefer static observation before dynamic observation.** Inventory, extract, hash, parse, and map dependencies before running controlled trials.
4. **Use public surfaces as probes.** Foundation Models, App Intents, Shortcuts, Spotlight, Siri, and privacy reports are safer and more stable than private API calls.
5. **Represent uncertainty explicitly.** Use claim cards with evidence grade, local reproduction state, and counterevidence.
6. **Avoid API overfitting.** Private APIs can change across minor builds; capture build-specific deltas.
7. **Use negative evidence.** Absence of strings/logs/services under a controlled trial is informative when the collection predicate is recorded.

## Recommended agent loop

```text
Task → hypothesis → collection plan → local artifact → observation record
     → candidate claim → constraint/lint check → counterevidence search
     → confidence update → next query/tool call
```

## MOTIF-style type-inference pattern

Use this pattern for Objective-C-heavy private frameworks:

1. Extract selectors, classes, method names, string tables, load commands, and nearby disassembly.
2. Generate candidate type signatures only for methods with enough context.
3. Validate against constraints:
   - Selector arity equals Objective-C colon count.
   - Return/argument types are consistent with message sends and call sites.
   - Referenced classes/protocols exist or are explicitly unresolved.
   - Produced pseudo-header parses and compiles in a synthetic harness when possible.
4. Store every inferred signature as a claim, not a fact, until a consumer compiles and runtime behavior is checked.

## Evidence quality rubric

| Grade | Example | Use |
|---|---|---|
| A | Apple primary documentation, local binary metadata, local entitlement dump | Strong factual anchors |
| B | Local controlled runtime logs, local call graph, local pseudo-header validation | Strong behavior evidence, build-specific |
| C | Shared-cache diffs from public repos, entitlement catalogs, community indexes | Discovery hints and cross-build signals |
| D | Blog/forum/community topology notes | Hypothesis generation only |

## Agent failure modes

| Failure mode | Mitigation |
|---|---|
| Treating names as contracts | Require call sites, dependencies, or logs. |
| Treating iOS evidence as macOS fact | Mark as cross-OS hint until reproduced on Mac. |
| Treating generated headers as real headers | Label as pseudo-headers and keep provenance. |
| Overusing dynamic tracing | First use logs, entitlements, launchd, and public-surface trials. |
| Context overload | Follow `LLM_LOAD_ORDER.md`; only load scripts/docs relevant to current lane. |
