# Block 2 — Ops Console Contract v0.1

> Estado: `CANDIDATE / LOCAL EXECUTED / MAR REQUIRED`

## Propósito y autoridad

Ops presenta el último recorrido del Orchestrator y separa motores
`EXECUTED` de `REUSED_CHECKPOINT`. Consume únicamente el read model del Project
Graph. No inicia runs, altera checkpoints, acepta calidad, publica ni promueve
gates.

## Entradas, salidas e invariantes

Entrada: nodos `ENGINE_REGISTRY`, `ORCHESTRATOR_RESUME`, `ENGINE_STAGE` y
`ENGINE_STAGE_RESUME`, más la frontera de autoridad del snapshot. Salida:
identidad abreviada del Registry, conteos de ejecución/reuso, Execution Tape y
estado operacional.

- Ausencia de Registry se muestra como `MISSING / RETURN_UPSTREAM`, nunca PASS.
- Run inicial equivale a ocho motores ejecutados; Resume conserva el
  `execution_state` registrado por stage.
- `hidden` debe producir ocultamiento renderizado, no sólo estado DOM.
- Vista responsive sin overflow global y con navegación por botones nativos.
- Toda pantalla conserva `NOT_PUBLISHED / NOT_ACCEPTED`.

Ops demuestra observabilidad local, no disponibilidad distribuida, exactitud
del motor, CI, revisión independiente ni aceptación.
