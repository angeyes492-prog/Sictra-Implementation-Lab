# Dossier — Block 3 Account Research Orchestration v0.1

| Estado | Valor |
|---|---|
| Designed | `YES` |
| Bound | `LOCAL` |
| Implemented | `YES` |
| Executed | `YES / LOCAL` |
| Validated | `LOCAL + adversarial + formal complement` |
| Integrated | `NO` |
| Accepted | `NO` |

## Jurisdicción

Posee el binding y orden del flujo Excel → aprobación → web oficial → memoria
→ recibo. No posee la identidad real del revisor, consentimiento, facts, M05,
CRM ni delivery.

## Invariantes

1. Una fila Excel no dispara red sin aprobación vigente y coincidente.
2. Una aprobación no puede reusarse para otra cuenta, tenant, URL, fila o lote.
3. El dossier se persiste antes del recibo; un recibo no sustituye evidencia.
4. Repetición exacta es idempotente; colisión o alteración falla cerrada.
5. Toda salida sigue siendo shadow-only y no posee efecto de contacto.
