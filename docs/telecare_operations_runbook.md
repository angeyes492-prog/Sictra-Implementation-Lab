# Operación local de Telecare OS

## Iniciar y usar

1. Ejecuta `start_telecare.cmd`. El proceso sigue activo al cerrar el navegador.
   Conserva estado y claves en `%LOCALAPPDATA%\TelecareOS\Operations`.
2. En Orchestrator abre «Registrar una versión de la fuente aprobada» y elige
   un XLSX del conjunto marítimo Eurostat `tran_r_mago_nm`, nivel país/NUTS.
   La primera versión establece la base; registra una segunda versión distinta
   para producir diferencias y un dossier. No se descargan fuentes remotas.
3. El servicio procesa la entrada y genera un artefacto de diseño basado en el
   dossier: jerarquía de información, componentes para cambios observados,
   preguntas, incertidumbre y procedencia visible. Lee el resultado sin cambiar
   de pestaña con «Abrir artefacto».
4. Usa «Configurar el perfil editorial objetivo» para adaptar tono, profundidad
   y selección geográfica. Es una audiencia genérica declarada, no un registro
   de personas ni inferencia de intención. El perfil vence a los 90 días.
5. Opcionalmente activa «Vigilar carpeta local» y deposita XLSX aprobados en la
   ruta que muestra la consola. Se exigen dos lecturas idénticas antes de registrar
   una versión; su hash se revalida al ejecutar. No se recorren otras carpetas.
6. Si la entrada queda en revisión, los artefactos siguen visibles. El operador
   puede registrar una abstención para permitir el siguiente archivo. El servicio
   nunca inventa una aprobación de ese dossier ni una recuperación tras fallo.

## Pausa, parada y arranque

La pausa se conserva tras reiniciar. «Detener» crea un archivo STOP que impide
nuevos ciclos. Para quitar explícitamente ese bloqueo, cierra el proceso del
servicio identificado, ejecuta el comando `reset-stop` y vuelve a iniciarlo.
No borres las bases de datos para recuperar el sistema.

`install_telecare_startup.ps1` registra un inicio al entrar a Windows para el
usuario actual, sin privilegios elevados. No sobrescribe una tarea con otra
configuración. Deshabilítala con el Programador de tareas de Windows si quieres
dejar de iniciar automáticamente. El equipo debe estar encendido y la sesión
iniciada; esto no es alojamiento de disponibilidad continua.

## CLI y pruebas

Desde el repositorio, con `PYTHONPATH` apuntando a `src`:

```powershell
python -m sictra_block4_orchestrator.operations --state RUTA init
python -m sictra_block4_orchestrator.operations --state RUTA serve --port 8768
python -m sictra_block4_orchestrator.operations --state RUTA status
python -m sictra_block4_orchestrator.operations --state RUTA backup DESTINO_NUEVO
python -m sictra_block4_orchestrator.operations --state RUTA restore BACKUP NUEVA_BASE.sqlite
python -m sictra_block4_orchestrator.pilot --state RUTA_NUEVA_PARA_PILOTO
```

El piloto crea datos sintéticos etiquetados y verifica dos versiones, dos
perfiles, contenido numérico y restauración. No descarga ni simula aprobación
de una fuente real. No mezcles su carpeta con la operación real.

## Respaldo, incidentes y alcance

El servicio crea diariamente un respaldo firmado de su journal de operaciones,
configuración y artefactos de diseño. `restore` sólo admite un destino inexistente y
verifica firmas/hash. Ese respaldo **no incluye** claves, pipeline de fuentes
ni cola de entrada; éstos conservan los mecanismos de backup/recovery de
`sictra_block1.operator_pipeline` y `sictra_block4_orchestrator.local_worker`.
Respalda esos componentes antes de migrar o retirar el equipo. No se promete
recuperación integral a partir del respaldo de operaciones por sí solo.

Ante error de integridad el servicio detiene su worker. `/health` responde 503
si no está ejecutándose o está en error. Revisa `service.stderr.log` y conserva
los archivos originales. No se repite una ingesta interrumpida automáticamente.
Las salidas vencidas, revocadas o asociadas a un perfil reemplazado se bloquean.

La generación actual es determinista: Bloque 2 crea un artefacto de diseño que
preserva hechos extraídos y hace visible evidencia, incertidumbre y límites;
Bloque 3 adapta esa presentación. No es un proveedor LLM conectado ni investigación
abierta en Internet. El análisis causal, fuentes adicionales, perfiles reales,
proveedor externo, identidad organizacional, ancla externa anti-rollback y
promoción de producción conservan sus decisiones y validaciones pendientes.
