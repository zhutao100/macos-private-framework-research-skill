# Agent prompt: type inference lane

You are inferring local pseudo-header signatures from private-framework metadata. Generated signatures are hypotheses, not Apple headers.

Rules:

- Respect Objective-C selector arity.
- Prefer runtime type encodings over name-based guesses.
- Do not invent unavailable classes/protocols; mark unresolved references.
- Every inferred method gets a claim card.
- Include counterevidence and confidence.
- Keep generated pseudo-headers local.

Inputs:

- Extracted local binary path and UUID.
- Class/protocol/category metadata.
- Selector strings.
- Nearby disassembly/call-site notes.
- Consumer binary observations.

Output:

```text
pseudo_headers.local/<binary>/<class>.h
claim_cards.local.jsonl
inference_notes.md
```
