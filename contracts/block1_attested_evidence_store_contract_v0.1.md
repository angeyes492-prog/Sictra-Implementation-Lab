# Contract — Durable attested evidence store v0.1

Version `0.1`; producer/consumer:
`sictra_block1.attested_evidence_store.AttestedEvidenceStore`. Scope:
`BLOCK1_LOCAL_ATTESTED_EVIDENCE_STORE`. Authority: local admission-time
verification, immutable retention and current-runtime retrieval.

Configuration requires a path, non-empty evidence-key map, exact evidence
scope, non-negative freshness window, controlled claim set, separate 32-byte
integrity key, integer clock and capacity from 1 to 1,000. Secrets are never
persisted.

`persist` accepts a gateway record only when `EvidenceVerifier` returns
`SOURCE_VERIFIED` at the trusted write time. Required signed extensions are
`source_url`, `publisher`, `content_sha256`, `ingestion_method`,
`source_approval_fingerprint` and `source_binding_fingerprint`. Content hash
must match exact UTF-8 bytes; approval/binding fingerprints must be lowercase
SHA-256; provenance must be `gateway-source:{source_id}`; ingestion must be
`MANUAL_SOURCE_BUNDLE`; and reconstructed outer content must pass the complete
Eurostat un-attested-bundle validator.

Each record stores evidence identity, admission time, predecessor HMAC,
record HMAC and the complete signed evidence. Every load recomputes exact
schema, identity, admission-time verification, source extensions, chain and
HMAC. Exact replay does not append.

`runtime_records(now)` re-verifies freshness/signature/scope/claim at `now`
and returns defensive copies of only current records. `list_receipts(now)`
retains all history and reports verifier reason/status without laundering stale
records into current evidence.

Writes use fsync plus atomic replacement. Non-claims: no truth validation,
independent root, causal inference, scheduler, encryption, KMS, cross-process
locking, retention deletion, backup/restore, editorial approval or gate
promotion.
