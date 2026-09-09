# Bloque 1 Intelligence — Source Governance Slice v0.1

## Gate

`SOURCE_GOVERNANCE_LOCAL_SLICE`

## Status

`YELLOW` — una ruta local retenida de Eurostat está verificada para el alcance
de laboratorio; el registro ampliado conserva 18 candidatos sin promoverlos a
fuente real ni a cierre global.

## Evidence

- `evidence/block1_source_control_store_preflight_v0.1.md`: durable local
  registration/approval/binding reconstruction and one ephemeral observed
  Eurostat record, with no secret persisted; 245/245 local tests.
- `evidence/block1_attested_evidence_store_preflight_v0.1.md`: one real
  workbook bundle was signed by a locally reconstructed gateway, persisted,
  reopened and recovered as a current record; its temporary stores and keys
  were destroyed after the exercise. This demonstrates the local Layer 4
  boundary, not retained operational evidence.
- `evidence/block1_attested_runtime_bridge_preflight_v0.1.md`: recovered
  local evidence was the sole source input to a bounded E01–E08 run. Its
  local `COMMITTED` effect and `CANDIDATE` assessment are expressly
  non-promotional and were not retained after the temporary preflight.
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
- Ejecución local del current source-governance state: 279 pruebas, 0 fallos,
  0 errores.
- `docs/source_master_registry_v1.md`: 18 candidatos con rol propuesto,
  licencia/acceso/revisión explícitos, referencia oficial y cero admisibles.
  No añade conectores ni permisos de adquisición.
- El binding HMAC exige coincidencia exacta de identidad, scope, hosts,
  claims, límite de bytes y `MANUAL_SOURCE_BUNDLE`; la aprobación rechazada,
  futura o incongruente falla cerrada. Los campos temporales booleanos se
  rechazan aunque vengan firmados.

## Test

- Suite local actual: 279 pruebas, `OK`, el 2026-09-08. Incluye contrato y
  rechazo de rol/referencia del Source Master Registry.
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

2026-09-08.

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

1. `VERIFIED / B` — el pipeline local retiene una única ruta Eurostat `BOUND`
   bajo claves locales, con binding y evidencia actual verificables. Esto no
   habilita a ningún candidato del registro, no es una configuración de
   producción y no sustituye una revisión independiente.
2. `INSUFFICIENT EVIDENCE / A` — para los otros 17 candidatos faltan revisión
   de términos, approval record, allowlist, claims acotados y binding; una
   página pública o una API registrada no es autorización de reutilización.
3. `INSUFFICIENT EVIDENCE / A` — la clave HMAC y el reviewer son mecanismos
   locales de referencia, no identidad de producción ni KMS.
4. `INSUFFICIENT EVIDENCE / A` — falta revisión humana independiente sobre
   este SHA o uno posterior; la revisión adversarial de Codex no es
   independiente.
5. `VERIFIED / A` — el gateway no tiene cliente HTTP, scraper, credenciales
   ni scheduler; por diseño no puede investigar Internet por sí mismo.

## Confidence

- Contrato, persistencia y comportamiento local: `VERIFIED / B`.
- Ejecución CI sobre SHA exacto: `VERIFIED / A` para los pasos observados.
- Ruta Eurostat retenida: `VERIFIED / B`; preparación de los demás candidatos:
  `INSUFFICIENT EVIDENCE / A`.
- Gate local: `YELLOW / B`.

## Reviewer / validator

Pruebas y revisión adversarial: Codex. CI: GitHub Actions #314 sobre
`24fabd68bf5b3511d2c415c137b8ff4f8ccd05aa` (y #298/#197 como antecedentes).
Revisión
independiente humana: pendiente.

## Next reassessment

Tras una revisión independiente del SHA final y, para cualquier candidato
nuevo, una revisión de términos seguida de approval/binding y una comparación
de versión retenida. La revisión editorial humana solo aplica cuando exista
un dossier real con corroboración suficiente.

## Non-claims

Este ledger no declara una fuente como verdadera, licenciada, actual o
admisible; tampoco declara ingesta de Internet, producción, aceptación global,
ni operación integrada de los Bloques 2–4.
