# Local operations candidate v0.1

Date: 2026-09-13. Status: CANDIDATE, MAR remains open. Scope:
LABORATORY_INTERNAL_SUPERVISED. This implements the owner's request for a
working, proactive local product; it does not promote the existing gates.

## Observed gap and bounded implementation

The previously tested Block 2 adapter invokes reference_run_input, including
synthetic copy and synthetic review fixtures. Its execution receipts establish
mechanism execution, not actual source-based copy or editorial acceptance.
The previous autonomy loop also lacks an entry point, persistent scheduler,
configured profiles and visible output; fixed-size prefix selection starves
later dossiers. Existing closure claims are restricted to those tested slices.

The new operations service schedules source-bound content-design candidates.
Block 1's approved Eurostat file pipeline retains evidence and literal change
dossiers. Block 2 owns an evidence-first information hierarchy, visual component
structure and deterministic local render; it does not acquire research semantics.
Block 3 applies a declared generic audience presentation policy (role, depth,
tone, geographic selection) to that fixed design. It never invents a person,
account fact, consent, or M01-M07 acceptance. Block 4 persists the output,
revision identity, execution stages, waits and failures. Uninterpreted dossiers
remain review-needed; preparing a design artifact never enables editorial
handoff or publication.

## Interfaces, invariants, failure and recovery

Input: approved file bytes via explicit registration; signed local config
contains versioned generic profiles. Output: Block 2 design artifact plus Block
3 adaptation, source and profile hashes, literal facts, uncertainty, missing
evidence and questions. The local renderer is deterministic and makes no
external model requests. A separate provider integration would require its own
tests and configured credentials.

The operation journal is SQLite with HMAC-chained immutable events. Each output
is appended atomically; pure draft construction can repeat after interruption
without external effects. Existing intake recovery remains explicit because
ingestion has multiple side effects. Missing profile is a wait, not permanent
invalidation. Polling uses persistent round-robin position, bounded batches,
single-writer process lease, interruptible delay, pause/stop and heartbeat.
Source and profile expiry are checked during execution and when reading output.

Backups use SQLite snapshots and signed manifests; verification and restore
reject alteration and existing targets. Keys stay outside repository/inbox.
The local seal does not prevent privileged rollback: external anchor and
deployment identity remain production requirements. No contact or publication.

## Validation and next boundary

Independent expected values in tests verify actual numbers and source identity,
profile differences, missing profile recovery, fairness beyond a full batch,
stale/tampered records, HTML injection, duplicate execution, process restart,
pause/stop, backup/restore and hostile HTTP origins. A fresh local pilot uses
explicitly labelled synthetic XLSX data; it is not a real-source production pilot.
No historical approval is reused for this increment.
