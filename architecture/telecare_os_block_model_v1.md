# Telecare OS — Modelo de Bloques v1.0

## Decisión

**Telecare OS** es el sistema paraguas. SICTrA / Intelligence es su primer
bloque de capacidad, no el nombre del sistema completo.

## Bloques

| Bloque | Nombre | Responsabilidad declarada |
|---|---|---|
| 1 | Intelligence | Adquisición, verificación, razonamiento, construcción de inteligencia y conocimiento gobernado. Internamente usa ocho motores. |
| 2 | Design | Determina cómo debe expresarse el conocimiento adquirido. |
| 3 | Precision | Determina la forma concreta en que debe transmitirse la información. |
| 4 | Master Orchestrator | Gestiona y gobierna la colaboración entre los demás bloques. |

## Límites vigentes

- Los bloques se construyen y validan de forma aislada antes de aceptar una arquitectura transversal.
- El Master Orchestrator no hereda ni crea autoridad de los demás bloques por defecto.
- Contratos comunes, protocolo interbloques, grafo de dependencias y criterios de promoción requieren aceptación explícita posterior.
- La existencia de este modelo no prueba implementación, integración, runtime ni cierre de ningún gate.

## Estado

La declaración original describía sólo el corte inicial de Bloque 1. Desde
2026-09-14 existe una ruta local candidata, aún no aceptada globalmente:
`fuente aprobada → Bloque 1 dossier → Bloque 2 artefacto de diseño → Bloque 3
adaptación de audiencia declarada → Bloque 4 revisión humana`.

La ruta no altera los límites del modelo: conserva controles locales, bloquea
publicación/entrega y no convierte sus pruebas en integración o aceptación
global. El contexto y contrato candidatos están en
`architecture/telecare_context_map_v0.2.md` y
`contracts/telecare_content_design_handoff_v0.1.md`.

## Registro de cambio

- Versión: 1.0
- Cambio: adopción de Telecare OS como nombre del sistema y definición de sus cuatro bloques.
- Autoridad: decisión explícita del usuario.
- Fecha: 2026-08-24
- Evidencia: decisión de arquitectura registrada en este repositorio.
- Impacto: nomenclatura y límites de arquitectura; no cambia por sí misma los gates existentes.
- Nota de implementación: 2026-09-14, se corrige la ruta local para que Bloque
  2 sea propietario del artefacto de diseño, sin modificar la autoridad de los
  bloques ni promover gates.
