# Block 1 — Durable attested evidence store v0.1

`IMPLEMENTED CANDIDATE / LOCAL-TESTED / B`. This Layer 4 component retains
gateway-issued observed records in an atomic, HMAC-chained local ledger. Before
every write and read it verifies the evidence signature at admission time,
the complete Eurostat manual-bundle schema, content SHA-256, gateway
provenance, ingestion method, approval lineage and binding lineage.

An admitted record remains immutable history after freshness expires. Current
runtime input is a separate read operation that revalidates the evidence at the
caller-supplied current time and excludes stale records. Exact replay is
idempotent; append order and logical time cannot regress.

This store owns retention and integrity of a local evidence record, not truth,
independent corroboration, interpretation, licensing, source acquisition or
gate promotion. Evidence and store keys remain external. HMAC is a local
reference trust mechanism, not production KMS/PKI.

Failure/recovery: malformed schemas, invalid signatures, stale/future evidence
at admission, content/lineage mismatch, wrong key/capacity, record mutation,
identity collision, exhausted capacity and failed atomic replacement fail
closed. A failed replacement preserves the previous file.
