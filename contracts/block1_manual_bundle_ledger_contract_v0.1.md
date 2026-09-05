# Contract — Manual bundle ledger v0.1

Producer/consumer: `sictra_block1.manual_bundle_ledger`. Scope:
`BLOCK1_LOCAL_UNATTESTED_BUNDLE_LEDGER`. Authority: local durable recording
and integrity verification only.

Input is exactly an un-attested bundle constructed under
`block1_eurostat_manual_bundle_assembly_contract_v0.1`: the seven gateway
fields, a canonical JSON content envelope at schema `0.1.0`,
`UNATTESTED_MANUAL_BUNDLE`, `eurostat`, the controlled claim vocabulary and
the preserved `MAPPED_NOT_EVIDENCE` / `SELECTED_NOT_EVIDENCE` states. The
store needs a caller-held integrity key of at least 32 bytes, a bounded
capacity, a deterministic entry identity source and a non-negative logical
record time.

An accepted first write atomically replaces the complete ledger and returns an
immutable receipt with entry identity, bundle SHA-256, predecessor hash,
record hash, recorded time and
`RECORDED_UNATTESTED_NOT_EVIDENCE`. An exact replay returns the existing
receipt without extending the chain. Every load recomputes strict shape,
bundle SHA-256, predecessor linkage and HMAC; malformed JSON, capacity
exhaustion, key mismatch or any mutation raise `ManualBundleLedgerViolation`.

The ledger never adds an attestation, changes `evidence_class`, binds a
source, calls a gateway, derives a fact, schedules work, fetches the network or
declares acceptance. It does not provide encryption, KMS, identity,
cross-process locking, backup, restore, retention or production audit
guarantees.
