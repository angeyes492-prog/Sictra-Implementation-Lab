# Bloque 1 Intelligence — Perfil Operacional Acotado v0.3

## Gate definido

`BOUNDED OPERATIONAL` significa que el paquete Python puede aceptar una
petición atestada, ejecutar E01–E08, autorizar antes del efecto, persistir el
resultado, sobrevivir replay/concurrencia/reinicio/fallo transaccional y emitir
evidencia correlacionable dentro de un único host con SQLite local.

No significa producción, alta disponibilidad, verdad de fuentes, gestión de
claves, aceptación normativa global ni operación de los Bloques 2–4.

## Flujo operacional

`E01 request → E04 route → E02 verify/acquire → E03 execute → E05 assess →
E06 prepare → E07 stability/store health → E08 authorize → runtime dispatch →
E06 reauthorize → atomic durable effect + terminal record`

E04 es un enforcement transversal observable; no altera el payload ni crea
autoridad. El adapter del runtime es el único consumidor de la decisión E08 y
registra por separado decisión y efecto.

## Límites de confianza

- E02 solo admite fuentes HMAC atestadas por issuers configurados.
- La atestación vincula identidad, contenido, tiempo, procedencia, clase,
  scope, correlación, claim y polaridad.
- E08 solo admite capabilities HMAC emitidas por issuers configurados y
  vinculadas a audiencia, task, run, acción, epoch, vigencia, nonce y commit.
- E03 atesta su resultado y el fingerprint de evidencia; E05 rechaza cualquier
  sustitución o alteración posterior.
- E08 atesta cada decisión contra task/run/acción/input/candidato; E06 verifica
  esa atestación y vuelve a verificar la capability antes del efecto.
- El reloj lo inyecta el host, no la petición, y se vuelve a consultar en E08
  y dentro de la transacción, después de adquirir el lock de escritura.
- Las claves de fixture de CI no son claves operativas ni de producción.

## Estado y recuperación

- SQLite usa transacciones `BEGIN IMMEDIATE`, WAL y `synchronous=FULL` en
  archivo.
- `run_id` es único en el store. Reuso exacto devuelve el terminal anterior;
  reuso materialmente diferente es `IdentityCollision`.
- E06 tiene unicidad por run, versionado atómico por task y cadena HMAC
  verificable con una clave de integridad separada de SQLite.
- Efecto y terminal se confirman en la misma transacción. Un fallo inyectado
  entre ambos revierte los dos; un retry o restart comienza sin efecto parcial.
- El replay de un terminal queda marcado como histórico y no se presenta como
  reautorización con la hora actual.
- Un journal durable distingue `STARTED`, `FAILED`, `TERMINAL_NO_EFFECT` y
  `EFFECT_AND_TERMINAL_COMMITTED`.
- Memoria y journal tienen capacidades independientes configurables. Al
  agotarse, fallan cerrado; no se expulsa silenciosamente identidad contractual.
- SQLite schema v6 rechaza versiones futuras/anteriores y tablas operacionales
  sin versión; no promueve esquemas desconocidos implícitamente.
- Los terminales `COMMITTED` son únicos por run y deben corresponder a su fila
  de memoria. Los `NOT_EXECUTED` son terminales durables por fingerprint de
  intento, por lo que se pueden reproducir sin bloquear un intento autorizado nuevo.
- E07 observa capacidad pero no la reserva. Si otro writer consume el último
  cupo, se registra un terminal `NOT_EXECUTED` con la razón del cambio, sin
  presentar el intento como efecto ejecutado.
- Semántica: at-least-once delivery con efectos idempotentes; exactly-once no
  se reclama.

## Observabilidad

Cada envelope preserva task/run/message, lineage, logical time, producer,
consumer, fingerprint, estado epistémico, incertidumbre y restricciones. E04
audita rutas, duplicados, mismatch, topología prohibida y colisiones. El
terminal distingue `governance.decision` de `enforcement.status`. Un fallo de
entrega posterior al commit no degrada el journal durable a `FAILED`.

## Criterios obligatorios

1. cero crítico/alto abierto en revisión independiente;
2. autoridad falsa/stale/futura/fuera de scope no escribe;
3. evidencia no atestada/stale/futura/sintética/foreign no escribe;
4. replay y concurrency no duplican ni pierden estado;
5. restart recupera terminal y memoria;
6. fallo entre efecto y terminal revierte ambos y el retry produce un único efecto;
7. CI externa pasa sobre el SHA exacto;
8. cierre preserva no-claims y requiere decisión humana para merge.

