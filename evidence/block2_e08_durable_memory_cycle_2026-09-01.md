# Block 2 / E08 — ciclo de memoria durable local (2026-09-01)

## Alcance y estado

- Estado de implementación: `IMPLEMENTED / EXECUTED LOCAL`.
- Estado de validación independiente y aceptación: `NOT VALIDATED / NOT ACCEPTED`.
- Certeza: `VERIFIED`; confianza `A` para los resultados locales enumerados.
- Límite de promoción: ninguna prueba de este ciclo cambia un gate global,
  habilita proveedores reales ni convierte una memoria candidata en aprendizaje
  aceptado.

## Cambio comprobado

`ProjectGraphCreativeMemoryStore` persiste el candidato E08 en las tablas
`creative_memory_records` y `creative_memory_events`, junto a un nodo
`CREATIVE_MEMORY_CANDIDATE` y su lineage. El adaptador comparte la transacción
del `ProjectGraph`: una excepción posterior revierte la memoria y el lineage.
El hash del candidato ahora cubre todos los campos materiales de gobierno; al
leer se verifican el payload, la identidad y cada evento de deprecación.

## Ejecución

| Fuente | Comando o vector | Resultado | Alcance |
|---|---|---|---|
| Git local | `python -m unittest tests.test_block2_creative_memory_durability -v` | 8/8 PASS | reinicio, eventos, colisión, rollback, tamper y concurrencia |
| Git local | `python -m unittest discover -s tests -p 'test_block2*.py' -v` | 169/169 PASS | regresión Bloque 2 |
| Git local | `python -m unittest discover -s tests` | 457/457 PASS | regresión workspace |
| Git local | `python -m compileall -q src tests` | PASS | compilación |
| Git local | `python -m sictra_block2_design` | PASS; publicación y aceptación siguen `NOT_*` | smoke E01–E08 |
| GitHub Actions | run `33575896009` sobre `a19b4df7cb023b47f5c9b39ba2aa12077bae3315` | `success` | regresión + compilación + smoke CI del SHA descendiente del cambio E08 |

El resultado hosted está ligado al SHA indicado. Un cambio posterior requiere
otra ejecución exacta; este resultado no se hereda por similitud de código.

## Red-team y límites

Los vectores alteran directamente el payload durable y el evento de
deprecación; ambos producen `E08ContractViolation`, por lo que no se tolera
una restauración silenciosa. La prueba concurrente exige exactamente un efecto
durable y una respuesta idempotente para el otro escritor. Esto no cubre una
revisión humana, un almacenamiento remoto, una política de retención aprobada
ni consumidores externos; dichos puntos permanecen `RETURN_UPSTREAM` cuando
se requieran para aceptación.

## Siguiente ataque

Ligar el commit a CI hosted del SHA exacto. En paralelo se abrió una auditoría
separada de render HTML/SVG en navegador; las dependencias globales
independientes siguen siendo MAR, provider real gobernado, revisión asistiva
humana y aceptación humana.
