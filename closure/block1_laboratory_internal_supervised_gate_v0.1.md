# Block 1 Intelligence — Laboratory internal supervised gate v0.1

## Gate

`LABORATORY_INTERNAL_SUPERVISED`

## Status

`YELLOW / TECHNICAL IMPLEMENTATION COMPLETE / HUMAN APPROVAL PENDING`.

All locally executable acceptance conditions are complete. The gate remains
`YELLOW` because independent human review and the owner's final supervised-use
approval are deliberately external. It does not supersede the production or
independent-review gate.

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

`PYTHONPATH=src python -m unittest discover -s tests -q`: 282 tests passed
locally. GitHub Actions runs `34303522368` and `34303518680` both succeeded on
the exact implementation SHA `e73cc427f7dd55983916cbe5b06cc59624fe45da`.
The commit containing this ledger must also pass the same workflow; that
external check is the final machine condition and does not require a document
rewrite after it succeeds.

## Remaining limitations and promotion boundary

- A second real newer workbook is required only to create a real delta/dossier
  during later operation. `AWAIT_NEWER_SOURCE` is a valid terminal state and
  is not a technical closure blocker.
- A second independent root and human interpretation remain mandatory before
  a particular editorial candidate can become ready; the laboratory correctly
  abstains without them.
- Independent review and the owner's final supervised-use approval are the
  only remaining gate conditions and are not represented as completed.
- The system remains local, single-user, manual-input and network-disabled.
  It is neither production security nor an operating system for Blocks 2–4.
