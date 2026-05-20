# Security Boundaries

## Included

This package includes:

- read-only symbol inventory;
- public-source reference mapping;
- safe local framework inspection methodology;
- public API fallback analysis;
- high-level security context for WindowServer/SkyLight as a security-sensitive service boundary;
- templates for responsible reporting and reproducible research notes.

## Not included

This package deliberately does not include:

- SIP disablement or weakening procedures;
- AMFI weakening instructions;
- TCC database editing or privacy-consent weakening;
- Apple-process attachment recipes;
- runnable code that posts private SkyLight events or weakens user focus/consent controls.

## Safe substitutes

| Requested area | Safe substitute in this package |
|---|---|
| SIP/AMFI weakening | SIP/AMFI constraint model; use disposable VM/lab machine; keep system integrity enabled. |
| TCC weakening | Permission-aware public API testing; record prompt behavior and signing identity stability. |
| Apple-process attachment | Static callsite analysis and log observation. |
| Crash/advisory workflow | Advisory tracking, patch-diff planning, crash-log triage template, responsible disclosure checklist. |
| Private event routing | Symbol presence inventory and public AX/CGEvent fallback analysis. |

## Research risk notes

WindowServer is a GUI-session critical process. Invalid private calls can freeze the session, log out the user, corrupt process state, or trigger a panic. Treat every mutation or event-routing experiment as lab-only and gate it behind explicit human review outside this package.
