# Eurostat workbook preflight — `tran_r_mago_nm`

| Field | Observation |
| --- | --- |
| Input filename | `tran_r_mago_nm$defaultview_spreadsheet (1).xlsx` |
| Source identity declared by workbook | Eurostat / ESTAT |
| Dataset declared by workbook | `tran_r_mago_nm$defaultview` |
| Declared measurement | `Freight loaded and unloaded [FR_LD_NLD]` |
| Declared unit | `Thousand tonnes [THS_T]` |
| Declared time columns | 2020–2024 |
| Preflight SHA-256 | `4d45ad8a11a49a1f79df57b845178d0e413483b4882200591f2f36b47c6dbeca` |
| Preflight result | `READY_FOR_SCHEMA_REVIEW` |
| Evidence state | `NOT_EVIDENCE` |

The local preflight found a structurally tabular XLSX with 268 rows containing
at least two non-empty cells. This is only a structural count: the workbook
also contains extraction metadata and filter rows, so it is not treated as a
validated count of observations.

The workbook's own extraction marker reads `05/09/2026 06:14:51`. Its temporal
meaning, currentness and compatibility with the operational clock remain
`UNCONFIRMED`; no claim has been generated from its values.

Next control: a schema mapper must identify the actual header and observation
rows, preserve all filter metadata, validate geography codes, years, units and
missing-value markers, and then submit a bounded manual bundle through a signed
Eurostat binding. This artifact neither binds Eurostat nor imports the workbook
into the runtime.
