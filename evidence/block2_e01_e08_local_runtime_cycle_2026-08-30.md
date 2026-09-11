# Bloque 2 E01–E08 — Evidencia de runtime local acotado

> Fecha/contexto: `2026-08-30`, Python local, Windows.  
> Certeza: `VERIFIED / A` para los comandos locales descritos.  
> Frontera: no hay SHA local, CI externa, producción ni aceptación.

## Closure delta

- Implementados E05 investigación/rights, E06 adapters HTML/SVG, E07 red-team
  y E08 memoria candidata.
- Implementado orquestador fail-closed E01→E08 y entrypoint
  `python -m sictra_block2_design`.
- Añadidos cinco contratos candidatos y una especificación de runtime.
- Candidato de referencia: `text/html`, SHA-256
  `aaa78dec99764388100567416140fe9d288e06608de1dd5edf2555d898987370`,
  alternativa `text/plain`, `NOT_PUBLISHED`, `NOT_ACCEPTED`.

## Ejecuciones

| Comando | Resultado | Clase de evidencia |
|---|---|---|
| `python -m sictra_block2_design` | E01–E08 completos, exit 0 | runtime sintético local |
| `python -m unittest discover -s tests -p 'test_block2*.py' -q` | 83/83 PASS | regresión Block 2 local |
| `python -m unittest discover -s tests -q` | 292/292 PASS | regresión workspace local |
| `python -m compileall -q src tests` | exit 0 | sintaxis/import local |

## Red-team y reparaciones

Los vectores rechazan imitación identificable, rights no vigentes, principio
dependiente de identidad, binary payload, copy no aprobado, publicación,
recursos remotos, self-review, criterio ausente, score crítico, feedback de la
misma generación, evidencia correlacionada y colisión de memoria. Markup HTML
aprobado se escapa, no se ejecuta. SVG conserva descripción textual.

## Reconciliación de fuentes

| Fuente | Hallazgo | Clasificación / límite |
|---|---|---|
| Slack | Wave 38 acredita E01 local y deja E02/E03 no confirmados en ese momento; otros resultados E01–E08 pertenecen al Bloque 1. | `VERIFIED / B` como memoria histórica; no autoridad actual de Bloque 2. |
| Notion | localiza reevaluaciones E01 y tareas generales; no especificación aceptada E05–E08 de Bloque 2. | `INSUFFICIENT EVIDENCE / C`; orden contextual. |
| GitHub | repo `angeyes492-prog/Sictra-Implementation-Lab`; PR #3 acredita sólo E01 y niega aceptación global. | `VERIFIED / A` remoto para E01; no acredita cambios locales. |
| Rovo | Confluence Bloque 1 Editorial Engine reporta handoff a Bloque 2, SHA `a9fb...`, CI y límites sintéticos. | `VERIFIED / B` como handoff contextual, no contrato Block 2. |
| Wolfram | grafo E01→E08 acíclico; orden topológico único y una ruta completa. | `VERIFIED / A` formal; no runtime/gate. |

## Riesgos y siguiente ataque

El checkout reporta `fatal: Needed a single revision`; todo el workspace sigue
untracked y no hay `HEAD`. No se puede afirmar identidad GitHub ni CI. Faltan
revisión independiente real, fixture upstream real y gobernado, brand/rights
manifests reales, auditoría perceptual/WCAG, pruebas de render en clientes,
persistencia multiusuario y adapters adicionales. Próximo ataque: crear un
commit coherente en una rama `codex/`, ejecutar CI hospedada y obtener revisión
independiente sin promover automáticamente el gate.

