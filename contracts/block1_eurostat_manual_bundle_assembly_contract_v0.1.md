# Contract — Eurostat manual bundle assembly v0.1

Producer: `sictra_block1.eurostat_manual_bundle`. Consumer: a future, bound
`SourceGateway`. Scope: `BLOCK1_EUROSTAT_MARITIME_MANUAL_BUNDLE_ASSEMBLY`.
Authority: deterministic selection serialization only.

Inputs are a preflightable Eurostat workbook filename and bytes, one explicit
geography level, a canonical Eurostat dataset URL, non-negative integer
`observed_at`, and a bounded correlation identifier. The source URL requires
HTTPS, `ec.europa.eu`, no credentials, no explicit port, no fragment, and the
path token `tran_r_mago_nm`.

The producer calls the schema mapper and level selector; its output has
exactly the gateway fields `source_id`, `source_url`, `content`,
`observed_at`, `claim_key`, `polarity`, and `correlation_id`. `content` is
canonical JSON and carries: the source-file SHA-256, dataset code and declared
update time, filters, selected geography level, grain, years, coverage,
observations, mapping/selection states and `UNATTESTED_MANUAL_BUNDLE`.
`claim_key` is exactly `maritime_freight_weight_thousand_tonnes`; polarity is
the controlled value `1` and is not an editorial conclusion.

The serialized UTF-8 content must not exceed 131,072 bytes. No record is
attested, persisted, uploaded, fetched, scheduled, analysed, or published.
Any violation raises `EurostatManualBundleViolation`; nothing is partially
emitted. A matching approved source binding and a gateway attestation remain
separate prerequisites for an `OBSERVED` evidence record.
