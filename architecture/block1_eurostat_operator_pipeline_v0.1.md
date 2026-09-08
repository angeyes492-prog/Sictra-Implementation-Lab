# Block 1 — Eurostat operator pipeline v0.1

Status: `IMPLEMENTED CANDIDATE / LOCAL-TESTED / B`. Scope:
`BLOCK1_LOCAL_EUROSTAT_OPERATOR_PIPELINE`. This is the reproducible local path
for one explicitly supplied `tran_r_mago_nm` workbook and one explicit
geographic selection. It has no network client and cannot fetch, crawl or
contact a third party.

Flow: `approved source record and expiring binding → preflight → manual bundle
→ gateway attestation → durable evidence → E01–E08 bounded runtime → attested
watchlist → optional literal-fact dossier → blocked editorial reader`.

The pipeline owns orchestration and local layout only. Source Control owns
approval/binding retention; the gateway owns attestation; the evidence store
owns freshness; the runtime owns E01–E08; the watchlist owns technical deltas;
the dossier store owns literal fact extraction; and editorial remains blocked.
No component can infer source truth, causality, business impact, publication,
or a global gate from this path.

All key material resides in the local pipeline key directory outside Git and
the project workspace. The persisted manifest contains only fixed filenames,
source scope and the explicit network-disabled boundary. Each ledger validates
its own signature or HMAC chain on every load. A binding expires after 180 days
and then blocks further ingestion pending a separate renewal; expiry never
silently becomes approval.

Freshness is 24 hours. Historical evidence remains retained for provenance;
only the exact current receipt subset reaches E01–E08. Multiple current source
versions therefore fail closed at the watchlist boundary. A first accepted
release produces `BASELINE_ESTABLISHED_NOT_EVIDENCE`. Only a later valid release
may create `DELTA_DETECTED_NOT_EVIDENCE` and a dossier whose interpretation,
hypotheses and publication state remain empty/blocked.

Recovery is data-only. The backup contains integrity-verified source-control,
evidence, watchlist and dossier ledgers, never keys or the SQLite runtime
journal. Restore accepts only a complete absent ledger set under the original
local keys, refuses every overwrite, then verifies the restored ledgers. A
runtime execution can be replayed from retained current evidence; its historic
SQLite journal is not evidence and is not claimed as backup coverage.

Observability is local: the command returns preflight, source-control,
evidence, runtime, watchlist and dossier states, while the laboratory interface
shows the sanitized pipeline state. No raw workbook content, local key, source
credential or unpublished interpretation is exposed through the UI.
