# Candidate Objective-C Signature Inference Prompt

You are inferring a macOS private framework Objective-C method signature from bounded evidence.

## Hard Rules

- Do not change selector spelling, selector labels, arity, or `+`/`-` method kind.
- Do not invent private classes, protocols, typedefs, or structs unless they are present in the supplied headers or evidence.
- Prefer the original type when evidence is insufficient.
- Return JSON only.
- Include confidence for each type position: `validated`, `likely`, `plausible`, `unknown`, or `rejected`.

## Candidate

```objc
{{ORIGINAL_DECLARATION}}
```

## Context

```json
{{MOTIF_CONTEXT_JSON}}
```

## Required Output

```json
{
  "candidate_id": "{{CANDIDATE_ID}}",
  "original_declaration": "...",
  "inferred_declaration": "...",
  "selector_preserved": true,
  "positions": [
    {
      "position": "return",
      "original_type": "id",
      "inferred_type": "NSString *",
      "confidence": "likely",
      "evidence": ["caller sends UTF8String", "selector names displayName"]
    }
  ],
  "validation_plan": [
    "Run objc_signature_linter.py --compile",
    "Check caller xrefs for argument class"
  ],
  "uncertainty": [
    "First argument remains id because no concrete class evidence was found."
  ]
}
```
