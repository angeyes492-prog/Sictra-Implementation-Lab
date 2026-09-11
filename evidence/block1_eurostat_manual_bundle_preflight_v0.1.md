# Eurostat manual bundle assembly — local preflight

## Scope and state

`VERIFIED / B` for deterministic local assembly only. This is not an
attestation, a source admission, a factual claim, a durable evidence record or
a gate decision.

## Input identity

| Field | Value |
| --- | --- |
| Local filename | `tran_r_mago_nm$defaultview_spreadsheet (1).xlsx` |
| Source-file SHA-256 | `4d45ad8a11a49a1f79df57b845178d0e413483b4882200591f2f36b47c6dbeca` |
| Dataset | `tran_r_mago_nm`, annual `FR_LD_NLD`, `THS_T` |
| Declared source update | `2026-03-15T23:00` |
| Explicit test selection | `COUNTRY` |
| Controlled test URL | `https://ec.europa.eu/eurostat/databrowser/view/tran_r_mago_nm/default/table?lang=en` |

The controlled URL identifies the bounded dataset route used to exercise the
contract; this record does not independently prove the browser download origin
of the local file.

## Local result

`build_eurostat_manual_bundle` produced exactly the seven gateway fields and a
canonical UTF-8 content payload of 17,733 bytes, below the 131,072-byte
governed limit. Its serialized content records the file hash, controlled
filters, declared update, `COUNTRY` coverage and observations. It contains
`UNATTESTED_MANUAL_BUNDLE`; it has no `attestation` field.

## Validation

- Eurostat mapper and bundle tests: 13 tests, `OK`.
- Full repository suite split at the terminal boundary: runtime group 67 tests,
  `OK`; all other groups 157 tests, `OK`; total 224/224, executed locally on
  2026-09-05.
- Adversarial checks reject non-HTTPS URLs, URLs outside the named dataset,
  credentials in URLs, boolean time values, malformed correlation IDs and an
  unsupported geography level.

## Boundary and next blocker

The output cannot pass through the source gateway until a current matching
`BOUND` registration and signed binding are independently configured. Even
then, a future attestation must be durably recorded and independently reviewed
before it can support runtime facts or an editorial brief. No such binding,
attestation, persistence or review was created here.
