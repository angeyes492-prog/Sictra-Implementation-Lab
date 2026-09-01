# Bloque 2 E01–E08 — Gate ledger runtime acotado v0.1

| GATE | STATUS | EVIDENCE | TEST | DATE | VERSION | DEPENDENCIES | CONTRADICTIONS | CONFIDENCE | REVIEWER/VALIDATOR | NEXT REASSESSMENT |
|---|---|---|---|---|---|---|---|---|---|---|
| Contratos E05–E08 | YELLOW | contratos candidatos v0.1 | 18 vectores nuevos | 2026-08-30 | 0.1 | MAR/rights reales | sin aceptación común | B | autor/oráculo E07 local | review independiente |
| Runtime E01–E08 local | YELLOW | CLI completo + hash | 83/83 Block 2 | 2026-08-30 | 0.1 | selección y validación externas sintéticas | no SHA/CI | B | suite local | bind a GitHub SHA |
| Regresión workspace | GREEN local | salida unittest | 292/292 | 2026-08-30 | workspace | entorno local | no CI externa | A local | unittest | reproducir en CI |
| Producción HTML/SVG | YELLOW | candidatos deterministas | escape, checksum, accesibilidad | 2026-08-30 | 0.1 | browsers/clientes reales | sin visual regression | B | tests locales | golden/render audit |
| Evaluación E07 | YELLOW | rúbrica + oráculo separado | pass/revise/block/self-review | 2026-08-30 | 0.1 | observadores reales | fixture sintético | B | oráculo local | evaluación independiente |
| Memoria E08 | YELLOW | store append-only | idempotencia/collision/deprecación | 2026-08-30 | 0.1 | persistencia gobernada | memoria volátil | B | tests locales | durable store + poisoning |
| Integración GitHub/CI | RED | `HEAD` inexistente | no ejecutable remoto ligado | 2026-08-30 | N/A | rama/commit/CI | repo local sin revisión | A | git local | crear baseline coherente |
| Aceptación global Bloque 2 | YELLOW | evidencia parcial local | no gate humano | 2026-08-30 | N/A | todos los anteriores | aceptación no demostrada | B | pendiente | MAR + aceptación humana |

## Reassessment — 2026-08-31

Las filas anteriores conservan el checkpoint histórico de 2026-08-30. El
estado actual resuelve el blocker GitHub/CI: PR #11 es mergeable; CI runs
`33464431457` sobre `6c3adb1…` y `33464751434` sobre `157b59f…` concluyeron
`success`; la regresión reconciliada es 449/449 y el subconjunto Bloque 2 es
161/161. Por tanto, `Integración GitHub/CI` pasa de `RED` histórico a
`GREEN HOSTED` para esos SHA exactos.

No se promueven las demás filas: provider real, ensayo perceptual, revisión
independiente, MAR y aceptación humana siguen separados y pendientes.

## Regla de promoción

`LOCAL EXECUTION != INTEGRATED != INDEPENDENTLY VALIDATED != ACCEPTED`.
Ningún resultado de este ledger publica contenido ni promueve el gate global.
