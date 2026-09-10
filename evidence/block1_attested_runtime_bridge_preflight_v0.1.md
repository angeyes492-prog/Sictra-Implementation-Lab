# Attested evidence to E01–E08 — Eurostat local preflight

## Result

`VERIFIED / B` for one bounded cross-layer handoff. The supplied Eurostat
workbook was mapped as `COUNTRY`, signed through a durable local source-control
and evidence-store sequence, reopened from the evidence store, then supplied
to E01–E08 only through `AttestedRuntimeBridge`.

| Field | Observed result |
| --- | --- |
| Workbook SHA-256 | `4d45ad8a11a49a1f79df57b845178d0e413483b4882200591f2f36b47c6dbeca` |
| Dataset / declared update | `tran_r_mago_nm` / `2026-03-15T23:00` |
| Durable evidence input after reopen | 1 `CURRENT` record |
| E02 / E03 evidence count | 1 / 1 |
| E05 assessment | `CANDIDATE` |
| E08/runtime enforcement | `COMMITTED` bounded local effect |
| Approval lineage | evidence approval fingerprint matched signed binding |
| Persisted secrets | absent from control, evidence and runtime artifacts |

`CANDIDATE` is not an accepted insight, source-truth judgment, editorial
output or publishing decision. `COMMITTED` identifies the existing local
runtime's bounded memory effect only; it does not promote a gate.

## Failure and test evidence

- No current evidence and a runtime/store clock mismatch reject before E01 and
  before a durable runtime effect.
- The bridge takes no caller-supplied source list; it reads only current,
  signature-verified records from the evidence ledger.
- Focused bridge plus evidence-store tests: 8 tests, `OK`.
- The real preflight used temporary stores and ephemeral local HMAC keys; all
  artifacts and keys were destroyed after the exercise.

## Boundary

This demonstrates one local, single-process integration path with a stable
shared clock. It does not demonstrate a retained operator run, independent
source review, source license acceptance, distributed clock behavior, KMS,
encryption, multi-user access, scheduler, editorial human review or corporate
operational readiness.
