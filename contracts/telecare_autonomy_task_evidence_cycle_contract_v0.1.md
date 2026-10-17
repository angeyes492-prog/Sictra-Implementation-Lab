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
New links include the Block 1 measurement comparison candidate defined in
`block1_cross_source_measurement_contract_v0.1.md`. It is visible on read and
recomputed for current links; legacy links without this field remain readable.
`NO_SHARED_MEASUREMENT` is a valid candidate-link result, not evidence that a
gap was resolved. The operator can record insufficiency; Block 4 cannot upgrade
the dossier or task from this comparison.
The Block 1 read-only need assessment derives from the exact need class and
fresh comparison. Its verdict is `INSUFFICIENT`, `MEASUREMENT_DISAGREEMENT`, or
`REVIEW_REQUIRED` with a reason code and next action. It always retains
`NOT_RESOLVED`, `NOT_ACCEPTED`, and `BLOCKED`. A reported-value disagreement is
not a causal explanation or a source-level contradiction. An exact match still
requires a source-specific Block 1 review; no current input can mint `RESOLVED`.
Block 4 links and snapshots may expose the assessment, while legacy links are
recomputed read-only without rewriting their journal records.
New tasks use `BLOCK1_CONTRACTED_RESOLUTION_REQUIRED` as their completion
boundary. Old task records retain their original metadata; snapshots mark it
`LEGACY_SUPERSEDED` and expose the current effective boundary without rewriting
the journal.
Known Block 1 need texts are classified by exact source-specific wording into
independent corroboration, source methodology, company exposure, or source
granularity. Unknown or changed wording is `UNCLASSIFIED`, never guessed from
keywords. A read-side `effective_kind` safely reclassifies legacy task metadata
without rewriting history. This is routing metadata, not a resolution verdict.

Only `INDEPENDENT_CORROBORATION` has the `INDEPENDENT_DOSSIER` route: it
requires a different evidence root and may use the candidate-dossier link.
`SOURCE_METHODOLOGY` uses `OFFICIAL_SOURCE_METHODOLOGY`: it requires retained
official metadata for the source, not an unrelated second root, and Block 4
does not link it through the cross-source comparison. `COMPANY_EXPOSURE` uses
`AUTHORIZED_ACCOUNT_CONTEXT`: it requires separately authorized account
context and likewise cannot be fulfilled by a generic dossier link. These two
routes are visible as task-specific waits, never as failed searches for another
root. Legacy records retain their historical fields; snapshots expose the
effective route and reject a link that conflicts with it. None of these routes
resolves a task or changes publication/acceptance.

`SOURCE_GRANULARITY` has the `SOURCE_SCOPE_DETAIL` route and asks for approved
product/origin/regime detail for the same periods, rather than another root.
Block 1 owns `route_data_need`; B4 consumes the returned route. Unknown wording
uses `MANUAL_CLASSIFICATION`. New evaluations bind the effective next action;
legacy task fields cannot override it. Prior research evaluations incompatible
with the new route become unavailable on read and a subsequent running cycle
appends the correct observation. No history is rewritten.

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
