# Plan de implementación — Intelligence Workspace

## Fuente y decisión

Deriva del diseño aprobado `2026-08-26-block1-logistics-intelligence-design.md`.
GitHub conserva autoridad técnica; Notion registra el plan; Slack aporta los
checkpoints; Wolfram desafía el modelo formal.

## Requisitos extraídos

- Herramienta independiente y utilizable diariamente por una persona no técnica.
- Investigación global, regional y local con fuentes, claims y contradicciones.
- Comparación evolutiva sin ranking absoluto.
- Insights acotados y watchlists 7/30/90.
- Validación adversarial accesible desde la interfaz.
- Cero dependencia de fuentes reales en esta fase aprobada.

## Fases

1. **Vertical slice de campo:** modelo, fixtures, API, shell de producto,
   Evidence Spine, Strategy Lab y Validation Deck.
2. **Cierre técnico:** contratos, pruebas negativas, regresión completa,
   revisión visual, commit y CI sobre SHA exacto.
3. **Field trial:** tareas de usuario, observación de errores, accesibilidad y
   registro de hallazgos; sin promover producción.
4. **Source gateway:** diseño y autorización separada para ingesta real.

## Criterios de éxito de la fase 1

- [x] Tres escalas navegables y claramente sintéticas.
- [x] Trazabilidad visual pregunta→fuente→claim→red team→disposición.
- [x] Comparador Pareto con dominancia, trade-off y evidencia insuficiente.
- [x] Watchlists y cuatro vectores del runtime en una sola herramienta.
- [ ] Suite completa verde en el commit final.
- [ ] CI externa verde en SHA exacto.
- [ ] Revisión independiente sin CRITICAL/HIGH.

## Riesgos

- Apariencia de producción sin backend de producción: mitigado con límites
  persistentes y clase de fixture en API/UI.
- Puntaje de estrategia falso: mitigado con comparación multiobjetivo y
  `INCOMPARABLE`.
- Fuente correlacionada contada dos veces: mitigado con raíces y prueba negativa.
- UI atractiva pero no verificable: mitigado integrando Validation Deck y API.
