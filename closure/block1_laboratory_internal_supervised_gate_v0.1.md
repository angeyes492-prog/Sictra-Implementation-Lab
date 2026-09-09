# Block 1 Intelligence — Laboratory internal supervised gate v0.1

## Gate

`LABORATORY_INTERNAL_SUPERVISED`

## Status

`YELLOW / TECHNICAL CLOSURE CANDIDATE`.

The candidate becomes admissible only if the CI run on the exact commit that
contains this ledger succeeds. It does not supersede the historic production
or independent-review gate.

## Evidence

- Exact operator chain: source binding, controlled XLSX preflight, gateway
  attestation, durable evidence, E01–E08, watchlist, dossier boundary and UI.
- Real local baseline receipt:
  `evidence/block1_eurostat_operator_baseline_2026-09-07.md`.
- Synthetic second-release integration test proves the delta → literal-fact
  dossier path while keeping interpretation/publication blocked.
- Backup/restore test proves data-only recovery under original local keys.
- Source Master Registry exposes 18 candidates with `PROPOSED` status,
  explicit license/access/revision fields, and `admissible_source_count=0`.
  It has no network acquisition or automatic import path.

## Test

`python -m unittest discover -s tests -q`: 279 tests passed locally. CI #362
passed on the preceding source-registry SHA
`2becf73806e5ae72bad6e747283b1850cfe37c79`; CI on the exact final preflight
SHA is still required before it becomes closure evidence.

## Remaining limitations and promotion boundary

- A second real newer workbook is still required before a real delta/dossier
  can exist. `AWAIT_NEWER_SOURCE` is correct, not a failure.
- A second independent root and human interpretation remain mandatory before
  any editorial candidate could become ready.
- Independent review is deferred and is not represented as completed.
- The system remains local, single-user, manual-input and network-disabled.
  It is neither production security nor an operating system for Blocks 2–4.
