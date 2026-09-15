# Ficha de trazabilidad local V1

Estado: implementación incremental de observabilidad; revisión arquitectónica
independiente diferida. Propietario B4. Alcance LABORATORY_INTERNAL_SUPERVISED.

Problema: el operador necesita consultar y conservar la identidad de un boletín
y el recorrido que produjo su contenido sin reunir información de cuatro vistas.
La ficha deriva de un OUTPUT firmado, vigente, su diseño y adaptación validados,
las abstenciones del mismo dossier y los recibos de recuperación del almacén.
No altera contratos B1–B3 ni crea aceptación, evidencia independiente o acciones.

GET /api/operations/outputs/{id}/factsheet muestra HTML accesible;
GET /api/operations/outputs/{id}/factsheet.json descarga JSON. Ambos heredan
Host/Origin, no-store, CSP y rechazo de identidad inexistente, fuente vencida,
perfil sustituido, integridad alterada o contenido desalineado. El servicio
revalida antes de devolver la ficha. No se escribe un nuevo evento al leerla.

TELECARE_FACTSHEET_V1 incluye identidad, fecha de lectura, clase de datos,
fuente/dossier/evidencia/hash, perfiles y huellas de diseño/adaptación, etapas,
revisiones diferidas, recuperación y límites. Los recibos de recuperación son
del almacén; nunca se presentan como recuperación individual de ese artefacto.
Pruebas e independencia aparecen explícitamente como no adjuntas al boletín.
El SHA256 permite detectar cambios en la copia JSON; no prueba autoría ni
vigencia futura y no reemplaza la firma interna. No exporta claves, tokens,
rutas de archivos fuente, HTML del boletín ni datos de otros dossiers.

Validación: identidad literal, hashes independientes, lectura sin escrituras,
escape HTML, rechazo de vencimiento, alteración del journal, origen hostil,
ausencia de identidad y aislamiento de revisiones. Rollback: retirar las rutas
y botones de ficha; las fuentes y los artefactos originales quedan intactos.

Inspiración consultada 2026-09-15: fichas de ciclo de vida de
[IBM](https://www.ibm.com/products/watsonx-governance/model-governance).
Se adapta sólo el patrón de documentación por activo al runtime determinista
existente. Es una decisión de diseño local, no una validación de IBM.
