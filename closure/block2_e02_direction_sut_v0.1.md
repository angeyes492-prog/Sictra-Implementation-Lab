# Block 2 / E02 — DirectionSet local bounded SUT ledger v0.1

| Gate / dimensión | Estado | Evidencia | Límite |
|---|---|---|---|
| Contrato E02 | `CANDIDATE` | `contracts/block2_e02_creative_direction_contract_v0.1.md` | no aceptado como contrato común. |
| SUT de preservación/diversidad | `IMPLEMENTED / LOCAL` | `src/sictra_block2_design/e02_direction.py` | clasifica propuestas sintéticas; no genera ni elige. |
| Oráculo diferencial | `EXECUTED / LOCAL` | `src/sictra_block2_design/e02_direction_oracle.py`, 20 pruebas | mismo autor/local; no revisión independiente. |
| Regresión workspace | `PASS / LOCAL` | 193 pruebas | no equivale a CI externa ni integración. |
| E02 end-to-end | `INSUFFICIENT EVIDENCE` | ninguno | no hay E01→E02 binding ni input autorizado. |
| E02 aceptación | `NO` | ninguno | requiere revisión arquitectónica, evidencia e integración. |

## Invariantes demostrados sólo en el SUT local

- variación cosmética o con un eje material no alcanza ready-for-selection;
- claim, certainty, contradicción, non-claim e incertidumbre no pueden mutar;
- E02 no selecciona ganador;
- referencias no permitidas/cuarentenadas no pasan;
- `RETURN_UPSTREAM` precede evaluación creativa.

## Próxima reevaluación

Antes de construir un adapter E01→E02 o probar un caso real: reconciliar la
autoridad de PR/main/workspace, aceptar/revisar contratos candidatos y obtener
un objeto upstream actual, autorizado y con procedencia completa.

