# Contract — Eurostat maritime schema mapper v0.1

Producer: `sictra_block1.eurostat_maritime_mapper`. Consumer: future governed
manual-bundle assembly. Scope: `BLOCK1_EUROSTAT_MARITIME_SCHEMA_MAPPING`.
Authority: schema and quality validation only.

Input is a preflighted XLSX filename plus bytes. The accepted workbook must
declare `tran_r_mago_nm`, `Annual [A]`, `Freight loaded and unloaded
[FR_LD_NLD]`, `Thousand tonnes [THS_T]`, a parsable `Last updated` timestamp,
`TIME`, and `GEO (Codes)` / `GEO (Labels)` headers. The grain is exactly
`(geo_code, time_period)`; data values must be finite and non-negative.

The output retains source metadata, controlled filters, content SHA-256,
observations, missing-value and flag counts, and `MAPPED_NOT_EVIDENCE`.
The Eurostat special value `:` is retained as a missing observation, never
converted to zero or estimated; Eurostat documents this convention in its
[Data Browser format guide](https://ec.europa.eu/eurostat/web/user-guides/data-browser/download-data/available-formats).
Quality output distinguishes declared geographies, geographies with at least
one observation and geographies missing across every selected period.
Unknown dataset or filter, invalid timestamp/geography/value, missing headers,
duplicate grain, malformed archive, or failed preflight raises a contract
violation. It never derives a claim, estimates missing values, releases a
bundle, writes storage, evaluates licence scope, calls a network endpoint or
promotes a gate.

Country, NUTS1 and NUTS2 identifiers may coexist in the export. Each mapped
observation declares `geo_level`, and the output requires a later explicit
level selection before analysis. The mapper does not aggregate across levels.
`select_eurostat_geography_level` accepts only `COUNTRY`, `NUTS1` or `NUTS2`
and returns only that level with explicit coverage; it remains non-evidentiary.
