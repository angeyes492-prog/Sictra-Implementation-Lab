# Cierre acotado — Block 3 Excel Account Import v0.1

| Campo | Estado |
|---|---|
| Gate | `YELLOW` |
| Capability | `IMPLEMENTED / EXECUTED / LOCAL BOUNDED SUT` |
| Local execution | `10/10 PASS`; regresión `241/241 PASS` |
| Formal | frontera de tenant, fórmula, URL y estado epistémico modelada |
| Integration | `NO`; sólo emite semillas revisables |
| CRM / persistence / crawl | `NOT EXECUTED` |
| Independent review | `PENDING` |
| Global acceptance | `NO` |

## Closure delta

- lector `.xlsx` sin escritura, sin macros y con presupuesto de archivo, ZIP,
  descompresión, filas, columnas y celdas;
- schema `Accounts` limitado a `account_id`, `official_url`, `company_name` y
  `source_reference`, con aliases español/inglés;
- tenant y propósito ligados fuera del workbook;
- evidencia por fila con hash del workbook, proveniencia y estado
  `UNCONFIRMED`, sin promoción a fact;
- rechazos explicables para fórmulas, URL no HTTPS/query/fragment, macro,
  entity declaration, ZIP bomb, columnas no mapeadas, duplicados y filename
  inseguro;
- preservación del número físico de fila de Excel y cero efectos posteriores.

## Límites y siguiente gate

No existe aún workbook de producción aprobado, autenticación de operador,
cifrado del archivo, `.xls`/OCR, persistencia de lote, scheduler, crawling
automático, CRM ni shadow run con datos reales. El siguiente gate requiere CI
hospedada en SHA exacto, revisión independiente y una prueba shadow con una
plantilla aprobada y datos sintéticos o explícitamente autorizados.


