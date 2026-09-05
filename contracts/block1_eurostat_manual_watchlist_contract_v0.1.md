# Contract — Eurostat manual watchlist v0.1

Producer: `sictra_block1.eurostat_maritime_delta`. Consumer: future governed
watchlist orchestration. Scope: `BLOCK1_EUROSTAT_MARITIME_MANUAL_WATCHLIST`.
Authority: deterministic comparison only.

Inputs are two workbook filename/byte pairs and exactly one `COUNTRY`, `NUTS1`
or `NUTS2` selection. Both workbooks must independently pass the current
mapper. Identical content is a valid no-change result. Different content must
have a strictly newer `Last updated` value in the current workbook; equal-time
content drift and temporal regression are rejected.

The comparison grain remains `(geo_code, time_period)`. Output preserves both
file hashes and release timestamps, selected coverage snapshots and an ordered
change list. Change types are `ADDED_OBSERVATION`, `REMOVED_OBSERVATION`,
`VALUE_CHANGED` and `FLAG_CHANGED`. A value delta is emitted only when both
values exist; percentages, interpolation and cross-level totals are forbidden.

All outputs carry `NOT_EVIDENCE`. The comparator does not attest source state,
prove causality, derive an insight, persist a checkpoint, schedule collection,
notify a user or promote a gate. Invalid source versions or ambiguous input
raise `EurostatMaritimeDeltaViolation` without partial output.
