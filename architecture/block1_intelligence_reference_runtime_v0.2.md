# Bloque 1 Intelligence — Runtime de Referencia v0.2

> **SUPERSEDED:** el perfil operacional acotado v0.3 reemplaza esta baseline
> de referencia. Este documento permanece como historial.

## Decisión acotada

Se construye un runtime de referencia ejecutable para los ocho motores de
Intelligence. Esta decisión autoriza código, contratos y pruebas en la rama de
implementación; no convierte diseños de Slack en arquitectura global aceptada,
ni demuestra un runtime de producción.

## Motores y propiedad semántica

| Motor | Propiedad local | No posee |
|---|---|---|
| E01 Agent | petición de trabajo y coordinación local | evaluación, memoria o autorización |
| E02 Acquisition | adquisición y empaquetado de evidencia | verdad global o promoción |
| E03 Practice/Experiment | ejecución y resultado reproducible | validez epistémica |
| E04 Integration | routing, idempotencia y contención | scheduling universal o autoridad |
| E05 Evaluation | assessment, contradicciones y limitaciones | autorización o mutación de reglas |
| E06 Memory/Learning | memoria candidata, versiones y lineage | promoción gobernada |
| E07 Stability | salud, observabilidad y modo de control | política global |
| E08 Governance | decisión acotada bajo autoridad vigente | prueba de enforcement/runtime |

## Flujo mínimo

`E01 request → E04 route → E02 acquire → E03 execute → E05 assess → E06 store candidate → E07 assess health → E08 decide`

Cada paso emite un sobre inmutable con identidad de mensaje, tarea y run;
productor/consumidor; versión; tiempo lógico; payload; procedencia; estado
epistémico; incertidumbre; restricciones; y contexto de autoridad.

## Invariantes comunes

- Un `message_id` repetido con igual payload es idempotente; con payload
  materialmente distinto es conflicto.
- Autoridad ausente, expirada, futura o fuera de scope nunca se transforma en
  `ALLOW`.
- E05 assessment no es E08 authorization.
- E03 completion no es learning validity.
- E06 storage no es promotion.
- E08 decision no prueba commit, activación ni enforcement.
- Contradicciones, incertidumbre y `UNKNOWN` sobreviven los handoffs.
- La procedencia se amplía de forma aditiva; nunca se reescribe.

## Ambigüedad E01

El canal Slack `01-agent-engine` más reciente declara explícitamente trabajo
local de Bloque 2. No se importan esas reglas. E01 de Intelligence queda
restringido al mínimo necesario para crear una petición trazable y no
autorizante. Una especificación posterior puede especializarlo sin romper el
contrato común.

## Estado

`CANDIDATE / REFERENCE RUNTIME`. La aceptación exige ejecución, CI externa,
revisión independiente y evidencia real para cualquier claim de producción.

