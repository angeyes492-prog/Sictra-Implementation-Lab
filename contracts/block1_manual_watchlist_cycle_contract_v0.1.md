# Contract — Durable manual watchlist cycle v0.1

Version `0.1`; producer/consumer:
`sictra_block1.manual_watchlist_cycle.ManualWatchlistCycle`. Scope:
`BLOCK1_LOCAL_MANUAL_WATCHLIST_CYCLE`. Authority: atomic local checkpoint and
delta retention only.

Input is one fully self-consistent `UNATTESTED_MANUAL_BUNDLE`. Configuration
requires a local path, an integrity key of at least 32 bytes, a non-negative
integer clock, a unique cycle-ID source and capacity from 1 to 100. The key is
never stored in the ledger.

Each durable entry contains the complete current bundle, its SHA-256, a
baseline or deterministically recomputed delta, delta SHA-256, prior record
hash, record HMAC, cycle identity and record time. Every open/read/write checks
the exact ledger/entry schema, key/capacity binding, monotonic time, unique
identity, bundle validity, predecessor linkage, delta recomputation and HMAC.
Exact source-file replay is idempotent and does not append. The returned
receipts and latest delta are defensive copies.

Initialization has no fabricated previous state and returns
`BASELINE_ESTABLISHED_NOT_EVIDENCE`. Later source content must satisfy the
manual watchlist comparison contract. Atomic replacement ensures an exception
before replacement leaves the prior file intact; an exception after a complete
replacement is recoverable by reopening and verifying the new state.

Malformed JSON/schema/key, content or observation inconsistency, changed data
at an equal release time, temporal regression, duplicate identity, invalid
clock and capacity exhaustion raise `ManualWatchlistCycleViolation`.

Non-claims: no attestation, source admission, network acquisition, scheduling,
notification, interpretation, human approval, KMS, encryption, cross-process
serialization, backup/restore or gate promotion.
