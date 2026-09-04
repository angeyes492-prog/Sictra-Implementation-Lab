# Bloque 2 / Design — E01 Clean External Trial Fixture v0.1

> **Estado:** `CANDIDATE / LOCAL BLOCK-2 ARCHITECTURE / NOT IMPLEMENTED`  
> **Gate:** `YELLOW` — artefacto de diseño preparado; no ejecutado, no validado
> empíricamente y no aceptado como arquitectura común.

## Propósito y límite

Definir un fixture acotado para comprobar una **afirmación perceptual concreta**
sobre dos candidatos visuales sin confundir preferencia, familiaridad, etiquetas,
orden, contexto o incertidumbre con un efecto de codificación.

No es un generador de visuales, un experimento ya ejecutado, una prueba de
superioridad de E01 ni un contrato común. Su único producto potencial es una
observación de caso clasificada de manera trazable.

## Autoridad y dependencias

| Elemento | Estado / propiedad |
|---|---|
| Arquitectura del fixture | Local a Bloque 2 / E01 |
| Inteligencia de entrada, hechos y certeza | Upstream; E01 no la reinterpreta ni completa |
| Contexto de audiencia y decisión | Upstream o Bloque 3 cuando corresponda |
| Decisión de promoción / aceptación | Fuera de E01; no se infiere del resultado |
| Principios transferidos de Bloque 1 | Procedencia, incertidumbre, contradicción, evidencia antes de promoción |
| Semántica propia de Bloque 1 | Excluida |

Si falta una entrada material o su autoridad no está clara, el resultado es
`RETURN_UPSTREAM`, no un ensayo aproximado.

## Afirmación y unidad de prueba

Antes de preparar candidatos se registra una sola afirmación con alcance:

`CLAIM_ID → TARGET → ACTION → SCOPE → CANDIDATE_A → CANDIDATE_B →
INTENDED_MANIPULATION → EXPECTED_OBSERVABLE → EVIDENCE_CLASS_CEILING`

El techo inicial es `EXTERNALLY_OBSERVED / SINGLE TRIAL`. Ningún resultado de
una ejecución puede declararse reproducido, regla local aceptada o mejora
general de E01.

Los cuatro resultados admisibles son:

| Resultado | Significado permitido |
|---|---|
| `A_SUPPORTED` | A favorecido en la tarea declarada, sin fallo material de integridad |
| `B_SUPPORTED` | B favorecido en la tarea declarada, sin fallo material de integridad |
| `NO_DISCRIMINATION` | No hay diferencia material demostrable; requiere revisión de sensibilidad |
| `INVALID_TRIAL` | Una condición material impide atribución causal; sólo aprendizaje metodológico |

## Preflight obligatorio

El fixture no puede exponerse a observador hasta que todos los controles
aplicables estén registrados y evaluados.

| Control | Registro mínimo | Fallo / salida |
|---|---|---|
| Integridad de tarea | versión, Target/Action/Scope, texto exacto | `INVALID_TRIAL` o `RETURN_UPSTREAM` |
| Equivalencia semántica | contenido, escala, unidades, incertidumbre, etiquetas | `INVALID_TRIAL` |
| Paridad de dificultad | densidad, anotaciones, llamadas, texto explicativo | `INVALID_TRIAL` |
| Aislamiento causal | manipulación prevista y variables controladas | `INVALID_TRIAL` |
| Independencia del observador | rol, exposición previa, tesis/ejemplos vistos, instrucciones | evidencia no promovible |
| Orden y atención | orden, aleatorización/contrabalanceo, condición de atención | evidencia limitada o `INVALID_TRIAL` |
| Familiaridad | idioma visual y relación con la tarea | confounder registrado; no prueba de superioridad |
| Sensibilidad nula | diferencia esperada, observables, ruido y poder de discriminación | `NO_DISCRIMINATION` no promovible sin revisión |
| Autoridad de entrada | identidad, procedencia y estado epistémico del objeto | `RETURN_UPSTREAM` |

La **Fixture Equivalence Matrix** debe cubrir exactamente:

`CONTENT / TASK / LABELS / SCALE / UNCERTAINTY / ANNOTATION / CONTEXT /
ORDER / ATTENTION / IMPLEMENTATION_BURDEN`.

Todo cambio entre A y B se rechaza salvo la `INTENDED_MANIPULATION` registrada.

## Registros requeridos

### Task Leakage Record

`TASK_WORDING → REQUIRED_CONTEXT → POTENTIAL_CUE → LEAKAGE_RISK → VERSION`

La consigna no puede nombrar la metáfora, tesis, mecanismo ni respuesta
esperada. Si hacerlo es necesario para la tarea, se registra como cambio de
versión de tarea y no como comparación equivalente.

### Observer Independence Profile

`OBSERVER_ROLE → SOURCE_RELATIONSHIP → PRIOR_EXPOSURE → THESIS_EXPOSURE →
EXAMPLES_SEEN → TASK_INSTRUCTIONS → ORDER_CONDITION → EVALUATION_CONTEXT →
RESPONSE_MODE`

`EXTERNAL != INDEPENDENT`. Cualquier filtración que explique de forma plausible
la respuesta bloquea la promoción empírica.

### Confounder Register

`VARIABLE → MANIPULATED | CONTROLLED | PROHIBITED | TOLERATED |
DISCOVERED_POST_TRIAL → MATERIALITY → DISPOSITION`

Un confounder material descubierto después de la ejecución convierte el
resultado en `INVALID_TRIAL`, salvo que una regla predeclarada justifique y
acote su tolerancia.

### Null Sensitivity Review

`EXPECTED_DIFFERENCE → DETECTION_RATIONALE → OBSERVABLE → NOISE_LIMITATION →
NULL_INTERPRETATION`

Valores permitidos para `NULL_INTERPRETATION`: `NO_MATERIAL_DIFFERENCE`,
`INSUFFICIENT_SENSITIVITY`, `EXCESS_NOISE`, `TASK_NON_DISCRIMINATING` e
`INVALID_TRIAL`.

## Clasificación, cuarentena y memoria

La secuencia de atribución es:

`TASK_INTEGRITY → SEMANTIC_EQUIVALENCE → CAUSAL_ISOLATION → OBSERVATION →
ATTRIBUTION → MEMORY_DISPOSITION`.

Para un fallo se registra un **First-Sufficient-Stop Record**:

`FAILED_LAYER → EVIDENCE → CLAIMS_BLOCKED → DOWNSTREAM_DATA_QUARANTINED →
METHODOLOGICAL_LEARNING → RETEST_CONDITION`.

El fallo debe ser suficiente respecto de la afirmación declarada; el primer
síntoma temporal no se confunde con la causa. Varias causas suficientes se
preservan como conjunto mínimo, sin escoger una causa única artificial.

- `A_SUPPORTED`, `B_SUPPORTED` y evidencia limitada se conservan como
  observaciones **atómicas** con condiciones, limitaciones y límite de reutilización.
- `INVALID_TRIAL`, contaminación o entrada insuficiente sólo alimentan
  **Methodological Memory**; nunca etiquetan una ruta visual como buena o mala.
- Dos observaciones válidas no se combinan automáticamente. Toda combinación
  abre una afirmación nueva con `SOURCE_RECORDS`, condiciones compartidas/no
  compartidas, estado de interacción y una prueba discriminante futura.

## Ejecución propuesta y recuperación

1. Seleccionar un objeto de inteligencia verificable y un único claim.
2. Crear A y B con la matriz de equivalencia y el registro de confounders.
3. Pasar el preflight independiente de filtración y equivalencia.
4. Registrar el perfil del observador antes de su primera interpretación.
5. Recoger la respuesta de la tarea antes de exponer tesis, metáfora o racional.
6. Clasificar el resultado y conservar la evidencia de control.
7. Si hay un fallo material, cuarentenar conclusiones descendentes, registrar el
   aprendizaje metodológico y volver al paso que indique la condición de retest.

No hay reanudación automática después de una contaminación o de una ambigüedad
de autoridad. El ensayo debe versionarse y volver a pasar el preflight.

## Validación pendiente y red team

| Vector | Resultado esperado | Estado |
|---|---|---|
| Fuga por redacción de tarea | `INVALID_TRIAL` | `UNCONFIRMED` |
| Asimetría de etiquetas/anotaciones | `INVALID_TRIAL` | `UNCONFIRMED` |
| Cambio oculto de semántica de incertidumbre | `INVALID_TRIAL` | `UNCONFIRMED` |
| Efecto de orden sin control | evidencia limitada o `INVALID_TRIAL` | `UNCONFIRMED` |
| Familiaridad como explicación alternativa | confounder, no superioridad | `UNCONFIRMED` |
| Nulo sin sensibilidad demostrada | no promoción | `UNCONFIRMED` |
| Observador externo pero contaminado | no promoción empírica | `UNCONFIRMED` |
| Combinación de observaciones estrechas | `UNSUPPORTED_COMBINATION` | `UNCONFIRMED` |

## Evidencia, contradicciones y siguiente gate

**Evidencia de diseño:** el Canvas de Slack `E01 — Visual Intelligence Engine —
Construction Record v0.1` (`F0BRUAFJ3AQ`), Waves 29–37, describe los ataques de
contaminación, el trial family, la independencia del observador y el límite de
composición de claims. Es contexto de diseño, no autoridad normativa ni prueba
de ejecución.

**Contradicción / riesgo abierto:** el Canvas y los mensajes de Slack declaran
el mismo E01 `YELLOW / ARCHITECTURALLY COHERENT / NOT IMPLEMENTED`, mientras el
repositorio no contenía antes un artefacto de Bloque 2. Este documento reduce
esa brecha documental, pero no resuelve la falta de un objeto de inteligencia
autorizado ni produce evidencia humana independiente.

**Siguiente gate:** ejecutar el preflight sobre un único caso con objeto
upstream verificable y realizar la revisión independiente de integridad del
fixture. Sólo entonces puede considerarse una observación externa de caso;
la promoción, integración y aceptación permanecen fuera de alcance.

## Registro

- Versión: `0.1`
- Fecha: `2026-08-24`
- Autoridad: propuesta local de Bloque 2, derivada de Slack y consolidada en el repositorio
- Certeza: `PROBABLE` para el diseño; `INSUFFICIENT EVIDENCE` para ejecución,
  validez empírica, integración y aceptación
- Impacto downstream: ninguno aceptado; no introduce contrato común ni cambia
  el runtime del Bloque 1.

## Reassessment de implementación — 2026-08-31

La frase histórica `NOT IMPLEMENTED` describe correctamente el checkpoint del
24 de agosto, pero ya no es el estado actual del runtime candidato. E01 tiene
preflight, normalización upstream, entrypoint, oráculo y binding Create→E01
ejecutados localmente y en CI dentro de PR #11. Esto resuelve la ausencia de
implementación y SHA, no la validación perceptual externa: aún falta un objeto
SICTrA real autorizado y un observador humano independiente. El fixture externo
continúa `YELLOW / NOT EMPIRICALLY VALIDATED`.
