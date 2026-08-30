# Bloque 1 — Editorial Engine gobernado v0.1

## Estado y propósito

`IMPLEMENTED CANDIDATE / LOCAL-TESTED / B`. Convierte señales ya gobernadas en
una lista corta editorial y un expediente ejecutivo trazable. Es una capacidad
compuesta E01–E08, no un noveno motor ni una autoridad de publicación.

## Topología

```text
governed candidates
  → strict contract + evidence eligibility
  → research priority | editorial readiness
  → Pareto frontier
  → diversity-aware shortlist
  → human flagship selection
  → bounded Block 2 handoff candidate
```

El Workspace expone radar, candidatos bloqueados, lista corta, perfil
multidimensional, interpretación, pregunta ejecutiva, linaje y handoff. Los
fixtures son sintéticos y la decisión es efímera.

## Invariantes

- `RESEARCH PRIORITY != EDITORIAL READINESS`.
- Incertidumbre alta nunca mejora readiness.
- Correlación no crea independencia.
- Pareto e incomparabilidad sustituyen al ranking agregado.
- Una cuota editorial no promueve candidatos dominados o inadmisibles.
- La elección humana no salta compuertas ni crea verdad.
- Global/Segment/Account conserva el contrato de tres capas y no sustituye la
  escala geográfica.
- Handoff no equivale a publicación, distribución ni aceptación global.

## Fallos y recuperación

Entradas no contratadas, procedencia rota, alcance o licencia inválidos fallan
cerrados. Evidencia insuficiente vuelve a investigación; fallos de seguridad
entran en cuarentena. La recuperación reconstruye el ciclo desde entradas
inmutables; ningún estado de selección local necesita restauración en v0.1.

## Evidencia y límites

Pruebas unitarias, adversariales, contractuales y HTTP ejercen doble ruta,
correlación, Pareto, diversidad, mínimos, cuarentena, selección y handoff. La
regresión local completa reporta 197 pruebas verdes el 2026-08-30. CI en SHA
exacto y revisión independiente siguen pendientes, por lo que no cambia el
gate global.
