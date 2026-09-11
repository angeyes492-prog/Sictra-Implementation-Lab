# Block 2 — Design Console Read Model Contract v0.1

> Estado: `CANDIDATE / LOCAL EXECUTED / READ-ONLY / MAR REQUIRED`

## Propósito y autoridad

La consola muestra el mismo Project Graph y CDD local como Project Rail,
semantic canvas, Evidence Inspector y Lineage Ribbon. Es un read model: no
edita, genera, acepta, publica, cambia rights, invoca proveedores o promueve
gates. `UNKNOWN` y proyecto ausente se muestran como error explícito.

## Entradas y salidas

Entrada: path SQLite resuelto localmente y `project_id` explícito. Salida:
HTML/CSS/JS estático y JSON allowlisted con nodes, edges, versiones CDD y
estados `NOT_PUBLISHED / NOT_ACCEPTED`. No expone paths, credenciales, contenido
binario, comandos ni endpoints de mutación.

## Seguridad y recuperación

- Bind exclusivo a `127.0.0.1`.
- Host/origin/fetch-site guards; CSP; `no-store`; `nosniff`; no-referrer;
  frame y form bloqueados.
- Sólo GET allowlisted; POST/PUT/PATCH/DELETE/OPTIONS responden 405.
- Todo texto del read model se escapa antes de entrar al DOM.
- Error de lectura no se reinterpreta como proyecto vacío ni PASS.
- Reiniciar el servidor no cambia el grafo; no mantiene autoridad en memoria.

## Accesibilidad y responsive

Landmarks, skip link, foco visible, botones semánticos, regiones live/error,
controles táctiles de al menos 44px, estado expresado con texto, reduced motion
y layout móvil sin overflow global. La Lineage Ribbon conserva scroll interno
horizontal deliberado. WCAG 2.1 AA completa requiere todavía prueba humana con
NVDA/VoiceOver y zoom de navegador.

## No-claims

La consola v0.1 no prueba edición tipo Figma, render fidelity, colaboración,
proveedores, derechos, accesibilidad del artefacto producido, publicación,
aceptación o seguridad de despliegue remoto.

