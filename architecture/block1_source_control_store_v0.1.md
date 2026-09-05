# Block 1 — Durable source control store v0.1

`IMPLEMENTED CANDIDATE / LOCAL-TESTED / B`. This Layer 1/4 component preserves
bounded source registration, exact human approval and signed binding as one
durable control record. It stores no secret. On every read it reconstructs the
typed records, verifies approval lineage, binding signature/scope/time-at-write,
an HMAC record chain and capacity/key metadata.

A caller may request the currently active record for one source or construct a
`SourceGateway` from it using a separately supplied evidence issuer. Expired
bindings remain immutable history but cannot construct a gateway. Binding
rotation appends; it never replaces prior authority evidence. Exact replay is
idempotent.

Authority boundaries: the store does not approve terms, issue a binding,
create evidence, keep secrets, fetch content or promote a gate. Binding keys
and the store-integrity key are caller-held. HMAC remains a local reference
mechanism, not KMS/PKI or independent identity.

Failure and recovery: malformed schema, wrong key/capacity, altered approval,
invalid/unknown binding issuer, chain mutation, non-monotonic rotation,
identity collision, capacity exhaustion or atomic-write failure fail closed.
The prior file remains recoverable when replacement does not complete.
