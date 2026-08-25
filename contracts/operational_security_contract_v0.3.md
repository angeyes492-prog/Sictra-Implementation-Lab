# Contrato Operacional y de Seguridad v0.3

## Fuente atestada

La atestación cubre el registro canónico completo, incluido issuer,
`schema_version`, extensiones y los campos obligatorios `source_id`, `content`,
`observed_at`, `root_provenance`, `evidence_class`, `scope`, `correlation_id`,
`claim_key` y `polarity`. Solo `OBSERVED`, scope y claim configurados, issuer
confiable, HMAC válido y tiempo dentro de la ventana son admisibles.

La conectividad transitiva entre `root_provenance` y `correlation_id`
determina independencia; compartir cualquiera de los dos colapsa los registros
en una misma raíz independiente. Polaridades opuestas para un claim canónico
producen contradicción sin depender de un booleano autoafirmado.

## Capability de autoridad

Campos firmados: issuer, audiencia, task, run, acciones, epoch, issued-at,
not-before, expiry, nonce y committed. E08 falla cerrado ante firma inválida,
issuer desconocido, binding distinto, epoch distinto, revocación, acción fuera
de scope o vigencia inválida.

La capability autoriza una acción acotada; no prueba que el runtime la haya
ejecutado. El efecto se registra después mediante un objeto de enforcement.
La decisión E08 lleva una atestación interna ligada al fingerprint del input y
del candidato. E06 exige esa atestación y revalida la capability con una nueva
lectura del reloj dentro del lock transaccional; una etiqueta `producer=E08`
no constituye autoridad.

## Integridad de ejecución

E03 firma el fingerprint canónico de método, input, outcome, separación de
validación y evidencia actual. E05 verifica firma y vuelve a calcular tanto el
outcome como la evidencia; una sustitución posterior queda `INSUFFICIENT`.

## Persistencia e idempotencia

- `memory_candidates.run_id` y el terminal `COMMITTED` por run son únicos;
  terminales `NOT_EXECUTED` se identifican por request fingerprint.
- Todas las consultas SQLite usan parámetros.
- Efecto, asignación de versión y terminal ocurren en una única transacción
  `BEGIN IMMEDIATE`; cualquier excepción revierte la unidad completa.
- Los registros forman una cadena HMAC comprobada en cada lectura; la clave de
  integridad no reside en SQLite.
- El terminal vincula request fingerprint, result fingerprint y envelope en un
  HMAC de integridad verificado al leer.
- Memoria y journal tienen capacidades configuradas y fallan cerrado al agotarse.
- Solo schema SQLite v7 exacto es admitido, incluidas restricciones, CHECK e
  índice parcial exacto;
  una base sin versión que ya contiene tablas protegidas se rechaza sin mutación.
- Un terminal `COMMITTED` se invalida si falta o difiere su efecto durable.
- La metadata HMAC fija identidad de clave y capacidades globales; una conexión
  con configuración divergente no puede abrir el store.
- Tablas, índices, vistas o triggers no autorizados hacen fallar la apertura o
  la transacción; la coherencia durable se valida nuevamente antes del commit.
- Lecturas devuelven snapshots profundamente inmutables.
- Replay exacto devuelve el terminal existente; collision no escribe.

## Compatibilidad

Solo `0.3.0` es admitido. Prerelease, cualquier otra versión y tipos JSON
ambiguos son rechazados.

## No-claims

HMAC local no es PKI/KMS de producción. No se reclama verdad del contenido,
exactly-once, HA, escalado distribuido, rotación de claves, revocación remota ni
aceptación global.

