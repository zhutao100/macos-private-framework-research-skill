# Boundary and non-goals

## Included

This package supports defensive and compatibility-oriented research on a researcher-controlled macOS system:

- Static framework inventory.
- Local dyld shared-cache extraction.
- Mach-O load-command, dependency, symbol, string, UUID, and Swift/ObjC metadata collection.
- Entitlement, launchd, Mach/XPC service-name, and unified-log observation.
- Controlled public-surface trials through Foundation Models, App Intents, Siri, Shortcuts, Spotlight, and Apple Intelligence privacy reports.
- LLM-agent claim triage and type-inference scaffolding.

## Excluded

This package does not provide:

- Apple private binaries, redistributed private framework headers, entitlement-bearing executables, or Apple-internal materials.
- SIP, AMFI, sandbox, or TCC bypass instructions.
- Process injection recipes against Apple services.
- Exploit chains, vulnerability weaponization steps, persistence, stealth, or privilege-escalation workflows.
- Instructions to subvert Apple Intelligence privacy controls.

## Safe substitutes for excluded items

| Requested item | Substitute in this package |
|---|---|
| Private binaries | Local-only discovery/extraction scripts for the researcher’s own machine. |
| Private headers | Local pseudo-header generation workflow plus claim cards; no redistribution. |
| SIP/AMFI/TCC bypass | High-level control-plane checklist: detect entitlements, service gates, protected files, sandbox profiles, and privacy-report behavior. |
| Apple-process injection | Non-invasive unified-log, launchd, entitlement, and dependency observation. |
| Exploit workflow | Reproducible negative/positive evidence records and responsible vulnerability note template. |
