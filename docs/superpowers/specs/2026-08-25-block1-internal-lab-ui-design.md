# Telecare OS — UI de laboratorio interno para Bloque 1

## Estado

`PROPOSED` — diseño aprobado verbalmente; pendiente de revisión del documento
antes de implementar.

## Propósito y alcance

Una única página web local permite a una persona no técnica ejecutar y entender
cuatro escenarios deterministas del laboratorio de Intelligence Bloque 1.
No es la interfaz comercial de Telecare OS ni una integración de producción.

## Usuario y trabajo principal

Usuario: equipo interno sin conocimientos de programación.

Trabajo principal: seleccionar una prueba, ejecutarla y comprobar con claridad
si el runtime registró un efecto controlado o bloqueó correctamente la acción.

## Diseño de la pantalla

- Cabecera: `Telecare OS — Laboratorio interno · Bloque 1`.
- Aviso fijo de límites: entorno local, sin datos reales, sin envío de mensajes
  y sin integraciones externas.
- Cuatro controles: prueba válida, evidencia vencida, falta de autorización y
  alcance incorrecto.
- Panel de resultado con estado legible:
  - `Efecto controlado registrado` solo si el escenario válido devuelve
    `COMMITTED` y exactamente un registro de memoria.
  - `Bloqueado correctamente; no se registró ningún efecto` solo si un escenario
    adversarial devuelve `NOT_EXECUTED` y cero registros de memoria.
  - `Resultado inesperado; revisar detalle técnico` para cualquier otra salida.
- Sección plegable `Ver detalle técnico`, con traza E01–E08, journal,
  restricciones y no-claims que devuelve el laboratorio.
- Control `Limpiar resultado` que elimina únicamente el resultado mostrado;
  no modifica el runtime ni un archivo SQLite.

## Arquitectura y límites

La UI sirve contenido estático local y llama a un adaptador local que invoca
`sictra_block1.lab.execute_scenario`. La ejecución usa el almacén efímero por
defecto. La UI no acepta secretos, fuentes, rutas de archivo, tareas ni runs
del usuario.

No se implementan autenticación, red, adquisición de datos, HubSpot, envíos,
persistencia de resultados, multiusuario ni promoción de gates.

## Errores y seguridad

- Los cuatro escenarios están enumerados del lado del servidor; no se aceptan
  valores arbitrarios.
- Un error del adaptador se presenta con mensaje claro y detalle técnico
  plegable, sin afirmar que el motor bloqueó correctamente.
- La página expone los `non_claims` del reporte para impedir una lectura como
  evidencia de producción.
- La UI no transforma un resultado `COMMITTED` en aceptación de arquitectura o
  gate global.

## Validación

- Pruebas unitarias del adaptador: cada escenario llega al laboratorio correcto
  y su resumen humano concuerda con `enforcement.status` y
  `memory_record_count`.
- Prueba de integración HTTP local: los cuatro botones generan respuesta JSON
  válida y los valores no permitidos se rechazan.
- Regresión del runtime existente: suite completa sin debilitamientos.
- Comprobación manual: abrir la página, ejecutar los cuatro escenarios, abrir
  detalle técnico y limpiar resultado.

## Criterio de aceptación local

Una persona puede usar los cuatro controles sin terminal, distinguir éxito
controlado de bloqueo correcto, y verificar el detalle sin que la interfaz
realice ninguna acción externa.

## Non-claims

Este artefacto no declara una UI comercial, producción, datos reales,
integración externa, aceptación global, ni cierre del gate de Bloque 1.
