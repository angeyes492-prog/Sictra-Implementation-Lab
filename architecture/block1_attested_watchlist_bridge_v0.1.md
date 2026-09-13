# Block 1 — Attested watchlist bridge v0.1

`IMPLEMENTED CANDIDATE / LOCAL-TESTED / B`. This adapter accepts one and only
one current source record from the Layer 4 attested evidence store and submits
its reconstructed manual bundle to the existing durable watchlist cycle.
Its output is signed by a separately configured bridge issuer so downstream
stores can reject fabricated or altered receipts.

It owns admission to the watchlist, not delta storage, source truth, change
interpretation, human review, insight generation or publication. No current
record, a stale record, or more than one current record for the requested
source fails before the watchlist is modified. The resulting delta remains
`ATTESTED_INPUT_DELTA_NOT_EVIDENCE` and requires review when changes exist.

This is a local, single-process bridge. It does not solve retained operator
secrets, cross-process locking, a source-version selection policy, scheduler,
notification, encryption, KMS or editorial interpretation.
