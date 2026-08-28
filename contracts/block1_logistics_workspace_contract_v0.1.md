# Contrato — Intelligence Workspace v0.1

## Identidad

- Versión: `0.1`.
- Productores: `sictra_block1.logistics` y `sictra_block1.lab_web`.
- Consumidor: navegador local en la misma computadora.
- Scope: `BLOCK1_LOGISTICS_INTELLIGENCE_WORKSPACE`.
- Clase de datos: `SYNTHETIC_FIELD_TEST`.
- Autoridad: lectura de fixture; ninguna autoridad arquitectónica o de gate.

Este contrato amplía la superficie de laboratorio v0.1. Conserva sus cuatro
escenarios y sus límites operacionales.

## Superficie HTTP

| Método | Ruta | Postcondición |
| --- | --- | --- |
| `GET` | `/` | Shell HTML del producto. |
| `GET` | `/app.css`, `/app.js` | Asset allowlisted, sin contenido externo. |
| `GET` | `/health` | Estado, scope y clase de fixture. |
| `GET` | `/api/workspace` | Snapshot defensivo del catálogo. |
| `GET` | `/api/investigations/{id}` | Expediente conocido o `404`. |
| `GET` | `/api/comparisons/{id}?left=A&right=B` | Comparación compatible o error explícito. |
| `POST` | `/api/scenarios/{scenario}` | Resultado del fixture existente; payload prohibido. |

No se admiten otras rutas, métodos, archivos, IDs o parámetros implícitos.
Métodos no enumerados devuelven `405` JSON. El adapter exige `Host` local con
el puerto activo, rechaza `Origin` externo y `Sec-Fetch-Site: cross-site`; no
emite CORS permisivo. La comparación admite exactamente `left` y `right`.

## Contrato de estrategia

Cada observación contiene exactamente identidad, nombre, question ID, scope
key, métricas, red team y estabilidad. Porcentajes están en `[0,100]`; toda
métrica es numérica no negativa y `bool` no es numérico admisible.

Resultados posibles:

- `PREFER_LEFT` / `PREFER_RIGHT`: dominancia Pareto demostrada.
- `INCOMPARABLE`: ventajas cruzadas.
- `INSUFFICIENT_EVIDENCE`: red team o estabilidad no admisibles.
- `SCOPE_MISMATCH`: pregunta o scope incompatible.

Comparar una estrategia consigo misma, usar ID desconocido, campo extra,
métrica ausente o valor inválido produce rechazo. El resultado conserva las
observaciones por métrica y declara el método `PARETO_V0.1`.

## Procedencia y lineage

Cada claim referencia únicamente source IDs existentes. Los source packets
declaran una raíz; paquetes con la misma raíz permanecen correlacionados y no
incrementan independencia. Enlaces `source.supports` y `claim.source_ids` son
bidireccionales; el número declarado de raíces debe igualar el lineage real y
una estrategia no puede declarar más raíces que su investigación. El fixture separa `FACT`, `INTERPRETATION`,
`HYPOTHESIS` y `FORECAST`; no transforma tipos para presentar un insight.

## Error, compatibilidad y recuperación

Errores de input son `400`; recursos desconocidos son `404`; fallos internos
son `500` sin convertirse en validación positiva. La compatibilidad se limita a
v0.1 y a los campos documentados. El snapshot se reconstruye desde fixtures
inmutables; v0.1 no promete persistencia de interacción.

## No-claims

- No internet, scraping, APIs, uploads, credenciales ni datos reales.
- No autenticación, multiusuario, publicación, CRM o acciones comerciales.
- No verdad de fuentes, forecast, score universal o recomendación autónoma.
- No gate GREEN, producción, Bloques 2–4 ni aceptación global.
