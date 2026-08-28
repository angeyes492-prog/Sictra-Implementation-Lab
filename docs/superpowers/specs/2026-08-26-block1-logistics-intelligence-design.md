# Telecare OS — Bloque 1 Intelligence Logístico

## Estado y autoridad

`PROPOSED / PLAUSIBLE / C` — diseño aprobado conceptualmente por el usuario;
pendiente de revisión del documento, implementación, pruebas y aceptación.

Este documento no cambia el gate `BOUNDED OPERATIONAL`, no afirma producción y
no convierte Slack o Notion en autoridad canónica. GitHub y los contratos
aceptados conservarán la autoridad técnica al implementar.

## Propósito

Convertir una pregunta logística en un insight trazable y limitado. Bloque 1
investiga, valida, desafía y compara estrategias de indagación; no contacta
prospectos, publica contenido, gestiona CRM ni decide acciones comerciales.

Los usuarios finales previstos son equipos que estudian importadores,
exportadores y decisores de compra a escala global, regional y local.

## No-objetivos de esta fase

- Ingesta de fuentes reales, scraping, APIs externas o credenciales.
- Perfiles de empresas reales, datos personales, contacto o enriquecimiento.
- Producción, multiusuario, alta disponibilidad, recomendación comercial o
  automatización de mensajes.
- Sustituir el futuro Bloque 3 Precision, Bloque 2 Design o Bloque 4
  Orchestrator.
- Promoción de una hipótesis, un insight o una estrategia a hecho global.

## Ciclo de inteligencia propuesto

```text
Pregunta logística acotada
  → estrategia de investigación versionada
  → source packets y claims trazables
  → validación de procedencia/frescura/cobertura
  → contradicciones y explicaciones alternativas
  → comparación de estrategias
  → insight limitado + watchlist 7/30/90
  → memoria de aprendizaje, no de verdad automática
```

Cada transición preserva identidad, tiempo, procedencia, estado epistémico,
restricciones, incertidumbre y lineage. Un insight siempre conserva referencias
a sus claims y a la estrategia que lo originó.

## Responsabilidad por motor

| Motor | Semántica logística propuesta | Límite innegociable |
| --- | --- | --- |
| E01 Agent | Formula pregunta, alcance, actor, geografía, industria, ruta, modalidad y período. | No evalúa evidencia ni autoriza. |
| E02 Knowledge Acquisition | Registra y verifica source packets; identifica cobertura y huecos. | No declara verdad ni crea fuentes. |
| E03 Practice / Experiment | Ejecuta y compara estrategias de indagación reproducibles. | `EJECUTADA != VALIDADA`. |
| E04 Integration | Conserva enlaces tipados entre estrategia, fuente, claim, contradicción e insight. | No se vuelve scheduler ni autoridad. |
| E05 Evaluation / Red Team | Evalúa independencia, contradicción, alternativas y límites. | Evaluar no autoriza. |
| E06 Memory / Learning | Versiona estrategias, evaluaciones e insights de ensayo. | `GUARDADO != PROMOVIDO`. |
| E07 Stability | Señala frescura, suficiencia, capacidad y necesidad de revalidación. | Salud no convierte incertidumbre en certeza. |
| E08 Governance | Emite `DRAFT`, `RESEARCH_NEEDED` o `DELIVERABLE_BOUNDED`. | Decisión no es enforcement ni aceptación global. |

Los nombres de decisión son candidatos de contrato: no tienen autoridad de
runtime hasta que el contrato y sus pruebas sean aceptados.

## Modelo canónico logístico propuesto

### Logistics scope

Un `LogisticsScope` identifica: `geography_level` (global, regional o local),
geografía concreta, industria, actor económico, modalidad, ruta o nodo
logístico, período y pregunta de investigación. Un campo no conocido permanece
`UNSPECIFIED`; no se infiere para completar una ficha.

### Source packet

Un `SourcePacket` contiene identidad de fuente, organización, método de
obtención, URL o referencia, fecha de publicación, fecha de acceso, contenido
o extracto, limitaciones, source tier, correlación conocida, alcance y firma o
atestado cuando el runtime lo requiera. Es un objeto de evidencia, no un claim.

### Claim

Un `LogisticsClaim` contiene: identidad, pregunta relacionada, afirmación,
tipo (`FACT`, `INTERPRETATION`, `HYPOTHESIS`, `FORECAST`), alcance, período,
source packets, independencia, contradicciones, estado epistemológico,
confianza, expiración y limitaciones. Un claim sin procedencia admisible queda
`INSUFFICIENT EVIDENCE`.

### Research strategy

Una `ResearchStrategy` contiene una pregunta, hipótesis inicial, orden de
fuentes previstas, criterios de exclusión, consultas/preguntas previstas,
condición de detención, costo observado, duración, cobertura lograda,
incertidumbre inicial/final, claims producidos, contradicciones y resultado de
red team. Los costos son métricas observadas de experimento; no son una medida
universal de calidad.

### Insight y watchlist

Un `LogisticsInsight` agrega únicamente claims admisibles: tipo de señal
(oportunidad, riesgo, cambio, necesidad de investigación), actores afectados,
alcance, evidencia, restricciones, explicaciones alternativas, confidence,
estado y watchlist. La watchlist tiene observables verificables para 7, 30 y
90 días, responsable y condición de revalidación.

## Comparación evolutiva de estrategias

E03 debe comparar estrategias solo dentro de preguntas y scopes compatibles.
El resultado no será un ranking absoluto; será una explicación versionada de
qué estrategia logró mejor combinación observada de:

- cobertura de la pregunta;
- diversidad e independencia de fuentes;
- frescura de evidencia;
- reducción de incertidumbre;
- contradicciones detectadas y resueltas explícitamente;
- costo y duración observados;
- resultado de E05 y estado de E07.

Una estrategia con más fuentes no vence automáticamente a otra. Fuentes
duplicadas, correlacionadas o vencidas no aumentan corroboración. Si no hay
comparabilidad o evidencia suficiente, el resultado es `INCOMPARABLE` o
`INSUFFICIENT EVIDENCE`, nunca una recomendación implícita.

## Estados y control humano

| Estado | Significado | Próxima acción |
| --- | --- | --- |
| `DRAFT` | Material investigado, no apto para entregar. | Continuar o descartar. |
| `RESEARCH_NEEDED` | Faltan fuente, cobertura, frescura o contradicción. | Abrir gap y watchlist. |
| `DELIVERABLE_BOUNDED` | Insight acotado con límites explícitos. | Revisión humana antes de uso externo. |
| `QUARANTINED` | Autoridad, procedencia o integridad falló. | No usar; preservar evidencia. |
| `SUPERSEDED` | Evidencia posterior reemplazó una versión. | Mantener lineage, no borrar historia. |

Ningún estado permite contacto, publicación, actualización de CRM o decisión
comercial. Esas fronteras pertenecen a bloques posteriores y a decisión humana.

## Fallos, recuperación y seguridad

- Fuente vencida, alcance incorrecto, firma inválida o fuente no confiable:
  rechazo explícito sin efecto durable.
- Fuentes correlacionadas o contradictorias: conservar ambas; reducir
  corroboración y solicitar evaluación.
- Campo logístico desconocido: `UNSPECIFIED`, no enriquecimiento inventado.
- Estrategias no comparables: resultado `INCOMPARABLE` y explicación.
- Error de cálculo, memoria o storage: E07 falla cerrado; E08 no entrega como
  insight válido.
- Corrección posterior: crear nueva versión con lineage, no sobrescribir claim
  o insight histórico.
- Datos reales futuros: aislamiento de secretos, minimización, retención,
  licencias y controles de acceso requieren una revisión de arquitectura antes
  de conectar cualquier fuente.

## Frontera con Bloque 3 Precision

Bloque 1 conserva el registro de estrategia, evidencia y resultado. Bloque 3
podrá emitir posteriormente una evaluación de precisión o utilidad observada,
atada a la versión exacta de insight y estrategia. E03 puede usar esa señal
como observación de experimento, pero Bloque 3 no reescribe evidencia ni cambia
el estado epistemológico sin un nuevo ciclo E02/E05/E08.

## Prototipo demostrable posterior

El primer incremento implementará solo casos sintéticos trazables: una pequeña
biblioteca de investigaciones globales, regionales y locales; filtros de scope;
vista de claims, fuentes, contradicciones, estrategia e insight; y comparador
de estrategias. No representará datos sintéticos como cobertura real.

## Validación requerida

1. Contratos con versiones, productor/consumidor, pre/postcondiciones,
   restricciones y non-claims.
2. Casos limpios y mutaciones: fuente vencida, identidad sustituida, claim sin
   lineage, contradicción, correlación duplicada, scope incompatible y revisión
   expirada.
3. Pruebas de integración E01–E08 que demuestren que el insight no se entrega
   si E02, E05, E07 o E08 falla.
4. Oráculo independiente para comparar estrategias y detectar ranking circular.
5. CI sobre SHA exacto y revisión independiente sin CRITICAL/HIGH abierto.
6. Revisión de arquitectura antes de adaptar fuentes reales o compartir
   resultados fuera del laboratorio.

## Dependencias y contradicciones

- El runtime actual verifica source envelopes HMAC de fixture; no define aún el
  adaptador, licencia o identidad operacional de fuentes reales.
- La arquitectura global y E02/E06/E07 tienen historia de gaps de cobertura en
  Slack. Esta propuesta no los declara resueltos.
- Los umbrales cuantitativos de calidad y el modelo de producción siguen
  `UNSPECIFIED` hasta contar con evidencia y una decisión de arquitectura.

## Criterio de promesa técnica

La propuesta será prometedora si, con datos sintéticos, logra demostrar de
forma reproducible que estrategias distintas producen distinta cobertura,
incertidumbre y manejo de contradicciones, sin violar procedencia, gobernanza,
memoria o no-claims. Será sobresaliente solo si una revisión independiente y
pruebas adversariales confirman esos resultados; nunca por apariencia de UI o
volumen de datos.
