# Block 2 / E08 — Creative Memory & Learning Contract v0.1

> Estado: `CANDIDATE / LOCAL IMPLEMENTATION AUTHORIZED / NOT ACCEPTED`

## Propósito y autoridad

E08 conserva patrones y fallos como registros versionados, append-only y con
lineage. Sólo recibe un E07 recomendado y una validación externa actual,
atribuible y fuera del motor. No reentrena, cambia E03/E07, promueve reglas ni
alimenta la misma generación.

## Invariantes ejecutables

1. Observación, interpretación e hipótesis son campos separados.
2. Un registro requiere evidencia independiente, owner de promoción, vigencia,
   privacidad/rights permitidos y generación futura explícita.
3. La misma identidad+contenido es idempotente; misma identidad+contenido
   materialmente distinto es colisión y se rechaza.
4. Deprecación conserva historia y motivo; no borra ni reescribe el registro.
5. Preferencia, correlación o repetición no se convierten automáticamente en
   principio causal.

Resultados: `MEMORY_CANDIDATE_READY`, `RETURN_TO_EVALUATION`,
`RETURN_UPSTREAM`, `QUARANTINE_MEMORY`, `IDENTITY_COLLISION` o
`UNSUPPORTED_VERSION`. Ninguno equivale a aprendizaje aceptado o gate global.

