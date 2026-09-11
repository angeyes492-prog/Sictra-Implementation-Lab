# Bloque 2 / Design Intelligence OS — Architecture Candidate v0.5

> Clasificación: `ARCHITECTURAL CHANGE / CANDIDATE / MAR REQUIRED`  
> Fuente: dirección humana + runtime v0.4 + contratos E01–E08 v0.1.  
> Certeza/confianza: `PLAUSIBLE / B`; CDD y Project Graph tienen ahora una
> implementación acotada local v0.1, sin MAR, CI, integración o aceptación.

## Propósito, alcance y decisión

Extender el runtime acotado E01–E08 hacia un Design Intelligence OS sin alterar
la propiedad semántica de los motores. La arquitectura introduce seis
componentes comunes: Design Orchestrator, Project Graph, Canonical Design
Document, Engine Registry, Model Gateway y Export Service. Son infraestructura,
no motores adicionales ni autoridades globales.

La especificación completa está en
`docs/superpowers/specs/2026-08-30-block2-design-intelligence-os-design.md`.

## Ownership y contratos

| Componente | Owns | No owns | API candidata |
|---|---|---|---|
| Orchestrator | run state, journal, checkpoints, invalidation | contenido, calidad, aceptación | start/resume/retry/fork/replay |
| Project Graph | IDs, typed edges, version lineage | verdad o autorización | append/query/trace/diff-roots |
| CDD | documento editable versionado | provider o publicación | create_version/apply_proposal/diff |
| Engine Registry | manifests y compatibility | auto-activation | resolve/pin/verify |
| Model Gateway | capability match y execution receipts | prompts semánticos/claims/rights | plan/execute/status/cancel |
| Export Service | serialización contratada | delivery/publication | preflight/render/package |

## Inputs y outputs

Entrada raíz: Design Context Envelope actual y autorizado. Objetos intermedios:
DirectionSet, SelectionRecord, SystemProfile, InformationBlueprint,
ReferenceResearchPack, AssetSpec, ProductionPlan, CDD version, VisualAssessment,
ExternalValidation y MemoryCandidate. Salidas: candidatos HTML/SVG y paquetes
de export no publicados con lineage completo.

## Invariantes

1. E01–E08 conservan la semántica descrita en runtime v0.4.
2. Sólo E06 puede invocar Model Gateway.
3. `PROJECT GRAPH != SOURCE OF TRUTH FOR FACTS`; sólo conserva objetos/edges.
4. `CDD VERSION != RENDER != EXPORT != PUBLICATION`.
5. Resume exige hashes/manifests/policies actuales; `UNKNOWN != VALID`.
6. Editar crea versión; deprecar conserva historia; collision no sobrescribe.
7. Provider output está en cuarentena hasta validation.
8. E07 recomienda; autoridad externa valida; E08 registra para futuro.
9. UI no puede inventar una transición que el Orchestrator rechaza.
10. Local runtime evidence no promueve arquitectura compartida.

## Estado y recuperación

El state machine candidato avanza desde DRAFT hasta EXPORT_READY con gates
explícitos de selección y validación externas. Una transición fallida registra
reason y conserva el último checkpoint válido. Retry es idempotente; Resume
revalida currentness; Fork crea nueva lineage; Replay no muta historia. Rights
revocado o identity collision bloquean y propagan invalidation tipada.

## Seguridad y observabilidad

Entradas/provider outputs son no confiables; no scripts, URLs remotas, paths o
credenciales en CDD. Assets se direccionan por contenido. El journal append-only
registra actor, engine/provider manifest, hashes, policy, rights, latency, cost,
retry y correlation. Ops lee el journal; no lo convierte en evaluación.

## Compatibilidad y migración

El runtime v0.4 se encapsula como primer Engine Plane. Los dataclasses actuales
se adaptarán a Project Graph/CDD mediante adapters explícitos; no se reescriben
silenciosamente. SQLite/local assets son backend v0.1. Futuras implementaciones
PostgreSQL/S3/Temporal deben satisfacer las mismas interfaces y contract tests.

## Impactos

- Directo: nuevos contratos comunes, storage, UI y provider boundary.
- Segundo orden: mayor superficie de seguridad, migrations, a11y, visual diff,
  cost/latency y reproducibilidad.
- Tercer orden: un error en invalidación o memoria puede contaminar versiones,
  exports y futuros recipes; exige property/mutation tests independientes.
- Coste de migración: moderado en Slice 1; alto si se introduce infraestructura
  distribuida antes de estabilizar CDD/Project Graph.

## Validación y promoción

Requiere schema/contract/property/adversarial/integration/end-to-end, restart,
concurrency, tamper, rights revocation, provider substitution, stale checkpoint,
semantic diff, a11y y browser tests. Ningún gate cambia con este documento.
Promoción necesita MAR, implementación, CI exacta, revisión independiente y
aceptación humana separada.

## Delta ejecutable local 2026-08-30

El primer componente de Slice 1 implementa CDD, Project Graph SQLite WAL y un
adapter trazable sobre runtime v0.4. No cambia la semántica E01–E08. Evidencia:
`evidence/block2_traceable_state_local_cycle_2026-08-30.md`; ledger:
`closure/block2_design_intelligence_os_slice1_v0.1.md`. Estado común permanece
`CANDIDATE / MAR REQUIRED`.

El read model local Design Console implementa Project Rail, semantic canvas,
Evidence Inspector y Lineage Ribbon sobre el mismo grafo. Es deliberadamente
sólo lectura; Create, Ops, edición/diff y checkpoints siguen pendientes. La
revisión visual y responsive está en
`evidence/block2_design_console_local_cycle_2026-08-30.md`.

E06 usa ahora el Model Gateway local determinista y el Project Graph conserva
la ruta E06→receipt→asset. El manifiesto está fijado por identidad y hash
canónico. Esto prueba la frontera local, no un proveedor externo. Evidencia:
`evidence/block2_model_gateway_local_cycle_2026-08-30.md`.

## Delta ejecutable local 2026-08-31

Document Evolution, semantic diff, invalidation, checkpoint/resume, edición
controlada de Studio y Export Service HTML/SVG están ejecutados localmente. El
E2E conserva E01–E03 tras edit de contenido, exige E04–E08 y bloquea export de
la versión editada hasta revalidación. Evidencia:
`evidence/block2_slice1_evolution_checkpoint_export_cycle_2026-08-31.md`.
La reejecución parcial real, Engine Registry, Create/Ops, provider sandbox,
Git/CI y review independiente siguen pendientes; arquitectura común permanece
`CANDIDATE / MAR REQUIRED`.

## Delta ejecutable local 2026-08-31 — Registry/Resume/Ops

Engine Registry fija e importa manifests E01–E08 y persiste sus identidades en
Project Graph. El Orchestrator distingue reuso de ejecución y reejecuta el
sufijo real desde E04 después de invalidación de contenido; el E2E conserva
E01–E03, ejecuta E04–E08 y registra el Resume. Ops presenta esa procedencia en
un read model responsive. Evidencia:
`evidence/block2_registry_partial_ops_cycle_2026-08-31.md`.

Create, provider sandbox, Git/CI, revisión independiente y MAR permanecen
pendientes; no cambia el gate global `YELLOW / NOT ACCEPTED`.

## Delta ejecutable local 2026-08-31 — Create/Provider Sandbox

Create compila un handoff explícito en Design Context Envelope o devuelve todos
los faltantes sin payload utilizable. Su UI muestra un Handoff Seal y conserva
la frontera `CONTINUE != E01 EXECUTED`. E06 dispone de sandbox gobernado para
adapters inyectados con manifest, policy, rights, budget, timeout, cancelación,
output limits, receipts y cuarentena. Evidencia:
`evidence/block2_create_provider_sandbox_cycle_2026-08-31.md`.

La vinculación Create→run, un adapter de proveedor real, history/diff visual,
validación independiente, Git/CI y MAR continúan pendientes. Estado global:
`YELLOW / NOT ACCEPTED`.

Create se vincula ahora al run por igualdad exacta de fingerprint, message y
campos upstream; E01 conserva un edge hacia el Design Context. Studio presenta
historia/diff, y Project Graph pasó restart, rollback por cierre y contención de
seis writers. No se promueve el gate hasta resolver evidencia externa restante.
