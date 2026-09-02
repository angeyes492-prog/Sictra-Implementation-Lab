# Block 2 — auditoría local de render HTML/SVG (2026-09-01)

## Alcance

- Estado: `IMPLEMENTED / EXECUTED LOCAL / NOT ACCEPTED`.
- Certeza: `VERIFIED`; confianza `A` para Edge headless y los paquetes locales
  generados desde la fixture sintética.
- Límite: no demuestra compatibilidad con clientes de email, lectores SVG de
  terceros, NVDA/VoiceOver, calidad creativa ni aceptación global.

## Hallazgo y reparación

Se detectó por inspección que SVG no aplica wrapping por defecto: copy válido
pero largo podía exceder el lienzo. `export_service._svg_lines` ahora divide el
copy por palabras y fragmentos deterministas, genera `tspan` y calcula el alto
del `viewBox` a partir de las líneas. El texto íntegro permanece disponible en
`desc` y en el companion accesible, por lo que la reparación no trunca el
contenido ni sustituye accesibilidad por layout.

## Ejecución

| Vector | Comprobación | Resultado |
|---|---|---|
| Unidad | `python -m unittest tests.test_block2_export_service -v` | 5/5 PASS; incluye copy largo y no truncamiento del companion accesible |
| Browser | `python tools/block2_export_render_probe.py` con Edge headless | HTML: un `main`, un `h1`, overflow horizontal `0`; SVG normal: role/img, título+descripción, 2 `tspan`, 0 cajas fuera del viewBox |
| Browser red-team | mismo probe con 120 repeticiones de `evidencia-trazable` | 31 `tspan`, viewBox `1200×1238`, 0 cajas de texto fuera del viewBox |
| Sintaxis | `node --check tools/block2_export_render_probe.js` y `python -m compileall -q src tests tools/block2_export_render_probe.py` | PASS |

El probe genera los paquetes mediante `execute_traceable_block2` y
`persist_export`, no con HTML/SVG escrito a mano. No publica artefactos:
ambos permanecen `NOT_PUBLISHED / NOT_ACCEPTED`.

## Revisión WCAG local

La comprobación cubre estructura HTML (`main`, `h1`), reflow horizontal,
semántica SVG (`role=img`, `aria-labelledby`, `title`, `desc`) y contenido
dentro del viewBox. Los colores de texto fijos `#182033` sobre `#ffffff`
superan holgadamente el umbral 4.5:1 de WCAG AA, pero esta evaluación
automatizada sólo es parcial. La revisión con tecnología asistiva humana queda
pendiente y no cambia el gate de accesibilidad.

## Siguiente ataque

Vincular los dos commits del ciclo a GitHub Actions sobre su SHA exacto. Luego,
mantener las cuatro condiciones globales separadas: MAR, provider real
gobernado, revisión asistiva humana y aceptación humana.
