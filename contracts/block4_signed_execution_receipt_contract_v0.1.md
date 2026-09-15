# Block 4 Signed Execution Receipt Contract v0.1

Status: `CANDIDATE / LOCAL BOUNDED SUT / NOT ACCEPTED / MAR REQUIRED`.
Date: 2026-09-13. Producer/consumer: `BLOCK2` or `BLOCK3` → `BLOCK4`.

## Purpose and scope

This candidate contract distinguishes a coordination transition from evidence
that a producer runtime was invoked. Block 4 may record a state transition only
after it verifies a producer-specific HMAC receipt, the federated case/run
identity, the exact parent fingerprint, the package validity interval and the
declared no-publication/no-delivery boundary.

It does not authorize shared production keys, cross-service activation,
publication, delivery, contact, CRM writes, content acceptance, human approval
substitution or gate promotion.

## Receipt schema and identity

Every receipt carries `case_id`, `run_id`, `execution_id`, `producer`,
`contract_version`, `parent_fingerprint`, `input_fingerprint`,
`output_fingerprint`, `disposition`, `executed_components`, `restrictions`,
`created_at`, an allowlisted producer payload and `signature`.

The three fingerprints are lowercase SHA-256 values. Timestamps are timezone
aware. The receipt cannot predate its Block 1 package or come from the future.
The orchestrator owns a configured, distinct key for each producer; a caller
cannot select the verification key at transition time. The journal integrity
key cannot be reused as a producer key.

## Producer-specific acceptance

- Block 2 advances only after `E01` through `E08` executed, the result completed,
  and the producer reports `NOT_PUBLISHED` and `NOT_ACCEPTED`. The candidate
  adapter uses the repository reference run input to prove mechanism execution;
  this is explicitly `REFERENCE_MECHANISM_NOT_CONTENT_ACCEPTANCE`.
- Block 3 foundation-only execution advances only for `ACCEPTED` or `PARTIAL`
  with a decision and runtime evidence for `M01` through `M05`. The supervised
  runner additionally requires a Block 2 receipt-bound authorized asset and
  executes `M06` and `M07`; only a `SEND_CANDIDATE` carrying
  `PROPOSAL_NOT_EXECUTION` can reach the human gate. It never sends or contacts.
- `M08` is intentionally not run in the pre-review route: it requires an actual
  delivery receipt and externally observed outcome. Running it earlier would
  manufacture learning evidence.
- Any incomplete, blocked or nonconforming result becomes `RETURN_UPSTREAM`.
  A verified Block 3 receipt is required before Block 4 can enter
  `HUMAN_REVIEW_REQUIRED` through the verified runner.

The supervised runner may resume from a verified Block 2 checkpoint. The
separate Block 1 dossier adapter can now export a real, current, signed dossier
package without interpretation. The runner still requires an explicit governed
`PrecisionInput`; neither contract invents a semantic mapping from an editorial
dossier to professional/person context.

## Replay, failure and recovery

Exact receipt replay is idempotent. Reusing an execution identity with different
signed material is a collision. Wrong producer, parent, run, signature,
component set, authority boundary, stale package or missing checkpoint is
rejected or returned upstream. On restart, Block 4 verifies the complete journal
and then re-verifies stored producer receipts before resuming.

## Validation and known non-claims

The focused suite invokes the real Block 2 E01–E08 implementation and the real
Block 3 M01–M07 candidate path, exercises checkpoint recovery, and attacks tamper,
wrong keys, cross-case identity, replay, missing components, absent decisions,
unbound assets, stale/expired/contradicted evidence and temporal substitution.
Passing this suite is local integration evidence only. Activation, key custody,
the dossier-to-precision mapping, post-delivery M08 evidence and production
acceptance remain outside this candidate contract and require the final
architecture decision.
