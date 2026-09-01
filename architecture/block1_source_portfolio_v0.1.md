# Block 1 — Source Portfolio gobernado v0.1

**Clasificación:** cambio metodológico incremental, local a E02.
**Estado:** `IMPLEMENTED CANDIDATE / LOCAL-TESTED` tras ejecutar su suite.
**Propietario semántico:** E02 Knowledge Acquisition.

## Propósito y alcance

El Portfolio es un catálogo finito de candidatos de investigación logística.
Separa el descubrimiento de una fuente de su habilitación para ingresar
evidencia. Permite planear cobertura internacional sin que un nombre, dominio o
recomendación se conviertan automáticamente en una fuente `BOUND`.

La v0.1 contiene doce candidatos. No hace red, no verifica licencias ni
contenido, no descarga datos y no los entrega al runtime.

## Invariantes y autoridad

- Acepta como máximo 50 perfiles propuestos.
- `PROPOSED` es el único estado permitido en este catálogo.
- Un ID y un host candidato pertenecen a un único perfil.
- La selección regional puede incluir fuentes `GLOBAL`, pero nunca las presenta
  como evidencia ni como cobertura regional observada.
- Este componente no modifica `SourceGateway` ni crea `SourceRegistration`.

La superficie local `python -m sictra_block1 --source-readiness --region
AMERICAS --domain TRADE` muestra candidatos, capacidad, bloqueos y cero fuentes
admisibles. Es una vista de planificación JSON; no abre una conexión de red.

Para llegar a `BOUND`, una revisión humana debe aportar evidencia independiente
de términos o licencia, método de acceso, host allowlist, claims, límite de
contenido, responsable y fecha. Ese evento requiere un contrato posterior.

## Dependencias, fallos y validación

Depende de `ContractViolation` y comparte el límite de 50 del Source Gateway.
No depende de red. Perfiles malformados, dominios locales o IP, cobertura o
dominios vacíos, estados no propuestos, IDs u hosts duplicados fallan cerrados.
La suite cubre catálogo inicial, límite 50/51, duplicación, host inseguro,
selección regional/dominio, copia defensiva y ausencia de fuentes habilitadas.
No prueba disponibilidad, derechos de uso, actualidad, calidad ni gate global.
