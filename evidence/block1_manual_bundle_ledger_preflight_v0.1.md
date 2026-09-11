# Manual bundle ledger — local preflight

## Scope and result

`VERIFIED / B` for the local, HMAC-chained persistence boundary only. The
result is a durable **un-attested** bundle receipt, not a source attestation,
admitted observation, factual claim, editorial output or gate change.

| Field | Value |
| --- | --- |
| Input file SHA-256 | `4d45ad8a11a49a1f79df57b845178d0e413483b4882200591f2f36b47c6dbeca` |
| Explicit selection | `COUNTRY` |
| Recorded bundle SHA-256 | `e30fae35d0926b7cf4a14fb5316c84fcfbae5898bda1cbdcebab06ed0175cbed` |
| Receipt status | `RECORDED_UNATTESTED_NOT_EVIDENCE` |
| Receipt evidence state | `NOT_EVIDENCE` |
| Temporary ledger entries | 1 |

The controlled Eurostat dataset URL was used only to satisfy the bounded local
contract. The temporary ledger was deleted after the exercise; no external
upload, source binding, content attestation or persistent operator dataset was
created.

## Checks

- Exact replay returns the original receipt and does not extend the chain.
- Mutation of bundle content, record hash, predecessor, ledger schema or key
  configuration fails closed on read.
- Invalid URL, unsupported source/state, altered gateway fields, capacity
  exhaustion, duplicate entry identity and logical-time regression fail closed.
- Full local suite: runtime group 67 tests `OK`; remaining group 161 tests
  `OK`; 228/228 on 2026-09-05.

## Remaining boundary

The integrity key is local reference material, not a KMS or durable identity.
The ledger offers no encryption, retention, backup, restore, authentication or
cross-process concurrency. A future current `BOUND` registration and signed
gateway attestation remain necessary before any record can become `OBSERVED`
evidence; independent review remains necessary before operational use.
