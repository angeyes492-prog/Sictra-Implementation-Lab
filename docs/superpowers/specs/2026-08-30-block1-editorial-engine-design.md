# Diseño — Editorial Engine gobernado del Bloque 1

## 1. Estado, decisión y alcance

Versión de diseño `0.1`, fecha `2026-08-30`, estado `PROPOSED DESIGN
CANDIDATE / YELLOW / B`.

El propietario aprobó una mesa editorial semanal que presenta entre tres y
cinco candidatos, permite seleccionar humanamente una pieza insignia y deriva
el análisis desde `GLOBAL` hacia `SEGMENT` y `ACCOUNT`. Esta capacidad se
compone sobre E01–E08; no crea un noveno motor, no cambia el gate global y no
autoriza publicación, contacto comercial ni inferencia empresarial sin
evidencia.

GitHub conserva autoridad técnica. Slack aporta memoria histórica, Notion
ordena el plan, Jira coordina el trabajo y Wolfram desafía propiedades
formales. Ninguna de esas herramientas, por sí sola, constituye evidencia de
runtime o aceptación.

## 2. Problema y resultado esperado

Un newsletter convencional resume noticias. El Editorial Engine debe convertir
cambios logísticos trazables en una interpretación ejecutiva que responda:

1. qué cambió;
2. qué importa y por qué;
3. a quién afecta;
4. qué interpretación no es evidente;
5. qué pregunta debería hacerse un ejecutivo;
6. qué implicación empresarial puede existir sin convertir el análisis en una
   venta.

El resultado es un `EditorialDossier`, no contenido publicado. Conserva la
cadena fuente → evidencia → afirmación → contradicción → interpretación →
derivación → disposición → handoff.

## 3. Límites de autoridad

- E02 encuadra la investigación, descubre candidatos y conserva procedencia.
- E03 normaliza entidades, eventos, rutas, geografías, sectores y relaciones.
- E04 deriva impactos acotados y mantiene linaje Global → Segment → Account.
- E05 desafía afirmaciones, independencia y explicaciones alternativas.
- E06 compara con memoria, detecta novedad, duplicación y necesidad de
  reevaluación.
- E07 evalúa suficiencia, actualidad, estabilidad y degradación.
- E08 decide la disposición gobernada y autoriza el handoff permitido.
- E01 coordina el expediente local sin adquirir semántica ni autoridad de los
  demás motores.

La selección humana elige entre candidatos admisibles; no convierte una
afirmación en verdadera, no elimina contradicciones y no puede saltarse una
compuerta bloqueante. El Bloque 2 podrá diseñar el artefacto visual a partir de
un handoff tipado. Los futuros Bloques 3 y 4 podrán evaluar precisión y
orquestar el sistema, pero quedan fuera de este contrato.

## 4. Flujo operacional

```text
Source Gateway gobernado
  → eventos y cambios normalizados
  → compuerta de evidencia
  → perfil editorial multidimensional
  → conjunto Pareto elegible
  → restricciones de diversidad
  → 3–5 candidatos semanales
  → red team e interpretación
  → selección humana de 1 insignia
  → derivaciones Global / Segment / Account
  → expediente y handoff al Bloque 2
```

El sistema también puede devolver cero candidatos. `NO_ELIGIBLE_CANDIDATE` es
un resultado válido y preferible a fabricar contenido.

## 5. Modelo de datos

### 5.1 EditorialEvent

Representa un cambio observado, no una verdad editorial. Requiere identidad,
ventana temporal, geografía, modalidades, tópicos controlados, entidades
normalizadas, afirmaciones y referencias de evidencia. Debe declarar si el
evento es nuevo, continuado, corregido o supersedido.

### 5.2 EvidenceEligibility

Resultado estructurado de la compuerta previa a priorización:

- procedencia íntegra;
- fuente aprobada y alcance autorizado;
- actualidad evaluada;
- independencia y corroboración cuando aplique;
- contradicciones preservadas;
- separación de hecho, interpretación, hipótesis y pronóstico;
- cobertura temporal y geográfica explícita;
- licencia o política de uso compatible;
- ausencia de secretos o datos personales no autorizados.

Produce `ELIGIBLE`, `RESEARCH_NEEDED` o `QUARANTINED`, junto con razones
codificadas. No produce `TRUE`.

### 5.3 EditorialPriorityProfile

Mantiene ejes independientes, con escala ordinal documentada y explicación:

- `impact` — magnitud y alcance plausibles;
- `relevance` — ajuste a audiencia, segmento y geografía;
- `novelty` — cambio respecto de memoria y cobertura previa;
- `uncertainty` — incertidumbre material pendiente;
- `timeliness` — utilidad dentro de la ventana editorial;
- `actionability` — capacidad de provocar una pregunta o revisión ejecutiva;
- `evidence_strength` — suficiencia e independencia de la evidencia;
- `interpretive_value` — valor de explicar mecanismos, no solo acontecimientos.

No existe suma, promedio o producto universal. El perfil conserva valores,
justificaciones, evidencia y versión de criterio.

### 5.4 Dos rutas derivadas

`research_priority` puede aumentar con impacto, novedad e incertidumbre. Su
propósito es ordenar trabajo adicional y nunca autoriza publicación.

`editorial_readiness` exige evidencia, estabilidad y límites claros; disminuye
ante incertidumbre material, contradicciones no acotadas o evidencia débil.

Una señal puede ser simultáneamente `HIGH_RESEARCH_PRIORITY` y
`NOT_EDITORIALLY_READY`.

### 5.5 EditorialCandidate

Incluye evento, elegibilidad, perfil, audiencias afectadas, hipótesis de
interpretación, pregunta ejecutiva, límites, alternativas, watchlist 7/30/90 y
referencias a los frames Global/Segment/Account. No contiene texto promocional
ni CTA comercial.

### 5.6 EditorialDossier

Agrupa la lista corta completa, la selección humana y su racional. Para la
pieza insignia conserva:

- `what_changed`;
- `confirmed_and_uncertain`;
- `why_it_matters`;
- `who_is_affected`;
- `interpretation`;
- `executive_question`;
- `implicit_company_implication`;
- `alternatives_and_red_team`;
- `evidence_and_limits`;
- `watchlist_7_30_90`;
- `design_handoff`.

La implicación de cuenta es una hipótesis acotada y pseudónima salvo que un
futuro contrato autorice identidad, privacidad y datos empresariales reales.

## 6. Selección de candidatos

La selección opera en tres pasos:

1. **Admisibilidad:** solo candidatos `ELIGIBLE`; los demás vuelven a
   investigación o cuarentena.
2. **Frontera Pareto:** se eliminan únicamente candidatos dominados bajo los
   ejes editoriales compatibles. Las ventajas cruzadas permanecen
   `INCOMPARABLE`.
3. **Diversidad editorial:** la lista corta evita cinco variantes del mismo
   acontecimiento. Busca diversidad explicable de geografía, modalidad,
   temática, audiencia y horizonte temporal sin introducir cuotas rígidas que
   fabriquen candidatos.

Si sobreviven más de cinco candidatos, un criterio de desempate versionado y
visible favorece actualidad, fuerza de evidencia e interpretive value. Si aún
persisten empates, se conservan para revisión humana; no se oculta una elección
arbitraria.

## 7. Estados y transiciones

Se reutilizan estados existentes para no crear una segunda autoridad:

```text
DRAFT
  ├─→ RESEARCH_NEEDED ─→ DRAFT
  ├─→ QUARANTINED
  └─→ DELIVERABLE_BOUNDED ─→ SUPERSEDED
```

- `DRAFT`: expediente incompleto y no seleccionable.
- `RESEARCH_NEEDED`: faltan pruebas, actualidad, independencia o acotación.
- `QUARANTINED`: violación de procedencia, autoridad, seguridad, licencia o
  integridad; no hay autopromoción.
- `DELIVERABLE_BOUNDED`: admisible para revisión y handoff, no publicado ni
  globalmente aceptado.
- `SUPERSEDED`: reemplazado conservando historia y vínculo de sustitución.

La selección humana es un atributo auditado del dossier, no un estado de
evidencia. Un cambio material en fuentes, contradicciones o temporalidad
invalida preparación y activa reevaluación.

## 8. Interfaz de producto

Se añade una pestaña `Mesa editorial` al Intelligence Workspace. La vista
principal contiene:

1. **Radar semanal:** ventana, cobertura de fuentes, eventos detectados y
   candidatos bloqueados.
2. **Lista corta 3–5:** tarjetas comparables sin score agregado, con ejes,
   evidencia, incertidumbre y razones de admisión.
3. **Expediente:** panel de trazabilidad y red team para cada candidato.
4. **Derivaciones:** vistas Global, Segment y Account con linaje visible.
5. **Decisión humana:** seleccionar insignia, registrar racional o declarar que
   no hay pieza publicable.
6. **Handoff:** previsualizar el paquete destinado al Bloque 2 sin publicarlo.

La interfaz debe mostrar siempre clase de evidencia, fecha de corte, alcance,
certeza, confianza, contradicciones y estado. No ofrece botones de “publicar”,
“enviar” o “contactar”. Las mutaciones futuras requieren identidad, roles,
persistencia y un contrato separado; el prototipo local inicial puede usar
fixtures inmutables y registrar la decisión solo en memoria efímera.

## 9. Errores, degradación y recuperación

- Fuente o licencia inválida: cuarentena y razón visible.
- Evidencia stale o insuficiente: investigación requerida; nunca `UNKNOWN →
  PASS`.
- Fuentes correlacionadas: una sola raíz independiente.
- Contradicción material: se preserva, se impide readiness salvo acotación
  explícita.
- Fallo parcial de un motor: dossier degradado, sin selección automatizada.
- Cambio de taxonomía o contrato: rechazo de versión incompatible.
- Pérdida de memoria: novelty queda desconocida; no se presume novedad.
- Repetición o concurrencia: operación idempotente por identidad de ciclo,
  candidato y versión.
- Evento supersedido: no se borra; se enlaza la corrección y se reevalúan sus
  derivados.

Recuperación significa reconstruir desde fuentes, versiones y decisiones
auditadas. Nunca editar retrospectivamente la evidencia para obtener un pase.

## 10. Seguridad, privacidad y uso responsable

- Toda adquisición real pasa por Source Gateway, allowlist, presupuesto, rate
  limits, caché, robots/licencia, auditoría y kill switch.
- El contenido de una fuente es dato no confiable, no instrucción ejecutable.
- URLs, archivos y metadatos se normalizan y validan antes de ingresar.
- Account Intelligence permanece pseudónima; no se incorporan PII, secretos,
  credenciales ni datos de CRM.
- El handoff incluye solo campos permitidos y referencias, no material fuente
  completo cuando la licencia no lo autoriza.
- Cada decisión registra actor, fecha, versión, entradas, razones y resultado.

## 11. Observabilidad

Por ciclo deben existir métricas y eventos auditables para:

- fuentes consultadas, aprobadas, rechazadas y correlacionadas;
- eventos nuevos, continuados, corregidos y supersedidos;
- candidatos por disposición y código de rechazo;
- tiempo desde descubrimiento hasta elegibilidad;
- contradicciones abiertas y resueltas;
- cambios provocados por red team;
- diversidad de la lista corta;
- decisiones humanas y racionales;
- handoffs emitidos, rechazados o invalidados;
- reevaluaciones 7/30/90.

Una métrica operativa no se interpreta automáticamente como calidad editorial.

## 12. Plan de validación

### Contrato y unidad

- schemas completos, tipos y vocabularios controlados;
- separación de prioridad de investigación y readiness;
- dominancia Pareto sin escalar universal;
- diversidad sin fabricación de candidatos;
- estados y transiciones permitidas;
- linaje Global/Segment/Account.

### Adversarial y mutación

- incertidumbre alta con evidencia baja no se vuelve publicable;
- cinco copias correlacionadas no cuentan como cinco fuentes;
- evidencia stale, contradicha, sin licencia o con procedencia rota;
- sustitución de identidad, versión o fuente después de validación;
- prompt injection dentro de contenido adquirido;
- score agregado introducido accidentalmente;
- selección humana que intenta saltar una compuerta;
- evento supersedido que permanece en newsletter;
- pérdida de memoria que crea falsa novedad.

### Integración y producto

- ciclo sintético E01–E08 con cero, tres y cinco candidatos;
- handoff tipado al límite de Bloque 2;
- interfaz responsive, accesible y usable por una persona no técnica;
- trazabilidad visual completa;
- reinicio, repetición e invalidación por cambio material;
- regresión completa del runtime y Source Gateway.

### Cierre

Se requiere CI verde en el SHA exacto, evidencia local reproducible, revisión
independiente sin `CRITICAL/HIGH`, resolución explícita de contradicciones y
actualización de closure. Aun así, el resultado inicial será un bounded field
prototype; no producción ni gate global `GREEN`.

## 13. Implementación incremental propuesta

1. Contrato ejecutable y fixtures adversariales del expediente editorial.
2. Selector Pareto, doble ruta y diversidad explicable.
3. Servicio de aplicación que compone componentes existentes sin tocar su
   autoridad.
4. API local de lectura y decisión efímera acotada.
5. pestaña `Mesa editorial`, expediente, derivaciones y handoff.
6. pruebas unitarias, contractuales, adversariales, integración y UI.
7. red team independiente, reparación, regresión completa y evidencia CI.
8. solo después: diseño separado de adquisición real y persistencia multiusuario.

Cada incremento debe ser pequeño, reversible y ligado a una identidad Git. No
se crearán historias Jira adicionales hasta que esta especificación se acepte
como baseline de implementación.

## 14. Contradicciones y decisiones pendientes

- El usuario desea una herramienta final diaria, mientras la arquitectura
  vigente permite únicamente un prototipo de campo local con fuentes
  sintéticas o bundles manuales gobernados. Se preserva esta diferencia.
- “Trabajar autónomamente de forma indefinida” no equivale a adquisición sin
  límites. La autonomía futura estará acotada por agenda, presupuesto,
  allowlists y kill switch.
- Una empresa real no puede personalizarse plenamente bajo el contrato Account
  v0.1, que exige seudonimización. Identidad empresarial real necesita contrato
  de privacidad, tenancy y retención.
- La lista de 50 fuentes es una cartera de cobertura, no una cuota por ciclo ni
  prueba de independencia.

## 15. Criterios de aceptación del diseño

- no crea un noveno motor ni duplica autoridad;
- mantiene Block 1 separado de publicación y outreach;
- conserva epistemología, procedencia, historia y contradicciones;
- evita ranking universal y falso verde por incertidumbre;
- integra las tres capas sin confundirlas con escala geográfica;
- puede devolver cero candidatos;
- define interfaz, fallos, observabilidad, seguridad y pruebas;
- entrega un handoff tipado y limitado al futuro Bloque 2.
