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

La única implementación actual es un corte acotado del Bloque 1:
`Contexto → Reassessment`. Su CI externa valida reproducibilidad del corte,
no la integración del sistema Telecare OS.

## Registro de cambio

- Versión: 1.0
- Cambio: adopción de Telecare OS como nombre del sistema y definición de sus cuatro bloques.
- Autoridad: decisión explícita del usuario.
- Fecha: 2026-08-24
- Evidencia: decisión de arquitectura registrada en este repositorio.
- Impacto: nomenclatura y límites de arquitectura; no cambia por sí misma los gates existentes.
