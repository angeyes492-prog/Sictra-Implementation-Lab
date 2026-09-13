# Tasks

## Active

## Waiting On

- [ ] **Revisión final del PR #15** - para reviewer designado, desde 2026-09-13.
  - Validar el SHA que GitHub muestre como Head actual del PR y la CI exitosa de ese mismo SHA; no reutilizar una aprobación de un commit anterior.
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

- [x] ~~Cierre técnico estricto de Telecare OS~~ (2026-09-13)
  - Fuente de verdad consolidada, alcance congelado y lista única de cierre incorporada al PR #15.
  - SHA `b86898e33d47b79da8306aafcc85d7b365537d1c`; CI `34783166005` aprobada.
  - Límite conservado: `LABORATORY_INTERNAL_SUPERVISED`; sin publicación, contacto, CRM, entrega ni promoción automática.

- [x] ~~Cierre técnico integrado de Bloques 1–4~~ (2026-09-13)
  - Dossier durable → E01–E08 → M01–M07 → Orchestrator → revisión humana.
  - 732 pruebas Python, 4 pruebas JavaScript y CI final aprobada.
- [x] ~~Recuperación local supervisada~~ (2026-09-13)
  - Cola hash-bound, pausa, stop ante crash, recibos de recuperación y backups firmados.
