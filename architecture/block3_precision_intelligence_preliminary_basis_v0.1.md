# Bloque 3 / Precision Intelligence — Base preliminar v0.1

> **SUPERSEDED:** la decisión de diseño del usuario sobre los ocho motores se
> registra en `architecture/block3_precision_intelligence_engine_model_v1.md`.
> Este artefacto se conserva como la base exploratoria y la evidencia de las
> ambigüedades identificadas antes de esa decisión.

> Estado: `USER-PROPOSED / CANDIDATE ONLY`. Este documento procesa una base
> aportada por el usuario; no acepta arquitectura común, contratos,
> implementación, integración, uso de datos personales, ejecución de outreach
> ni promoción de gates.

## Identidad y evidencia

| Campo | Valor |
|---|---|
| Fuente | Texto aportado por el usuario, adjunto `pasted-text.txt` |
| Fecha de procesamiento | 2026-08-26 |
| Hecho verificable | El texto propone este modelo y sus principios (`VERIFIED / A`, como atribución) |
| Evidencia de eficacia comercial, conductual o causal | `INSUFFICIENT EVIDENCE / E` |
| Estado arquitectónico | `CANDIDATE`; requiere Master Architecture Review |

## Misión propuesta

Transformar inteligencia y expresión disponibles en una **recomendación
trazable de relevancia y contacto**: qué comunicar, para qué contexto
profesional, con qué ángulo, profundidad, formato, canal, momento y techo de
personalización; después, registrar observaciones para informar una siguiente
hipótesis.

La recomendación no es una afirmación sobre la psicología de una persona, ni
una autorización para contactar, ni evidencia de que el contacto producirá un
resultado.

## Alineación comprobada y límites

- `architecture/telecare_os_block_model_v1.md` ya denomina al Bloque 3
  **Precision** y le asigna, de forma general, determinar la forma concreta de
  transmisión. Esto es `VERIFIED / A` para la existencia del límite nominal,
  no para el alcance ampliado aquí propuesto.
- El contrato local de Bloque 2 E01 exige `AUDIENCE_CONTEXT` y
  `DECISION_CONTEXT` ya registrados por un owner upstream. El contrato es
  `CANDIDATE / LOCAL BOUNDED SUT`; no crea un protocolo común ni asigna esas
  responsabilidades a Precision.
- No se localizó evidencia admisible de que `Account Intelligence` exista
  actualmente como sistema aceptado anterior al Editorial Engine. Esa
  afirmación queda `INSUFFICIENT EVIDENCE / E`.
- Bloque 1 sólo posee un corte operacional acotado y no prueba integración con
  Bloque 2 o 3. Precision no puede reinterpretar facts, evidence, certainty,
  provenance, authority, contradictions ni temporal state de Bloque 1.

## Principio rector candidato

> La personalización no consiste en demostrar cuánto sabemos del prospecto;
> consiste en demostrar que entendemos qué le resulta relevante.

Regla de integridad derivada:

> Precision puede seleccionar, priorizar, enmarcar y enrutar inteligencia; no
> puede corromper la inteligencia subyacente ni fabricar relevancia.

## Dominios candidatos y frontera semántica

| Dominio | Responsabilidad propuesta | Estado de sus conclusiones |
|---|---|---|
| Person Intelligence | Contexto profesional, función, responsabilidades y cercanía decisoria | Facts sólo con procedencia; cercanía decisoria suele ser hipótesis |
| Decision Intelligence | Necesidades, restricciones y decisión profesional relevante | Hipótesis explícita, con evidencia y límites |
| Behavioral Intelligence | Señales observadas de interacción y su contexto de medición | Evidencia observacional; no prueba interés o causalidad por sí sola |
| Relationship Intelligence | Historia verificable de relación, conversaciones y etapa | Hechos de interacción separados de interpretación comercial |
| Context Intelligence | Eventos de empresa, industria y entorno temporal | Debe preservar identidad, fuente, certeza y vigencia de Bloque 1 |
| Message Intelligence | Hipótesis de ángulo, profundidad, prueba, CTA y fricción | Recomendación, no hecho sobre el destinatario |
| Timing Intelligence | Hipótesis de canal, momento, frecuencia y abstención | Recomendación condicionada; no autorización de entrega |
| Learning Engine | Versionar hipótesis, observaciones, resultados y límites de reutilización | Almacenamiento no equivale a promoción de regla |

`Decision Psychology` y los arquetipos conductuales sólo son admisibles como
hipótesis dinámicas observables, nunca como diagnóstico, personalidad o verdad
atribuida a la persona.

## Invariantes candidatos

1. **Integridad upstream.** Un claim de Bloque 1 conserva facts, evidencia,
   certeza, contradicciones, procedencia, autoridad y estado temporal. Precision
   no puede incrementar certeza ni convertir impacto posible en impacto de la
   cuenta sin prueba específica.
2. **Hipótesis explícita.** Inferencias sobre prioridad, cercanía de decisión,
   orientación de riesgo, arquetipo o timing identifican su base, fecha,
   incertidumbre, confidence y condición de falsación.
3. **Datos mínimos.** Edad, género y atributos personales no son variables de
   persuasión. Tampoco se usa información disponible si no es necesaria para la
   relevancia profesional declarada.
4. **Personalización invisible con techo.** Toda salida declara nivel `0–5`
   (Generic, Segment, Account, Role, Behavioral, Contextual) y sólo emplea los
   datos permitidos por dicho nivel. Un nivel superior no es intrínsecamente
   mejor.
5. **Abstención segura.** Evidencia insuficiente, contradicción, dato vencido,
   fatiga, incertidumbre de permiso o relevancia baja permiten y obligan a
   devolver `DO_NOT_SEND`, `WAIT` o `RETURN_UPSTREAM`; no se rellena con
   familiaridad inventada.
6. **Separación entre recomendación y entrega.** Precision puede emitir una
   estrategia propuesta. El canal/CRM/operador que entrega conserva autoridad
   separada sobre consentimiento, políticas, frecuencia, opt-out y ejecución.
7. **Aprendizaje no causal por defecto.** Aperturas, silencio y clics son
   señales contextuales, no prueba de interés, rechazo ni de que el mensaje
   causó un resultado. Explicaciones alternativas permanecen registradas.
8. **No spam.** El historial de contactos, canal, tema, respuesta, frecuencia
   y tiempo desde la última interacción se evalúan antes de recomendar entrega.

## Tensión de flujo que requiere decisión humana

El texto propone a la vez `Bloque 1 → Bloque 2 → Bloque 3` y que Account/Person
Intelligence informe al Editorial Engine. Ambas afirmaciones no definen una
única dependencia aceptable.

| Opción candidata | Flujo | Consecuencia |
|---|---|---|
| A — selección antes de expresión | `B1 → Precision brief → B2 → Precision delivery` | Precision tendría dos fases y requeriría un contrato de brief hacia Design |
| B — selección después de expresión | `B1 → B2 asset → Precision routing` | Design produce un asset común; Precision no redefine su expresión, sólo lo selecciona y enruta |

No se adopta ninguna. Un flujo híbrido sólo puede aceptarse tras definir qué
parte de Precision posee cada fase y cómo se preservan las fronteras de Bloque
2.

## Modelo de salida candidato

La unidad no debe ser un mensaje ni un envío implícito, sino una
`PRECISION_RECOMMENDATION` versionada con:

- identidad, productor, versión, timestamp y scope;
- referencias inmutables al objeto de inteligencia, asset expresivo y fuentes
  de contexto;
- destinatario/rol sólo en el grado autorizado y necesario;
- hipótesis de relevancia, ángulo, profundidad, prueba, CTA, fricción, canal y
  timing;
- vector de factores de relevancia visible, su evidencia, incertidumbre y
  alternativas; no un score opaco;
- nivel de personalización, pressure/fatigue assessment y límites de uso;
- decisión propuesta: `SEND_CANDIDATE`, `WAIT`, `DO_NOT_SEND` o
  `RETURN_UPSTREAM`;
- condiciones de ejecución, observaciones esperadas, criterios de actualización
  y rollback.

El `Perceived Relevance Score` queda como instrumento candidato de decisión.
No puede ocultar ausencia de datos ni reemplazar sus factores: relevancia
global, industria, cuenta, rol, oportunidad temporal e interés observado deben
permanecer separables, con certeza y procedencia propias.

## Riesgos y controles iniciales

| Riesgo | Control candidato |
|---|---|
| Inferencia psicológica o estereotipo | Limitar a contexto y comportamiento observables; etiquetar inferencias como hipótesis |
| Sobreclaim desde un evento global | Requerir evidencia específica antes de afirmar impacto en cuenta, margen u operación |
| Personalización invasiva | Personalization ceiling, minimización y revisión del lenguaje expuesto |
| Spam o fatiga | Pressure score explicable, caps de frecuencia y resultado `WAIT`/`DO_NOT_SEND` |
| Métricas engañosas | Mantener instrumentación, entrega, apertura, interacción, respuesta y conversión como señales distintas |
| Confundir entrega con autoridad | Separar recomendador, aprobador y ejecutor; conservar permiso y opt-out fuera de Precision |
| Aprendizaje circular | Preservar hipótesis previa, observación cruda, confounders y actualización posterior como objetos distintos |
| Canal sensible (por ejemplo, WhatsApp) | No recomendar ejecución hasta que exista una política autorizada de consentimiento, jurisdicción, registro y opt-out |

## Estado de construcción

| Dimensión | Estado |
|---|---|
| Nombre y misión candidata | `PROBABLE / C` como propuesta coherente con el modelo de bloques |
| Límites semánticos iniciales | `PROBABLE / C` |
| Interfaz interbloques | `UNCONFIRMED / E` |
| Modelo de datos y gobierno de datos | `UNCONFIRMED / E` |
| Motor de scoring, aprendizaje o delivery | `NOT IMPLEMENTED` |
| Evidencia de eficacia | `INSUFFICIENT EVIDENCE / E` |
| Integración y aceptación | `INSUFFICIENT EVIDENCE / E` |

## Siguiente insumo mínimo

Antes de especificar o implementar motores, se necesita: (1) decisión sobre el
flujo A/B; (2) owner y contrato del contexto de persona/cuenta; (3) autoridad
de consentimiento, frecuencia y ejecución; (4) taxonomía de señales,
incertidumbre y outcomes; (5) una matriz de retención/uso de datos; y (6) casos
de prueba adversariales contra sobreclaim, identidad sustituida, dato obsoleto,
no consentimiento, fatiga, score opaco, feedback ambiguo y fuga de datos.

## Closure delta

- Se preservó la propuesta como base identificable sin elevarla a arquitectura
  aceptada.
- Se separaron facts, hipótesis, recomendaciones, observaciones y autorización.
- Se identificó la contradicción de orden entre Precision y Editorial/Design.
- Se establecieron abstención, techo de personalización y separación de delivery
  como límites candidatos para la próxima especificación.
