# Block 1 — Eurostat maritime schema mapper v0.1

`IMPLEMENTED CANDIDATE / LOCAL-TESTED / B`. The mapper is the Layer 3 quality
control for one bounded asset: annual `tran_r_mago_nm` freight loaded and
unloaded, in thousand tonnes. It consumes only a preflighted XLSX byte payload
and has no filesystem, browser, network, persistence, binding or insight
authority.

It requires the workbook's dataset identifier, annual frequency, `FR_LD_NLD`
transport measure, `THS_T` unit, valid last-update value, `TIME` and `GEO`
headers, finite non-negative freight values, and unique `(geo_code, year)`
grain. It preserves numeric observations, Eurostat `:` special-value absences,
publication flags and end-of-table legends separately. Its result remains
`MAPPED_NOT_EVIDENCE` until a matching
source binding, manual-bundle attestation and independent review exist.

The export can contain `COUNTRY`, `NUTS1` and `NUTS2` rows together. The mapper
labels each level and returns `REQUIRES_GEO_LEVEL_SELECTION`; it never sums,
compares or selects across levels on its own.

The companion selection function accepts exactly one of those levels and
returns its coverage profile and observations as `SELECTED_NOT_EVIDENCE`. It
does not choose a default or create a cross-level aggregate.

Failure is explicit and recoverable: a changed export, unit, dataset, header,
geography, value or duplicate must be corrected or receive a new reviewed
mapper. The mapper does not silently coerce, aggregate, fill missing values or
deduplicate source data.
