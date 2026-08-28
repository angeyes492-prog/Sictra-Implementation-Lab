# Bloque 1 Intelligence — Infraestructura de producto v0.1

## Estado, versión y decisión

`IMPLEMENTED CANDIDATE / PLAUSIBLE / C`, versión `0.1`.

Esta arquitectura implementa una superficie independiente para pruebas de campo
del flujo de investigación logística con fixtures sintéticos. No cambia el gate
`BOUNDED OPERATIONAL`, no reclama producción y no autoriza ingesta real.

## Propósito y alcance

Permitir que una persona no técnica explore investigaciones globales,
regionales y locales; inspeccione fuentes, claims, contradicciones e insights;
compare estrategias; consulte watchlists; y ejecute vectores adversariales del
runtime desde una herramienta diaria coherente.

## Topología implementada

```text
Navegador local
  └─ Intelligence Workspace (HTML/CSS/JS sin dependencias externas)
      └─ adapter HTTP 127.0.0.1 / API de solo lectura
          ├─ catálogo defensivo de investigaciones sintéticas
          ├─ comparador Pareto de estrategias observadas
          └─ Validation Deck
              └─ runtime operacional existente E01 → E08 + SQLite efímero
```

El adapter sirve únicamente una allowlist de tres assets. No expone rutas del
sistema de archivos, no acepta uploads, credenciales, consultas arbitrarias ni
URLs. El catálogo entrega copias defensivas para impedir mutación compartida.
El límite HTTP valida `Host`, `Origin` y Fetch Metadata para contener DNS
rebinding y activación cross-site del servicio local.

## Componentes y propiedad semántica

| Componente | Propiedad | No posee |
| --- | --- | --- |
| Scope Lens | Filtro visual global/regional/local | Fusión o inferencia de scopes |
| Research Desk | Lectura de expedientes acotados | Captura de datos reales |
| Evidence Spine | Trazabilidad fuente→claim→red team→disposición | Declaración de verdad |
| Strategy Lab | Comparación Pareto explicable | Ranking universal o autorización |
| Watchlists | Observables 7/30/90 | Predicción automática |
| Validation Deck | Ejecución de cuatro fixtures del runtime | Evidencia de producción |
| HTTP adapter | Entrega local y rutas allowlisted | Identidad, auth o acceso remoto |

## Inputs, outputs e invariantes

Inputs implementados: selección de vista, escala, investigación, par de
estrategias y vector de validación. Outputs: snapshots JSON, expediente visual,
comparación multiobjetivo y reporte técnico del fixture.

Invariantes:

- `FIXTURE != REAL SOURCE`; toda respuesta declara `SYNTHETIC_FIELD_TEST`.
- Una fuente correlacionada no crea una raíz independiente adicional.
- Estrategias de preguntas o scopes diferentes producen `SCOPE_MISMATCH`.
- No existe score agregado. Solo dominancia, trade-off o evidencia insuficiente.
- Red team distinto de `PASS` o estabilidad distinta de `STABLE` impiden
  preferencia.
- `DELIVERABLE_BOUNDED != FACT != GLOBAL ACCEPTANCE`.
- El navegador no recibe autoridad de runtime ni acceso al store.

## Comparador formal

Maximiza cobertura, raíces independientes, frescura, reducción de
incertidumbre y contradicciones resueltas. Minimiza contradicciones abiertas,
duración y costo observado. Una estrategia domina únicamente si no empeora
ninguna métrica y mejora al menos una. Ventajas cruzadas producen
`INCOMPARABLE`.

Wolfram evaluó el modelo el 2026-08-27: dominancia A>B verdadera, trade-off A/C
incomparable, máquina de estados acíclica, sin retorno de
`DELIVERABLE_BOUNDED` a `DRAFT`, sin autopromoción desde `QUARANTINED` y sin
atajo `DRAFT→DELIVERABLE_BOUNDED`. El resultado formal complementa, pero no
sustituye, las pruebas Python.

## Autoridad, dependencia y seguridad

La API de workspace es una proyección de lectura sin autoridad. La única ruta
que ejecuta el runtime conserva el flujo protegido existente y usa store
efímero. CSP bloquea scripts, estilos y conexiones externas; el proceso solo
puede enlazarse a `127.0.0.1`. GitHub continúa como fuente técnica canónica;
Notion registra plan; Slack conserva memoria contextual.

## Fallos, recuperación y observabilidad

Rutas, investigaciones y estrategias desconocidas fallan de forma explícita.
Un error del workspace no se interpreta como bloqueo correcto. Refrescar la
página reconstruye el snapshot desde fixtures inmutables; no hay estado de
usuario que recuperar en v0.1. `/health` declara scope y clase de fixture.

## Evolución de infraestructura

1. **v0.1 — actual:** producto local, dataset sintético, comparación y pruebas.
2. **v0.2 — siguiente gate:** importación manual de source bundles con schema,
   cuarentena y atestación; todavía sin navegación autónoma.
3. **v0.3 — conectores gobernados:** gateway de fuentes con allowlist,
   presupuesto, rate limits, caché, robots/licencia, auditoría y kill switch.
4. **v1 — producción:** identidad y roles, tenancy, secret manager, workers,
   almacenamiento durable, observabilidad, backup/restore, despliegue firmado,
   SLO y revisión de seguridad/privacidad.

Cada fase exige contrato, threat model, pruebas negativas, CI en SHA exacto y
revisión independiente. No se habilita por continuidad de interfaz.

## Validación y downstream

Se requieren pruebas unitarias del comparador, contrato de API, integración
HTTP, mutaciones de métricas, correlación de fuentes, scopes incompatibles,
allowlist estática, regresión E01–E08, revisión visual responsive y revisión
independiente. El futuro Bloque 2 puede consumir un handoff visual tipado, pero
esta UI no le concede propiedad de investigación. Bloques 3 y 4 permanecen
fuera de alcance.

## Contradicciones y límites abiertos

- “Producto final” describe la calidad y coherencia de la superficie, mientras
  el runtime sigue siendo un producto de campo local, no producción.
- La fuente real, autenticación y persistencia de investigaciones aún tienen
  `INSUFFICIENT EVIDENCE`; implementarlas ahora violaría el diseño aprobado.
- Revisión humana independiente, CI del SHA final y decisión de merge siguen
  pendientes.
