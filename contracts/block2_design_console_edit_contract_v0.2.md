# Block 2 — Design Console Controlled Edit Contract v0.2

> Estado: `CANDIDATE / LOCAL EXECUTED / MAR REQUIRED`

## Alcance y autoridad

Extiende el read model v0.1 con una única mutación: proponer edición de un campo
CDD permitido. La consola no modifica la versión base; invoca Document Evolution
y muestra child, diff e invalidación. No renderiza, publica, acepta, cambia
claims/evidence ni ejecuta automáticamente motores invalidados.

## Seguridad y concurrencia

- Servidor exclusivo `127.0.0.1`, host/origin/fetch-site guards y CSP existente.
- Sesión efímera same-origin entrega token anti-CSRF; POST exige header exacto.
- JSON máximo 16 KiB, content type exacto y schema allowlisted.
- Cliente aporta `edit_id` y timestamp para replay; servidor deriva version ID.
- Base version/hash current son obligatorios. Dos editores concurrentes: el
  primero crea child; el segundo recibe stale y debe recargar.
- Errores no exponen paths, SQL, stack traces o contenido de otros proyectos.

## UX y accesibilidad

El inspector muestra label, textarea, estado de guardado y resultado del diff.
“Guardar nueva versión” describe la acción real. El foco permanece controlable,
los errores usan `role=alert`, el éxito `role=status`, y ninguna actualización
depende sólo de color.

## No-claims

Guardar una versión no valida el cambio, no lo renderiza de nuevo, no actualiza
E08 y no abre publicación. Su estado obligatorio es
`EDITED_CANDIDATE_NOT_VALIDATED` hasta reejecución y revisión.
