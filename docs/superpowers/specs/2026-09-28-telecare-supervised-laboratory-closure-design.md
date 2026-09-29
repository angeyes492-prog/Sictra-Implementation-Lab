# Telecare OS — gestión de cierre del laboratorio supervisado

Estado: `DISEÑO ESTRATÉGICO APROBADO POR EL USUARIO / SIN PROMOCIÓN DE GATE`
Fecha: 2026-09-28
Alcance autorizado: `LABORATORY_INTERNAL_SUPERVISED`

## Decisión y propósito

Telecare OS avanzará por cierre verificable de capacidades locales, no por número de integraciones o apariencia de autonomía. Una ejecución autónoma sólo puede repetir acciones previamente acotadas sobre fuentes, perfiles, presupuestos y rutas aprobados. La contradicción, caducidad, evidencia insuficiente, cambio de semántica o cualquier efecto externo obligan a abstenerse, detenerse o solicitar revisión humana. Publicar, entregar, contactar terceros y decidir comercialmente permanecen bloqueados.

Este documento diseña **el sistema de gestión del trabajo técnico**. No modifica contratos de los bloques, no acepta arquitectura transversal, no incorpora complementos al runtime y no demuestra que un requisito esté implementado. Su primera entrega es un inventario de evidencia y una cola de cierre reconciliada; cada subproyecto posterior requiere su propio contrato, pruebas y, cuando corresponda, revisión de arquitectura.

## Contexto y conflicto que debe reconciliarse

- `AGENTS.md` exige recorrer ocho requisitos de Bloque 1 en orden de riesgo y no reabrir trabajo ya cerrado sin evidencia contradictoria nueva.
- `closure/closure_execution_queue_v0.1.md` presenta `B4-INTEGRATION-REBASE` como trabajo técnico listo. Su prioridad no puede desplazar la secuencia protegida de Bloque 1.
- `docs/telecare_astra_execution_playbook.md` documenta un checkout integrado, instalación local y pruebas de septiembre, pero es una fotografía histórica que debe revalidarse contra SHA, árbol de trabajo, servicios y CI actuales.
- `architecture/telecare_os_block_model_v1.md` declara cuatro responsabilidades y advierte que el modelo no prueba integración. Su párrafo de estado refleja un corte anterior; no se actualiza ni se usa como prueba del runtime sin una revisión arquitectónica.
- La página [Notion de Bloque 1](https://app.notion.com/p/3c789f66067b8108bb44c13ac4b15ac0) es contextual, no verificada y anterior al trabajo de septiembre. Las pruebas de complementos de `evidence/telecare_plugin_experiments_2026-09-27.md` son investigación, no aceptación de fuente ni de gate.

Resolución de proceso: conservar ambas afirmaciones, verificar su vigencia y documentar el resultado en **una sola cola ordenada**. Si los ocho requisitos de Bloque 1 están probados en el límite local, el siguiente trabajo técnico puede ser la integración acotada de Bloque 4. Si falta evidencia de un requisito anterior, se atiende primero ese requisito. Una decisión sobre semántica compartida, autoridad o producción se eleva a Master Architecture Review; no se resuelve cambiando el orden de una tabla.

## Arquitectura del proceso

El proceso tiene cinco objetos de gestión, distintos de los objetos del runtime:

1. **Ficha de capacidad:** requisito, bloque dueño, contrato, dependencia, estado diseñado/implementado/ejecutado/validado/integrado/aceptado y límite de autoridad.
2. **Paquete de evidencia:** SHA, prueba y oráculo independiente, resultado, hora, alcance, fuente, certeza, confianza A–E, CI exacta y contradicciones.
3. **Tarjeta de bloqueo:** estado, evidencia, dueño de la decisión, siguiente acción local segura y frontera de promoción. `UNKNOWN` e `INSUFFICIENT EVIDENCE` nunca equivalen a pase.
4. **Cambio reversible:** diff pequeño, prueba positiva, prueba adversarial pertinente, modo de fallo, observabilidad y rollback.
5. **Manifiesto de cierre:** capacidades y límites realmente demostrados, regresión, CI, riesgo residual, revisión independiente diferida y siguiente decisión externa.

GitHub conserva identidad técnica, código, pruebas y CI. El ledger del repositorio es la cola canónica de trabajo. Notion puede ordenar contexto y decisiones humanas, pero no sustituye el ledger. Wolfram analiza modelos formales; Exa y Firecrawl descubren material externo; Vercel se reserva para evaluación de una superficie futura. Ninguno concede autorización a otro bloque ni transforma material de investigación en evidencia admitida.

## Flujo de selección y ejecución

Al inicio de cada ciclo se lee el SHA, estado Git, CI correspondiente, instalación local si aplica, contratos, pruebas y ledger. Se audita cada requisito de la secuencia protegida de Bloque 1: fuente retenida; cambio de watchlist; dossier; E01–E08; revisión editorial; interfaz; operación reproducible; manifiesto. Para cada uno se decide `VERIFIED`, `CONTRADICTED` o `INSUFFICIENT EVIDENCE` **en el alcance preciso observado**, sin inferir aceptación global. El primer requisito de mayor riesgo no cerrado se convierte en el único incremento activo; el resto permanece ordenado.

Cada incremento sigue `READ → DIAGNOSE → PRIORITIZE → ATTACK → BUILD → TEST → RED TEAM → REPAIR → RETEST → REASSESS → RECORD → NEXT`. Se exige una prueba positiva y al menos una de rechazo, tamper, caducidad, replay o recuperación con oráculo independiente. Las pruebas focalizadas se ejecutan durante el cambio y la regresión completa antes de un commit material. El commit sólo cuenta como evidencia de cierre cuando CI termina satisfactoriamente en **ese SHA exacto**. Un PR abierto o una instalación que responde no equivalen a integración aceptada.

La cadena funcional que se verifica, sin volver a construir lo ya demostrado, es: fuente aprobada y retenida → versiones y watchlist → dossier → atestación E01–E08 → candidato editorial → adaptación por perfil → revisión humana en Bloque 4. El identificador de caso, hashes, contratos, incertidumbre y límites atraviesan los handoffs. Una identidad ausente, alterada, vencida o fuera de alcance debe suprimir el efecto descendente. El resultado sigue siendo un borrador local, nunca publicación.

## Uso de los complementos

| Complemento | Tarea admisible ahora | Condición para uso futuro en runtime |
| --- | --- | --- |
| Notion | Recuperar contexto, decisiones y preguntas; enlazar el SHA y el ledger canónico. | Ninguna página confiere autoridad técnica o aceptación. |
| Exa | Descubrir documentación y fuentes candidatas, priorizando originales. | Resultado revisado y autorizado mediante el contrato de fuente; relevancia no basta. |
| Firecrawl | Leer páginas públicas para investigación y ensayar captura offline con sobres pregrabados. | Fuente, host, claims, alcance, licencia, presupuesto, retención, hash y kill-switch aprobados; tráfico desactivado por defecto. |
| Wolfram | Buscar ciclos, atajos de transición y rutas que eludan revisión humana en modelos extraídos de contratos. | El modelo formal debe contrastarse con pruebas del código; no promueve gates. |
| Vercel | Consultar documentación de despliegue, entornos y observabilidad para una decisión posterior. | Proyecto, identidad, secretos, política de datos, revisión arquitectónica y autorización explícita antes de desplegar o programar cron. |

Los complementos son **herramientas del proceso de construcción**, no dependencias obligatorias del programa local. Sus resultados se archivan con URL o identidad, fecha, alcance, certeza y límite de promoción. La investigación previa de Eurostat indica que, para una fuente futura admitida, hay que retener el cuerpo exacto y su hash antes de comparar versiones; un campo `updated` no sustituye esa retención.

## Fallos, revisión y recuperación

- Evidencia obsoleta, circular, incompleta o contradictoria: bloquear la promoción, conservar la contradicción y abrir una tarjeta de reparación o revisión.
- Fallo de un complemento: continuar con evidencia local admisible; no degradar controles ni fabricar una respuesta externa.
- CI ausente o fallida en el SHA final: el cambio permanece sin cierre técnico aunque las pruebas locales pasen.
- Necesidad de fuente real, credencial, licencia, decisión comercial, revisión independiente o publicación: completar primero el trabajo local seguro; dejar una tarjeta con dueño, dato faltante y frontera exacta.
- Pausa, STOP, replay o restauración: probar que no crean una aprobación, publicación o efecto duplicado; la recuperación vuelve al estado restringido que establezca el contrato.

## Hitos de aceptación del proceso

1. **Línea base reconciliada:** inventario de los ocho requisitos con enlaces a contratos, pruebas, SHA/CI y discrepancias; una sola cola priorizada sin borrar historia.
2. **Primer delta de cierre:** reparación o validación nueva del requisito prioritario, con prueba positiva y adversarial y resultado reproducible.
3. **Cadena local comprobada:** recorrido B1→B2→B3→B4 con el mismo caso, trazas y abstenciones correctas; datos sintéticos etiquetados y separados del estado del operador.
4. **Operación y recuperación:** pausa/STOP, replay, respaldo/restauración, arranque repetido y ruta de operador no técnico probados.
5. **Manifiesto final:** regresión completa, preflight adversarial, CI del SHA exacto, capacidades, límites, riesgos y revisión independiente pendiente. El reclamo máximo por defecto es `LABORATORY_INTERNAL_SUPERVISED`.

Una mejora innovadora transversal —por ejemplo, una ficha verificable por corrida que reúna procedencia, contratos, controles y recibos de recuperación— sólo entra al backlog después de demostrar problema, usuario, objeto, autoridad, fallo, observabilidad, prueba independiente y rollback. Si altera semántica compartida, exige Master Architecture Review. No desplaza el primer requisito sin cierre.

## Exclusiones y siguiente especificación

Este diseño no autoriza scraping de red en el runtime, proveedor de IA, CRM/PII, despliegue Vercel, envío, publicación, aceptación global ni afirmación de autonomía irrestricta. Tampoco declara completado ninguno de los ocho requisitos. Tras revisión del usuario, el plan de implementación debe detallar únicamente el **hito 1, línea base reconciliada**, con archivos, comandos, pruebas y criterios de salida; los subproyectos de producto se especifican según los hallazgos de ese inventario.
