# Bloque 2 — Evolución, checkpoint y export, ciclo local integrado

> Fecha/contexto: `2026-08-31`, Python/SQLite/Edge local.  
> Certeza/confianza: `VERIFIED / A` para ejecución local; `PROBABLE / B` para
> experiencia y accesibilidad hasta revisión humana independiente.  
> Frontera: `SLICE 1 LOCAL / NOT CI-BOUND / NOT ACCEPTED`.

## Closure delta

- Edición CDD inmutable con base version/hash current, replay idempotente,
  colisión/stale fail-closed y rollback.
- Diff tipado `CONTENT/GEOMETRY/STYLE/ASSET/ACCESSIBILITY/RIGHTS`.
- Invalidación conservadora mínima: style→E03, content/geometry/a11y→E04,
  asset/rights→E05; E06–E08 siempre se revalidan tras cambio material.
- Checkpoint current con request/registry/policy/rights hashes; resume completo
  rehidrata E01–E08 sin ejecución y edit de contenido exige E04–E08.
- Studio permite guardar sólo content/a11y mediante POST local, token anti-CSRF,
  schema y tamaño allowlisted; muestra diff e invalidación.
- Export Service HTML/SVG determinista, con alternativa textual, lineage,
  replay y estados `NOT_PUBLISHED / NOT_ACCEPTED`; versión editada sin
  revalidación queda bloqueada.

## Ejecuciones

| Verificación | Resultado |
|---|---|
| Document Evolution focal | 6/6 PASS |
| Checkpoint focal | 6/6 PASS |
| Export Service focal | 4/4 PASS |
| Design Console server/UI | 7/7 PASS |
| Design OS E2E integral | 1/1 PASS |
| Bloque 2 completo | 123/123 PASS |
| Workspace | 332/332 PASS |
| `compileall` + `node --check` | exit 0 |

## Browser E2E

Edge headless 390×844 ejecutó: abrir Studio → seleccionar CHART-001 → editar →
guardar. Resultado: segunda versión, estado
`EDITED_CANDIDATE_NOT_VALIDATED`, diff `CONTENT`, preserva E01–E03, reejecuta
E04–E08, overflow global 0px y aceptación `NOT_ACCEPTED`.

## Red-team y reparaciones

- Canonical JSON no serializaba dataclasses anidadas en tuplas: reparado en el
  canonizador común y regresionado.
- Replay de edit se confundía con base stale: ahora distingue child exacto
  idempotente de branch concurrente stale.
- El test de recursos remotos confundía `xmlns` SVG con fetch externo: el
  oráculo ahora bloquea `href/src` remotos y conserva namespace obligatorio.
- Claims, evidence, limitations y lineage no son editables desde Studio.
- Token ausente, origin/host inválido, JSON excesivo, field no allowlisted,
  base/hash stale y export editado fallan cerrados.

## Estado y siguiente ataque

Slice 1 tiene un camino local demostrable, pero no cumple aún CI exacta,
revisión independiente, reejecución parcial real desde E04, Engine Registry
ejecutable, history/diff visual completo ni pruebas NVDA/VoiceOver. Siguiente
ataque: Registry + Orchestrator parcial, luego Create/Ops y provider sandbox.

