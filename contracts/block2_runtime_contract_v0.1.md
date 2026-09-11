# Block 2 / Design — Bounded Runtime Contract v0.1

> Estado: `CANDIDATE / LOCAL EXECUTABLE TARGET / NOT INTEGRATED OR ACCEPTED`

El runtime coordina E01→E08 y se detiene en el primer resultado no listo. No
fabrica selección E02, rights, observaciones E07 ni validación externa E08.
Éstas llegan como objetos atribuibles. Un run exitoso produce un artefacto
E06, una recomendación E07 y un candidato de memoria E08; no publica ni abre
gates.

La ruta es acíclica. E05 aporta restricciones antes de E06; E07 evalúa el
candidato; E08 sólo puede registrar para una generación posterior. Cada stage
registra disposición y reasons. Cualquier fallo conserva outputs previos como
evidencia local y no ejecuta stages descendientes.

El runtime parcial v0.1 acepta únicamente un prefijo canónico verificado. Los
stages rehidratados se marcan `REUSED_CHECKPOINT`; el sufijo se marca
`EXECUTED`. Engine Registry debe importar E01–E08 y coincidir con la identidad
del checkpoint antes de Resume. Mismatch, prefijo no contiguo o estado semántico
faltante falla cerrado.
