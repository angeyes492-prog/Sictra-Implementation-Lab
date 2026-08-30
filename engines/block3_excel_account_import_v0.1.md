# Dossier — Block 3 Excel Account Import v0.1

| Estado | Valor |
|---|---|
| Designed | `YES` |
| Bound | `LOCAL` |
| Implemented | `YES` |
| Executed | `YES / LOCAL` |
| Validated | `LOCAL + adversarial + formal complement` |
| Integrated | `NO` |
| Accepted | `NO` |

## Propósito y autoridad

Transformar una tabla Excel explícita en semillas de cuenta con proveniencia
para el Account Knowledge Fabric. El motor posee el parseo y rechazo del
archivo; no posee tenant, propósito, crawling, memoria durable, hechos,
relevancia, persona, CRM ni delivery.

## Riesgos y defensas

| Riesgo | Defensa |
|---|---|
| tenant o propósito inyectado en archivo | ambos se ligan fuera del workbook |
| fórmula/caché engañosa | toda fórmula de columna admitida se rechaza |
| macro, entity expansion o ZIP bomb | rechazo antes de leer la hoja |
| columna escondida con datos | `UNMAPPED_COLUMN_VALUE` visible |
| fila reordenada/omitida | se conserva número físico de Excel |
| declaración tomada como hecho | evidencia `UNCONFIRMED`, restricción explícita |

## Integración prevista

`ExcelAccountSeedImporter` → revisión humana o scheduler autorizado →
`AccountKnowledgeEngine.enrich`. La flecha es propuesta de integración, no una
ejecución automática ni autoridad de crawl.


