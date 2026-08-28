# Bloque 3 — Dossiers ejecutables M06–M08 y A∴ v0.1

> Estado común: `IMPLEMENTED / EXECUTED / LOCAL BOUNDED SUT`;
> CI externa, integración y aceptación: `INSUFFICIENT EVIDENCE`.

| Componente | Semántica | Output | Fallo cerrado | No posee |
|---|---|---|---|---|
| Relevance Gate | suficiencia por dimensión | `RelevanceDecision` | stale/contradiction → return | delivery |
| Adaptive Controller | nivel L0–L3 sostenible | `AdaptiveLevelDecision` | guard/regression → L0 | gate o authority |
| M06 | estrategia comunicacional | `MessageStrategy` | asset inválido → return | facts/copy/send |
| M07 | timing/canal/presión propuestos | `DeliveryProposal` | stale/frequency/opt-out → wait/block | ejecución |
| M08 | siguiente prueba falsable | `NextBestTest` | cadena incompleta → no learning | promoción |

## Estado

| Unidad | Designed | Bound | Implemented | Executed | Validated | Integrated | Accepted |
|---|---|---|---|---|---|---|---|
| Gate | YES | LOCAL | YES | YES | LOCAL + oracle | FOUNDATION | NO |
| Adaptive | YES | LOCAL | YES | YES | LOCAL + oracle + Wolfram | FOUNDATION | NO |
| M06 | YES | LOCAL | YES | YES | LOCAL | FOUNDATION | NO |
| M07 | YES | LOCAL | YES | YES | LOCAL | FOUNDATION | NO |
| M08 | YES | LOCAL | YES | YES | LOCAL | FOUNDATION | NO |

## Red-team material

1. Assets declarativos podían simular autoridad de Bloque 2: reparado con
   authority reference, evidence source gobernada y freshness.
2. Historial de canal carecía de provenance: reparado con EvidenceRef y rechazo
   de stale history.
3. M08 podía recibir execution sobre `WAIT/DO_NOT_SEND`: reparado; sólo
   `SEND_CANDIDATE` admite receipt ejecutado.
4. La detección self-authored no reconocía `root:M08:*`: reparada y regresionada.
5. Raíces correlacionadas entre dimensiones no eran visibles: M05 y Gate ahora
   preservan root provenance y emiten razón explícita.

## Gaps

- autoridad real de Account Intelligence y assets de Bloque 2;
- adapters CRM/email y executor de delivery;
- firma/attestation de policies, assets, history, receipt y outcome;
- memoria durable, concurrency y tenancy;
- independent human review y hosted CI del head final;
- outcome real y validación causal/comercial.


