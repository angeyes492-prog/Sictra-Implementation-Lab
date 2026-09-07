# Block 1 — Intelligence dossier store v0.1

`IMPLEMENTED CANDIDATE / LOCAL-TESTED / B`. This Layer 3 component converts a
review-required, attested-input watchlist delta into an immutable local dossier
and preserves it in an atomic HMAC-chained ledger.

The generated dossier separates literal change facts from empty
interpretation and hypothesis sections. It records uncertainty, limitations,
affected geography/time, executive questions and next-data needs. Its initial
state is always `REQUIRES_HUMAN_INTERPRETATION`; publication is always
`BLOCKED`. The component cannot infer causality, business impact, forecasts or
editorial readiness.

Each load recomputes the input contract, dossier content, identity, chain and
HMAC. Exact replay is idempotent. Mutation, wrong key/capacity, time regression,
invalid delta linkage and failed atomic replacement fail closed. Secrets remain
external. This local reference does not provide encryption, KMS, cross-process
locking, retention deletion, backup/restore, human identity or production
authority.
