# Block 2 / E05 — Reference & Visual Research Contract v0.1

> Estado: `CANDIDATE / LOCAL IMPLEMENTATION AUTHORIZED / NOT ACCEPTED`

## Propósito y autoridad

E05 transforma referencias gobernadas en un `ReferenceResearchPack` de
principios visuales transferibles. Lee el blueprint E04 y el
`ReferenceRightsManifest`; no descarga assets, concede licencias, clona una
identidad, crea estilos finales ni acepta una dirección.

## Entrada y salida

La entrada contiene identidad y fingerprint de E04, canal, referencias con
decisión de rights vigente y principios con dimensión, regla abstracta,
evidencia y fuente. La salida clasifica `RESEARCH_PACK_READY_FOR_PRODUCTION`,
`RETURN_TO_PREVIOUS`, `QUARANTINE_REFERENCE`, `CONTRADICTED`,
`UNSUPPORTED_CHANNEL` o `UNSUPPORTED_VERSION`.

## Invariantes ejecutables

1. Sólo `ALLOW_CONSTRAINT_ONLY`, `ALLOW_LICENSED_ASSET` y
   `ALLOW_METADATA_INDEX` son consultables; `QUARANTINE` y `REVOKED` dominan.
2. Un asset licenciado sólo es usable dentro de canal y vigencia registrados.
3. Cada principio cita una referencia y evidencia existentes, es
   `identity_independent` y pertenece a la taxonomía contratada.
4. Un pack listo requiere al menos cuatro principios en tres dimensiones.
5. Solicitar logo, fuente exacta, trade dress, composición o imitación
   identificable produce cuarentena.
6. E05 conserva lineage y no incorpora payload binario ni declara derechos.

## Fallo, recuperación y observabilidad

El input incompleto vuelve a E04; rights ausentes/conflictivos se ponen en
cuarentena; contradicciones de identidad se bloquean. Recuperar exige un nuevo
manifest o sustituir la referencia. Registrar IDs, decisiones, evidencia,
dimensiones, riesgos, versión y reasons. `READY` no equivale a licencia,
producción, accesibilidad, similitud segura ni aceptación.

