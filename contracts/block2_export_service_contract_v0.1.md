# Block 2 — Export Service Contract v0.1

> Estado: `CANDIDATE / LOCAL EXECUTED / MAR REQUIRED`

## Propósito y autoridad

Export Service serializa una versión CDD current en un paquete HTML o SVG
determinista y accesible. Export no entrega, publica, acepta, concede rights ni
reemplaza E07 o validación externa.

## Precondiciones y salida

La versión debe existir, conservar validations current, no estar editada sin
revalidación y usar un target `HTML` o `SVG` allowlisted. Salida:
`ExportPackage` con IDs, CDD hash, media type, bytes, SHA-256, alternativa
textual, exporter/time y estados `NOT_PUBLISHED / NOT_ACCEPTED`.

## Seguridad, errores y replay

- Copy, labels e IDs se escapan; no scripts, recursos remotos o executable URLs.
- CDD editado con validations vacías devuelve `REVALIDATION_REQUIRED`.
- Target, version o lineage desconocidos fallan cerrados.
- Mismo request/document produce bytes y hash idénticos.
- Registrar export añade node y edge `DOCUMENT_VERSION EXPORTED_AS PACKAGE` de
  forma atómica e idempotente; colisión no sobrescribe.

## No-claims

Un paquete conforme no prueba render cross-client, entrega, publicación,
legalidad, derechos suficientes, calidad, aceptación ni accesibilidad humana.
