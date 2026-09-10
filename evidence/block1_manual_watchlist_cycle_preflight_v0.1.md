# Durable manual watchlist cycle — local preflight

## Closure delta

`VERIFIED / B` for one local manual watchlist state machine. Baseline bundle,
derived delta and chain identity are now written atomically and every restart
recomputes the complete bundle and delta lineage before exposing state.

The supplied Eurostat workbook established one temporary `COUNTRY` baseline
with `BASELINE_ESTABLISHED_NOT_EVIDENCE`, zero changes and source-file SHA-256
`4d45ad8a11a49a1f79df57b845178d0e413483b4882200591f2f36b47c6dbeca`.
An exact replay returned `replay=true` and retained exactly one durable cycle.
The temporary state was removed after the exercise.

## Failure and recovery evidence

- A newer fixture release stores one exact recomputable delta and survives
  close/reopen.
- Corrupted stored delta, wrong integrity key and divergent capacity fail
  closed on read.
- An injected `OSError` immediately before atomic replacement leaves the
  previous checkpoint byte-identical and recoverable.
- Same-release data drift, source-time regression, manual-time regression,
  duplicate cycle identity and exhausted capacity do not advance state.
- Returned delta objects are defensive copies.

## Test

- Focused cycle/comparator/ledger suite: 15 tests, `OK`.
- Runtime group: 67 tests, `OK`.
- Remaining repository group: 172 tests, `OK`.
- Total: 239/239 tests on 2026-09-05.

## Boundary

All checkpoints and deltas remain `NOT_EVIDENCE`. There is no network fetch,
scheduler, alert delivery, durable identity/KMS, encryption, cross-process
locking, retention policy, independent human review or gate promotion.
