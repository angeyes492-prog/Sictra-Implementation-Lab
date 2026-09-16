# Block 1 — Honduras customs period snapshots v0.1

Status: `IMPLEMENTED CANDIDATE / LOCAL-TESTED`; independent review deferred.
This is an additive source adapter, not a rewrite of the protected Eurostat
contract. Its purpose is to compare the owner-supplied normalized 1T2024 and
1T2025 Honduras customs snapshots while preserving their shared `HN_SARAH`
root and their distinction from raw historical revisions.

Flow: `owner approval → controlled XLSX preflight → exact schema and provenance
mapping → raw-byte retention → signed chronological journal → literal delta →
blocked intelligence dossier → existing design/audience review surfaces`.

Inputs and outputs are defined in the corresponding contract. The adapter owns
only normalization, reconciliation, chronology, source-specific delta facts and
retention. Existing B2/B3/B4 components own presentation, audience adaptation
and supervised review. A composite reader dispatches by dossier identity and
does not allow either source adapter to validate the other.

Failure is fail-closed. Revalidation reads exact retained bytes; integrity,
schema, source-root, chronology, reconciliation or HMAC failure blocks export.
Recovery includes data and keeps keys separate. The source registry workbook is
retained exactly as catalog context and is not ingested as observations.
Eurostat recipe rows marked
`raw_file_bundled = NO` remain non-ingestible until a real raw export exists.

Downstream effects are bounded to generic unit-aware design copy and an
additional source option. No production acceptance, independent corroboration,
causal conclusion or external effect follows from a passing local ingestion.
