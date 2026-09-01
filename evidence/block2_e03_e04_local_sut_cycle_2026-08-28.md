# Block 2 / E03–E04 — Ciclo SUT local y técnicas profesionales

> Fecha: `2026-08-28`  
> Estado: `IMPLEMENTED / EXECUTED / LOCAL BOUNDED DIFFERENTIAL`; no integrado,
> no validado externamente y no aceptado.

## Closure delta

Se implementaron dos validadores locales y dos oráculos separados:

- E03: perfil de sistema con tokens semánticos, fallback no cromático,
  componentes con estados/accesibilidad, rights por canal y vigencia,
  excepciones temporales con owner y rollback, y preservación upstream;
- E04: blueprint con claim/evidence/limit mapping, lectura, fallback por medio,
  selección de encoding por relación, unidades/polaridad/incertidumbre,
  atribución, identidad única y prohibición de output ejecutable/publicado.

Los mecanismos convierten técnicas profesionales en restricciones falsables;
no afirman poseer criterio estético humano ni años de experiencia real.

## Ejecución y reparación

| Ejecución | Resultado | Alcance |
|---|---|---|
| E03 targeted | `10/10 PASS` | derechos, tokens, componentes, metadata, selección y matriz diferencial. |
| E04 targeted | `11/11 PASS` | mapping, charts, accesibilidad, scope, identidades y matriz diferencial. |
| Block 2 discovery | `65/65 PASS` | regresión local completa del bloque. |
| workspace discovery final | `224 PASS / 1 ERROR` de 225 | falla concurrente fuera de scope en Block 3: `account_memory.py` referencia `_tokens` inexistente. |
| compileall | éxito | sintaxis local de `src` y `tests`. |

El primer E03 run detectó una diferencia de mayúsculas en incertidumbre y fue
reparado sin relajar el test. Un red-team posterior reemplazó vigencia booleana
de rights/excepciones por rights actuales y ventanas temporales con reloj
inyectado. E04 añadió rechazo de identidades duplicadas. La primera consulta
formal de mutaciones estaba mal formulada; se descartó y se repitió.

## Reconciliación de cuatro fuentes

| Fuente | Observación | Clasificación y frontera |
|---|---|---|
| GitHub PR #3, 2026-08-28 | acredita sólo E01 y permanece sin aceptación global; no contiene E03/E04. | `VERIFIED / A` para identidad remota; no evidencia E03/E04. |
| Slack | búsquedas específicas de E03/E04 sin resultados. | `INSUFFICIENT EVIDENCE`; ausencia no confirma inexistencia. |
| Notion | resultados relevantes siguen siendo reassessments E01; no registro E03/E04 localizado. | `INSUFFICIENT EVIDENCE`; contexto no autoridad. |
| Rovo | no localizó especificación SICTrA E03/E04; sólo plantillas genéricas. | `INSUFFICIENT EVIDENCE`; no promoción. |
| Wolfram | promotion graph acíclico; sin `INTEGRATED`, aceptación no es alcanzable; tres atajos inyectados fueron detectados. | `VERIFIED / A` para el modelo formal; no runtime ni gate. |

## Estado por dimensión

| Dimensión | E03 | E04 |
|---|---|---|
| Diseñado | `CANDIDATE` | `CANDIDATE` |
| Implementado | `LOCAL BOUNDED SUT` | `LOCAL BOUNDED SUT` |
| Ejecutado | `YES` | `YES` |
| Validado | `LOCAL DIFFERENTIAL` | `LOCAL DIFFERENTIAL` |
| Integrado | `NO` | `NO` |
| Aceptado | `NO` | `NO` |

## Riesgos, límites y siguiente ataque

No se usó dirección seleccionada real, brand manifest completo, licencia
jurídica, contenido real, render, prueba perceptual/humana, auditoría WCAG,
software de diseño, CI externa ni review independiente. El workspace global no
está green por una regresión concurrente de Block 3 que este ciclo no modificó.
E05–E08 siguen como
arquitectura candidata; el siguiente delta responsable es contrato E05 y
rúbrica E07 antes de implementar producción E06 o memoria E08.
