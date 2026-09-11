# Bundle checkpoint integrity and watchlist bridge v0.1

## Closure delta

`HIGH / B` pre-repair risk: the ledger authenticated its outer record and
canonical JSON but did not prove that coverage, geography selection and
observations agreed internally. An intact HMAC chain could therefore preserve
a self-contradictory, caller-crafted un-attested bundle.

`VERIFIED / B` local repair: every read and write now revalidates exact
provenance fields, SHA-256 form, declared update time, controlled filters,
selection/grain/year domain, observation key uniqueness and numeric range, and
coverage arithmetic. Five adversarial internal mutations fail before the
ledger file is created.

## Durable watchlist bridge

The ledger now returns a defensive, revalidated latest bundle. The release
comparator accepts that checkpoint and a current bundle, checks geographic and
manual-time compatibility, and produces the same bounded delta schema without
requiring the original prior XLSX.

An execution using the supplied Eurostat workbook recorded a temporary
checkpoint, recovered it, and compared it against the same source bundle. It
returned `IDENTICAL_FILE_NOT_EVIDENCE`, zero changes, and preserved workbook
SHA-256
`4d45ad8a11a49a1f79df57b845178d0e413483b4882200591f2f36b47c6dbeca`.
The temporary ledger was removed after the exercise.

## Validation

- Focused ledger/bundle/watchlist suite: 13 tests, `OK`.
- Runtime suite: 67 tests, `OK`.
- Remaining repository suite: 167 tests, `OK` after repairing one flaky test
  oracle that regenerated timestamped ZIP bytes instead of reusing one source
  payload.
- Total: 234/234 tests, executed locally on 2026-09-05.

## Boundary

The checkpoint remains `NOT_EVIDENCE`; no source binding, attestation,
scheduler, notification or editorial promotion was created. Cross-process
locking, encryption, key management, retention and independent review remain
outside this local repair.
