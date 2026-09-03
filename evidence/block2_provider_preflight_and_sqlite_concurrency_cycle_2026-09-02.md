# Block 2 — provider preflight y concurrencia SQLite (2026-09-02)

## Estado y límite de promoción

- Implementación: `IMPLEMENTED / EXECUTED LOCAL`.
- Validación independiente, integración remota y aceptación: `NOT VALIDATED / NOT INTEGRATED / NOT ACCEPTED`.
- Certeza: `VERIFIED`; confianza `A` para los comandos locales de esta tabla.
- Límite: el preflight no resuelve secretos, no usa red y no autoriza un
  provider. La reparación SQLite sólo estabiliza el estado local durable; no
  satisface MAR, provider real, revisión asistiva ni aceptación humana.

## Closure delta

### Preflight de provider candidato

`ProviderTrialReadinessRecord` formaliza el paquete declarativo mínimo de un
trial futuro: lane, snapshot, handle no secreto, estado de credencial, términos,
política de datos, derechos, presupuesto, autoridad y referencia MAR. Las lanes
`GENERATIVE_MEDIA` y `DESIGN_PLATFORM` exigen scopes distintos. Una declaración
completa produce únicamente `PRECONDITIONS_DECLARED`, con
`execution_authorized=false` y `NOT_ACCEPTED`. Credenciales no disponibles,
expiración o scopes incompletos devuelven `RETURN_UPSTREAM`; material que parece
una API key se rechaza antes de evaluar.

El contrato está en
`contracts/block2_provider_trial_preflight_contract_v0.1.md`. No existe adapter
remoto ni se ha conectado esta capacidad al runtime determinista.

### Carrera de escritura E08

La regresión monolítica reveló una espera no acotada en
`test_concurrent_exact_writers_converge_without_duplicate_memory`: dos
conexiones SQLite podían competir al inicializar un archivo nuevo antes de
alcanzar la barrera de la prueba. `ProjectGraphStore` ahora inicia transacciones
de escritura con `IMMEDIATE` y reintenta de forma acotada la transición WAL /
creación de esquema cuando SQLite informa contención transitoria. La barrera de
regresión tiene un timeout para convertir una futura falla de inicialización en
un error diagnosticable, no en un CI indefinido.

La semántica probada sigue siendo la misma: dos escritores exactos producen un
único registro durable y las acciones `{STORED, IDEMPOTENT}`.

## Ejecución local

| Vector | Resultado | Alcance |
|---|---:|---|
| `python -m unittest tests.test_block2_provider_trial_preflight -v` | 4/4 PASS | declaración completa no operativa, expiry/credencial, scope por lane, rechazo de secreto |
| `python -m unittest tests.test_block2_creative_memory_durability -v` | 8/8 PASS | reinicio, append-only, tamper, rollback y dos escritores concurrentes |
| `python -m unittest discover -s tests -q` | 466/466 PASS en 30.726 s | regresión workspace en un único proceso |
| `python -m compileall -q src tests` | PASS | sintaxis de fuentes y pruebas |
| GitHub Actions `33700400122` | `success` sobre `0a48487eaeee04cdc797e88dd8a16d6cee830296` | regresión, compilación, validación JavaScript y runtimes de referencia |

El run hosted está ligado al SHA de implementación indicado. El commit de
evidencia posterior no altera código de runtime; aun así, la PR requiere una
ejecución propia antes de declarar su head verificado.

## Red-team, fuentes y riesgos

- El vector de secreto usa un prefijo `sk-`; la API no acepta el valor en el
  registro. Esto no valida un vault real ni detecta todas las formas posibles
  de secreto: el boundary de provider deberá hacer verificación independiente.
- La concurrencia se probó con dos conexiones locales y SQLite/WAL. No demuestra
  seguridad distribuida, lock manager externo ni rendimiento bajo carga.
- La consulta de Slack y Notion del 2026-09-02 no aportó una promoción MAR ni
  aceptación de Bloque 2; GitHub PR #11 no tenía review humano. Esas fuentes
  quedan `INSUFFICIENT EVIDENCE` para aceptación. El intento de análisis formal
  de Wolfram falló internamente, por lo que tampoco se cuenta como evidencia.

## Siguiente ataque

Ejecutar CI hosted para el SHA exacto de este cambio. Si resulta verde, conservar
la evidencia como runtime local/hosted; mantener `RETURN_UPSTREAM` para el
adapter remoto con credenciales, términos y derechos verificables, MAR y el
resto de gates humanos.
