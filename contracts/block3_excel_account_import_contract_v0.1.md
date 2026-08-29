# Contrato candidato — Block 3 Excel Account Import v0.1

**Estado:** `CANDIDATE / LOCAL BOUNDED SUT`.

## Jurisdicción

El adaptador lee un archivo `.xlsx` no macro y devuelve un lote de semillas de
cuenta revisables. Es una frontera de entrada: no abre URLs, no persiste, no
escribe CRM, no prepara copy ni habilita delivery.

El `tenant_id` y el `authorized_purpose` son entradas gobernadas por el
operador; una celda nunca puede escogerlos. Esto evita que una hoja traslade
una cuenta a otro tenant o amplíe su propósito.

## Esquema admitido

La hoja requerida se llama `Accounts`. Encabezados admitidos (inglés y
equivalentes españoles):

| Campo | Estado | Semántica |
|---|---|---|
| `account_id` | requerido | identidad de cuenta dentro del tenant |
| `official_url` | requerido | URL HTTPS oficial sin query, fragment ni credenciales |
| `company_name` | opcional | declaración de la hoja; no es fact |
| `source_reference` | opcional | referencia declarada para revisión |

Encabezados no admitidos, duplicados, fórmulas, columnas con valor sin
encabezado, rutas de archivo, macros, XML con entidades, ZIP bombs, filas o
campos sobre el presupuesto causan rechazo visible. Una fila inválida no se
importa silenciosamente; se reporta con su número físico de Excel y una razón
gobernada.

## Salida, evidencia y límites

`ExcelAccountImportBatch` preserva hash SHA-256 del workbook, nombre de origen,
fecha lógica, política, aceptaciones, rechazos y restricciones. Cada
`ImportedAccountSeed` incluye `EvidenceRef` con:

- `epistemic_state = UNCONFIRMED`
- `confidence = C`
- raíz de proveniencia `excel-workbook:<sha256>` y fila original.

La semilla puede alimentar el componente de enriquecimiento oficial en una
operación posterior y autorizada. No lo activa automáticamente ni convierte
los valores de Excel en contexto M05, hechos, permiso de contacto o identidad
de persona.

## No-claims

No existe escritura a Excel, autenticación de operador, cifrado del archivo,
OCR, soporte `.xls`/`.xlsm`, CRM, crawling automático, persistencia, delivery,
consentimiento ni aceptación de gate global. La lectura es local, acotada y
shadow-only.


