# Plan de implementación — Editorial Engine gobernado

## Baseline

Diseño aprobado: `2026-08-30-block1-editorial-engine-design.md`. GitHub es la
fuente técnica canónica. Jira `SI-13` organiza el trabajo; Slack y Notion
conservan checkpoints contextuales. La implementación no promueve el gate
global ni habilita fuentes reales.

## Incrementos verificables

1. **Contrato ejecutable**
   - Modelo estricto de evento, elegibilidad, perfil y candidato.
   - Separación comprobable entre prioridad de investigación y readiness.
   - Estados y razones fail-closed.

2. **Algoritmo editorial**
   - Filtro de admisibilidad.
   - Frontera Pareto sin score universal.
   - Lista corta de hasta cinco con diversidad explicable.
   - Selección humana acotada y dossier tipado.

3. **Fixtures y API local**
   - Ciclo semanal sintético con candidatos elegibles y bloqueados.
   - Endpoints de radar, candidato y selección sin persistencia ni publicación.
   - Rechazo de IDs, query strings y payloads no contratados.

4. **Mesa editorial**
   - Pestaña diaria con radar, shortlist, perfil, red team, derivaciones y
     handoff.
   - Límite sintético siempre visible y ausencia de acciones de publicación.

5. **Validación**
   - Unit, contrato, mutación, adversarial, HTTP, regresión y revisión visual.
   - Reparación de hallazgos y nueva ejecución limpia.
   - CI verde ligado al SHA exacto y revisión independiente antes de cualquier
     reclamo operacional.

## No-claims

- No Internet ni conectores autónomos en este incremento.
- No empresa real, PII, CRM, newsletter publicado ni cuenta persistente.
- No score agregado, predicción causal ni selección autónoma de pieza final.
- No `GREEN` global derivado de fixtures o pruebas locales.
