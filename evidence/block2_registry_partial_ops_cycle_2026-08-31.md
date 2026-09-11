# Bloque 2 — Engine Registry, Resume parcial y Ops, ciclo local

> Fecha/contexto: `2026-08-31`, Python/SQLite/Edge local.  
> Certeza/confianza: `VERIFIED / A` para ejecución local y browser observado.  
> Frontera: `LOCAL / NOT SHA-BOUND / NOT CI / NOT ACCEPTED`.

## Closure delta

- Registry ejecutable fija ocho manifests, contratos `0.1.x`, bindings
  importables, dependencias lineales, semántica y autoridad; su hash cambia ante
  cualquier mutación material.
- Registry/manifests se conservan append-only en Project Graph.
- Resume ejecuta realmente el sufijo invalidado: contenido conserva E01–E03 y
  ejecuta E04–E08; Resume completo ejecuta cero motores.
- Registry/policy/rights/request mismatch rechaza antes de runtime.
- Stage fallido ya no se clasifica como completado en checkpoint.
- Journal de Resume conserva decisión y `EXECUTED != REUSED_CHECKPOINT`.
- Ops expone Registry, conteos, Execution Tape y fronteras sin autoridad de
  mutación, publicación o aceptación.

## Ejecuciones

| Verificación | Resultado |
|---|---|
| Registry + persistencia | 6/6 PASS |
| Orchestrator parcial | 5/5 PASS |
| Design OS E2E integral | 1/1 PASS |
| Design Console/Ops | 8/8 PASS |
| Bloque 2 completo | 136/136 PASS |
| Workspace | 345/345 PASS |
| `compileall` + `node --check` | exit 0 |

## Browser y red-team

Edge real a 390×844 abrió `?view=ops`: título `Runtime provenance`, ocho filas,
overflow global 0px, Studio oculto y `NOT_ACCEPTED` visible. Captura:
`C:/Users/angel/.codex/visualizations/2026/08/25/01a036cf-2113-79e1-af94-fc7b4c7da1ac/block2_ops_mobile_2026-08-31.png`.

La primera inspección descubrió que `.workspace { display:grid }` anulaba
visualmente `hidden`: el DOM decía oculto pero Studio seguía renderizado. Se
reparó con `[hidden]{display:none!important}` y prueba de regresión. El
Execution Tape usa azul para ejecutado y cian para reutilizado.

## Límites y siguiente ataque

No hay Git HEAD, SHA, CI alojada, revisión independiente ni MAR. Create continúa
deshabilitado y E06 usa stub determinista, no un provider sandbox gobernado.
Siguiente ataque: Create como compilador de un Design Context Envelope local,
seguido por sandbox de proveedor con timeout/cancel/budget/quarantine.
