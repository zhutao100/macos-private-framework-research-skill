# Security Boundaries

## Included

This package includes:

- read-only symbol inventory;
- public-source reference mapping;
- safe reverse-engineering methodology;
- public API fallback analysis;
- high-level security context for WindowServer/SkyLight as an attack surface;
- templates for responsible reporting and reproducible research notes.

## Not included

This package deliberately does not include:

- SIP disablement or weakening procedures;
- AMFI bypass instructions;
- TCC database editing or privacy-consent bypasses;
- Apple-process injection recipes;
- exploit chains, weaponization, payloads, persistence, evasion, or privilege-escalation steps;
- runnable code that posts private SkyLight events or bypasses user focus/consent controls.

## Safe substitutes

| Requested area | Safe substitute in this package |
|---|---|
| SIP/AMFI bypass | SIP/AMFI constraint model; use disposable VM/lab machine; keep system integrity enabled. |
| TCC bypass | Permission-aware public API testing; record prompt behavior and signing identity stability. |
| Apple-process injection | Static callsite analysis and log observation; no injection. |
| Exploit workflow | Advisory tracking, patch-diff planning, crash-log triage template, responsible disclosure checklist. |
| Private event injection | Symbol presence inventory and public AX/CGEvent fallback analysis. |

## Research risk notes

WindowServer is a GUI-session critical process. Invalid private calls can freeze the session, log out the user, corrupt process state, or trigger a panic. Treat every mutation or event-routing experiment as lab-only and gate it behind explicit human review outside this package.
