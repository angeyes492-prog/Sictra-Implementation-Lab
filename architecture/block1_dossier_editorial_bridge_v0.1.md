# Block 1 — Dossier to editorial bridge v0.1

`IMPLEMENTED CANDIDATE / LOCAL-TESTED / B`. This bridge reads a recomputed,
integrity-verified dossier from `IntelligenceDossierStore` and converts it to
the existing editorial candidate contract. It does not accept a caller-owned
dossier.

Because the current dossier has one source root, no independent corroboration,
no human interpretation and unknown freshness/stability/red-team state, the
bridge deliberately emits `RESEARCH_NEEDED`: uncertainty 100, required roots
2, contradiction bounding false and publication unavailable. Literal facts,
lineage, limitations and executive questions remain visible.

The editorial engine remains owner of eligibility and shortlist behavior. This
bridge cannot create readiness, human review, a Block 2 handoff or publication.
Recovery is reconstruction from the durable dossier ledger; unknown identity,
duplicate identity or mutated store history fail closed.
