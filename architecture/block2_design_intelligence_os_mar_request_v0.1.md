# Master Architecture Review Request — Block 2 Design Intelligence OS

> Fecha: `2026-08-30` · Estado: `OPEN / NO PROMOTION`

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

## Evidencia disponible

Runtime E01–E08 local v0.4, 161 pruebas Block 2 y 449 pruebas workspace,
contratos v0.1, reconciliación Slack/Notion/GitHub/Rovo y modelos formales
Wolfram. La rama reconciliada con `main` tiene SHA
`6c3adb15484af34e654b650f8b1b2a71010af79e`; GitHub Actions run
`33464431457` concluyó `success`. La UI Create/Studio/Ops fue ejecutada en Edge
y tiene un probe automatizado de reflow, nombres, targets y navegación. Siguen
pendientes un provider API real, NVDA/VoiceOver y la decisión humana de este
MAR; ninguno se infiere del CI.

## Recomendación

Aprobar sólo Slice 1 como candidate implementation boundary. Mantener adapters
reales, infraestructura distribuida, publicación y aceptación bloqueados hasta
sus revisiones separadas.
