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

## Evidencia disponible

Runtime E01–E08 local v0.4, 83 pruebas Block 2, 292 workspace, contratos v0.1,
reconciliación Slack/Notion/GitHub/Rovo y modelos formales Wolfram. No existe
todavía HEAD local, CI para esta arquitectura, provider API, UI ejecutada ni
revisión independiente.

## Recomendación

Aprobar sólo Slice 1 como candidate implementation boundary. Mantener adapters
reales, infraestructura distribuida, publicación y aceptación bloqueados hasta
sus revisiones separadas.

