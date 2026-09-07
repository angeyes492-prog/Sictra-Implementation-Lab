# Intelligence dossier — local preflight v0.1

## Result

`VERIFIED / B` for the deterministic local dossier boundary. A synthetic but
contract-valid sequence of two separately attested Eurostat-shaped releases
produced a review-required watchlist delta with two changed observations. That
signed bridge result generated two literal facts and no interpretations or hypotheses.
The dossier remained `REQUIRES_HUMAN_INTERPRETATION` and publication `BLOCKED`.

The dossier store persisted, reopened and replayed the result idempotently.
Returned data was defensive. Broken delta linkage, non-delta input, malformed
configuration, wrong integrity key, on-disk dossier mutation and injected
atomic-replacement failure all failed closed; an injected write failure
preserved the prior bytes.

## Boundary

This test proves schema separation and local retention, not the factual truth
of the synthetic change, independent corroboration, causal interpretation,
company impact, editorial readiness or publication authority. The supplied
real Eurostat workbook currently provides only one retained-reference release,
so no real two-release dossier is claimed.

## Validation

- Focused dossier/watchlist integration group: 12 tests, `OK`.
- Full local regression: 195 general tests plus 67 runtime tests; 262/262,
  `OK` on 2026-09-06.
- Exact-SHA CI must be recorded after this increment is committed; until then
  this artifact is local evidence only.
