# Bloque 2 — Design Console local, ciclo ejecutable

> Fecha/contexto: `2026-08-30`, Edge headless local + Python/SQLite.  
> Certeza/confianza: `VERIFIED / A` para ejecución local; `PROBABLE / B` para
> accesibilidad hasta prueba humana con tecnología asistiva.  
> Frontera: `READ MODEL / NOT PUBLISHED / NOT ACCEPTED`.

## Closure delta

- Añadido read model JSON seguro desde Project Graph y CDD.
- Añadido servidor local sólo lectura con CSP, host/origin guards y métodos de
  mutación bloqueados.
- Materializada la interfaz Design Studio: Project Rail, semantic canvas,
  Evidence Inspector y Lineage Ribbon.
- Añadida CLI `python -m sictra_block2_design.design_console_web` con bootstrap
  sintético determinista opcional.
- Añadidas seis pruebas de API, seguridad, estado ausente, estructura HTML,
  accesibilidad base y responsive CSS.

## Ejecuciones

| Comando/verificación | Resultado | Clase |
|---|---|---|
| `python -m unittest tests.test_block2_design_console -v` | 6/6 PASS | focal UI/server |
| `python -m unittest discover -s tests -p 'test_block2*.py' -q` | 99/99 PASS | regresión Bloque 2 |
| `python -m unittest discover -s tests -q` | 308/308 PASS | regresión workspace |
| `python -m compileall -q src tests` | exit 0 | sintaxis/import Python |
| `node --check .../app.js` | exit 0 | sintaxis JS |
| Edge 1440×1000 | 8 stages, 2 elements, Inspector y Ribbon visibles | browser local |
| Edge 390×844 | global overflow 0px; Ribbon 1120/324px interna | responsive local |

## Red-team y reparaciones

La primera inspección móvil detectó ancho global de 117px adicional y choque
entre el título del canvas y su state chip. Se encapsuló el scroll en Lineage
Ribbon, se limitó el main a viewport y se apiló el header móvil. Retest:
`document.scrollWidth == clientWidth == 390`.

La navegación real por teclado enfoca primero `Saltar al estudio`; Enter mueve
el foco a `<main id="studio">`. Seleccionar `CHART-001` actualiza el inspector.
POST a `/api/project` devuelve 405 y el mensaje explícito de sólo lectura.

## Límites

No se ejecutaron NVDA/VoiceOver, browser zoom real 200%, análisis automatizado
axe, visual regression por pixel ni revisión humana independiente. Las capturas
fueron inspeccionadas durante el ciclo, pero no constituyen aceptación visual.
La UI no implementa aún edición, diff, checkpoints, Create u Ops.

