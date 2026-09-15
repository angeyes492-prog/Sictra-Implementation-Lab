# Telecare OS context map v0.2

Status: `CANDIDATE / IMPLEMENTED LOCAL ROUTE / MAR REQUIRED`.
Date: 2026-09-14. Confidence: B for local behavior; no global acceptance.

## Purpose and corrected boundaries

Telecare is organized around four bounded contexts, each with a distinct
business capability. This corrects an operational coupling found in v0.1 where
the local Block 2 output was described as a research draft instead of a design
artifact.

| Context | Owns | Receives | Emits | Must not do |
| --- | --- | --- | --- | --- |
| Block 1 — Intelligence | source validity, change detection, dossier facts, evidence, uncertainty | approved retained source | signed dossier package | design, audience inference, publication |
| Block 2 — Design | information hierarchy, content components, visual system and accessible candidate render | current typed dossier | content-design candidate | acquire research semantics, infer causality, personalize, accept/publish |
| Block 3 — Precision | declared-audience relevance, view selection and presentation framing | fingerprinted design candidate and explicit profile | local audience adaptation | alter source facts, mint consent, infer person/account facts or deliver |
| Block 4 — Orchestrator | durable case state, scheduling, idempotency, recovery, audit and human stop | typed cross-context events | current review queue / persisted artifacts | source truth, creative authority, profile semantics, publication |

The route is:

`approved source → B1 dossier → B2 content-design candidate → B3 declared-audience adaptation → B4 human review`

Each arrow is a versioned published language with a downstream anti-corruption
check. Shared IDs correlate a case but do not make one block's model or authority
available to another.

## Invariants, failure and recovery

Facts, uncertainty and provenance are immutable across the route. Design can
change structure but not source meaning; Precision can change selection and
framing but not design/source meaning; Orchestrator can retry a step but not
recover by fabricating an earlier result. Any stale source/profile, altered
fingerprint, absent geographic match, contradiction, unsupported version or
unbounded action ends in a visible wait/return/rejection state.

Block 4 records canonical case and artifact identities in an append-only local
journal, uses idempotent outputs and a fair cyclic cursor, and requires explicit
operator recovery for intake. Its local SQLite recovery is useful for this scope
but is not a production durable-workflow service nor an external rollback anchor.

## Observability and validation

Every artifact retains `case_id`, dossier/evidence/source IDs, source hash,
profile fingerprint, currentness/expiry and output hash. The UI renders those
identities inside a sandboxed local frame. The validation plan includes contract
mutations, stale profile/source, tampered journal, replay, crash/restart,
profile fairness, cross-origin controls and a complete local source-to-design
pilot.

This map is informed by DDD context mapping and durable-workflow/observability
references, but those sources do not accept SICTrA architecture. The final MAR
must decide ownership, cross-version compatibility, production scheduler,
identity/key custody, external telemetry, retention and human-review authority.

Professional implementation references consulted on 2026-09-14:

- Microsoft’s [domain analysis guidance](https://learn.microsoft.com/en-nz/azure/architecture/microservices/model/domain-analysis)
  supports one cohesive business capability per bounded context and a published
  language/anti-corruption layer at integration points.
- [Temporal workflow execution](https://docs.temporal.io/workflow-execution)
  distinguishes a durable execution record from ordinary in-process work. The
  present SQLite worker borrows only the checkpoint/idempotency goal; it is not
  represented as an equivalent production workflow platform.
- [OpenTelemetry context propagation](https://opentelemetry.io/docs/concepts/context-propagation/)
  supports correlating a trace across process boundaries; the candidate retains
  equivalent causal identifiers locally and reserves external telemetry for a
  separately authorized deployment.
- Google’s [SRE automation guidance](https://sre.google/sre-book/introduction/)
  motivates automating repeatable operations. It does not justify automating a
  source, approval or publication decision that has no declared authority.

## Reconciliation record

Jira SI-1 says Block 2 designs experiences/newsletters/assets from typed
handoffs and must not acquire Intelligence semantics. Jira SI-5 says Block 3
refines profiles/relevance without substituting Intelligence provenance. Notion
Block 2 E01 records local claim-composition ownership; the Block 3 plan requires
separate source identity, evidence and account-boundary controls. Slack records
the same boundary discipline and warns that synthetically approved copy does not
prove a real design outcome. This implementation adopts the common conclusion;
no historical context is treated as a gate approval.
