# Bloque 3 / Precision Intelligence — Contrato fundacional M01–M05 v0.1

> Estado: `CANDIDATE / LOCAL BOUNDED SUT`. Este contrato autoriza únicamente
> la implementación y prueba local del corte M01–M05. No es contrato común,
> producción, Relevance Gate, delivery, consentimiento ni aceptación global.

## Productor, consumidor y scope

- **Productores:** adapters explícitos de evidencia profesional, conductual,
  relacional, contextual y señales de decisión.
- **Consumidores:** M01, M03, M04 y M05; M02 consume sus outputs y señales de
  decisión explícitas.
- **Output:** perfiles/hipótesis tipados y `EngineAssessment` por motor.
- **Versión de implementación:** `0.1`.

Topología local:

`ProfessionalEvidence → M01`; `BehaviorEvents → M03`;
`InteractionHistory → M04`; `ContextEvidence → M05`;
`M01 + M03 + M04 + M05 + DecisionSignals → M02`.

## Primitiva común de evidencia

Todo `EvidenceRef` requiere:

- `evidence_id`, `source_identity` y `root_provenance` no vacíos;
- `observed_at` entero no negativo;
- `temporal_state` gobernado;
- `epistemic_state` limitado a las seis etiquetas protegidas;
- `confidence` A–E;
- `provenance_refs` no vacío y comenzando en `root_provenance`.

Un record es corriente para el corte sólo cuando `temporal_state=CURRENT` y
`observed_at <= now`. Futuro, stale, historical o superseded no se presenta
como evidencia actual.

## Contratos por motor

### M01 — Person Intelligence

Input: `ProfessionalFact[]` de una única identidad. Campos permitidos:
contexto profesional, responsabilidad, contacto funcional y proximidad de
decisión explícita. Edad, género, sexo, etnicidad, raza, religión, salud,
discapacidad, política, orientación sexual y personalidad son rechazados.

Output: `PersonProfile`; una proximidad no demostrada es `UNKNOWN`.
Conflictos entre facts permanecen `CONTRADICTED`; un buzón funcional nunca se
convierte por sí solo en autoridad decisoria.

### M03 — Behavioral Intelligence

Input: eventos observados con identidad, tiempo y procedencia. Output:
`BehavioralEvidenceProfile` con patrones por tema, formato, canal y CTA.

Invariantes: `open != interest`, `click != purchase intent`, `silence !=
rejection`. `UNSUBSCRIBE` se conserva como señal explícita que requiere
enforcement del ejecutor; M03 no ejecuta el bloqueo.

### M04 — Relationship Intelligence

Input: historial demostrable y `RelationshipPolicy` versionada/autorizada para
dormancy. Output: `COLD`, `AWARE`, `ENGAGED`, `CONVERSATIONAL`, `OPPORTUNITY` o
`DORMANT`, más permiso **contextual**.

La última transición de oportunidad prevalece. `ACTIVE` y `CLOSED` en el mismo
timestamp producen `CONTRADICTED`. Permiso contextual no es consentimiento
legal, de plataforma o de delivery.

### M05 — Context Intelligence

Input: señales tipadas `GLOBAL`, `INDUSTRY`, `ACCOUNT`, `ROLE`, `MOMENT` con
ventana temporal, polarity y clase `FACT/HYPOTHESIS`. Sin `GLOBAL` actual,
devuelve `RETURN_UPSTREAM`. Scopes faltantes permanecen visibles y producen
`PARTIAL`; polaridades opuestas para el mismo claim producen `CONTRADICTED`.

Output: `ContextRelevanceMap`. M05 informa qué ocurre; no emite una hipótesis
de decisión.

### M02 — Decision Intelligence

Input: outputs de M01/M03/M04/M05 y `DecisionSignal[]`. Output:
`DecisionHypothesis` con candidates `DRIVER`, `HORIZON`,
`EVIDENCE_PREFERENCE` y `FRAMING`.

Sólo selecciona un valor cuando existe un líder único por raíces de evidencia.
Empates quedan ambiguos; polarity positiva y negativa conserva contradicción.
La confidence derivada adopta la evidencia material más débil y nunca se
fortalece por repetición. Todo output permanece `HYPOTHESIS_NOT_FACT` y
`NO_DELIVERY_AUTHORITY`.

La fuente declarada de cada signal se limita a M01/M03/M04/M05,
`ACCOUNT_INTELLIGENCE` o `GOVERNED_RULE`; cualquier engine extranjero se
rechaza antes de formular la hipótesis.

## Precedencia de fallo

En el pipeline fundacional:

1. `RETURN_UPSTREAM` domina;
2. sin lo anterior, `CONTRADICTED` domina;
3. después, `PARTIAL` domina;
4. `ACCEPTED` sólo existe si todos los motores son `ACCEPTED`.

Wolfram agotó las `4^5 = 1024` combinaciones y confirmó las cuatro propiedades.
Esto es evidencia formal complementaria; no runtime ni gate acceptance.

## Identidad, replay y límites

- ID repetido + contenido idéntico: deduplicación idempotente local.
- ID repetido + contenido diferente: `PrecisionIdentityCollision`.
- Cada colección tiene un límite configurable; excederlo produce
  `PrecisionCapacityExceeded` sin resultado parcial oculto.
- Los outputs tienen fingerprint SHA-256 determinista sobre representación
  canónica.
- Cruce de `person_id`, `insight_id` o `target_id` produce rechazo.

## Error, recuperación y rollback

- Violación estructural: excepción contractual antes de output.
- Falta de input esencial: `RETURN_UPSTREAM` y ausencia de output dependiente.
- Evidencia no corriente: se omite y se registra por ID; el caller debe reparar
  o reemitir una versión corriente.
- Contradicción: se preserva; no hay resolución automática.
- El runtime no tiene efectos externos ni estado durable, por lo que rollback
  consiste en descartar el resultado inmutable y reejecutar con inputs nuevos.

## Non-claims

Este contrato no demuestra NLP, enrichment, CRM, entrega, consentimiento,
Relevance Gate, Message Intelligence, Timing/Channel, Learning, producción,
eficacia comercial, integración con Bloques 1/2 ni aceptación arquitectónica
global.
