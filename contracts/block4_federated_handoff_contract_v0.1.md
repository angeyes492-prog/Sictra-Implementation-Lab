# Block 4 Federated Handoff Contract v0.1

Status: `CANDIDATE / LOCAL BOUNDED SUT / NOT ACCEPTED`.

## Producer and consumer

Producers: `BLOCK1`, `BLOCK2`, `BLOCK3`. Consumer: `BLOCK4`. The consumer
coordinates only. It cannot create, edit or upgrade a producer claim.

## Required envelope

`case_id`, `run_id`, `message_id`, `evidence_id`, `dossier_id`, `producer`,
`contract_version`, `source_hash`, `provenance_root`, `observed_at`, `expires_at`,
`currentness`, `certainty`, `uncertainty`, `disposition`, `lineage`, `payload`
and `signature` are mandatory. Contract version is exactly `0.1.0`; producers
must appear in lineage in order, with no duplicate or substituted identity.

`currentness` is `CURRENT` only when `observed_at ≤ now < expires_at`. Allowed
certainty values are `VERIFIED`, `PROBABLE`, `PLAUSIBLE`, `UNCONFIRMED`,
`CONTRADICTED`, and `INSUFFICIENT EVIDENCE`.

## Preconditions and transitions

An HMAC over canonical JSON must verify before persistence. The source hash,
provenance root and case/run identity remain unchanged through all stages.
Block 1 can enter only as current and non-contradicted. Block 2 and Block 3 are
locally synthesized coordination receipts, never proof that their independent
runtimes executed. The only forward transitions are the architecture state
machine; a terminal state cannot advance.

## Rejection and recovery

Malformed schema, unknown producer/version, invalid signature, expiry,
contradiction, missing lineage, source/provenance substitution, illegal
transition, collision, unknown case and retry exhaustion reject or return
upstream without downstream execution. Exact replay is idempotent. Restart
verifies the append-only HMAC chain before any read; integrity failure blocks
the store.

## Authority and non-claims

The contract authorizes no network, publication, delivery, CRM, contact,
credential use, human-approval substitution or gate promotion. `HUMAN_REVIEW_REQUIRED`
is a stopping state. Contract conformance and a local journal do not prove
cross-block runtime execution, real-source validity, independent review or
production readiness.
