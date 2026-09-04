# Block 2 / E06 — Prototype & Production Contract v0.1

> Estado: `CANDIDATE / LOCAL IMPLEMENTATION AUTHORIZED / NOT ACCEPTED`

## Propósito y autoridad

E06 materializa un blueprint E04 y un pack E05 listos en un
`ProductionCandidate` reproducible. La implementación local permite adapters
`HTML_EMAIL` y `SVG`; escapa contenido, genera checksum y manifest, y no usa
red, credenciales, archivos externos, envío, despliegue ni aceptación.

## Invariantes ejecutables

1. Fingerprint, blueprint, profile, canal y claims deben conservarse.
2. Sólo copy previamente aprobado puede incorporarse.
3. Toda salida incluye alternativa accesible (`text/plain` para email y
   descripción material para SVG).
4. Assets no permitidos, script/event handlers, URLs remotas o publicación
   solicitada producen bloqueo.
5. Misma entrada y versión producen exactamente los mismos bytes y SHA-256.
6. Un candidato permanece `NOT_PUBLISHED` y puede descartarse sin efecto.

Las disposiciones son `PRODUCTION_CANDIDATE_READY_FOR_REVIEW`,
`RETURN_TO_PREVIOUS`, `QUARANTINE_REFERENCE`, `UNSUPPORTED_ADAPTER`,
`SCOPE_VIOLATION` y `UNSUPPORTED_VERSION`. La salida no prueba calidad visual,
entrega, render equivalente entre clientes ni aceptación.

