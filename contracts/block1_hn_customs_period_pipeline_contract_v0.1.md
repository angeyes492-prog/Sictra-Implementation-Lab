# Contract — Honduras customs period pipeline v0.1

Version `0.1`; producer `sictra_block1.hn_customs_pipeline`; consumers are the
local Telecare intake, Block 1 dossier reader and the B4 package adapter. Scope
`BLOCK1_LOCAL_HN_CUSTOMS_PERIOD_PIPELINE`. Authority is limited to owner-supplied
local XLSX files that conform to `HN_CUSTOMS_Q1_V1`. There is no network,
publication, source-truth, causal, recommendation or gate-promotion authority.

The source identity is `HN_ADUANAS_BULLETINS`, with root evidence identity
`HN_SARAH` and the exact official 1T2025 bulletin URL. A workbook must contain
only `DATA`, `PROVENANCE` and `CHECKS`; the exact stable data columns; six unique
customs-point rows; Honduras, CIF imports, USD millions, preliminary status,
the declared source/root/version; a Q1 period; and reconciliation within 1.0
USD million of the published total. Macro, external-link, unsafe ZIP, duplicate,
reordered-period, altered retained bytes and different-byte normalized replay
inputs fail closed.

Exact bytes are retained by SHA-256. Each read reparses them and recomputes the
signed append-only journal. The first chronological snapshot is a baseline. A
later period with the same schema creates literal value-change facts and a
blocked dossier. Period snapshots are explicitly not represented as byte-level
revisions of one raw source file. Published totals, normalized sums and gaps
remain distinct.

The package export is current for 24 hours from controlled ingestion and never
outlives the owner binding. It carries facts, lineage, uncertainty and limits;
it cannot publish, deliver, write CRM or infer cause. Rollback removes the
source-specific adapter and UI option while leaving retained files and the
Eurostat pipeline intact. Local recovery must include the journal, manifest and
retained XLSX while keeping the HMAC key external to the archive.

The owner-supplied trade source registry is retained byte-for-byte in a
separate contextual catalog with its SHA-256 and a signed immutable record. It
has `runtime_effect = NONE`: catalog rows, URLs and recipes cannot become
observations or evidence merely because the catalog is present.
