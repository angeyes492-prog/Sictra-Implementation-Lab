# Telecare OS — cierre técnico local de Astra

Fecha de observación: 2026-09-15, America/Tegucigalpa.
Alcance: `LABORATORY_INTERNAL_SUPERVISED`.
Estado de construcción local planificada: terminada dentro de esta frontera.
Estado de aceptación global/independiente: no concedida.

Este manifiesto cierra la secuencia del addendum 2026-09-15 de
`docs/telecare_astra_execution_playbook.md` del checkout original, commit
3523de26cbb863d3623cbc42c68dcc6008dd9ce3. No declara SICTrA globalmente GREEN,
producción ni investigación autónoma abierta en Internet. Las revisiones
diferidas no son aprobaciones. No hace falta solicitar evidencias para terminar
la construcción local aquí descrita.

## Identidad y evidencia ejecutada

| Incremento | SHA | CI exacta |
| --- | --- | --- |
| Cadena integrada, UI de referencia, revisión diferida y recuperación | eb6f5be2fb165d8d0f358fab6e484678ff5d50d3 | [34975973919: success](https://github.com/angeyes492-prog/Sictra-Implementation-Lab/actions/runs/34975973919) |
| Rutas persistentes y arranque Windows | 300ec67ba07f2ca5db3708661570168d1526168e | [35017520665: success](https://github.com/angeyes492-prog/Sictra-Implementation-Lab/actions/runs/35017520665) |
| Producto final, ficha y entrada operativa de Intelligence | eda3f0873896c6e18c664d92f9b254822a23b93c | [35018654437: success](https://github.com/angeyes492-prog/Sictra-Implementation-Lab/actions/runs/35018654437) |

Rama: `codex/astra-telecare-closure`. El commit posterior que incorpora este
manifiesto sólo cambia documentación y ledger: no sustituye la evidencia del
SHA de producto ni implica una nueva implementación. Su identidad se obtiene
con `git log -1 --format=%H -- closure/telecare_astra_local_closure_manifest_20260915.md`;
su CI debe consultarse por ese SHA exacto antes de entregar el cierre.
No se ha fusionado silenciosamente esta rama en main ni aceptado el PR #15.

Regresión final local ejecutada en Windows/Python 3.12: **767 pruebas Python**,
**9 pruebas JavaScript**, y comprobaciones PowerShell de ruta predeterminada,
preservación de legado, override explícito, esquema inválido, ruta relativa y
JSON corrupto; todas satisfactorias. CI sobre Linux/Python 3.11 confirma también
compilación, sintaxis JS y los tres runtimes acotados de referencia.

Se preserva el resultado fallido del incremento 8b9ab198874d18564a9f4a569bd9dd40b6a7e2a7:
[CI 35018031319](https://github.com/angeyes492-prog/Sictra-Implementation-Lab/actions/runs/35018031319).
Un test nuevo fijaba un digest de un XLSX generado cuyo contenedor variaba entre
plataformas. La reparación calcula independientemente el hash de los bytes de
entrada y del contenido retenido, y verifica su enlace de procedencia; no toma
la conclusión de la ficha como oráculo ni debilita el rechazo. Ese SHA fallido
no fue desplegado. Las cuatro pruebas de ficha y la regresión completa pasaron
de nuevo antes del commit reparado.

## Capacidad instalada y comprobación integrada

Instalación: `C:/Users/angel/AppData/Local/TelecareOS/Application`.
Estado del operador: `C:/Users/angel/AppData/Local/TelecareOS/Operations`.
Entrada: `http://127.0.0.1:8768/`; lanzador: `start_telecare.cmd`.

- B1/8765: `pipeline_reader=AVAILABLE`, `dossier_reader=AVAILABLE`. Intelligence
  abre Dossiers, no el catálogo sintético ni el Orchestrator antiguo.
- B2/8766 y B3/8767: `/api/review-artifacts` devuelve `AVAILABLE`; son lectores
  del mismo artefacto vigente y no confieren aceptación.
- B4/8768: `RUNNING`, `watch_enabled=true`, `evidence_review_deferred=true`,
  `publication=BLOCKED`. Pausa, reanudación, STOP, vigilancia, perfiles y entrada
  de archivo mantienen sus controles. La pausa de mantenimiento fue explícita
  y la operación previa se reanudó después de respaldar e instalar.
- Navegación por navegador B4→B1→B2→B3→B4 comprobada en la instalación final.
  El botón «Ejecutar ciclo completo» produjo el recibo
  `ffe3108a13c376922343f3a7c7af1dbf9fb0c059c3f4ff65b47e7db6243c848a`:
  `ORCHESTRATION_EXECUTED`, entrada `IDLE`, sin salidas ni entrega. No se confunde
  esa ejecución vacía con el procesamiento de una fuente real.
- Inicio repetido conservó los servicios/rutas; se probó también Windows
  PowerShell 5, usado por `TelecareOS-LocalOperations` al entrar a la sesión.
  Un puerto servido por otra versión falla explícitamente.
- Orchestrator conserva la jerarquía de la referencia: escena isométrica
  ilustrativa, tarjetas claras compactas, profundidad suave, espacios y acento
  naranja. La imagen nunca actúa como mapa ni telemetría. Pruebas de escritorio
  y móvil pertenecen al ciclo de UI; la navegación instalada se repitió al final.

Las consolas B2/B3 conservan debajo su laboratorio de motores sintéticos,
etiquetado y separado de los boletines operativos. No se presenta ese contenido
como actividad real del operador ni se afirma un rediseño total de cada motor.

## Datos reales frente a piloto

El estado del operador tiene **0 boletines**, sin sustituirlo por demostraciones.
Está listo para las dos versiones aprobadas del XLSX marítimo Eurostat
`tran_r_mago_nm`: la primera establece base; una versión distinta permite delta
y dossier. La vigilancia exige estabilidad y revalida identidad/hash.

El piloto separado `C:/Users/angel/AppData/Local/Temp/telecare-astra-pilot-0915`
es `SYNTHETIC_PILOT`: cuatro salidas históricas, dos `CURRENT`, dos
`STALE_OR_REVOKED`, dos revisiones diferidas y cero entradas esperando. El
`pilot-report.json` conserva el ciclo inicial y la restauración verificada;
el snapshot posterior prueba la continuación sin aprobar contenido. Se retienen
sus archivos como evidencia, pero sus tres servidores temporales se detuvieron
y su pestaña se cerró. Nada del piloto se importó al estado real.

El flujo determinista fuente→dossier→diseño→adaptación no demuestra análisis
causal, relevancia editorial independiente ni aceptación E01–E08 global. Los
estados de caso/atestación y los de borrador editorial son contratos diferentes;
una salida `DESIGN_REVIEW_REQUIRED` no promueve un checkpoint del caso.

## Única innovación transversal entregada

Ficha por boletín vigente `TELECARE_FACTSHEET_V1`, consultable y exportable como
JSON desde B4. Ver [contrato](../architecture/telecare_factsheet_contract.md).
Incluye fuente normalizada, hashes, dossier, versión de diseño, perfil,
adaptación, etapas, incertidumbre, revisiones diferidas del mismo dossier y
límites de recuperación. No escribe al leer ni expone claves/tokens/rutas fuente.

Se verificó por navegador la ficha del artefacto sintético
`0a20aa0d62d12e226f5075a96268303a400e6db42ce8f1b7d1e93e53817a8f1d`,
su identidad y enlace JSON. Pruebas HTTP cubren descarga, CSP, lectura sin
escrituras, escape, origen hostil, ID inexistente, expiry, alteración del journal
y desalineación del contenido aun con un registro correctamente sellado.

El checksum de exportación no acredita autoría ni vigencia futura. El hash de
fuente es del contenido canónico mapeado, no del archivo XLSX original. Los
recibos de recuperación son historia del almacén, no prueba de recuperación
individual de ese boletín. Pruebas por artefacto y revisión independiente figuran
como `NOT_ATTACHED`. No se exporta una aprobación.

Inspiración primaria consultada: [IBM, model governance y factsheets](https://www.ibm.com/products/watsonx-governance/model-governance).
Sólo se adapta su patrón de documentación por activo. Ontología amplia,
bandeja adicional y nuevas propuestas de acciones quedan `DEFERRED_DESIGN`,
no como capacidad construida ni deuda necesaria para este cierre.

## Recuperación, rollback y conservación

Con los cuatro escritores detenidos se creó
`C:/Users/angel/AppData/Local/TelecareOS/Backups/astra-final-20260915`:
seis archivos de datos/configuración, claves excluidas. Se conserva también
`astra-pre-eb6f5be`. El respaldo final contiene la pausa de mantenimiento;
restaurar no implica reactivar automáticamente el trabajo.

La recuperación integral local exige claves retenidas separadamente, ruta
original inexistente, inventario y hashes válidos; no sobrescribe datos, no
reloca identidades y queda pausada. Los tests cubren restauración completa/vacía,
claves incorrectas, manipulación, lock y fallo parcial con STOP. No se restauró
destructivamente sobre el estado sano del operador.

`launch-paths.json` preserva el intake y la traza Design anteriores. El archivo
de respaldo conserva esas referencias, **no los datos externos referenciados**:
`.sictra-intelligence/research-intake.json` y `.runtime/block2-console.sqlite`
en el checkout original. No se movieron ni eliminaron esos archivos.
No se promete cifrado de custodia, HA o ancla externa anti-rollback.
Para incidentes y comandos, ver [runbook](../docs/telecare_operations_runbook.md).

Rollback de la ficha: retirar endpoints/botones sin tocar fuente ni artefactos.
Rollback de despliegue: detener escritores y seleccionar un SHA compatible con
su configuración; conservar antes el estado y claves. Nunca borrar bases para
recuperar ni cargar automáticamente un backup antiguo como si fuera vigente.

## Preflight adversarial y fronteras pendientes

| Frontera | Evidencia/resultado | Propietario y siguiente acción fuera del cierre |
| --- | --- | --- |
| Integridad, vigencia y alcance | Tests de tamper, stale, perfil reemplazado, origen y replay; rechazo sin efecto | Agente de construcción: reevaluar si cambia implementación/contrato |
| Recuperación y autoridad | Tests de claves, lock, STOP y restauración pausada | Operador: custodiar claves y respaldar archivos externos |
| Revisión diferida | Abstención trazable, no aceptación; pausa/error/expiry siguen bloqueando | Propietario editorial: revisar contenido cuando haya evidencia real |
| Calidad editorial y causalidad | `INSUFFICIENT EVIDENCE`, confianza E para afirmaciones externas | Responsable editorial: evaluación posterior con fuentes aprobadas |
| MAR y revisión independiente | Diferidas, no fabricadas; gates históricos sin promoción | Autoridad arquitectónica/revisor independiente: evaluar SHA final y contratos |
| Publicación, entrega, CRM y proveedor de IA | Bloqueados/no conectados | Propietario: decidir alcance y controles antes de cualquier habilitación |
| Disponibilidad de producción y rollback externo | No demostrados | Responsable de despliegue: identidad, custodia y controles de producción |

Hechos de implementación/ejecución acotados: `VERIFIED`, confianza A dentro de
las observaciones indicadas. Interpretación: el alcance local del playbook está
cubierto por esas pruebas. Hipótesis de utilidad/impacto externo: no evaluadas.
No se confunde autorrevisión adversarial con validación independiente.

Contexto Slack/Notion/Rovo/Wolfram reconciliado en
[arquitectura del ciclo](../architecture/telecare_astra_local_closure_20260915.md);
no sustituye evidencia ejecutable GitHub ni autoridad arquitectónica. El
checkout original conserva intactos `AGENTS.md` modificado y `.work-block1/`
ajenos al trabajo. No se modifica la jerarquía de fuentes ni la historia.

No queda reparación, prueba o capacidad local planificada abierta en la cola
Astra. Los únicos pendientes aquí son datos reales, evaluación editorial,
autoridad/revisión independiente y controles de un alcance externo/producción;
no se solicitan para usar el laboratorio construido.
