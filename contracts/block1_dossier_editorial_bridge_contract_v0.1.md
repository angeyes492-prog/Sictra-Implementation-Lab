# Contract — Dossier to editorial bridge v0.1

Version `0.1`; producer/consumer:
`sictra_block1.dossier_editorial_bridge.DossierEditorialBridge` to
`BLOCK1_EDITORIAL_ENGINE_V0.1`. Authority: conservative candidate composition
only.

Input is a dossier ID present exactly once in a verified
`IntelligenceDossierStore`. The candidate preserves source/delta lineage,
literal change statements, limitations, uncertainty and questions. It must
declare one current source root against two required independent roots,
`RESEARCH_NEEDED`, unknown freshness/red-team/stability, no bounded
contradiction, high uncertainty and no company-specific implication.

The resulting candidate must pass the editorial input schema and must be
assessed `BLOCKED` / `RESEARCH_NEEDED`. Unknown or duplicate dossier identity
rejects. Non-claims: interpretation, source truth, corroboration, readiness,
selection, handoff, publication or gate promotion.
