# Bloque 1 — Contrato de UI de laboratorio interno v0.1

> **SUPERSEDED:** `block1_logistics_workspace_contract_v0.1.md` reemplaza la
> superficie visual y conserva los cuatro escenarios como Validation Deck.
> Este archivo permanece como evidencia histórica del laboratorio aislado.

## Identidad y alcance

- Productor: servidor local `sictra_block1.lab_web`.
- Consumidor: navegador en la misma computadora.
- Versión: `0.1`.
- Alcance: `BLOCK1_LOCAL_INTERACTIVE_LAB_UI`.
- Autoridad: no concede autoridad de runtime, arquitectura ni gate.

## Superficie aceptada

| Método | Ruta | Resultado |
| --- | --- | --- |
| `GET` | `/` | Página HTML local. |
| `GET` | `/health` | `{"status":"ok","scope":"BLOCK1_LOCAL_INTERACTIVE_LAB_UI"}`. |
| `POST` | `/api/scenarios/{scenario}` | Reporte del laboratorio y resumen humano. |

`{scenario}` solo puede ser `valid`, `missing-authority`, `stale-evidence` o
`wrong-scope`. Cualquier otra ruta o escenario se rechaza con `404` y JSON.

## Respuesta de escenario

La respuesta tiene `scope`, `scenario`, `summary` y `report`. `summary.status`
solo puede describir `COMMITTED`, `BLOCKED_CORRECTLY` o `UNEXPECTED` y se
deriva de `report.result.enforcement.status` y `report.memory_record_count`.

## Límites y no-claims

- El servidor escucha exclusivamente en `127.0.0.1`.
- No acepta fuentes, secretos, rutas, tareas, runs ni configuración de runtime.
- El reporte usa el almacén efímero del laboratorio.
- No hay autenticación, red, datos reales, HubSpot, envío, persistencia,
  aceptación de gate ni operación de producción.

## Error y compatibilidad

Errores de rutas, método o escenario devuelven JSON con `error`. Una excepción
interna devuelve `500`, sin convertirla en un bloqueo correcto. La UI v0.1 no
promete compatibilidad para endpoints distintos de los enumerados.
