# Block 1 — Dossier workspace reader v0.1

`IMPLEMENTED CANDIDATE / LOCAL-TESTED / B`. The local Intelligence Workspace
can receive an explicitly constructed `IntelligenceDossierStore` and expose a
read-only view of its recomputed dossiers and conservative editorial
assessment.

The default server remains unconfigured. It reports `NOT_CONFIGURED` and an
empty list rather than presenting fixtures as retained evidence. A configured
reader verifies the complete dossier ledger on every list/detail request; a
mutation returns an integrity error and never falls back to the synthetic
editorial cycle.

The browser receives no HMAC key, raw watchlist bridge input, store path,
write route, selection authority, handoff or publication authority. The
synthetic editorial desk remains visibly separate from the signed dossier
reader. This is a local laboratory observation boundary, not operator
configuration, source acquisition, review acceptance or production access.

