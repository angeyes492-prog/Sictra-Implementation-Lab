# Block 2 / E08 — Creative Memory & Learning Contract v0.1

> Estado: `CANDIDATE / LOCAL DURABLE IMPLEMENTATION EXECUTED / NOT ACCEPTED`

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
6. La memoria local se persiste en el mismo `ProjectGraph` transaccional que
   su ejecución: registro inmutable, nodo `CREATIVE_MEMORY_CANDIDATE` y eventos
   append-only de deprecación. Una falla posterior en la traza revierte el
   registro, su nodo y sus eventos junto con el resto de la transacción.
7. El hash de contenido cubre identidad, contrato, fuentes, observación,
   interpretación, hipótesis, evidencia, owner, rights, privacidad y vigencia.
   Al recargar, el adaptador verifica ese hash y la integridad de cada evento;
   un payload o evento alterado se pone en cuarentena y no puede reaparecer como
   memoria válida.

## Límite de promoción

La persistencia SQLite demuestra continuidad local y detección de manipulación,
no aprendizaje aceptado, generalización causal ni validación independiente.
El adaptador participa en una transacción propiedad de la traza; no abre por sí
solo un límite de commit ni autoriza una promoción.

Resultados: `MEMORY_CANDIDATE_READY`, `RETURN_TO_EVALUATION`,
`RETURN_UPSTREAM`, `QUARANTINE_MEMORY`, `IDENTITY_COLLISION` o
`UNSUPPORTED_VERSION`. Ninguno equivale a aprendizaje aceptado o gate global.
