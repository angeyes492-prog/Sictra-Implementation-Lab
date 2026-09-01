# Block 2 — Checkpoint and Resume Contract v0.1

> Estado: `CANDIDATE / LOCAL EXECUTED / MAR REQUIRED`

## Propósito y autoridad

El Orchestrator produce checkpoints de runs E01–E08 y decide qué stages pueden
rehidratarse. El checkpoint conserva identidad y currentness; no acepta outputs,
no convierte cache en evidencia nueva y no permite saltar invalidaciones.

## Forma y precondiciones

Checkpoint: project/run/checkpoint IDs, envelope y request hash, engines
completados, CDD/asset/receipt refs, hashes de Engine Registry, policy y rights,
fecha y estado. Resume exige coincidencia exacta de todos los hashes y que el
checkpoint esté `CURRENT`.

## Transiciones

- Sin invalidación y con E01–E08 completos: `RESUMED_COMPLETE`; rehidrata todos
  los stages y no ejecuta motores.
- Con invalidación: sólo reutiliza los engines preservados por el plan y
  devuelve `REEXECUTE_FROM_<root>`; el Orchestrator ejecuta realmente el sufijo
  y etiqueta por separado `REUSED_CHECKPOINT` y `EXECUTED`.
- Checkpoint parcial current: `REEXECUTE_FROM_<next_stage>`.
- Cualquier mismatch, estado stale/unknown, stage desconocido o lineage roto:
  `RESUME_REJECTED`; no ejecuta ni interpreta UNKNOWN como válido.

## Persistencia, replay y no-claims

El checkpoint se registra append-only en Project Graph con hash canónico.
Replay exacto es idempotente; misma identidad con contenido distinto colisiona.
Rehidratar metadata y CDD no prueba que proveedores sigan disponibles, que
rights externos permanezcan vigentes ni que una validación anterior acepte una
versión editada.

Un stage detenido se considera intentado, no completado. El checkpoint conserva
solamente el prefijo exitoso anterior y obliga a reejecutar el stage fallido.
