# Bloque 1 Intelligence — Source Governance Slice v0.1

## Gate

`SOURCE_GOVERNANCE_LOCAL_SLICE`

## Status

`YELLOW` — implementación y CI verificadas para el alcance local; no
promovible a fuente real ni a cierre global.

## Evidence

- SHA canónico de implementación: `829f5a3e4a096da16dcb53af47fcbe6ae81a5563`.
- `evidence/ci-run-33325016910.json`: GitHub Actions run `33325016910`
  (`#197`), terminado en `success` sobre ese SHA exacto.
- Ejecución local del mismo estado: 181 pruebas, 0 fallos, 0 errores.
- El binding HMAC exige coincidencia exacta de identidad, scope, hosts,
  claims, límite de bytes y `MANUAL_SOURCE_BUNDLE`; la aprobación rechazada,
  futura o incongruente falla cerrada.

## Test

- `PYTHONPATH=src python -m unittest discover -s tests -q` — 181 pruebas,
  resultado `OK`, ejecutado localmente el 2026-08-30.
- CI #197: pruebas del repositorio, manifest local acotado y runtime de
  referencia de ocho motores, todos `success`.
- Red-team contractual: binding ausente, vencido o alterado; aprobación
  rechazada/futura/incongruente; host/IP/puerto/claim/tiempo inválidos; y
  adquisición de red rechazada.

## Date

2026-08-30.

## Version

`block1_source_gateway_contract_v0.1`; slice de implementación v0.1.

## Dependencies

- Arquitectura: `architecture/block1_source_portfolio_v0.1.md`
- Contrato: `contracts/block1_source_gateway_contract_v0.1.md`
- Implementación: `src/sictra_block1/source_gateway.py`
- Pruebas: `tests/test_block1_source_gateway.py`,
  `tests/test_block1_source_portfolio.py`, `tests/test_block1_lab_web.py`
- Revisión propuesta: PR #10 (permanece draft).

## Contradictions and blockers

1. `INSUFFICIENT EVIDENCE / A` — no existe una fuente real `BOUND`, ni
   evidencia de términos, licencia o acceso real aprobada por una persona.
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

Pruebas y revisión adversarial: Codex. CI: GitHub Actions #197. Revisión
independiente humana: pendiente.

## Next reassessment

Tras una revisión humana independiente de PR #10 y un registro real,
aprobado y firmado para una fuente, manteniendo el SHA/CI correspondiente.

## Non-claims

Este ledger no declara una fuente como verdadera, licenciada, actual o
admisible; tampoco declara ingesta de Internet, producción, aceptación global,
ni operación integrada de los Bloques 2–4.
