# Contrato ejecutable — Block 1 Source Portfolio v0.1

**Versión:** `0.1.0`
**Productor:** catálogo de candidatos de E02.
**Consumidores:** Strategy Lab, revisión humana y futuro Source Gateway.
**Scope:** `intelligence`.
**Autoridad:** planificación; ninguna de adquisición o gate.

## Perfil de candidato

`SourceCandidate` contiene identidad, editor, hosts candidatos, regiones,
dominios, cadencia y estado.

- El ID es único y no vacío.
- Los hosts son DNS normalizados; IP, localhost, puertos, credenciales y rutas
  se rechazan.
- Regiones y dominios son conjuntos canónicos y no vacíos.
- La cadencia es `ANNUAL`, `QUARTERLY`, `MONTHLY` o `EVENT_DRIVEN`.
- En v0.1 el estado debe ser `PROPOSED`; los estados operativos pertenecen al
  Source Gateway y no pueden declararse aquí.

## Consulta y límites

Un `SourcePortfolio` acepta como máximo 50 perfiles. IDs y hosts son únicos.
`summary()` expone conteos y bloqueos de promoción, no calidad ni verdad.
`candidates_for(regions, domains)` rechaza valores desconocidos, devuelve sólo
perfiles propuestos compatibles y puede sumar candidatos `GLOBAL` a una región.
Nunca crea una `SourceRegistration`, atestación ni petición de red.

La CLI local `--source-readiness` requiere una región no global y un dominio.
Devuelve el snapshot de portfolio, candidatos `PROPOSED`,
`admissible_source_count=0` y
`RESEARCH_BLOCKED_PENDING_SOURCE_BINDING`; no acepta URL, contenido,
credenciales, archivos ni configuración de fuente.

La compatibilidad se limita a v0.1. Habilitar una fuente exige versión nueva,
evidencia de aprobación humana y revisión de arquitectura.
