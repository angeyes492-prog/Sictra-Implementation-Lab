# Block 1 — Dossier workspace reader preflight v0.1

Date: 2026-09-06. Evidence class: local implementation and integration test.

Verified behaviors:

- unconfigured server reports an explicit empty reader;
- configured server lists one integrity-verified dossier;
- detail preserves literal facts, empty interpretation and editorial
  `BLOCKED` state;
- unknown identity and invalid configuration reject;
- post-start ledger mutation produces HTTP `500`, health
  `INTEGRITY_ERROR`, and no fixture fallback;
- JavaScript syntax check passes;
- browser inspection confirms the Dossiers view separates signed facts,
  absent interpretation and editorial blocking.
- full local regression passes: 265/265 tests.

Limitations: the displayed dossier is a synthetic two-release integration
fixture. No retained real delta exists, the ordinary launcher does not yet
configure keys/store, and exact-SHA CI is pending for this increment.
