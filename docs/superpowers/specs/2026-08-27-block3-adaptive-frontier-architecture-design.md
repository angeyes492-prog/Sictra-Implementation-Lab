# Telecare OS / Bloque 3 — Arquitectura A∴ Adaptive Frontier v0.1

> **Estado:** `CANDIDATE / USER-APPROVED DESIGN`; requiere Master Architecture
> Review antes de promover contratos comunes o autoridad interbloques.
> **Fecha:** 2026-08-27, America/Tegucigalpa.
> **Base ejecutable:** M01–M05 bounded runtime, PR #7, SHA
> `b1fa1948fe20f45190b3228d0cc889d71c14a81a`.
> **Base normativa:**
> `architecture/block3_precision_intelligence_engine_model_v1.md`.
> Este documento extiende la dirección de diseño; no demuestra runtime,
> integración, delivery, outcome ni aceptación global.

## 1. Decisión

Se adopta como arquitectura objetivo **A∴ Adaptive Frontier**:

1. un núcleo determinista, reproducible y gobernado por contratos;
2. una envolvente adaptativa que puede ampliar recuperación contextual,
   selección entre alternativas autorizadas y experimentación;
3. una frontera de versión que impide que el aprendizaje modifique la
   ejecución que lo produjo;
4. una regla de eficiencia marginal que detiene o revierte adaptación cuando
   su beneficio deja de compensar coste, latencia, complejidad o riesgo.

La arquitectura preserva las jurisdicciones de M01–M05. No redefine sus
outputs, no convierte observaciones en hechos, no promueve hipótesis y no
transfiere autoridad de consentimiento o delivery al Bloque 3.

## 2. Objetivo y resultado esperado

Completar Precision Intelligence con Relevance Gate, Persona State,
Personalization Ceiling, M06 Message Intelligence, M07 Timing & Channel
Intelligence y M08 Learning Engine sin deshacer el runtime fundacional.

El resultado de una ejecución es una cadena reproducible:

```text
M01/M03/M04/M05 → M02 → Precision Context Pack → Relevance Gate
→ M06 Message Strategy → M07 Delivery Proposal
→ external Delivery Enforcement → Outcome Ledger
→ M08 Next Best Test → Candidate Queue → Governance Review
→ Future Version Registry
```

La flecha hacia una versión futura es temporal. No existe un ciclo dentro de
una ejecución.

## 3. Non-goals y límites de autoridad

Esta arquitectura no autoriza:

- enriquecimiento externo no contratado;
- diagnóstico psicológico o atributos sensibles de persuasión;
- generación de facts por similitud semántica;
- rediseño de identidad editorial de Bloque 2;
- envío de mensajes, uso de credenciales o selección final de destinatario;
- inferencia de consentimiento, opt-in u opt-out enforcement;
- promoción automática de aprendizaje a regla;
- modificación de M01–M07 por M08 dentro de la misma generación;
- aceptación global a partir de diseño, tests locales o CI acotada.

## 4. Principios e invariantes

1. `MORE MEMORY != MORE AUTHORITY`.
2. `RELEVANCE != DELIVERY PERMISSION`.
3. `SEMANTIC MATCH != EVIDENCE`.
4. `OBSERVATION != INFERENCE != HYPOTHESIS != RULE`.
5. `CEILING = MAXIMUM ALLOWED`, nunca nivel objetivo.
6. La estrategia aplicada cumple `applied_level <= effective_ceiling`.
7. Una ejecución usa un snapshot inmutable y una versión única de políticas.
8. Toda degradación reduce capacidad; nunca relaja controles.
9. M08 termina en una candidate queue; no escribe estados aceptados.
10. La ruta L0 determinista permanece disponible como fallback.
11. Ante empate, contradicción o evidencia insuficiente prevalece la opción
    menos adaptativa y de menor presión.
12. Ningún beneficio cuantitativo compensa una violación de autoridad,
    privacidad, provenance, auditabilidad o rollback.

## 5. Componentes y ownership

| Componente | Semántica propia | Output | No posee |
|---|---|---|---|
| M01–M05 | perfiles e hipótesis fundacionales | outputs v0.1 existentes | gate, mensaje, delivery |
| Context Pack Composer | congelar inputs y outputs materiales de una ejecución | `PRECISION_CONTEXT_PACK` | reinterpretar evidencia |
| Persona State Projector | estado temporal derivado | `PERSONA_STATE_PROJECTION` | etiqueta permanente o psicología |
| Ceiling Resolver | máximo de personalización permitido | `PERSONALIZATION_CEILING` | relevancia o consentimiento |
| Relevance Gate | suficiencia de relevancia por dimensiones | `RELEVANCE_DECISION` | valor comercial probado o delivery |
| M06 | estrategia comunicacional | `MESSAGE_STRATEGY` | facts, copy obligatorio o envío |
| M07 | propuesta de timing, canal y presión | `DELIVERY_PROPOSAL` | ejecución, credenciales o consentimiento |
| Delivery Enforcement externo | revalidar y ejecutar según autoridad | `DELIVERY_RECEIPT` o rechazo | reinterpretar estrategia |
| Outcome Ledger | registrar eventos y outcomes atribuibles | records inmutables | causalidad automática |
| M08 | inferencia de aprendizaje y siguiente prueba | `NEXT_BEST_TEST` | promoción o escritura directa |
| Adaptive Frontier Controller | nivel adaptativo permitido | `ADAPTIVE_LEVEL_DECISION` | gate, facts o delivery |
| Governance Review | aceptar o rechazar candidatos futuros | decisión de promoción | reescribir historia |
| Version Registry | publicar configuración aceptada | versión inmutable | autoaprobación |

El Composer, Projector, Resolver, Gate, Controller, memoria y Registry son
arquitectura común del Bloque 3; no se presentan como motores adicionales.

## 6. Precision Context Pack

Cada ejecución genera un paquete inmutable con:

- `context_snapshot_id`, `schema_version`, `policy_version`, `created_at` y
  ventana de vigencia;
- identidades de persona, cuenta, insight, tenant y propósito autorizado;
- fingerprints de M01–M05;
- facts, observaciones, inferencias e hipótesis en colecciones separadas;
- evidencia, provenance roots, certainty, confidence y temporal state;
- contradicciones, omisiones, alternativas y restricciones;
- Persona State derivado y Personalization Ceiling;
- assets de Bloque 2 permitidos por identidad y versión;
- adaptive level autorizado para esa ejecución.

Si cambia una fuente o política, se crea un nuevo snapshot. No se modifica el
snapshot anterior. Cruce de identidad, versión incompatible o evidencia
esencial no vigente produce `RETURN_UPSTREAM`.

## 7. Relevance Gate

### 7.1 Vector visible

Evalúa por separado `GLOBAL`, `INDUSTRY`, `ACCOUNT`, `ROLE`, `MOMENT` e
`OBSERVED_INTEREST`. Cada dimensión declara:

- estado: `SUPPORTED`, `PARTIAL`, `ABSENT`, `CONTRADICTED` o `INAPPLICABLE`;
- evidence IDs y raíces independientes;
- certainty, confidence y freshness;
- explicación, counterevidence y alternativas;
- impacto sobre ceiling, CTA, fricción y presión.

`OBSERVED_INTEREST=ABSENT` no equivale a desinterés ni fuerza `LOW`; impide
usar personalización conductual como si existiera evidencia positiva.

### 7.2 Disposiciones

- `RETURN_UPSTREAM`: identidad, provenance, vigencia, versión, autoridad o
  contexto esencial ausente/contradictorio impide una decisión segura.
- `LOW`: existe evidencia suficiente para concluir que la propuesta carece de
  relevancia o que el uso pretendido está fuera de política. Produce
  `DO_NOT_SEND` aguas abajo.
- `MEDIUM`: existe valor plausible pero parcial. Impone ceiling menor,
  estrategia informativa, CTA/fricción reducidos o espera por contexto.
- `HIGH`: la cadena Insight → Account → Role → Moment está respaldada y no
  existe blocker material. Habilita M06; no autoriza delivery.

El gate usa una lattice de reglas explícitas y versionadas, no un score único.
Todo cambio de reglas exige versión, regresión y oráculo independiente.

## 8. Persona State Model

Es una proyección temporal compartida, no un motor ni una etiqueta identitaria:

```text
NORMAL → DISRUPTION → RISK_AWARE → SOLUTION_SEEKING
→ EVALUATION → DECISION → STABILIZATION
```

M03, M04 y M05 son los contribuidores principales. Una política versionada
define transiciones permitidas y evidencia requerida. Cada transición conserva
estado anterior, evidencia, alternativas, confidence, vigencia y razón.

El estado puede retroceder, expirar, quedar `UNKNOWN` o `CONTRADICTED`. No se
permite inferirlo sólo por una apertura, clic, silencio o recomendación previa
del sistema. M08 puede proponer revisar una política de transición para una
versión futura; no puede ejecutar la transición aceptada.

## 9. Personalization Ceiling

Niveles gobernados:

0. `GENERIC`
1. `SEGMENT`
2. `ACCOUNT`
3. `ROLE`
4. `BEHAVIORAL`
5. `CONTEXTUAL`

El ceiling efectivo es el mínimo entre:

- evidencia disponible;
- relación demostrada;
- política de uso y propósito;
- límite impuesto por Relevance Gate;
- capacidad y riesgo del canal/formato;
- sensibilidad y restricciones del dato.

El resolver devuelve cada límite componente, el mínimo efectivo y las razones.
M06 puede elegir un nivel inferior, nunca superior. Consentimiento y delivery
siguen siendo verificaciones separadas del ejecutor.

## 10. Adaptive Frontier Controller

### 10.1 Niveles

- `L0 SAFE`: ruta determinista, sin recuperación o experimentación avanzada.
- `L1 CONTEXT`: recuperación contextual adicional, siempre enlazada a records
  autoritativos.
- `L2 CHOICE`: comparación entre estrategias previamente autorizadas.
- `L3 TEST`: experimento controlado con baseline, stopping rule y rollback.

No existe un nivel de autoalteración de reglas o autoridad.

### 10.2 Regla de selección

Primero valida restricciones duras: autoridad, privacidad, provenance,
auditabilidad, reproducibilidad, rollback y SLO máximo. Si una falla, el nivel
se reduce hasta cumplirlas o la ejecución retorna upstream.

Después compara beneficio marginal demostrado contra sacrificio medido:

- beneficio: relevancia, reducción de incertidumbre, outcome válido,
  aprendizaje transferible y menor trabajo humano;
- sacrificio: latencia, coste, error, drift, complejidad, exposición de datos,
  mantenimiento y pérdida de explicabilidad.

Se elige el nivel más alto cuyo beneficio tiene evidencia suficiente para
superar el sacrificio sin degradar baseline ni restricciones duras. Evidencia
insuficiente o empate conserva el nivel inferior. Histéresis evita oscilación;
circuit breaker degrada ante regresión; feature flags y versiones permiten
rollback por tenant, caso de uso o canal.

## 11. M06 — Message Intelligence

### Input

Context Pack; Gate `HIGH` o `MEDIUM` cualificado; assets autorizados de Bloque
2; política de estrategia; adaptive level.

### Output `MESSAGE_STRATEGY`

- objetivo y ruta de audiencia: directa, institucionalmente reenviable o
  informativa;
- `WHAT`, `WHY`, ángulo, profundidad, prueba, formato, CTA y fricción;
- claims/evidence/asset refs, sin duplicar ni alterar su contenido;
- ceiling máximo y nivel aplicado;
- hechos que no pueden afirmarse, alternativas y incertidumbre;
- vigencia, versión y fingerprint.

Gate `MEDIUM` obliga a una de estas respuestas gobernadas: reducir ceiling,
reducir CTA/fricción, usar estrategia informativa, emitir alternativas o
`RETURN_UPSTREAM`. Gate `LOW` no permite crear estrategia enviable.

M06 no redacta obligatoriamente el mensaje final, no rediseña identidad de
Bloque 2 y no autoriza contacto.

## 12. M07 — Timing & Channel Intelligence

### Input

Message Strategy; relación; comportamiento; contexto temporal; historial de
contacto; capacidades de canal; política versionada de frecuencia/presión.

### Output `DELIVERY_PROPOSAL`

- disposición: `SEND_CANDIDATE`, `WAIT`, `DO_NOT_SEND` o `RETURN_UPSTREAM`;
- canal candidato, ventana `not_before`, expiración y timezone;
- `CONTACT_PRESSURE`, cadencia, follow-up y fricción CTA;
- razones, incertidumbre, alternativas y checks obligatorios del ejecutor;
- identidades de strategy, snapshot y policy.

Fatiga, contradicción, baja freshness o poca relación sólo pueden reducir
presión, esperar o bloquear. Una propuesta caducada no se reutiliza. El
ejecutor externo vuelve a verificar consentimiento, opt-out, frecuencia,
credenciales y autorización inmediatamente antes de cualquier efecto.

## 13. M08 — Learning Engine

### Input

Cadena completa y temporalmente coherente:

```text
context_snapshot_id → gate_decision_id → strategy_id → proposal_id
→ delivery_receipt_id → behavior_event_ids → outcome_id
```

Un rechazo del ejecutor no es conducta del receptor. Ausencia de receipt u
outcome atribuible produce `NO_LEARNING` o aprendizaje inconcluso, no éxito ni
fracaso imputado.

### Output `NEXT_BEST_TEST`

- hechos observados;
- inferencias con límites y confounders;
- counterhypotheses;
- hipótesis falsable siguiente;
- población/scope elegible: persona, cuenta, segmento o global;
- baseline, métrica primaria, guardrails, muestra mínima gobernada, stopping
  rule, expiración y rollback;
- propuesta de actualización y evidencia requerida para promoverla.

M08 conserva resultados negativos y evita contaminación por decisiones del
propio sistema. Su output entra en Candidate Learning Store; sólo Governance
Review puede aceptar una versión futura.

## 14. Precision Memory Fabric

1. **Evidence Ledger:** eventos append-only con identidad, fuente, tiempo,
   propósito, permiso, retención y lineage.
2. **Snapshot Store:** Context Packs inmutables y reproducibles.
3. **Temporal Claim Graph:** facts, hipótesis, contradicciones, vigencia y
   supersession.
4. **Semantic Discovery Index:** localiza records; es derivado, reconstruible y
   nunca autoridad probatoria.
5. **Decision & Outcome Ledger:** decisiones, versiones, execution receipts y
   outcomes observados.
6. **Candidate Learning Store:** propuestas, pruebas, resultados negativos,
   expiración y rollback.

Una consulta interactiva responde con facts, hipótesis, contradicciones, datos
faltantes, fuentes, freshness y versión. La conversación del operador no se
convierte en fact. Una corrección crea un nuevo record autorizado y enlaza
supersession; no reescribe silenciosamente el pasado.

La memoria se particiona por tenant y propósito. Retención, tombstones,
propagación de borrado, cifrado, control de acceso y auditoría son requisitos
de implementación, no capacidades demostradas por este diseño.

## 15. Fallo, degradación y recuperación

| Condición | Disposición | Recuperación |
|---|---|---|
| identidad/provenance/version inválida | `RETURN_UPSTREAM` | reparar y reemitir |
| contradicción esencial | `CONTRADICTED` | preservar alternativas; nueva evidencia |
| semantic index no disponible | degradar a L0/L1 | ledger y snapshot autoritativos |
| asset autorizado ausente | fallback explícito o return | resolver asset/version |
| canal incompleto | `WAIT` | recalcular antes de expiración |
| executor rechaza | `NO_DELIVERY` | registrar rechazo, no conducta |
| M08 sin receipt/outcome | `NO_LEARNING` | esperar o cerrar inconcluso |
| adaptive regression | circuit break | rollback y cuarentena |
| concurrencia/version mismatch | rechazo de intento | snapshot nuevo |
| capacity excedida | fallo contractual | particionar o aumentar límite aprobado |

IDs y fingerprints hacen el replay idempotente. ID repetido con contenido
distinto es colisión. Una escritura parcial no produce artefacto aceptado; el
caller reintenta con la misma idempotency key o crea una nueva generación.

## 16. Observabilidad

Cada artefacto expone trace ID, producer, schema/policy/model version, timestamps,
input/output fingerprints, evidence roots, disposition, reason codes,
uncertainty, adaptive level, latency, coste estimado y rollback identity.

Métricas mínimas:

- distribución de Gate y razones;
- ceiling máximo vs. nivel aplicado;
- degradaciones y circuit breakers;
- latencia/coste por nivel adaptativo;
- stale, contradiction y return-upstream rates;
- executor rejection por razón, separado de conducta;
- candidatos M08 propuestos, rechazados, expirados y promovidos;
- outcome attribution completeness;
- drift de inputs, políticas y desempeño respecto al baseline.

## 17. Seguridad y abuso

Pruebas y controles deben cubrir tenant crossover, identity substitution,
prompt/data injection en fuentes, provenance laundering, sensitive-attribute
leakage, semantic retrieval poisoning, permission escalation, opt-out bypass,
frequency bypass, replay duplicado, version downgrade, candidate self-promotion
y outcome fabrication.

Los adapters usan mínimo privilegio. El Bloque 3 no recibe credenciales de
delivery. La autoridad de ejecución debe ser verificable por identidad y
versión, con rechazo por defecto.

## 18. Estrategia de pruebas

1. unit y contract por componente;
2. property tests de invariantes, monotonicidad de restricciones e idempotencia;
3. adversarial y mutation para identidad, evidencia, temporalidad y autoridad;
4. state-machine tests para Persona State y propuestas M07;
5. fault injection para memoria, adapters, version registry y partial writes;
6. replay, concurrency y compatibility entre schemas/policies;
7. differential tests y oráculos independientes para Relevance Gate y
   Adaptive Frontier Controller;
8. end-to-end dry run sin delivery;
9. shadow integration con fuentes reales autorizadas;
10. experimento controlado con executor externo, stopping rules y rollback.

El oráculo no puede copiar la lógica de producción. Los outcomes no validan por
sí solos causalidad ni corrección arquitectónica.

## 19. Escalera de promoción

- `G0 CONTRACTS`: schemas, autoridad, failure y compatibilidad aceptados.
- `G1 LOCAL RUNTIME`: comportamiento determinista ejecutado y registrado.
- `G2 CI + RED TEAM`: SHA exacto, mutations y oráculos independientes.
- `G3 SHADOW`: adapters reales sin delivery ni efectos externos.
- `G4 L0 CONTROLLED`: delivery externo autorizado y rollback demostrado.
- `G5 L1/L2 EARNED`: beneficio neto y SLOs demostrados contra baseline.
- `G6 L3 EXPERIMENT`: experimentación limitada con revisión independiente.

Cada gate registra estado, evidencia, test, fecha, versión, dependencias,
contradicciones, confidence, reviewer y próxima reevaluación. Ningún PASS local
salta niveles.

## 20. Orden de construcción propuesto

1. contratos comunes y Context Pack;
2. Relevance Gate y oráculo independiente;
3. Persona State y Ceiling;
4. M06;
5. M07 sin executor real;
6. Outcome Ledger y M08 candidate-only;
7. Memory Fabric mínima: ledger, snapshots y decision/outcome ledger;
8. Adaptive Controller L0/L1;
9. shadow adapters e integración interbloques;
10. L2 y L3 sólo después de evidencia comparativa.

Temporal graph y semantic discovery se incorporan después de la memoria
autoritativa; no son prerequisitos para el primer runtime determinista.

## 21. Compatibilidad y migración

M01–M05 permanecen intactos. El Composer consume sus outputs mediante adapters
versionados. Un schema incompatible produce rechazo explícito, no coerción.

La migración empieza en shadow mode: se generan Context Packs y decisiones sin
afectar delivery. Una versión anterior permanece disponible hasta que la nueva
demuestre replay, compatibilidad, rollback y ausencia de regresión material.

## 22. Validación formal realizada

Se modeló el flujo por ejecución como grafo dirigido. Wolfram verificó:

- `PerRunAcyclic = True`;
- ausencia de edges directos prohibidos;
- M08 no alcanza M01–M05 ni Relevance Gate en la generación actual;
- sólo M07 propone a Delivery Enforcement;
- el aprendizaje termina en la frontera de versión.

Esto es evidencia formal complementaria del diseño; no es runtime, integración
ni aceptación de gate.

## 23. Decisiones que requieren autoridad común antes de promoción

No se inventan en este documento:

- contrato autorizado de Account Intelligence;
- protocolos Precision ↔ Bloques 1 y 2;
- owner común de consentimiento, frecuencia y delivery;
- taxonomía y políticas autorizadas de canal;
- identidad y mandato de Governance Review;
- políticas de retención, borrado y uso por tenant/jurisdicción;
- métricas comerciales primarias y umbrales de beneficio marginal.

Hasta su resolución, pueden modelarse adapters y fixtures acotados, pero los
gates interbloque y de producción permanecen `YELLOW` o `UNKNOWN`.

## 24. Criterios de aceptación de esta especificación

La especificación está lista para un plan de implementación cuando:

- no contiene placeholders ni ownership implícito;
- preserva las jurisdicciones M01–M08 y las invariantes protegidas;
- diferencia diseño, runtime, integración y promoción;
- define inputs, outputs, fallos, recuperación, observabilidad y rollback;
- mantiene delivery y aprendizaje aceptado fuera de autoridad local;
- el usuario revisa el documento escrito y confirma que representa las cinco
  secciones aprobadas.

