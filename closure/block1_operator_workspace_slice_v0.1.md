# Block 1 — Local operator workspace slice v0.1

## Gate and status

`LOCAL_OPERATOR_WORKSPACE_SLICE`: `YELLOW`. A non-technical launcher can now
initialize and reopen the signed dossier reader without command-line key
handling, but backup/restore and a retained real delta remain incomplete.

## Evidence, blockers and next reassessment

- Contract/architecture/preflight:
  `block1_operator_workspace_contract_v0.1.md`,
  `block1_operator_workspace_v0.1.md`, and
  `evidence/block1_operator_workspace_preflight_v0.1.md`.
- Focused tests: 20/20; full regression: 268/268. Exact SHA and CI: pending for
  this increment.
- `YELLOW / B`: data/key backup boundary and restore exercise are absent.
- `INSUFFICIENT EVIDENCE / A`: no second real Eurostat release has generated a
  retained operator dossier.
- `INSUFFICIENT EVIDENCE / B`: local key files are integrity material, not a
  production secret manager or proven Windows ACL boundary.

Reassess after full regression and CI, then after a data backup/restore test.
