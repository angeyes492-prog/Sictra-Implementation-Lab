# Bloque 2 — Create y Provider Sandbox, ciclo local

> Fecha/contexto: `2026-08-31`, Python/SQLite/Edge local.  
> Certeza/confianza: `VERIFIED / A` para el SUT local.  
> Frontera: `LOCAL / INJECTED PROVIDER / NOT SHA-BOUND / NOT ACCEPTED`.

## Closure delta

- Create compila intención + binding upstream + límites en un Design Context
  Envelope inmutable; faltantes devuelven una lista agregada sin envelope.
- Certainty, temporalidad, versión, canales, rights y colisiones fallan cerrados.
- POST local de Create usa token, JSON/schema allowlisted y máximo 32 KiB.
- UI Create habilita tres secciones contractuales y Handoff Seal con fingerprint
  o razones `RETURN_UPSTREAM`.
- Sandbox E06 fija provider manifest, policy, rights, adapters, budget, timeout,
  max output, cancelación e idempotency.
- Receipts conservan cost/latency/budget/timeout/cancel/policy/rights; output
  divergente, exceso, timeout o excepción queda en cuarentena.

## Ejecuciones

| Verificación | Resultado |
|---|---|
| Design Context compiler/binding | 9/9 PASS |
| Provider Sandbox | 8/8 PASS |
| Design Console total | 13/13 PASS |
| Project Graph restart/contention | 3/3 PASS |
| Bloque 2 | 161/161 PASS |
| Workspace | 370/370 PASS |
| `compileall` + `node --check` | exit 0 |

## Browser y red-team

Edge real 390×844 compiló Create: `Listo para E01`, fingerprint de 64 caracteres,
Studio/Ops ocultos y overflow 0. Captura:
`C:/Users/angel/.codex/visualizations/2026/08/25/01a036cf-2113-79e1-af94-fc7b4c7da1ac/block2_create_mobile_2026-08-31.png`.

Un segundo recorrido vació object/audience/facts/evidence y obtuvo simultáneamente
`OBJECT_ID_MISSING`, `AUDIENCE_MISSING`, `FACTS_MISSING` y `EVIDENCE_MISSING`.
La primera versión del formulario usaba `required` y bloqueaba ese diagnóstico;
se eliminó el veto cliente y se preservó la validación server-side.

El primer sandbox integration intentó construir el spec usando cualquier
manifest presentado por el gateway. Las pruebas históricas detectaron que eso
legitimaba sustitución. Se reparó: el stub conserva manifest canónico y sólo el
sandbox gobernado puede construir un spec ligado a su manifest/policy.

## Límites y siguiente ataque

En este punto del ciclo Create aún no iniciaba un run completo derivado de su
envelope. El sandbox usa providers inyectados, no credenciales/API comercial
real. Persistían binding, history/diff, restart/contention, a11y asistiva,
Git/CI, revisión independiente y MAR; el delta posterior resuelve los cuatro
primeros frentes locales salvo la validación asistiva independiente.

## Delta posterior del mismo ciclo

Create quedó vinculado al E2E E01–E08 mediante fingerprint, message y campos
upstream exactos; sustitución devuelve `RETURN_TO_CREATE`. Studio muestra dos
versiones y diff `CONTENT · CHART-001` observado en Edge. Project Graph conserva
commits tras restart, descarta append sin commit y completó seis writers bajo
contención acotada. Captura del diff:
`C:/Users/angel/.codex/visualizations/2026/08/25/01a036cf-2113-79e1-af94-fc7b4c7da1ac/block2_history_diff_2026-08-31.png`.

Por tanto, los límites vigentes se reducen a provider real, accesibilidad y
review independientes, identidad Git/CI alojada y MAR.
