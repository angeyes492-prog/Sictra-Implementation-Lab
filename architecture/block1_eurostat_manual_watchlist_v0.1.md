# Block 1 — Eurostat manual watchlist v0.1

`IMPLEMENTED CANDIDATE / LOCAL-TESTED / B`. This Layer 7 component compares
two operator-supplied releases of the bounded Eurostat maritime workbook at one
explicit geography level. It detects source release change, value/flag change,
new observations and observations no longer published. It performs no network
fetch, scheduling, aggregation, imputation, trend interpretation or alert
delivery.

The same comparator accepts two fully revalidated manual bundles, allowing the
latest HMAC-ledger checkpoint to become the previous state without reopening
its original XLSX. It requires equal geography levels and non-regressive
manual observation time; both checkpoints remain non-evidentiary.

An identical file produces `IDENTICAL_FILE_NOT_EVIDENCE`. Different content
must declare a strictly newer source update; a changed file under the same
release timestamp or an older current release fails closed as source drift or
time regression. Detected differences remain
`DELTA_DETECTED_NOT_EVIDENCE` until both source states are separately bound,
attested and reviewed.

This manual comparator is the pilot precursor to a watchlist worker. Cadence,
rate limiting, retries, source acquisition, durable checkpoints, notifications
and kill switches remain separate operating-plane responsibilities.
