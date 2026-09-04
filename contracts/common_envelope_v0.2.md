# Common Envelope v0.2

> **SUPERSEDED:** v0.3 operational contracts replace this reference-only
> baseline. Retained for historical evidence.

## Obligaciones

Todo handoff material contiene identidad (`message_id`, `task_id`, `run_id`),
productor, consumidor, versión de contrato, tiempo lógico, payload,
procedencia, estado epistémico, incertidumbre, restricciones y contexto de
autoridad. El sobre es inmutable y su huella se calcula sobre representación
canónica.

## Autoridad

El contexto de autoridad es una referencia verificable, no autoridad creada por
el sobre. Para acciones protegidas se exige issuer, epoch, scope y expiración.
Epoch futuro/desconocido, scope incompatible o expiración producen rechazo o
cuarentena; nunca permiso implícito.

## Replay e identidad

- mismo `message_id` + misma huella: entrega duplicada idempotente;
- mismo `message_id` + distinta huella: `IdentityCollision`;
- versión mayor no soportada: rechazo explícito;
- procedencia vacía o cuyo primer elemento no coincide con la raíz: rechazo.

## Compatibilidad

El runtime acepta `0.2.x`. Campos desconocidos viven en payload y deben
preservarse. Compatibilidad sintáctica no demuestra compatibilidad semántica.

## No-claims

Conformidad del sobre no prueba ejecución, validez, promoción, enforcement ni
aceptación global.
