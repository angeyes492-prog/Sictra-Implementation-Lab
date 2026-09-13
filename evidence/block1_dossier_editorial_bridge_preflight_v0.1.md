# Dossier to editorial bridge — local preflight v0.1

## Result

`VERIFIED / B` for conservative local composition. An integrity-verified
durable dossier was converted into the existing editorial candidate schema.
The candidate retained its one Eurostat source root, literal fact, limitations
and executive question, while declaring two required independent roots,
freshness/red-team/stability unknown and uncertainty 100.

The editorial engine assessed it `RESEARCH_NEEDED` and `BLOCKED`, including
`INSUFFICIENT_INDEPENDENT_ROOTS` and `MATERIAL_UNCERTAINTY`. The bridge returned
no handoff and publication remained `BLOCKED`. Unknown dossier identity and an
on-disk dossier mutation failed closed.

## Boundary

This proves that a durable dossier can enter editorial evaluation without
escaping its evidence limitations. It does not create a reviewed candidate,
independent corroboration, interpretation, shortlist, selection, Block 2
handoff or publication authority.

## Validation

- Focused dossier/editorial path: 21 tests, `OK` after signed bridge lineage
  was added.
- Full local regression: 195 general tests plus 67 runtime tests; 262/262,
  `OK` on 2026-09-06.
- Exact-SHA CI remains required for this increment.
