# Block 2 — protocolo de revisión asistiva humana v0.1

> Estado: `CANDIDATE / HUMAN REVIEW REQUIRED / NOT ACCEPTED`.

## Propósito y límite

Convertir la revisión pendiente de NVDA/VoiceOver en una evidencia atribuible,
reproducible y limitada a la consola local. No aprueba la arquitectura, el
contenido, la producción ni el Bloque 2 global. El browser probe automatizado
es sólo preparación: no suplanta la experiencia de una persona usuaria de
tecnología asistiva.

## Entrada exacta

El revisor recibe:

- SHA Git y URL de la PR bajo revisión.
- Entorno: sistema operativo, navegador, versión de NVDA o VoiceOver, zoom y
  configuración de contraste.
- Fixture sintética `PROJECT-DEMO`, URL local de Design Console y salida de
  `python tools/block2_console_accessibility_probe.py`.
- Este protocolo, sin tesis creativa ni resultado esperado del review.

Un cambio de SHA, CSS, JS, fixture o configuración material obliga a un nuevo
recorrido; no se reutiliza un `PASS` histórico.

## Recorrido mínimo observable

1. Abrir la consola y confirmar que el primer foco anuncia el enlace para
   saltar al contenido; activarlo y registrar destino, anuncio y foco.
2. Recorrer por teclado Create, Studio y Ops. Para cada vista registrar orden,
   nombre/rol/estado de los controles y si existe foco visible.
3. En Create, enviar un handoff incompleto y registrar el anuncio de retorno y
   las razones. No introducir facts reales ni intentar publicación.
4. En Studio, seleccionar un stage y un elemento; registrar el cambio anunciado
   en inspector/canvas. Abrir la edición controlada sin guardar contenido real.
5. Activar reduced motion y alto contraste del sistema cuando estén disponibles;
   registrar si se pierde significado, foco o lectura.
6. Repetir el recorrido con zoom 200% y texto aumentado; distinguir reflow
   local de scroll intencional de la banda de lineage.

## Recibo de revisión

El reviewer entrega por cada hallazgo: `SHA → fixture → tecnología/version →
paso → esperado observado → resultado observado → severidad WCAG → evidencia
reproducible → limitación`. Estados permitidos: `PASS_LOCAL`,
`ISSUE_REPRODUCED`, `INCONCLUSIVE` o `RETURN_UPSTREAM`.

`PASS_LOCAL` sólo declara que ese paso funcionó para el entorno identificado;
no equivale a conformidad WCAG total, aceptación humana general ni promoción de
gate. Un hallazgo crítico o mayor deja la fila accesibilidad en `YELLOW` o
`RED` hasta reparación, retest y revisión independiente.

`contracts/block2_assistive_review_receipt_contract_v0.1.md` y
`assistive_review.py` validan localmente el binding del recibo a SHA, fixture,
URL loopback y hash del probe. Esa validación no sustituye ni valida la
experiencia de la persona revisora.

## Dependencias y recuperación

La ejecución requiere una persona con NVDA o VoiceOver y autoridad para
registrar la revisión. Si falta tecnología, identidad, evidencia, SHA o el
entorno no es reproducible, la salida es `RETURN_UPSTREAM`; el agente no
infiere la experiencia ni fabrica un receipt. Los hallazgos deben entrar como
issue/review y recibir un vector regresivo antes de cualquier promoción.
