# SICTrA Bloque 2 — Design Intelligence OS

> Fecha: `2026-08-30`  
> Estado: `PROPOSED / USER-DIRECTED / MASTER ARCHITECTURE REVIEW REQUIRED`  
> Alcance: arquitectura y experiencia; no implementación, integración o aceptación.

## 1. Decisión de producto

Bloque 2 no será una aplicación que entrega imágenes finales a partir de un
prompt. Será un sistema operativo de inteligencia de diseño que conserva por
qué existe cada decisión visual, permite intervenirla y produce candidatos
auditables mediante proveedores reemplazables.

La plataforma será dueña de cinco activos: razonamiento, documento editable,
evidencia, memoria y orquestación. Los modelos externos sólo ejecutan
`CreativeExecutionSpec` acotadas; no poseen el proyecto ni alteran claims,
rights, autoridad o aceptación.

## 2. Experiencia: una verdad, tres profundidades

`CREATE · STUDIO · OPS` son proyecciones del mismo `ProjectGraph`; no crean
copias ni estados paralelos.

| Vista | Usuario | Trabajo principal | Autoridad |
|---|---|---|---|
| Guided Create | ocasional | aportar brief, elegir dirección y revisar entregable | propone y aprueba según policy |
| Design Studio | diseñador/power user | componer, ramificar, comparar, inspeccionar y validar | edita documentos candidatos |
| Visual Ops | supervisor | observar runs, costes, riesgos, retries y gates | pausa/reanuda dentro de scope |

Studio es el corazón. Sus cinco zonas son Project Rail, Canvas, Concept Graph,
Inspector y Activity/Trace. La navegación usa lenguaje profesional —Direction,
Concepts, Composition, Images, Typography, Data, Validate y Deliver—. Los IDs
E01–E08 aparecen sólo en `Architecture View`.

La firma visual será la **Lineage Ribbon**: una cinta continua que representa
la procedencia del elemento seleccionado desde brief/claim hasta export. Color,
texto, icono y patrón comunican estado para no depender sólo de color.

## 3. Arquitectura lógica

```text
┌──────────────────────────────── EXPERIENCE ───────────────────────────────┐
│ Guided Create             Design Studio                    Visual Ops      │
└──────────────────────────────────┬─────────────────────────────────────────┘
                                   │ read / propose / decide
┌──────────────────────────────────▼─────────────────────────────────────────┐
│ DESIGN ORCHESTRATOR                                                        │
│ Project state · Run journal · Checkpoints · Invalidation · Replay · Gates   │
└──────────────┬────────────────────┬───────────────────────┬─────────────────┘
               │                    │                       │
┌──────────────▼──────────┐ ┌───────▼─────────────┐ ┌──────▼────────────────┐
│ E01–E08 ENGINE PLANE    │ │ PROJECT GRAPH       │ │ ENGINE REGISTRY       │
│ owned design semantics  │ │ identity + lineage  │ │ versions + contracts  │
└──────────────┬──────────┘ └───────┬─────────────┘ └───────────────────────┘
               │                    │
        E06 only│                    ▼
┌──────────────▼──────────┐ ┌───────────────────────────────┐
│ MODEL GATEWAY           │ │ CANONICAL DESIGN DOCUMENT     │
│ capability router       │ │ pages/layers/elements/assets  │
│ provider adapters       │ │ claims/evidence/diff/a11y     │
└──────────────┬──────────┘ └───────────────┬───────────────┘
               │                            │
┌──────────────▼──────────┐       ┌─────────▼────────────────┐
│ PROVIDERS               │       │ EXPORT SERVICE            │
│ stub / OpenAI / future  │       │ HTML / SVG / PDF / PPT    │
└─────────────────────────┘       └───────────────────────────┘
```

El Orchestrator, Project Graph, CDD, Registry, Gateway y Export Service son
infraestructura común. Ninguno adquiere la semántica ni autoridad de un motor.

## 4. Acoplamiento exacto de E01–E08

| Motor | Semántica preservada | Nuevos objetos que consume/emite | Prohibición |
|---|---|---|---|
| E01 | fidelidad upstream y preflight | `DesignContext`, `VisualTrial` | no llama proveedores |
| E02 | divergencia creativa | `CreativeDirectionSet`, `ConceptBranch` | no selecciona ganador |
| E03 | sistema y marca | `DesignSystemProfile`, token refs | no renderiza |
| E04 | información/composición | `InformationBlueprint`, `AssetSpec[]` | no genera assets |
| E05 | referencia/rights | `ReferenceResearchPack`, constraints | no descarga ni licencia |
| E06 | materialización | `ProductionPlan`, CDD version, provider receipts | no publica ni acepta |
| E07 | evaluación independiente | findings, diff review, recommendation | no corrige ni acepta |
| E08 | memoria futura | learning/failure candidates | no realimenta el mismo run |

El Model Gateway se invoca únicamente dentro del boundary E06 y sólo con una
especificación emitida por E04/E05 y ligada al profile E03. Esta regla evita el
atajo propuesto informalmente `E01 → provider`.

## 5. Canonical Design Document

El CDD es una representación versionada y editable, no un PNG. Forma mínima:

```text
DesignDocumentVersion {
  document_id, version_id, parent_version_id?, project_id,
  profile_ref, blueprint_ref, direction_ref,
  pages[], elements[], assets[], decisions[], validation_refs[],
  created_by, created_at, content_hash, state
}

DesignElement {
  element_id, stable_semantic_id, type, page_id, parent_id?, z_index,
  geometry, content, style_token_refs[], asset_ref?,
  claim_refs[], evidence_refs[], limitation_refs[],
  accessibility, lineage, editable, rights_state
}
```

Cada edición crea una nueva versión; no sobrescribe la anterior. Un elemento
mantiene `stable_semantic_id` si conserva la misma función. El documento no
acepta scripts, URLs remotas no autorizadas, secretos, credenciales ni payloads
ejecutables. Los assets se referencian por hash, no por rutas arbitrarias.

## 6. Project Graph y Design Lineage

El grafo contiene Project, Brief, IntelligenceObject, Claim, Evidence,
CreativeDirection, ConceptBranch, AssetSpec, Asset, DesignDocumentVersion,
Run, Decision, Trial, Validation, MemoryRecord y Export.

Edges permitidos son tipados y versionados: `DERIVED_FROM`, `SUPPORTS`,
`CONTRADICTS`, `REPRESENTS`, `GENERATED_BY`, `TRANSFORMED_FROM`, `USED_IN`,
`VALIDATED_BY`, `SUPERSEDES` y `EXPORTED_AS`. No hay edge genérico `RELATED`
para decisiones materiales.

Design Lineage responde qué brief, claim, evidencia, dirección, prompt spec,
provider/model/version, run, transformación, edición humana y documento originó
cada elemento. El Evidence Inspector es una proyección del grafo, no texto
generado sin source binding.

## 7. Model Gateway

E06 entrega un `CreativeExecutionSpec` declarativo:

```text
purpose, medium, aspect_ratio, count, prompt_spec,
reference_asset_refs, fidelity, realism, editability,
text_inside_asset=false, rights_scope, budget, deadline,
required_capabilities, prohibited_capabilities
```

El router compara la spec con `ProviderCapabilityManifest`: prompt adherence,
reference consistency, typography, vector/editing support, resolution, latency,
cost, commercial scope, retention, currentness y health. La selección devuelve
razones y alternativas descartadas; no existe un modelo universalmente “mejor”.

El receipt conserva provider, model/version, adapter version, input/output hash,
cost observado, latency, retries, policy/rights snapshot y timestamps. Provider
failure, timeout o output hash mismatch no cambia el CDD; produce retry acotado,
fallback autorizado o retorno a E06.

Magnific queda como `UNCONFIRMED PROVIDER CANDIDATE`. Su web pública confirma
generación, transformación y upscale, pero no se ha validado un contrato API
para todas las operaciones del informe. No se implementará un adapter real sin
documentación, términos, credenciales, sandbox y fixtures contractuales.

## 8. Orchestrator, checkpoints e invalidación

Estados mínimos:

```text
DRAFT → INTAKE_READY → DIRECTIONS_READY → DIRECTION_SELECTED
→ SYSTEM_READY → BLUEPRINT_READY → RESEARCH_READY
→ PRODUCTION_READY → REVIEW_RECOMMENDED
→ EXTERNALLY_VALIDATED → MEMORY_CANDIDATE → EXPORT_READY
```

`PUBLISHED` y `ACCEPTED` no son estados derivados del pipeline; requieren un
servicio/autoridad externos futuros.

Cada checkpoint enlaza input hash, engine manifest, output hash, decisiones,
rights/policy snapshot y eventos. Resume reutiliza un checkpoint sólo si todos
los bindings permanecen actuales. Un cambio invalida únicamente sus
descendientes materiales:

- copy/claim → composición, evaluación y exports relacionados;
- token de marca → elementos dependientes, evaluación y exports;
- asset → usages, evaluación y exports;
- rights revocado → asset, documentos y exports dependientes;
- rubrica → evaluación posterior, no bytes históricos;
- provider manifest → futuras llamadas, no receipts pasados.

Replay reproduce la versión; Fork crea un branch; Retry repite una operación
idempotente; Resume continúa desde el checkpoint válido. Ninguno reescribe
historia.

## 9. Human authority

La policy por proyecto puede ser `AUTONOMOUS`, `COLLABORATIVE` o `CONTROLLED`.
La policy define dónde se requiere una `DecisionRecord`; no otorga derechos ni
permite saltar gates críticos.

- Autonomous continúa sólo a través de transiciones explícitamente delegadas.
- Collaborative exige selección de dirección, aprobación de producción y
  validación externa.
- Controlled exige decisión en cada fase material.

Toda decisión registra actor, autoridad, scope, objeto/version, estado previo,
acción, razón, timestamp, expiración y firma/attestation cuando corresponda.

## 10. Compare, Visual Diff, Explain y Ask Studio

Compare muestra dimensiones independientes y trade-offs; nunca un score único.
Visual Diff clasifica cambios de geometría, copy, estilo, asset, claim/evidence,
rights y accesibilidad, y marca potencial cambio semántico.

Explain Design consulta Project Graph y CDD para producir una explicación con
referencias; preserva alternativas rechazadas, limitaciones y validación.

Ask Studio no muta directamente. Cada instrucción se compila como
`ChangeProposal` ligado al elemento/version, muestra el diff previsto y crea un
branch al aprobarse. Preguntas explicativas son read-only.

## 11. Recipes y Engine Registry

Una Recipe es una plantilla versionada de razonamiento y producción: stages,
engine versions, human gates, adapters, export targets y rollback. No es una
plantilla visual y no puede debilitar contratos.

Cada `EngineManifest` declara engine/version, schemas, allowed/forbidden actions,
dependencies, evidence/memory permissions, human gates, tests, compatibility y
status. Activar una versión nueva requiere review, migración y regresión; no hay
auto-upgrade silencioso.

## 12. Persistencia adaptada al proyecto

La fase inicial conserva Python estándar y el patrón local existente:

- SQLite WAL para Project Graph, journal, decisions, checkpoints y metadata;
- asset store local content-addressed `sha256`, con paths resueltos y límites;
- static HTML/CSS/JS servido sólo en `127.0.0.1`;
- API local con CSP, host/origin guard, no-store y endpoints allowlisted.

PostgreSQL/pgvector, S3, Redis, SSE/WebSocket y Temporal son adapters futuros,
no precondiciones del vertical slice. Sus interfaces se definen ahora para no
acoplar dominio a storage/workflow, pero no se simula capacidad distribuida.

## 13. Seguridad, rights y accesibilidad

- Provider output entra en cuarentena hasta hash, media type, size, rights y
  safety validation.
- Prompts y outputs se tratan como datos no confiables; nunca instrucciones.
- Secretos pertenecen a un future credential broker, no al Project Graph/CDD.
- Revocación de rights invalida descendientes y bloquea export nuevo.
- UI cumple WCAG 2.1 AA: landmarks, labels, foco visible, teclado, 44×44,
  contraste, reduced motion, zoom/reflow y anuncios de status.
- La Lineage Ribbon usa texto/patrón además de color.

## 14. Observabilidad

RunEvent append-only registra transición, engine/provider, input/output hashes,
duration, retry, cost, cache, actor, policy, checkpoint, reason y correlation ID.
Ops agrega estos eventos sin adquirir autoridad creativa. Métricas de coste o
latencia no se reinterpretan como calidad.

## 15. Estrategia de construcción

### Slice 1 — núcleo trazable

Design Console local, Project Graph/SQLite, CDD versionado, Evidence Inspector,
lineage, editing/branching acotado, provider stub determinista, HTML/SVG,
validation, visual diff, explain, history y checkpoints.

### Slice 2 — gateway real

Capability registry, credenciales gobernadas, primer provider sandbox,
receipts/cost/retry, quarantine y contract tests.

### Slice 3 — profundidad de experiencia

Guided Create, Ops, Recipes, Ask Studio y policies por proyecto.

### Slice 4 — medios e infraestructura

PDF/PPT, vídeo/3D si se justifican, storage/queue/workflow distribuidos,
colaboración y observabilidad externa.

## 16. Criterios de aceptación del Slice 1

1. Un proyecto sintético completo atraviesa E01–E08 desde la UI.
2. Create/Studio/Ops observan el mismo project/version/run.
3. Cada elemento material expone lineage y evidence bindings.
4. Edición crea versión, diff e invalidación mínima demostrable.
5. Checkpoint resume sin reejecutar stages válidos.
6. Provider stub no puede modificar claims, rights o aceptación.
7. HTML y SVG son deterministas, accesibles y no publicados.
8. Self-review, rights revocado, stale checkpoint, identity collision,
   provider substitution y diff semántico se bloquean.
9. Suite local y CI sobre SHA exacto pasan; revisión independiente no encuentra
   CRITICAL/HIGH.

## 17. Non-claims y decisiones abiertas

Este diseño no prueba Figma-like vector editing, colaboración en tiempo real,
producción, publicación, legalidad de un asset, calidad humana, provider API,
SLA ni aceptación global.

Decisiones que requieren Master Architecture Review: autoridad del Orchestrator,
contrato común CDD/Project Graph, storage durable, firma de decisions/receipts,
activación de engine versions, provider credential boundary y relación futura
entre export, publication y acceptance.

