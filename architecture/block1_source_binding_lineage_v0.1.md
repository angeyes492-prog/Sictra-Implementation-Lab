# Block 1 — Source binding approval lineage v0.1

`IMPLEMENTED CANDIDATE / LOCAL-TESTED / B`. A source binding now signs the
SHA-256 fingerprint of the exact normalized `SourceApprovalRecord` that
authorized issuance. The gateway propagates that approval fingerprint and a
fingerprint of the signed binding into the separately signed observed record.

Purpose: prevent a durable binding from becoming detached from reviewer
identity, review time, terms evidence, decision and the source limits that
justified it. Scope: the existing manual source gateway; no new source or
authority role is introduced.

Direct impact: binding schema changes and old local binding fixtures are
incompatible. Second-order impact: a future binding store can verify the public
approval artifact before creating a gateway. Third-order impact: evidence and
editorial audit can cite an exact approval lineage without receiving the
binding secret.

Failure/recovery: missing, malformed, altered or unsigned approval lineage
fails closed. Recovery requires reissuing a binding from the reviewed approval;
no compatibility fallback is permitted. The HMAC key remains external and the
fingerprint does not prove reviewer identity, legal correctness, source truth
or independent validation.
