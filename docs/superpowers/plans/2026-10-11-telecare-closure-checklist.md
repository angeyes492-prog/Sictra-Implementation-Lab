# Telecare OS — plan de cierre y checklist de doce procesos

> Para ejecución futura: usar superpowers:executing-plans sobre el incremento suficientemente especificado seleccionado. Este documento descompone el objetivo; no autoriza efectos externos ni inventa interfaces todavía no contratadas. Estado y prioridad permanecen exclusivamente en `closure/closure_execution_queue_v0.1.md`.

**Goal:** completar el alcance funcional de laboratorio mediante procesos comprobables, no sumar actividad ni declarar autonomía por tener tests.

**Architecture:** conservar B1 como autoridad de evidencia/resolución, B2 como Design, B3 como Precision y B4 como coordinador. Reutilizar controles, almacenes y journals actuales; no crear otro plano de aprobación. Los IDs P01–P12 nombran comprobaciones de las aristas existentes, no nuevos gates.

**Tech Stack:** Python, unittest, SQLite/journal HMAC, consola JavaScript y PowerShell; Windows local y Python 3.11 en GitHub Actions.

**Spec:** `AGENTS.md`, `architecture/telecare_twelve_aristas_v0.1.md`, `architecture/block4_federated_orchestrator_mar_request_v0.1.md`, contratos afectados y backlog único. La arquitectura de doce aristas sigue candidata/MAR; este plan no la acepta.

Fecha de planificación: 2026-10-11, contexto del propietario. Evidencia de ejecución fechada separadamente en UTC.

Disponibilidad: plan y actualización del ledger guardados localmente durante
esta petición; no están contenidos en el SHA 210843b. La skill local no tiene
repositorio Git configurado. No presentar estos documentos como artefactos
reproducibles desde ese commit ni su edición como cierre ejecutado del producto.

## Frontera de terminado

Objetivo autorizado actual: `LABORATORY_INTERNAL_SUPERVISED`. Autonomía significa completar ciclos permitidos, reconocer insuficiencia, abstenerse, recuperarse y detenerse; no resolver cualquier pregunta ni actuar sin límites. No incluye publicación, contactos, CRM, producción o instalación sobre la aplicación existente. Automatización pausada: no reanudarla desde este plan.

Se conservan dos comprobaciones distintas:

- **Cierre técnico interno:** mecanismo, integración, entradas admisibles, operación y los ocho hitos B1 al alcance requerido, con CI exacta. Una espera correcta puede satisfacer un mecanismo; no prueba que una necesidad concreta esté resuelta.
- **Autonomía ampliada de producto:** adquisición dentro del runtime, uso real por usuarios/cuentas, entrega y aprendizaje donde formen parte del alcance aprobado. Requiere contratos, entradas y autoridad propios. No excluir un requisito bloqueado para presentar el laboratorio como el producto completo.

«100%» sólo puede expresar cobertura comprobada de un alcance explícito y congelado. No es una estimación de horas, líneas o cantidad de pruebas. Este plan no promete ni demuestra ese 100%.

## Baseline que no debe confundirse con cierre

- HEAD y remoto revalidados: `210843b6ec43204461530512bdc3640930dca638`, rama `codex/telecare-integrated-autonomy`. Incremento de colección oficial finita y lectura offline; siete originales capturados, selección exacta, sin admisión ni resolución.
- Regresión local previa al commit: 1077 casos, 1076 pasados y una omisión de permisos Windows; 18 JavaScript. Preflight sobre HEAD limpio: 24/24, checkout estable, `product_completion=NOT_DEMONSTRATED`.
- **CI exacta [38088995012](https://github.com/angeyes492-prog/Sictra-Implementation-Lab/actions/runs/38088995012): FAILURE.** Job 114321361316: 1077 casos, una falla y una omisión. Falla `CollectionTests.test_remote_html_parser_assertion_is_durable_controlled_failure`, línea 284: esperado `AssertionError`, observado `ResearchAcquisitionError`. CI usa CPython 3.11.17; local anterior 3.12.10. La causa de esa diferencia de parser debe reproducirse, no inferirse exclusivamente de las versiones. Los pasos posteriores de CI fueron omitidos.
- El SHA anterior `74558abd4a93c8214280c42cd4e570398b491800` sí tenía CI exitosa 38077832715. Eso no valida el código nuevo.
- Los siete originales y lectura offline fueron válidos a su hora de captura del 2026-10-10; comprobar caducidad antes de reutilizarlos. Restaurar o recapturar no renueva aprobación ni constituye otra publicación estadística.
- Notion, consulta de este ciclo: último encabezado corresponde al checkpoint de recuperación/arranque 74558ab; siete frentes parciales. No contiene todavía el nuevo fallo CI. Slack público: sin resultados para Telecare; no demuestra ausencia de decisiones privadas. GitHub actualiza la identidad técnica, no la admisión de fuentes.
- Wolfram comprobó que el grafo de construcción para autonomía ampliada (incluyendo P11→P12) es acíclico y dio un orden topológico. El laboratorio omite esa dependencia de entrega externa; quitarla no crea un ciclo. El modelo de conjunción exige mecanismo, integración, evidencia real y autoridad; CI sola o admisión ausente no cierran. Son propiedades del modelo propuesto, no pruebas del programa ni decisiones de MAR.

## C0 — requisito inmediato, no decimotercera arista

**Owner:** agente de implementación. **Parent:** `COMPARABLE-APPROVED-INPUT`.
**Files:** `tests/test_research_collection.py`, `src/sictra_block1/research_collection.py`, contrato de colección y workflow existente sólo si la reproducción demuestra que corresponden.

- [ ] Reproducir la falla identificada en Python 3.11 y comparar el recorrido con 3.12, sin red ni cambios al entorno instalado.
- [ ] Separar el rechazo real de HTML malformado del vector que fuerza una excepción de parser. El primero debe demostrar resultado durable `FAILED`, presupuesto conservado, originales retenidos y ninguna selección utilizable. El segundo debe demostrar que la excepción concreta no escapa ni borra evidencia. No convertir el test en «cualquier excepción pasa».
- [ ] Si el contrato especifica una taxonomía pública, probarla; no usar el nombre interno de una excepción de biblioteca como oráculo universal.
- [ ] Ejecutar prueba positiva de colección/lectura y ambas refutaciones, regresión completa, preflight limpio y CI exitosa del nuevo SHA publicado.
- [ ] Registrar logs, reparación y diferencia de plataforma en el mismo item del ledger. Hasta entonces: incremento implementado/ejecutado localmente, cierre de commit no acreditado.

## Checklist de procesos restantes

Cada casilla es una **pregunta de aceptación**, no un estado que se pueda marcar por redactar este documento. El estado vivo y las pruebas se registran únicamente bajo el parent indicado del ledger. Todos los procesos tienen mecanismos parciales; ninguna fila se declara totalmente completa aquí.

### P01 — fuentes admisibles y evidencia recuperable (arista 1)

**Parent:** COMPARABLE-APPROVED-INPUT. **Depends:** C0 para cerrar el incremento nuevo; las investigaciones independientes no se bloquean por él.
**Owner:** agente prepara; autoridad de fuentes aprueba/binda; arquitectura decide adopción.
**Files:** B1 `research_admission.py`, `source_control_store.py`, `statistical_retention.py`; tests de admisión/retención; contrato de puente estadístico.

- [ ] Completar expediente por fuente necesaria: fenómeno, métrica, unidad, territorio, periodo, cobertura, método, derechos, origen aguas arriba, revisión, vigencia y límites.
- [ ] Consumir aprobación/binding auténticos para el formato y alcance exactos; preservar IDs de términos/metodología y checkpoints externos. JSON-stat no hereda permiso XLSX. Preparar el expediente sin inventar el recibo de aprobación.
- [ ] Demostrar fuente admitida y lectura tras restauración, y rechazo por ausencia/rotación de autoridad, sustitución de formato, hash alterado, caducidad y rollback de control.

**Close:** fuente del alcance realmente admisible y recuperable con línea de autoridad verificable; una cuarentena o firma de fixture no cierra. Política de renovación de IDs debe quedar explícita. MAR 12–13 y custodia externa permanecen decisiones distintas.

### P02 — obtención periódica acotada (arista 2)

**Parent:** COMPARABLE-APPROVED-INPUT. **Depends:** P01 para integración activa; adapter candidato puede probarse antes.
**Owner:** agente implementa; autoridad de fuente/arquitectura activa cada adapter.
**Files:** `research_acquisition.py`, `research_collection.py`, B4 `local_worker.py`, `operations.py`; tests de colección, intake y ciclo local.

- [ ] Conectar una fuente aprobada a su frecuencia, presupuesto, derechos, estado persistente, selección exacta y política de renovación; mantener configuración predeterminada sin efectos nuevos.
- [ ] Probar dos ejecuciones programadas, sin duplicar ni restablecer presupuesto al reiniciar; probar denegación, timeout, DNS privado/redirect no permitido, TLS inválido, tamaño y fallo parcial.
- [ ] Probar contrato/activación del adapter dentro del runtime cuando exista su autoridad; investigación del agente y scheduler instalado son capacidades diferentes.

**Close:** adquisición permitida y repetible sin intervención por archivo, límites y parada observables. La CLI de siete recetas ya ejecutada reduce trabajo, pero no demuestra esta integración activa. Presupuesto actual de investigación: 100 requests, 100 MiB/ciclo, 8 MiB/archivo, timeout 30 s, máximo tres intentos/request; prevalecen límites más estrictos.

### P03 — versiones, watchlist y contexto de revisión (arista 3)

**Parent:** RESOLUTION-INTELLIGENCE-EDITORIAL; referencias de fuente bajo COMPARABLE-APPROVED-INPUT. **Depends:** P01.
**Owner:** B1/agente; semántica específica de fuente requiere evidencia metodológica.
**Files:** `statistical_watchlist.py`, `change_context.py`, pipelines existentes; `test_statistical_watchlist.py` y tests de contexto.

- [ ] Integrar selección de versiones con el consumidor admitido, sin comparar dos años como si fueran revisiones del mismo periodo.
- [ ] Probar sin cambio, valor, flags, cobertura/missingness y revisión documentada; conservar padre e identidad. Metadata insuficiente deja causa no confirmada.
- [ ] Rechazar baseline alterado, reloj regresivo, cabeza ambigua y uso de historia vencida como raíz actual.

**Close:** comparación/espera correcta y recuperable. API con sólo última publicación admite `AWAIT_NEWER_SOURCE`; no exigir generar otra publicación ni recapturar idénticos bytes indefinidamente. Una revisión real sólo se declara con evidencia de esa revisión.

### P04 — correspondencia y corroboración real (arista 4)

**Parent:** COMPARABLE-APPROVED-INPUT. **Depends:** P01/P03.
**Owner:** B1; agente investiga; autoridad valida fuentes/semántica de correspondencia.
**Files:** `evidence_comparison.py`, `research_same_chain.py`; contratos de comparación y tests correspondientes.

- [ ] Construir matriz exacta de fenómeno, métrica, unidad, geografía, periodo, cobertura y método; ninguna conversión/tolerancia inventada.
- [ ] Documentar cadena de origen. Eurostat y Statbel pueden compartir origen portuario; editor/URL diferentes no son raíz independiente. CIF USD HN y toneladas BE no corroboran.
- [ ] Probar un caso comparable y un caso realmente independiente cuando la necesidad lo exija; adversariales de coincidencia numérica con distinto alcance, origen compartido y fuente vencida.

**Close:** la comparación conserva acuerdos, discrepancias y límites; sólo afirma corroboración donde independencia y equivalencia estén demostradas. Para necesidades metodológicas no imponer innecesariamente una segunda raíz.

### P05 — resolución por necesidad y reapertura (arista 5)

**Parent:** RESOLUTION-INTELLIGENCE-EDITORIAL. **Depends:** P04; consume P01 y metadata/cuenta según tipo de necesidad.
**Owner:** B1 semántica; arquitectura/negocio acepta política; B4 no emite resolución.
**Files:** `need_classification.py`, `need_assessment.py`, contrato de tareas y `operations.py`; tests de clasificación/evaluación/research cycle.

- [ ] Especificar política por ruta: corroboración, metodología oficial, detalle de fuente y exposición autorizada; desconocida conserva clasificación manual.
- [ ] Definir resultado resuelta/insuficiente/contradictoria y razones, evidencias, vigencia y condición de reapertura; no sustituir la política ausente por un score o LLM.
- [ ] Integrar una resolución contratada de B1 con transición durable de la tarea; probar respuesta suficiente y abstención, contradicción, cambio de fuente, replay y reapertura tras reinicio.

**Close:** una necesidad real especificada puede cerrarse o reabrirse por razones verificables; insuficiencia permanece explícita. El triaje actual y `REQUEST_BLOCK1_REASSESSMENT` no satisfacen este cierre. MAR 8–10.

### P06 — inteligencia útil y E01–E08 (arista 6)

**Parent:** RESOLUTION-INTELLIGENCE-EDITORIAL. **Depends:** P05.
**Owner:** B1; arquitectura/negocio valida interpretación y casos de referencia.
**Files:** `intelligence_dossier.py`, `statistical_dossier.py`, `dossier_editorial_bridge.py`, motores B1 y `statistical_review_archive.py`; tests de dossier/archive/engines.

- [ ] Conectar evaluación a un dossier durable separando hechos, evidencia, interpretación, hipótesis refutables, alternativas, incertidumbre, contradicciones, preguntas y próximos datos.
- [ ] Verificar E01–E08 con paquetes actuales y alcance exacto, contra casos independientes de la lógica implementada; no inventar explicación causal de una resta.
- [ ] Probar alteración, firma válida con cuerpo falso, evidencia incompleta/fuera de alcance, caducidad durante ejecución y recuperación/replay sin efecto adicional.

**Close:** dossier integrado y una conclusión acotada evaluada sobre evidencia real cuando sea sustentable; los casos insuficientes abstienen interpretación. Hechos literales y motores ejecutados no prueban utilidad estratégica por sí solos. MAR 14.

### P07 — calidad y decisión editorial (arista 7)

**Parent:** RESOLUTION-INTELLIGENCE-EDITORIAL. **Depends:** P06.
**Owner:** B1/editorial; autoridad de producto acepta criterios/corpus.
**Files:** `editorial.py`, `dossier_editorial_bridge.py` y tests editoriales existentes.

- [ ] Fijar criterios evaluables de relevancia/utilidad/calidad con casos de referencia aceptados, no copiar umbrales de Notion como norma.
- [ ] Probar shortlist trazable y selección/abstención; probar dossier no interpretado, evidencia vencida, contradicción y manipulación de score.
- [ ] Demostrar que shortlist/selección no publica ni vende ni entrega, manteniendo fuentes y limitaciones.

**Close:** candidato sustentado elegible en un caso real evaluado y abstención correcta en casos rechazados. `RESEARCH_NEEDED` es comportamiento válido, no prueba de contenido editorial listo.

### P08 — Design comprensible y accesible (arista 8)

**Parent:** DESIGN-PRECISION-EFFECTS. **Depends:** P07 para contenido evaluado; pruebas de render pueden adelantarse.
**Owner:** B2/agente; producto aporta evaluación de uso autorizada.
**Files:** B2 `design_artifact.py`, consola y tests de integridad/UI.

- [ ] Integrar diseño al brief/dossier evaluados, manteniendo evidencia y límites en la salida.
- [ ] Probar render, teclado, contraste/estructura accesible y exportación conforme al contrato; refutar HTML hostil, pérdida de fuente/advertencia y activos desactualizados.
- [ ] Evaluar comprensión con usuarios autorizados y tareas definidas antes del ensayo; registrar errores y correcciones, sin inventar participantes o resultados.

**Close:** producto comprensible/accesible con evidencia de las tareas acordadas, no sólo HTML generado. Métricas y umbrales de comprensión deben acordarse, no estimarse retrospectivamente.

### P09 — Precision con contexto autorizado (arista 9)

**Parent:** DESIGN-PRECISION-EFFECTS. **Depends:** P08; ingreso/validación candidato puede adelantarse.
**Owner:** B3/agente; autoridad de datos/cuenta define alcance y consentimiento aplicable.
**Files:** B3 `audience_draft.py`, fabric de cuentas/M01–M07 y tests de perfil/contexto.

- [ ] Completar contrato de contexto de cuenta/persona: exposición, fuente, actualización, permisos y límites de uso; no deducir exposición comercial de geografía declarada.
- [ ] Probar adaptación pertinente contra una cuenta autorizada y caso sin contexto que abstiene personalización.
- [ ] Rechazar contexto vencido/revocado, cruce de cuenta/identidad y exceso de alcance; verificar recuperación con permisos conservados.

**Close:** relevancia demostrada en el alcance autorizado. Perfil genérico, dato ficticio o scoring no constituyen conocimiento de una persona.

### P10 — orquestación de investigación de ciclo cerrado (arista 10)

**Parent:** LOCAL-RESEARCH-CYCLE. **Depends:** P02/P05/P06; composición offline construible antes con fixtures explícitos.
**Owner:** B4 coordina; B1 conserva decisión de evidencia/resolución.
**Files:** B4 `research_cycle.py`, `operations.py`, `operations_store.py`; tests de ciclo/piloto y contrato local.

- [ ] Encadenar necesidad → ruta permitida → evaluación B1 → resolución/espera → dossier nuevo → decisión nueva, sin enlace manual obligatorio.
- [ ] Probar ciclo positivo con fuentes admisibles; negativo con insuficiencia/contradicción sin promoción; presupuesto, fairness, no duplicados, pausa y STOP.
- [ ] Inyectar fallo entre etapas, restaurar y demostrar que el resultado/cursor no avanza falsamente ni repite efectos; fuente cambiada invalida respuesta anterior.

**Close:** vuelta completa trazable o espera terminal específica con reactivación sólo por entrada nueva. El ciclo actual busca dossiers locales y conserva evaluaciones, pero no demuestra resolución completa. MAR 10–11, contratos de red/resolución antes de activar esas rutas.

### P11 — entrega, recibos y aprendizaje (arista 11)

**Parent:** DESIGN-PRECISION-EFFECTS. **Depends:** P09, autorización de efecto y contrato de recibo.
**Owner:** B3/agente construye; autoridad de canal/datos activa el efecto.
**Files:** B3 `delivery.py`, `learning.py`, integración de recibos B4 y tests M06–M08.

- [ ] Construir/verificar recepción y aprendizaje candidato offline con activo, audiencia, canal, fecha y resultado ligados; etiquetar fixtures/simulaciones.
- [ ] Rechazar borrador como entrega, recibo inventado/alterado, identidad cruzada, outcome anterior a entrega, replay y correlación presentada como causalidad.
- [ ] Sólo tras autorización específica, obtener recibo del efecto realmente ejecutado y seguimiento observado; ninguno se puede fabricar para terminar la checklist.

**Close:** entrega autorizada y resultado real alimentan M08 al alcance aprobado. Hoy publicación/contactos/CRM permanecen bloqueados: no declarar cerrado este proceso de producto por una simulación. Una salida local sólo cuenta si su contrato define ese efecto y autoridad; no rebautizar borradores como entrega.

### P12 — interfaz operable, seguridad, operación y cierre (arista 12; transversal)

**Parent:** INTEGRATED-ACTIVATION. **Depends:** P10/P11 para autonomía ampliada; pruebas de recuperación/UI son paralelizables antes.
**Owner:** agente construye; autoridad de arquitectura/operación acepta activación/custodia y revisión exigida.
**Files:** B4 `laboratory_recovery.py`, `operations_store.py`, consolas/lanzador, `sictra/closure_preflight.py`, manifest vigente y tests de recuperación/integración.

- [ ] Mostrar estado/versión/limitaciones, fuente actual o indisponible, watchlists, dossiers, shortlist y espera; operador no técnico debe poder iniciar, pausar, diagnosticar y restaurar mediante guía reproducible.
- [ ] Verificar identidad/roles del operador, custodia separada de claves/checkpoints, retención y métricas de errores/latencia/capacidad; sin autenticar un backup por su propio hash restaurado.
- [ ] Probar respaldo/restauración integral en ruta nueva, no sobrescribir aplicación; migración/rollback, datos alterados, permisos incompletos, falta de claves, corte y STOP.
- [ ] Para laboratorio, preparar piloto integrado con fuentes admisibles y operador autorizado, duración y número de ciclos fijados por política, reinicio y restauración durante el piloto. No exigir cuentas, canales o entrega externos si están fuera de ese alcance. Tres ciclos sintéticos anteriores no prueban operación sostenida.
- [ ] Si se solicita y autoriza autonomía ampliada con P09/P11, añadir cuentas/canales autorizados y recibos reales al piloto. Su ausencia deja esos procesos de producto abiertos, no bloquea pruebas independientes del laboratorio ni autoriza activar efectos.
- [ ] Ejecutar regresión completa, JavaScript, compilación, lanzador, preflight adversarial y CI del SHA final; revisar doce procesos y ocho hitos B1; conservar límites y revisión independiente pendiente.

**Close:** versión integrada al alcance expresamente activado, operable y recuperable con evidencia del piloto y manifest final. No instalar, promover gate ni marcar `GREEN` por el checklist. MAR 1–6 y adopciones 12–15.

## Orden eficiente, sin construir todo desde cero

1. **Fase A — estabilizar:** C0; conservar mecanismos ya cerrados. No gastar otra sesión redescubriendo cuarentena, render, polling o backup existentes.
2. **Fase B — entrada fiable:** P01 y ruta de P02; P03/P04 sobre fuentes admisibles. Preparar decisiones de admisión concretas mientras se prueban adaptadores desactivados. No ampliar el catálogo antes de satisfacer la pregunta prioritaria.
3. **Fase C — núcleo de valor:** P05 → P06 → P07. Especificar primero una necesidad representativa y su oráculo; ampliar a las rutas ya definidas sólo tras un caso completo. No simular interpretación con texto plausible.
4. **Fase D — conectar la vuelta:** P10 con entradas/semántica de B–C. Prevenir recuperación parcial, caducidad y replay en la misma integración, no al final.
5. **Fase E — experiencia y efecto:** P08 → P09 → P11. Render/accesibilidad, permisos de contexto y recibos sin efecto pueden adelantarse si sus contratos están definidos; validación con usuarios/datos reales sigue separada.
6. **Fase F — operar y cerrar:** P12, piloto autorizado, manifest y reevaluación de todos los criterios. Evidencia faltante mantiene el proceso abierto; no cambiar el alcance para pintar 100%.

Dependencias de construcción (no el grafo de eventos en operación): C0→P01; P01→P02/P03/P04; P03→P04; P04→P05→P06→P07→P08→P09→P11; P02/P05/P06→P10. Para operación del laboratorio: P10→P12. Si se solicita y autoriza autonomía ampliada con entrega, añadir P11→P12; no imponerla al cierre técnico del laboratorio. Un nuevo dossier puede crear otra necesidad durante operación: esa recurrencia exige presupuesto/parada, no un ciclo infinito de construcción.

Trabajos independientes seguros: pruebas offline de permisos/recibos, accesibilidad, restauración y adapters candidatos suficientemente especificados. Paralelizar únicamente con autorización de delegación aplicable, propietario de archivos claro y sin tocar módulos compartidos a la vez; no es requisito usar todos los agentes. El riesgo manda el orden viable, no la fila más fácil de documentar.

## Protocolo único por incremento

- [ ] Leer SHA/CI/estado ajeno, AGENTS/contrato/tests y parent del backlog. Consultar esta checklist y elegir un criterio abierto, no todo el proceso como tarea indivisible.
- [ ] Escribir en el parent: ID, comportamiento, archivos/interfaces ya definidos, entrada requerida, prueba positiva, refutación, integración/recuperación, límite y condición observable. Semántica sin contrato: registrar decisión requerida; construir sólo la parte independiente especificada.
- [ ] Ejecutar RED → implementación mínima → GREEN → revisión/red-team → reparación. Oráculo externo a la conclusión del código.
- [ ] Ejecutar regresión completa antes de commit material y CI exacta después del push. No repetir regresión del producto por una edición exclusiva de skill/plan; validar los artefactos cambiados y registrar cualquier CI rojo preexistente.
- [ ] Registrar estado de mecanismo, integración, evidencia real y aceptación por separado, logs/SHA/run/UTC, límites y siguiente acción. Actualizar Notion sólo como proyección contextual cuando corresponda; no otra cola.

Ficha obligatoria en el ledger: `ID | parent | objetivo observable | dependencias | mecanismo | integración | evidencia real | autoridad/aceptación | positivo | adversarial | recuperación | SHA/CI/UTC | límite | owner | próximo paso`.

En cada ciclo declarar qué casilla técnica cambia. Si sólo cambia este plan, es planificación solicitada, **no progreso ejecutable del producto**. No reiniciar el contador durable de estancamiento por ella. Tras tres ciclos programados consecutivos sin delta o ausencia probada de ruta segura, conservar/poner PAUSED la automatización existente y un diagnóstico; no reintentar sin entradas nuevas.

## Crosswalk obligatorio de Bloque 1

| Hito AGENTS | Comprobaciones |
| --- | --- |
| 1 Fuente retenida/aprobada/recuperable | P01 |
| 2 Watchlist de versiones | P03 |
| 3 Dossier separado y durable | P05/P06 |
| 4 E01–E08, evidencia vigente y rechazos | P06 |
| 5 Shortlist/selección/abstención sin publicar | P07 |
| 6 Interfaz de laboratorio | P12, procedencia/limites de P08 |
| 7 Operación reproducible y recuperación | P12, entrada controlada de P02 |
| 8 Preflight/regresión/CI/manifest | C0 y cierre final P12 |

## Decisiones que no se pueden fabricar

Admisión/renovación por fuente y formato; equivalencia/tolerancia específica; política de resolución/interpretación y corpus editorial; métricas de comprensión; contexto de cuenta/consentimiento; canal/recibo/outcome; identidad/custodia/piloto/activación y MAR. Para cada decisión preparar propuesta, evidencia, opciones, owner y efecto exacto bloqueado. La ausencia de una decisión no bloquea el trabajo técnico independiente ni autoriza al agente a firmarla como un tercero.

No hay fecha de finalización porcentual defendible con esas entradas abiertas. Medir cierres de criterios con evidencia y fallos pendientes, no porcentaje supuesto de programación.

## Validación de esta actualización de skill/plan

- Línea base sin nueva referencia, cinco consultas de aplicación: el agente
  identificó que «No están definidos los IDs estables de proceso ni el mapeo
  oficial de las 12 aristas», faltaba secuencia contractual y no disponía de
  regla/valor del contador. No se interpreta esa falta de información como
  una falla del producto; demuestra el hueco de la referencia anterior.
- Prueba de uso por agente distinto con skill/contexto/checklist/plan, las
  mismas cinco consultas: recuperó los doce IDs/parents, seleccionó C0 con
  pruebas observables, no cerró CI roja, ubicó el único ledger/contador y
  separó datos de usuario/entrega de trabajo seguro offline. Sólo lectura;
  no es revisión independiente humana, regresión ni aceptación del producto.
- Hallazgo de alcance corregido: el piloto de laboratorio no impone cuentas/
  canales/entrega de autonomía ampliada; estos mantienen sus requisitos propios.
  Relectura por el evaluador confirmó la casilla y detectó el resumen de
  dependencias incondicional; también se explicitó allí la condición P11→P12.
- Limitación de reproducción explicitada: documentos locales no contenidos
  en 210843b; validar rutas locales no prueba disponibilidad desde el remoto.
- Validación estructural: quick_validate de skill aprobado; doce IDs únicos,
  doce mappings y 25 rutas necesarias existentes. Disciplina previa preservada;
  esta ampliación es referencia de cierre, no medición universal de eficacia.
