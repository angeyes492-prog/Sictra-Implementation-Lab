# Bloques 2 y 3 — pulido de interfaces, ciclo local ejecutable

> Fecha/contexto: `2026-09-11`, instalación limpia de Python, servidores
> loopback y Chromium mediante Playwright.  
> Runtime implementado: `af3c1b1b8a24d38ab02e997473d166fed232cab6`.  
> Certeza/confianza: `VERIFIED / A` para las comprobaciones automatizadas
> descritas; `INSUFFICIENT EVIDENCE` para aceptación humana integral.  
> Frontera: `LABORATORY_INTERNAL_SUPERVISED / NOT PRODUCTION / NOT GLOBAL
> ACCEPTANCE`.

## Estado del gate

| Campo | Estado |
|---|---|
| Gate | `YELLOW` |
| Capability | `IMPLEMENTED / EXECUTED / LOCAL BROWSER VERIFIED` |
| Evidencia focal | `23/23 PASS` |
| Regresión instalada limpia | `688/688 PASS` |
| Hosted CI | `PENDING` para el commit final que contiene esta evidencia |
| Revisión visual humana independiente | `INSUFFICIENT EVIDENCE` |
| Global acceptance | `NO` |

## Closure delta

- Bloque 2 presenta rutas operativas diferenciadas para Preparar, Taller y
  Operación, conserva códigos de disposición sin reinterpretarlos y ofrece
  orientación, recuperación, estados vacíos y límites de autoridad visibles.
- Bloque 3 mantiene contexto persistente de cuenta y evidencia, separa
  admisión, hipótesis, señales gobernadas y controles, y elimina contenido
  previo cuando una lectura falla para evitar una apariencia de vigencia.
- Ambas interfaces exponen foco visible, regiones vivas atómicas, estado de
  carga, reflow sin overflow global, soporte de movimiento reducido y colores
  forzados, sin afirmar conformidad WCAG.
- Se añadieron sondas browser reproducibles para los caminos normales, vacíos
  y fallidos, además de nueve capturas de escritorio/estrecho y vistas
  operativas. La ejecución terminó sin errores de consola.
- La instalación limpia reveló que `brand-mark.png` del Bloque 1 no estaba
  incluido en el paquete. La regresión rechazó la instalación con un error;
  se corrigió la declaración de package data y se confirmó la recuperación en
  una segunda instalación limpia junto con los nuevos favicons de Bloques 2 y
  3.

## Ejecuciones y oráculos

| Comando/verificación | Resultado | Clase |
|---|---|---|
| `python -m unittest tests.test_block2_design_console tests.test_block3_precision_console -v` | `23/23 PASS` | focal UI/server |
| `python tools/block2_console_accessibility_probe.py` | `PASS`; 0 overflow, 47 controles, 0 sin nombre o tamaño insuficiente | browser automatizado B2 |
| `python tools/block3_precision_console_probe.py` | `PASS`; normal/vacío/fallo, foco, stale suppression y códigos crudos | browser automatizado B3 |
| `node tools/interface_polish_capture.js` | `PASS`; 9 capturas, 0 errores de consola | inspección visual asistida |
| `node --check` sobre ambos clientes y sondas | exit `0` | sintaxis JavaScript |
| instalación limpia + `python -m unittest discover -s tests -q` | `688/688 PASS` en `37.336s` | regresión workspace instalada |

Los probes de navegador actúan como oráculos externos al código cliente para
comprobar DOM, foco, dimensiones y transiciones observables. No reutilizan la
conclusión de la implementación como resultado esperado.

## Red team, rechazo y recuperación

1. Una lectura fallida después de mostrar datos válidos debe marcar el contexto
   como no vigente, borrar paneles y mostrar `RETURN_UPSTREAM`; la sonda de
   Bloque 3 verificó el comportamiento completo.
2. Colecciones vacías no pueden aparentar señales o controles admitidos; el
   servidor y la sonda verificaron estados explícitos sin autoridad derivada.
3. Las disposiciones y reason codes se muestran en forma cruda y escapada; la
   interfaz no las traduce a recomendaciones ni scores.
4. La primera regresión instalada falló porque faltaba
   `sictra_block1/web/brand-mark.png`. La corrección de package data fue
   comprobada desde una segunda instalación aislada antes de repetir la
   regresión completa con éxito.

## Límites y próxima reasignación

- Las capturas y sondas no sustituyen una revisión humana con NVDA/VoiceOver,
  zoom real, Windows High Contrast ni evaluación cognitiva por operadores.
- No se probó publicación, entrega, venta, sincronización con CRM, identidad
  real, eficacia comercial ni operación fuera de loopback.
- Los datos observados son fixtures sintéticas locales; no son verdad de
  producción ni evidencia de aceptación del cliente.
- La siguiente promoción posible requiere CI exitosa sobre el SHA final y la
  evaluación humana que corresponda al alcance pretendido. Hasta entonces el
  gate permanece `YELLOW` y el sistema no excede
  `LABORATORY_INTERNAL_SUPERVISED`.
