# Durable attested evidence store — Eurostat local preflight

## Result

`VERIFIED / B` for the local Layer 4 persistence boundary. The supplied
Eurostat workbook was assembled as the explicit `COUNTRY` selection, crossed a
gateway reconstructed from a durable local source-control record, and was
persisted as one signed `OBSERVED` record. A newly opened evidence store
recovered exactly one current runtime record.

| Field | Observed result |
| --- | --- |
| Workbook SHA-256 | `4d45ad8a11a49a1f79df57b845178d0e413483b4882200591f2f36b47c6dbeca` |
| Dataset / declared update | `tran_r_mago_nm` / `2026-03-15T23:00` |
| Explicit selection | `COUNTRY`; 125 observations |
| Control binding | `ACTIVE` |
| Evidence admission | `CURRENT` / `SOURCE_VERIFIED` |
| Reopen result | one current runtime record |
| Approval lineage | signed approval fingerprint matched the binding |
| Secret persistence | binding, gateway and store keys absent from both JSON stores |

The control and evidence stores, their keys and the resulting record existed
only in a temporary directory and were destroyed after this preflight. This is
therefore a reproducible local behavior test, not retained operational evidence
or a source admission decision.

## Adversarial and regression evidence

- Exact duplicate evidence is idempotent.
- A stale record remains historical but cannot be supplied to runtime.
- Re-signed bad content hash, binding lineage, provenance or bundle content
  fails before a file is created.
- On-disk mutation, wrong evidence key, integrity-key/configuration drift,
  capacity exhaustion and injected failure before atomic replacement fail
  closed; the prior file remains byte-identical on the injected failure path.
- Focused attested-evidence, source-control and gateway suite: 18 tests,
  `OK`.
- Runtime suite: 67 tests, `OK`; all remaining repository modules: 183 tests,
  `OK`; total 250/250 locally on 2026-09-06.

## Boundary

The HMAC record proves only the configured local process preserved a record
that was valid when admitted. It neither proves external source truth,
license, reviewer identity, independent corroboration, current real-world
conditions nor production readiness. There is no KMS, encryption, retention,
backup/restore, scheduler, cross-process writer control or independent review.
