# Eurostat maritime mapping profile — `tran_r_mago_nm`

| Field | Result |
| --- | --- |
| Input identity | `tran_r_mago_nm$defaultview_spreadsheet (1).xlsx` |
| Content SHA-256 | `4d45ad8a11a49a1f79df57b845178d0e413483b4882200591f2f36b47c6dbeca` |
| Dataset and filter | `tran_r_mago_nm`; annual `FR_LD_NLD`; `THS_T` |
| Declared last update | `2026-09-05T06:14` |
| Output state | `MAPPED_NOT_EVIDENCE` / `REQUIRES_GEO_LEVEL_SELECTION` |
| Observation grain | `geo_code × time_period` |
| Years | 2020–2024 |

## Quality profile

| Check | Result | Interpretation |
| --- | --- | --- |
| Declared geographies | 253 | Includes rows with no available values. |
| Geographies with observations | 231 | 22 geographies have no values in any selected year. |
| Geography levels | 25 `COUNTRY`, 76 `NUTS1`, 152 `NUTS2` | The export has mixed geographic grain. |
| Numeric observations | 1,130 | No duplicate `(geo_code, year)` keys after mapping. |
| Missing cells | 135 of 1,265 (10.7%) | Eurostat `:` values preserved as missing, never zero-filled. |
| Missing by year | 2020: 29; 2021: 27; 2022: 27; 2023: 25; 2024: 27 | Missingness is present across the full selected period. |
| Publication flags | 0 | No flag values were present in this export. |
| End legend | 2 rows | Separately recognized and excluded from geographic observations. |

## Explicit level-selection coverage

| Selected level | Declared geographies | Observed geographies | Missing cells | Coverage implication |
| --- | ---: | ---: | ---: | --- |
| `COUNTRY` | 25 | 25 | 0 / 125 | Complete for the selected 2020–2024 table. |
| `NUTS1` | 76 | 70 | 37 / 380 | Six geographies have no values in any selected year. |
| `NUTS2` | 152 | 136 | 98 / 760 | Sixteen geographies have no values in any selected year. |

These profiles are selectable alternatives, not comparable totals and not an
automatic recommendation. The operator must choose the geographic question
before analysis or an editorial brief proceeds.

## Findings and decision boundary

1. `VERIFIED / B` — the local mapper accepted the workbook only after exact
   dataset, frequency, measure, unit, header, numeric-range and uniqueness
   checks.
2. `HIGH / B` analytical risk — country, NUTS1 and NUTS2 rows cannot be summed
   or compared in a single series. A downstream operator must select one level;
   the mapper refuses to choose or aggregate it automatically.
3. `MEDIUM / B` coverage risk — missing values and fully missing geographies
   can bias a regional comparison if they are silently omitted. Any dashboard
   must display coverage and exclude unsupported comparisons.
4. `INSUFFICIENT EVIDENCE / A` — this mapping does not create a source binding,
   evidence attestation, factual claim, insight, editorial output or gate
   promotion.

## Next controlled action

Implement explicit geography-level selection and a coverage report. Only after
that selection, a matching signed source binding and an independent review may
a compact manual evidence bundle be assembled. The Eurostat special-value
convention is documented in its [Data Browser format guide](https://ec.europa.eu/eurostat/web/user-guides/data-browser/download-data/available-formats).
