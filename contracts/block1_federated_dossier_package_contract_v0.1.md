# Block 1 Federated Dossier Package Contract v0.1

Status: `CANDIDATE / LOCAL BOUNDED SUT / NOT ACCEPTED / MAR REQUIRED`.
Date: 2026-09-13. Producer: Block 1 durable dossier adapter. Consumer: Block 4.

## Purpose and accepted input

The adapter exports one dossier only after reopening and verifying the complete
operator pipeline. It requires exactly one durable dossier with literal facts,
no interpretation or hypothesis, `REQUIRES_HUMAN_INTERPRETATION` and
publication `BLOCKED`. Its source approval/binding fingerprints, content hash,
source identity and observation time must match the unique currently attested
evidence record and an active retained source binding.

The package identity is deterministic over the dossier and evidence identities.
Its validity ends at the earlier of the attested evidence freshness boundary or
source-binding boundary. It preserves the dossier certainty and uncertainty,
adds no interpretation, and signs the exact federated package.

## Rejection and replay

Missing, duplicated, stale, superseded, ambiguous or altered evidence rejects
the export. Pipeline or dossier-store integrity failure is never converted into
an empty result. An identical current dossier exports the same package; changed
signed material under the same case identity is rejected downstream as a
collision.

## Authority and known non-claims

The package grants no publication, content acceptance, independent
corroboration or business-decision authority. The current Eurostat dossier is
`UNCONFIRMED` because it deliberately lacks independent interpretation and
company-specific evidence. This adapter does not invent the professional-person
context required by Block 3. Shared package-key custody, activation and the
dossier-to-precision semantic mapping remain final architecture decisions.
