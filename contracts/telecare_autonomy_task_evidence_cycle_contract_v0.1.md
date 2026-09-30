# Telecare supervised evidence-task cycle v0.1

Status: `CANDIDATE / LOCAL LABORATORY / MAR REQUIRED`. Producer: Block 4
Operations. Evidence authority: Block 1. Consumer: local Command Center.

## Purpose and boundary

A durable evidence task derived from a Block 1 dossier may be linked to one
**currently exportable** dossier from a different source root. The link is a
candidate for human reassessment, not corroboration, interpretation, content
acceptance, publication, delivery, or a global gate result. Block 4 never
changes a Block 1 dossier or mints an evidence receipt.

## Inputs and lineage

`link(task_id, evidence_dossier_id)` requires an existing `OPEN` or
`HUMAN_ACKNOWLEDGED` task, a current original dossier, and a distinct current
candidate dossier. Both are re-exported through the Block 1 adapter at the
current clock time. The candidate root must differ from the task's source
root. The journaled link binds task and both dossier IDs, candidate source
root, evidence ID, source hash, package expiry, and observation time. Repeating
the same current link is idempotent; replacing it requires a recorded negative
reassessment first.

`reassess(task_id, reviewer_id, rationale, decision)` requires the same exact
link still current and the local control token. `REQUEST_BLOCK1_REASSESSMENT`
records a request to reassess the specific need as
`BLOCK1_REASSESSMENT_REQUIRED`; `EVIDENCE_INSUFFICIENT` returns it to `OPEN`.
Neither closes the task: a different root does not prove that the new dossier
answers the question. The local reviewer ID is self-declared and is not
independent identity verification. The rationale is 20–1000 characters. Both
decisions retain an append-only record containing the previous link, and
`publication=BLOCKED`, `acceptance=NOT_ACCEPTED`.
`BLOCK1_REASSESSMENT_REQUIRED` cannot be relinked or reassessed by Block 4;
Block 1 must provide a separate contracted resolution before task closure.
New tasks use `BLOCK1_CONTRACTED_RESOLUTION_REQUIRED` as their completion
boundary. Old task records retain their original metadata; snapshots mark it
`LEGACY_SUPERSEDED` and expose the current effective boundary without rewriting
the journal.

## Failure, recovery, and compatibility

Local currentness clarification (2026-09-29): retention does not authorize new
work. Before deriving tasks, Operations must obtain a current signed Block 1
package matching the dossier identity and retained source hash. Invalid,
expired, superseded, contradictory or out-of-scope packages cannot create tasks
or enter the design batch. Recheck immediately before creating a new task;
existing design execution retains its own precommit checks.

`DOSSIER_EVIDENCE_STATE` is an append-only observation of status transitions,
not an authority cache. Unchanged polls and restarts do not append duplicates.
Snapshots re-export at the current clock without modifying the journal, expose
`dossier_evidence`, and add `source_evidence_status=CURRENT|UNAVAILABLE` to
each task. The paired local UI requires these fields; an older server is not
silently interpreted as current. Historical tasks remain unchanged and open
when their source expires. Acknowledgement also rechecks source authority;
link/reassessment retain their two-source revalidation. Source-unavailable
actions are hidden by the UI and rejected by the backend. Pause/STOP prevent
automatic lifecycle transitions; stale source history never stops unrelated
current design work. Intake crash/review recovery rules are unchanged.

Unknown task, same-root or same-dossier substitution, expired/tampered dossier,
changed evidence ID/hash, malformed decision, and replay collision fail before
any journal write. Snapshot revalidates linked evidence; stale links show
`STALE_OR_REVOKED` and cannot be reassessed. No state in this version asserts
that a source gap has been substantively resolved.

The existing `AUTONOMY_TASK` records and `HUMAN_ACKNOWLEDGED` state remain
readable. New fields are optional on old records. Neither action changes the
output or intake queue, starts network acquisition, clears pause/STOP, or
enables external effects. This candidate contract requires Master Architecture
Review before being accepted across blocks or at production scope.

## Validation and non-claims

Use a positive local link/reassessment test plus same-root, stale/tamper,
malformed request, replay, and no-effect assertions. A test fixture can prove
mechanism, not that two real sources independently corroborate a claim. The
state `BLOCK1_REASSESSMENT_REQUIRED` is a local workflow request, not an
accepted insight or independent review. A later Block 1 contract must define
how source-specific needs can be resolved before any task is actually closed.
