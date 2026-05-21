# Playbook 05: agent claim triage

## Objective

Prevent confident but unsupported internal-architecture claims.

## Claim card fields

Use `templates/claim_card.yaml`.

Minimum fields:

- Claim.
- Claim type: existence, role, behavior, dependency, entitlement, service, privacy boundary.
- Build and artifact scope.
- Evidence list.
- Counterevidence list.
- Reproduction status.
- Confidence.
- Next verification step.

## Confidence rules

| Confidence | Requirements |
|---|---|
| High | Primary Apple doc for public surface, or local artifact + local reproduction + counterevidence search. |
| Medium | Local static evidence plus at least one independent signal, or public diff + local confirmation. |
| Low | Name/string/community hint only. |
| Reject | Contradicted by local evidence or overbroad across surfaces/builds. |

## Promotion examples

| Starting observation | Do not claim | Promote to |
|---|---|---|
| String `orchestrator` in binary | This binary orchestrates Apple Intelligence. | Binary contains orchestrator-related strings on build X; test controlled App Intents trial. |
| Entitlement `com.apple.intelligenceflow.context` on a diagnostic appex | All transcripts are readable. | This diagnostic component has context entitlement and listed transcript stream labels. |
| `IntelligenceFlowPlannerSupport` has many functions | It is the planner. | It is a large binary with planner-support name and function count; role requires local call graph/log evidence. |
