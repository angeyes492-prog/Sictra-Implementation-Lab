# Bloque 1 Intelligence — Source Governance Slice v0.1

## Gate

`SOURCE_GOVERNANCE_LOCAL_SLICE`

## Status

`YELLOW` — implementación y CI verificadas para el alcance local; no
promovible a fuente real ni a cierre global.

## Evidence

- `evidence/block1_source_control_store_preflight_v0.1.md`: durable local
  registration/approval/binding reconstruction and one ephemeral observed
  Eurostat record, with no secret persisted; 245/245 local tests.
- `evidence/block1_source_binding_approval_lineage_v0.1.md`: repair `HIGH`
  linking each signed source binding and observed record to the exact
  normalized human approval; 240/240 local tests.
- SHA del incremento de ensamblaje manual Eurostat:
  `24fabd68bf5b3511d2c415c137b8ff4f8ccd05aa`.
- `evidence/ci-run-33992985995.json`: GitHub Actions run `33992985995`
  (`#314`), terminado en `success` sobre ese SHA exacto. Valida el
  ensamblaje local no atestado; no vincula una fuente ni promueve el gate.
- `evidence/block1_eurostat_manual_bundle_preflight_v0.1.md`: perfil local
  reproducible del archivo aportado y su selección `COUNTRY`, con hash,
  cobertura, límite de bytes y límites de no-evidencia explícitos.
- SHA canónico del incremento de implementación Eurostat: `844f16c15ed855e150ae7de0a6ec58ba63a8d881`.
- `evidence/ci-run-33943023301.json`: GitHub Actions run `33943023301`
  (`#298`), terminado en `success` sobre ese SHA exacto. Verifica que el
  candidato marítimo de Eurostat sigue bloqueado mientras sea `PROPOSED`.
- `evidence/block1_source_dossier_eurostat_maritime_v0.1.md`: dossier con
  términos oficiales, alcance `tran_r_mago_nm`, exclusiones y el límite de
  admisión; no es una autorización ni una ingesta.
- `evidence/ci-run-33325180999.json`: GitHub Actions run `33325180999`
  (`#201`), terminado en `success` sobre ese SHA exacto.
- `evidence/ci-run-33325016910.json`: antecedente verificable de la
  vinculación del método de acceso, CI #197 sobre `829f5a3`.
- Ejecución local del current source-governance state: 245 pruebas, 0 fallos,
  0 errores.
- El binding HMAC exige coincidencia exacta de identidad, scope, hosts,
  claims, límite de bytes y `MANUAL_SOURCE_BUNDLE`; la aprobación rechazada,
  futura o incongruente falla cerrada. Los campos temporales booleanos se
  rechazan aunque vengan firmados.

## Test

- Suite local dividida por límite del terminal: grupo runtime 67 pruebas,
  `OK`; todos los demás grupos 157 pruebas, `OK`; 224/224 el 2026-09-05.
- `tests/test_block1_eurostat_maritime_draft.py` — la propuesta de Eurostat
  declara host, límite, método y claims acotados, pero falla cerrada ante todo
  intento de atestar un bundle mientras su estado sea `PROPOSED`.
- CI #197: pruebas del repositorio, manifest local acotado y runtime de
  referencia de ocho motores, todos `success`.
- Red-team contractual: binding ausente, vencido o alterado; aprobación
  rechazada/futura/incongruente; host/IP/puerto/claim/tiempo inválidos; y
  adquisición de red rechazada. Incluye la mutación de un `issued_at=True`
  con HMAC recalculado.

## Date

2026-08-30.

## Version

`block1_source_gateway_contract_v0.1`; slice de implementación v0.1.

## Dependencies

- Arquitectura: `architecture/block1_source_portfolio_v0.1.md`
- Contrato: `contracts/block1_source_gateway_contract_v0.1.md`
- Implementación: `src/sictra_block1/source_gateway.py`
- Pruebas: `tests/test_block1_source_gateway.py`,
  `tests/test_block1_source_portfolio.py`,
  `tests/test_block1_eurostat_maritime_draft.py`,
  `tests/test_block1_lab_web.py`
- Revisión propuesta: PR #10 (permanece draft).

## Contradictions and blockers

1. `INSUFFICIENT EVIDENCE / A` — no existe una fuente real `BOUND` en el
   runtime, ni binding vigente configurado con una clave de producción. El
   registro acotado del owner y el dossier describen la decisión local, pero
   no sustituyen esa configuración ni una atestación durable.
2. `INSUFFICIENT EVIDENCE / A` — la clave HMAC y el reviewer son mecanismos
   locales de referencia, no identidad de producción ni KMS.
3. `INSUFFICIENT EVIDENCE / A` — falta revisión humana independiente sobre
   este SHA o uno posterior; la revisión adversarial de Codex no es
   independiente.
4. `VERIFIED / A` — el gateway no tiene cliente HTTP, scraper, credenciales
   ni scheduler; por diseño no puede investigar Internet por sí mismo.

## Confidence

- Contrato y comportamiento local: `VERIFIED / B`.
- Ejecución CI sobre SHA exacto: `VERIFIED / A` para los pasos observados.
- Preparación para fuentes reales: `INSUFFICIENT EVIDENCE / A`.
- Gate local: `YELLOW / B`.

## Reviewer / validator

Pruebas y revisión adversarial: Codex. CI: GitHub Actions #314 sobre
`24fabd68bf5b3511d2c415c137b8ff4f8ccd05aa` (y #298/#197 como antecedentes).
Revisión
independiente humana: pendiente.

## Next reassessment

Tras una revisión humana independiente de PR #10 y un registro real,
aprobado y firmado para una fuente, manteniendo el SHA/CI correspondiente.

## Non-claims

Este ledger no declara una fuente como verdadera, licenciada, actual o
admisible; tampoco declara ingesta de Internet, producción, aceptación global,
ni operación integrada de los Bloques 2–4.
