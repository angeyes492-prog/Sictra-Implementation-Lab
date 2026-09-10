# Bloque 1 Intelligence — Operator Research Intake v0.1

## Estado y propósito

`IMPLEMENTED CANDIDATE / PROBABLE / C`, versión `0.1`.

La entrada local permite que un operador formule y conserve una pregunta de
investigación logística dentro del Intelligence Workspace. Resuelve el vacío
entre explorar fixtures y preparar un expediente de campo, sin convertir una
petición humana o una referencia declarada en observación, evidencia o insight.

## Alcance y topología

```text
Operador local
  └─ formulario Research Desk
      └─ POST /api/investigations (JSON acotado)
          └─ ResearchIntakeStore (reemplazo atómico local)
              └─ OPERATOR_RESEARCH_DRAFT / DRAFT / INSUFFICIENT EVIDENCE / E
                  └─ snapshot defensivo del Workspace
```

La ruta está limitada al servidor local `127.0.0.1` ya existente. El archivo
por defecto es `.sictra-intelligence/research-intake.json` bajo el directorio
desde el que se inicia el Workspace y está excluido de Git. `--intake-store`
permite elegir otra ruta local. No existe endpoint de red, subida de archivo,
lectura de URL, credencial, scraper, scheduler ni efecto sobre el runtime.

## Inputs, outputs e invariantes

El input exacto requiere título, pregunta, escala `GLOBAL|REGIONAL|LOCAL`,
geografía, industria controlada, actor, modalidad, período, uno a cinco temas
controlados y una referencia opcional. Se limitan tipos, campos, longitud,
temas duplicados e industria desconocida. Un borrador resultante siempre tiene:

- `status=DRAFT`, `certainty=INSUFFICIENT EVIDENCE`, `confidence=E`;
- cero fuentes, claims, estrategias y raíces independientes;
- una referencia opcional con estado `NOT_FETCHED_NOT_EVIDENCE`;
- insight explícitamente ausente y watchlist de adquisición/revalidación.

Los borradores aparecen en Panorama, Investigaciones, Evidencia y Watchlists,
pero no pueden entrar a Strategy Lab porque no poseen observaciones comparables.
No se permite que una referencia declarada se proyecte como source packet.

## Autoridad, recuperación y observabilidad

El operador tiene autoridad únicamente para declarar una pregunta local. No
posee autoridad para aprobar fuentes, emitir bindings, afirmar claims, producir
una recomendación o promover un gate. El store usa un lock de proceso,
validación completa al abrir, máximo de 100 borradores y reemplazo atómico;
archivo malformado, identidad duplicada o registro alterado fallan cerrados.

La recuperación consiste en reabrir un store válido. No se promete concurrencia
entre procesos, autenticación, control de acceso, cifrado, backup ni migración
interversiones. Es un límite conocido de pruebas de campo locales, no un diseño
de producción.

## Validación y downstream

La validación cubre creación, persistencia tras reinicio, copia defensiva,
restricciones de schema/vocabulario, detección de alteración, límites HTTP y
no-ingreso de evidencia. La siguiente dependencia es el Source Gateway: una
fuente sigue requiriendo registro, revisión, binding y bundle manual antes de
que cualquier draft pueda evolucionar. Este componente no cambia el gate global
ni sustituye revisión humana independiente.
