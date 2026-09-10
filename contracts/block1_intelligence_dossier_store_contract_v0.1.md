# Contract — Intelligence dossier store v0.1

Version `0.1`; producer/consumer:
`sictra_block1.intelligence_dossier.IntelligenceDossierStore`. Scope:
`BLOCK1_LOCAL_INTELLIGENCE_DOSSIER`. Authority: deterministic fact extraction
and durable local retention only.

Input must be the exact `AttestedWatchlistBridge` result for one
`DELTA_DETECTED_NOT_EVIDENCE` cycle with `REQUIRES_REVIEW`. Source, change
count, status and canonical delta SHA-256 must match the watchlist receipt;
approval, binding, content and delta fingerprints must be lowercase SHA-256.
The exact bridge result, issuer identity and schema version must verify against
a configured 32-byte-or-longer bridge key.

Every delta change becomes one literal fact with the complete before/after
measurement and source/delta lineage. Interpretations and hypotheses are empty.
Uncertainties, limitations, affected scope, executive questions and next-data
needs are explicit separate fields. Certainty is `UNCONFIRMED`, confidence `C`,
review state `REQUIRES_HUMAN_INTERPRETATION` and publication state `BLOCKED`.

The store uses append-only HMAC chaining, canonical identity, fsync and atomic
replacement. Exact replay does not append. Invalid input, tamper, stale schema,
wrong configuration, capacity exhaustion and time regression reject. Non-claims:
truth, causality, independent corroboration, business impact, forecast,
editorial readiness, publication or gate promotion.
