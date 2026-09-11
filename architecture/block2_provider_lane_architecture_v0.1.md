# Block 2 — Provider Lane Architecture v0.1

> Estado: `PROPOSED / NOT IMPLEMENTED / MAR REQUIRED`  
> Fecha: `2026-08-31`

## Decisión propuesta

No modelar generación de imágenes, render determinista y edición en una
plataforma externa como un único `ProviderAdapter`. Son tres clases con
semánticas, estados y validaciones distintas:

1. **GENERATIVE_MEDIA** — produce una propuesta estocástica nueva.
2. **DETERMINISTIC_RENDER** — serializa una versión CDD ya definida.
3. **DESIGN_PLATFORM** — crea o vincula un documento remoto editable y luego
   exporta una versión concreta.

El sandbox actual exige que la respuesta coincida con el hash del artefacto
local esperado. Ese invariante es correcto para un stub/renderer de conformidad,
pero haría imposible una generación visual legítima. No debe debilitarse ni
reutilizarse silenciosamente: requiere contratos separados.

## Lane 1 — Generative Media

**Entrada:** prompt estructurado derivado de CDD, `DesignContextEnvelope`, brand
manifest, referencias permitidas, rights hash, restricciones de canal,
non-claims, modelo/snapshot, size/quality, presupuesto e idempotency key.

**Salida candidata:** bytes, media type, dimensiones, hash observado,
provider-request ID, modelo/snapshot, parámetros, usage/cost, timestamps,
moderation/safety state y provenance. El hash se calcula después de recibir la
imagen; nunca se compara con un hash de contenido imposible de predecir.

**Validación:** schema y límites de bytes/dimensiones; media sniffing; rights y
referencias; ausencia de scope expansion; presupuesto; E07 perceptual/brand/
accessibility review. Toda salida nace `QUARANTINED_PROPOSAL`; sólo E07 y una
decisión humana pueden hacerla elegible para composición. No publica.

**Primer adapter recomendado:** OpenAI `gpt-image-2` fijado por snapshot para
generación/edición. La documentación oficial expone endpoints de generación y
edición, entradas/salidas de imagen, tamaños flexibles y usage. Requiere API key
en secret store, límites reales, política de datos y pruebas con billing.

## Lane 2 — Deterministic Render

**Entrada:** CDD validado y target allowlisted (`HTML`, `SVG`, después PDF/PNG).

**Salida:** bytes deterministas, content hash, alternativa textual, renderer
version y receipt. Aquí sí aplica igualdad contra golden/hash cuando el renderer
y entorno están fijados. El `LocalDeterministicModelGateway` y Export Service
pertenecen a esta lane.

**Validación:** escaping, recursos remotos, accesibilidad estructural, render
cross-client, pixel/layout bounds y reproducibilidad. Exportar no equivale a
publicar ni aceptar.

## Lane 3 — Design Platform

**Entrada:** paquete importable o brand template, identidad de usuario/equipo,
OAuth scopes mínimos, rights, title, format y correlation ID.

**Salida:** remote design ID/version, owner/team, URLs temporales edit/view con
expiración, export job ID/status, formatos/páginas y hash de cada archivo
descargado. Los URLs temporales no se persisten como identidad canónica.

**Primer adapter recomendado:** Canva Connect para crear/importar diseños,
devolver una experiencia editable y exportar PNG/JPG/PDF/PPTX/MP4/GIF/HTML.
Su export es asíncrono, tiene scopes y rate limits propios, URLs descargables
temporales y errores de licencia/aprobación; todos deben convertirse en estados
tipados, no en retries ciegos.

**Segundo adapter:** Figma como fuente/inspector/exportador versionado. Su REST
API permite leer archivos/nodos y exportar JPG/PNG/SVG/PDF; la edición completa
requiere una decisión separada sobre Plugin API o un flujo de importación, por
lo que no debe prometerse como equivalente a Canva.

## Interfaz de producto resultante

- **Create:** recibe brief, evidencia, audiencia, canal, marca, restricciones,
  capturas/referencias y rights.
- **Studio:** compone CDD y ofrece tres acciones explícitas: `Generar propuesta`,
  `Renderizar versión` y `Abrir/crear en plataforma`.
- **Review:** compara variantes, lineage, derechos, accesibilidad y rubric E07.
- **Ops:** muestra provider/model/version, budget, job state, expiry, hashes,
  quarantine, retries y cancelación.
- **Export:** crea paquetes para newsletters, gráficos, presentaciones, social,
  briefs y otros medios contratados; cada adaptación conserva el mismo contexto
  y produce una versión distinta, nunca una mutación silenciosa.

Una captura de un sitio puede entrar como referencia sólo con manifest de
derechos. E03 extrae tokens candidatos (color, tipografía aproximada, ritmo,
forma), E05 conserva provenance y E07 comprueba similitud excesiva. El sistema
debe inspirarse en patrones de marca sin clonar activos protegidos ni afirmar
la fuente exacta cuando no esté verificada.

## Migración del contrato actual

1. Congelar `ProviderResponse` actual como `DeterministicRenderResponse` sin
   romper el runtime 0.1.
2. Añadir un discriminador `lane` al manifest 0.2 y schemas separados para
   `GenerativeAssetProposal` y `PlatformDesignHandle`.
3. Persistir receipts y assets en Project Graph con nodos distintos; ningún
   handle remoto sustituye CDD/version hash.
4. Agregar fixtures HTTP locales para OAuth expiry, 401/403/429, job polling,
   URL expiry, malformed media, oversize, cancellation y billing drift.
5. Ejecutar un único trial real por lane después de credentials/terms review.
6. Someter la migración a MAR antes de conectar credenciales o ampliar E06.

## Fuentes oficiales consultadas

- OpenAI GPT Image 2: https://developers.openai.com/api/docs/models/gpt-image-2
- OpenAI image streaming/events: https://platform.openai.com/docs/api-reference/images-streaming/image_generation/partial_image
- Canva Connect APIs: https://www.canva.dev/docs/connect/
- Canva Create design: https://www.canva.dev/docs/connect/api-reference/designs/create-design/
- Canva export jobs: https://www.canva.dev/docs/connect/api-reference/exports/create-design-export-job/
- Figma file/image endpoints: https://developers.figma.com/docs/rest-api/file-endpoints/

Las capacidades descritas son `VERIFIED / A` respecto de esas páginas al
2026-08-31. La selección propuesta es interpretación arquitectónica
`PROBABLE / B`; no demuestra credenciales, términos aprobados, ejecución real,
calidad visual ni aceptación.
