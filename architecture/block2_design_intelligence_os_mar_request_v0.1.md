# Master Architecture Review Request — Block 2 Design Intelligence OS

> Fecha de actualización: `2026-09-02` · Estado: `OPEN / NO PROMOTION`

## Cambio solicitado

Revisar la introducción de Project Graph, Canonical Design Document, Design
Orchestrator, Engine Registry, Model Gateway y Export Service como common
architecture del Bloque 2, conservando E01–E08 v0.4.

## Decisiones requeridas

1. Ownership común del state machine y reglas de invalidación.
2. Autoridad/formato de DecisionRecord y external validation.
3. CDD/Project Graph como contratos compartidos y migración de dataclasses.
4. Credential/provider boundary y condiciones de adapter real.
5. Persistencia local v0.1 y requisitos de futura migración durable.
6. Relación entre export, publication, delivery y acceptance.
7. Firma/attestation de checkpoints, receipts y memory promotion.
8. Aprobar o rechazar la separación `GENERATIVE_MEDIA`,
   `DETERMINISTIC_RENDER` y `DESIGN_PLATFORM` propuesta en
   `block2_provider_lane_architecture_v0.1.md`; elegir providers y secret owner.
9. Decidir si el recibo E01 y el preflight de provider candidato son
   instrumentación suficiente para pasar a un trial autorizado. La respuesta
   no puede inferirse de sus tests: ambos siguen fail-closed/no operativos.

## Evidencia disponible

Runtime E01–E08 local v0.4, contratos candidatos v0.1 y 468/468 pruebas
workspace en un solo proceso. La rama de PR #11 tiene SHA
`cd7c144ba3db2943fe7294a866b5a4e3fd94e16a`; GitHub Actions run
`33707108439` concluyó `success` para tests, compilación, consola y ambos
runtimes de referencia. La UI Create/Studio/Ops fue ejecutada en Edge y tiene
un probe automatizado de reflow, nombres, targets y navegación por teclado.

Como deltas posteriores al request inicial: E08 soporta reinicio, integridad,
deprecación, rollback y concurrencia durable; E01 tiene validación estructural
de receipt; y existe un preflight de provider que sólo acepta handles no
secretos y conserva `NOT_ACCEPTED`. Ninguno es una validación de provider real,
un objeto upstream autorizado ni una decisión MAR. Slack y Notion no aportaron
una promoción vigente; el último intento formal Wolfram de este ciclo falló
internamente y se clasifica `INSUFFICIENT EVIDENCE`.

Siguen pendientes un provider API real gobernado, revisión NVDA/VoiceOver,
fixture E01 autorizado con observador independiente y la decisión humana de
este MAR; ninguno se infiere del CI.

## Recomendación

Aprobar sólo el boundary de implementación candidata si las decisiones 1–9 se
resuelven expresamente. Mantener adapters reales, infraestructura distribuida,
publicación y aceptación bloqueados hasta sus revisiones separadas. Un rechazo
debe identificar el contrato afectado y preservar la evidencia actual como
histórica, sin reescribir sus estados.
