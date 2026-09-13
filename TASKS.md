# Tasks

## Active

- [ ] **Cierre técnico estricto de Telecare OS** - Codex mantiene como fuente de verdad el manifiesto de cierre y no abre alcance nuevo. Sólo implementa decisiones aprobadas del MAR o acciones de despliegue autorizadas.
  - Criterio de salida: cada cambio tiene prueba adversarial, regresión, SHA y CI exacta; el cambio se incorpora al manifiesto o se devuelve a revisión.
  - Límite: `LABORATORY_INTERNAL_SUPERVISED`; no publicación, contacto, CRM, entrega ni promoción automática.

## Waiting On

- [ ] **Revisión final del PR #15** - para reviewer designado, desde 2026-09-13.
  - Validar el SHA final `3fc2917cdb94f2f0c8d8a2b7e4b9dfb5423ae103` y CI `34782410675` aprobada.
  - Cierre: aprobación explícita o comentarios accionables sobre el PR.

- [ ] **Master Architecture Review** - para autoridad arquitectónica, desde 2026-09-13.
  - Decidir: activación de adaptadores, custodia de llaves, retención, kill-switch, identidad de despliegue, ancla externa contra rollback y el mapeo dossier → precisión.
  - Cierre: decisiones registradas como aceptar, revisar o rechazar, con alcance y responsable.

- [ ] **Aprobación de fuentes y piloto operativo** - para owner de datos/negocio, desde 2026-09-13.
  - Aprobar las fuentes reales y las rutas de ingreso; definir los datos de cuenta/persona permitidos para precisión.
  - Cierre: fuente/binding aprobados, política de datos vigente y entrada de piloto suministrada.

- [ ] **Promoción de producción** - para owner autorizado, después del piloto y del MAR.
  - Requiere controles externos de secretos/identidad/rollback, resultados de piloto y aprobación humana formal.
  - Cierre: decisión explícita de promover o mantener el sistema en laboratorio supervisado.

## Someday

- [ ] **M08 con resultados observados** - sólo después de una entrega autorizada, consentimiento aplicable y recibo de entrega real.

## Done

- [x] ~~Cierre técnico integrado de Bloques 1–4~~ (2026-09-13)
  - Dossier durable → E01–E08 → M01–M07 → Orchestrator → revisión humana.
  - 732 pruebas Python, 4 pruebas JavaScript y CI final aprobada.
- [x] ~~Recuperación local supervisada~~ (2026-09-13)
  - Cola hash-bound, pausa, stop ante crash, recibos de recuperación y backups firmados.
