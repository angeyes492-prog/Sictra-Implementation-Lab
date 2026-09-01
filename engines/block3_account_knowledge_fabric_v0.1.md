# Dossier — Account Knowledge Fabric v0.1

| Estado | Valor |
|---|---|
| Designed | `YES` |
| Bound | `LOCAL` |
| Implemented | `YES` |
| Executed | `YES / LOCAL` |
| Validated | `LOCAL + adversarial + formal complement` |
| Integrated | `NO` |
| Accepted | `NO` |

## Propósito

Convertir un dominio oficial autorizado en contexto de cuenta revisable y
durable. La unidad no es un motor M01–M08 adicional: es infraestructura común
de memoria/evidencia para alimentar, de manera limitada, M05.

## Riesgos prioritarios

SSRF, crawl fuera de alcance, inyección desde web, mezcla de tenants, facts
fabricados, cadena durable alterada, memoria vencida reutilizada y confundir un
dossier con permiso de contacto.

## Límites de promoción

Pruebas locales sólo prueban el SUT acotado. Antes de G3 se requieren
importador Excel, prueba shadow con dominios autorizados, políticas de
retención/cifrado y revisión independiente.
