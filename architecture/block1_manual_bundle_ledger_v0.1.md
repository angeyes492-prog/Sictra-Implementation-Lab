# Block 1 — Manual bundle ledger v0.1

`IMPLEMENTED CANDIDATE / LOCAL-TESTED / B`. This bounded Layer 4 component
persists an already assembled, un-attested Eurostat manual bundle in an atomic
local JSON ledger. Each entry is HMAC chained to its predecessor and is
re-validated before reading or extending the ledger. It records a durable
transformation/provenance artifact; it cannot attest, bind, admit, analyse,
publish, fetch or promote a source.

The ledger accepts only the exact seven gateway bundle fields and the canonical
`UNATTESTED_MANUAL_BUNDLE` content produced by the Eurostat assembler. It
returns `RECORDED_UNATTESTED_NOT_EVIDENCE`. Exact replay is idempotent by
bundle SHA-256; any altered field, content, prior hash, MAC, schema or
duplicate identity fails closed. The integrity key never resides in the ledger
file.

This is a local pilot boundary only. It does not encrypt data at rest, manage
retention, supply user identity, recover lost keys, offer concurrency across
processes, or substitute a later gateway attestation and independent review.
