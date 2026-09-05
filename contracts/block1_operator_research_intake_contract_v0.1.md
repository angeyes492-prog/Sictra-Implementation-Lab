# Contrato — Operator Research Intake v0.1

## Identidad

- Productor: `sictra_block1.research_intake` y `sictra_block1.lab_web`.
- Consumidor: navegador local en la misma computadora.
- Scope: `BLOCK1_LOCAL_OPERATOR_RESEARCH_INTAKE`.
- Autoridad: declaración de pregunta; ninguna autoridad de evidencia, runtime,
  fuente, arquitectura o gate.
- Compatibilidad: contrato `0.1`; campos desconocidos se rechazan.

## Request y respuesta

`POST /api/investigations` requiere `application/json`, máximo 4096 bytes y
exactamente estos campos:

```json
{
  "title": "texto de 3 a 160 caracteres",
  "question": "texto de 12 a 600 caracteres",
  "level": "GLOBAL | REGIONAL | LOCAL",
  "geography": "texto",
  "industry": "tema controlado de INDUSTRIES",
  "actor": "texto",
  "mode": "texto",
  "period": "texto",
  "topic_keys": ["uno a cinco temas controlados y distintos"],
  "source_reference": "texto opcional de hasta 500 caracteres"
}
```

El resultado `201` contiene `OPERATOR_RESEARCH_DRAFT` con identidad local,
fecha, scope, watchlist y los invariantes `DRAFT`, `INSUFFICIENT EVIDENCE`,
`E`, `sources=[]`, `claims=[]`, `strategies=[]`. Una referencia no vacía se
representa exclusivamente como `USER_DECLARED_UNBOUND_REFERENCE` y
`NOT_FETCHED_NOT_EVIDENCE`.

## Persistencia, errores y no-claims

El productor persiste hasta 100 registros en JSON local mediante reemplazo
atómico; todo registro se revalida en lectura. Error de JSON, tipo, tamaño,
campo, vocabulario, identidad o integridad devuelve `400` para request inválido
o bloquea la lectura local sin inventar un estado positivo. Ruta desconocida o
query string no contratada devuelve `404`; métodos no permitidos devuelven
`405`.

No hay fetch de la referencia, internet, evidencia admitida, source binding,
claims, scoring, insights, publicación, secretos, identidad, multiusuario,
cifrado, garantía de backup ni promoción de gate.
