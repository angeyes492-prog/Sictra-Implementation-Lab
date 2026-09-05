# Contract — Durable source control store v0.1

Version `0.1`; producer/consumer:
`sictra_block1.source_control_store.SourceControlStore`. Scope:
`BLOCK1_LOCAL_SOURCE_CONTROL_STORE`. Authority: durable retention and current
binding reconstruction only.

Configuration requires a path, non-empty trusted binding-key map, separate
integrity key of at least 32 bytes, non-negative integer clock, and capacity
from 1 to 50. Secrets never enter persisted JSON.

`persist` accepts a `BOUND` `SourceRegistration`, matching `APPROVED`
`SourceApprovalRecord`, and current signed binding. The binding's approval
fingerprint must equal the exact normalized approval. Stored time must lie in
the signed validity window. Exact replay returns the existing receipt; a newer
binding for the same source must have a strictly later issuance time.

Every record contains normalized registration, approval, binding, stored time,
binding identity, predecessor HMAC and record HMAC. Every load validates exact
schema, metadata key/capacity binding, monotonic time, unique binding identity,
typed reconstruction, approval/registration equality, approval fingerprint,
binding signature and predecessor chain.

`active_record(source_id, now)` returns a defensive copy of the newest binding
that is current at `now`, or `None`. `build_gateway` returns a gateway only
from that active record and a caller-supplied `EvidenceIssuer`; expired,
future, unknown or malformed bindings fail closed. History receipts distinguish
`ACTIVE` and `NOT_CURRENT` without deleting prior records.

Writes use fsync plus atomic replacement. This contract provides no approval,
binding issuance, secret manager, encryption, cross-process lock, network
access, evidence attestation by itself, source truth, independent review or
gate promotion.
