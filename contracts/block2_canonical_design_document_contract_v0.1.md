# Block 2 — Canonical Design Document Contract v0.1

> Estado: `CANDIDATE / BOUNDED IMPLEMENTED / LOCAL EXECUTED / MAR REQUIRED`

## Productor, consumidores y autoridad

E06 produce versiones CDD; Studio propone cambios; E07/Inspector/Export leen.
El CDD posee representación editable y lineage, no claims, rights, provider
authority, publicación o aceptación.

## Forma mínima

`DesignDocumentVersion` incluye document/project/version/parent IDs, profile,
blueprint/direction refs, pages, elements, assets, decisions, validations,
actor/time, content hash y state. Cada `DesignElement` contiene stable semantic
ID, type, parent/page/z-index, geometry, content, token/asset refs,
claim/evidence/limitation refs, accessibility, lineage, editability y rights.

## Invariantes y versiones

- IDs son únicos y el hash cubre forma canónica completa.
- Editar crea nueva versión; parent histórico es inmutable.
- Claims/evidence/rights sólo se referencian; no se mutan desde CDD.
- Asset refs son hashes allowlisted; no path, script, credential o remote URL.
- Un diff reporta geometría, contenido, estilo, asset, semántica, rights y a11y.
- Desconocer compatibilidad, lineage o currentness bloquea el consumo.

## No-claims

Conformidad CDD no prueba render, accesibilidad real, derechos, publicación,
calidad creativa, colaboración o aceptación.

## Estado ejecutable acotado

`canonical_document.py` implementa la forma mínima local, hash canónico,
versionado padre-hijo y adapter desde un run E01–E08 completado. Rechaza URLs,
scripts, paths ascendentes, assets sin SHA-256, reading order incompleto,
identidades duplicadas y parents inválidos. Esta ejecución local no acepta el
contrato compartido ni promueve el Master Architecture Review.
