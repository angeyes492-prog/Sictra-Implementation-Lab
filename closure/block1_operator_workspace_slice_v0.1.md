# Block 1 — Local operator workspace slice v0.1

## Gate and status

`LOCAL_OPERATOR_WORKSPACE_SLICE`: `YELLOW`. A non-technical launcher can now
initialize and reopen the signed dossier reader without command-line key
handling. Data-only local backup/restore is verified; a retained real delta and
disaster/key recovery remain incomplete.

## Evidence, blockers and next reassessment

- Contract/architecture/preflight:
  `block1_operator_workspace_contract_v0.1.md`,
  `block1_operator_workspace_v0.1.md`, and
  `evidence/block1_operator_workspace_preflight_v0.1.md`.
- Focused tests: 22/22; full regression: 270/270. Startup/key configuration SHA
  `7849ac66aff882c180b62ea7ffa4473688ea5f3d`, CI #348 success. Data-backup SHA
  `1458fc0d1618c62f3f6ef16663d177b88e48d01f`, CI #350 success.
- `VERIFIED / B`: data-only backup/restore detects tamper, preserves original
  keys and refuses overwrite. It is local accidental-loss recovery only.
- `INSUFFICIENT EVIDENCE / A`: no second real Eurostat release has generated a
  retained operator dossier.
- `INSUFFICIENT EVIDENCE / B`: local key files are integrity material, not a
  production secret manager or proven Windows ACL boundary.

Reassess after full regression and CI, then after a retained real delta; key or
off-device disaster recovery belongs to a later operating-plane gate.
