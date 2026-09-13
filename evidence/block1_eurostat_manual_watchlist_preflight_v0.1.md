# Eurostat manual watchlist — local preflight

## Result

`VERIFIED / B` for deterministic local comparison. The supplied workbook was
compared with an exact byte-identical copy at `COUNTRY` level and returned
`IDENTICAL_FILE_NOT_EVIDENCE`, zero changes, and the preserved source release
time `2026-03-15T23:00`.

This result proves that an unchanged manual input does not generate a false
delta. It does not prove that the source has not changed online because the
component has no network acquisition or scheduler.

## Regression and adversarial evidence

- A newer synthetic release reports value changes, additions and removals at
  exact `(geo_code, time_period)` grain and emits absolute deltas only when
  both values exist.
- Changed content under the same source timestamp fails closed as release
  drift.
- An older current release fails closed as temporal regression.
- `ALL` or any non-controlled geography selection fails closed.
- Full local suite: runtime 67 tests `OK`; all remaining groups 164 tests
  `OK`; 231/231 on 2026-09-05.

## Boundary

Every result remains `NOT_EVIDENCE`. The comparator neither fetches nor
attests either release and cannot infer causality, business impact or editorial
priority. A watchlist pilot still requires a durable prior checkpoint, current
source binding, two separately attested states and operator review.
