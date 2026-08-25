# Dossiers ejecutables E01–E08 v0.2

Estado común: `IMPLEMENTED IN REFERENCE RUNTIME`; aceptación global no reclamada.

## E01 — Agent Engine

- Input: objetivo y fuentes candidatas.
- Output: petición trazable.
- Invariante: coordina; no evalúa, promueve ni autoriza.
- Ambigüedad: el Slack E01 reciente pertenece a Bloque 2; no se importó.

## E02 — Knowledge Acquisition

- Input: fuentes candidatas.
- Output: evidencia adquirida + rechazos explícitos.
- Invariantes: identidad/procedencia/tiempo preservados; gaps no se improvisan.

## E03 — Practice / Experiment

- Input: evidencia y objetivo.
- Output: execution status + outcome reproducible.
- Invariante: `COMPLETED != VALIDATED`.

## E04 — Integration

- Input: sobre y consumidor esperado.
- Output: routing auditado, duplicate o rechazo.
- Invariantes: idempotencia; collision rechazada; no scheduling ni autoridad.

## E05 — Evaluation / Red Team

- Input: evidencia de ejecución.
- Output: assessment, contradicciones, independencia y limitaciones.
- Invariante: assessment no es autorización.

## E06 — Memory / Learning

- Input: assessment.
- Output: versión candidata persistida en memoria del proceso.
- Invariantes: historial aditivo; `stored != promoted`; índice no es verdad.

## E07 — Stability

- Input: assessment + observaciones.
- Output: health y control mode separados.
- Invariantes: ausencia/contradicción no promueve STABLE; acción no prueba recovery.

## E08 — Orchestrator / Governance

- Input: assessment, stability y authority context.
- Output: `ALLOW_REFERENCE_ACTION`, `REVALIDATE` o `QUARANTINE`.
- Invariantes: scope/epoch/expiry/commit obligatorios; decision no prueba enforcement.

## Failure/recovery y rollback

El runtime no realiza efectos externos. Un fallo conserva el último sobre y su
lineage; reintento usa nueva identidad o duplicate idempotente. El rollback del
runtime de referencia consiste en retirar el commit/branch sin migración de
datos; E06 actual es deliberadamente in-memory y no pretende persistencia de
producción.
