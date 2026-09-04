# Bloque 3 — Dossiers ejecutables M01–M05 v0.1

> Estado común: `IMPLEMENTED / LOCAL BOUNDED SUT`; validación externa e
> integración real `INSUFFICIENT EVIDENCE`.

| Motor | Semántica propia | Output | Fallo cerrado principal | No posee |
|---|---|---|---|---|
| M01 Person | contexto profesional y proximidad explícita | `PersonProfile` | sin evidencia actual: `RETURN_UPSTREAM` | psicología, decisión, delivery |
| M02 Decision | hipótesis falsable de decisión | `DecisionHypothesis` | sin signals actuales: `RETURN_UPSTREAM` | hechos personales, relevancia final, delivery |
| M03 Behavioral | patrones de eventos observados | `BehavioralEvidenceProfile` | no inventa patrón desde open/silence | intención, preferencia confirmada, causalidad |
| M04 Relationship | estado relacional y contexto permitido | `RelationshipProfile` | transición simultánea conflictiva: `CONTRADICTED` | consentimiento o permiso legal |
| M05 Context | mapa Global→Moment | `ContextRelevanceMap` | sin Global actual: `RETURN_UPSTREAM` | hipótesis de decisión o message strategy |

## Estado por dimensión

| Motor | Designed | Bound | Implemented | Executed | Validated | Integrated | Accepted |
|---|---|---|---|---|---|---|---|
| M01 | YES | LOCAL | YES | YES | LOCAL / 8 vectores | FOUNDATION ONLY | NO |
| M02 | YES | LOCAL | YES | YES | LOCAL / 6 vectores directos + pipeline | FOUNDATION ONLY | NO |
| M03 | YES | LOCAL | YES | YES | LOCAL / 5 vectores | FOUNDATION ONLY | NO |
| M04 | YES | LOCAL | YES | YES | LOCAL / 8 vectores | FOUNDATION ONLY | NO |
| M05 | YES | LOCAL | YES | YES | LOCAL / 6 vectores | FOUNDATION ONLY | NO |

## Dependencias y autoridad

- M01/M03/M04/M05 pueden ejecutarse independientemente sobre sus clases de
  evidencia.
- M02 depende de outputs íntegros de esos cuatro motores y señales explícitas.
- El pipeline no posee Relevance Gate ni authority plane.
- `UNSUBSCRIBE` se observa localmente; enforcement permanece en el ejecutor
  autorizado futuro.
- Los thresholds de dormancy pertenecen a `RelationshipPolicy`, no a la
  ontología de M04.

## Observabilidad

Cada `EngineAssessment` expone motor, disposition, razones, evidence IDs y
fingerprint de output. Outputs preservan omisiones, contradicciones,
restricciones y fingerprints de inputs materiales.

## Ataques ejecutados

- atributo personal prohibido;
- identidad reutilizada con payload diferente;
- mezcla de personas/insights/targets;
- evidencia futura/stale/expirada;
- facts y proximity contradictorios;
- open/click/silence sobredimensionados;
- unsubscribe sin authority shortcut;
- transición de oportunidad desordenada y simultánea;
- context sin Global y scopes incompletos;
- fact/hypothesis leakage;
- polarity opuesta;
- empate de drivers;
- confidence inflation;
- fuente de DecisionSignal no gobernada;
- repetición de una raíz presentada como corroboración;
- intento de continuar M02 tras fallo upstream;
- caso real de buzón funcional de atención al cliente.

## Gaps antes de promoción

1. Contrato autorizado de Account Intelligence.
2. Binding interbloques a outputs reales de Bloque 1 y assets de Bloque 2.
3. Adapter de eventos CRM/email con identidad, consentimiento y retención.
4. Catálogo gobernado de reglas que produzca `DecisionSignal`.
5. Relevance Gate y oráculo independiente.
6. Storage, replay durable, concurrency, SLOs y observabilidad de producción.
7. CI externa en SHA exacto y revisión independiente posterior a la última
   reparación.
