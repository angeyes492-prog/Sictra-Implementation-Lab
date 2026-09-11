# Block 2 — Engine Registry Contract v0.1

> Estado: `CANDIDATE / LOCAL EXECUTED / MAR REQUIRED`

## Propósito y alcance

Engine Registry fija la identidad técnica del plano E01–E08: versión de
manifiesto y contrato, implementación importable, dependencia inmediata,
semántica propia, límite de autoridad y estado habilitado. No activa versiones
automáticamente, no acepta resultados y no sustituye SHA, CI ni revisión.

## Invariantes

- Contiene exactamente E01–E08, en orden canónico y sin duplicados.
- E01 no depende de otro motor; cada E02–E08 depende sólo del anterior.
- Toda versión satisface la compatibilidad local `0.1.x`.
- Cada implementación usa identidad `module:callable` y debe poder importarse.
- Cualquier cambio material altera el hash canónico del Registry.
- Un hash distinto al fijado en checkpoint bloquea Resume.

## Fallo, recuperación y evidencia

Manifest desconocido, deshabilitado, mal ordenado, con dependencia divergente o
binding ausente falla cerrado antes de ejecutar. La reparación exige un nuevo
Registry explícito y nuevo checkpoint; nunca se reescribe evidencia previa.
Importabilidad prueba binding local, no corrección, integración ni aceptación.
