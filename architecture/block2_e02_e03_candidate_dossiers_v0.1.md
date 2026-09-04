# Bloque 2 / Design — Dossiers candidatos E02 y E03 v0.1

> **SUPERSEDED FOR CURRENT E02 STATE:** ver
> `architecture/block2_e02_e03_candidate_dossiers_v0.2.md`. Este documento se
> conserva como reconstrucción histórica al 2026-08-24.

> Estado: `UNCONFIRMED / CANDIDATE ONLY`. Los nombres E02 y E03 aparecen en el
> handoff, no en artefactos canónicos localizados. Estos dossiers no los
> aceptan como motores ni autorizan implementación.

## E02 — Creative Direction (candidato)

### Hipótesis de responsabilidad

Transformar una tesis visual candidata de E01 en un conjunto de direcciones
distintas y trazables, sin reinterpretar facts/evidence/certainty upstream ni
producir arte final.

### Entrada / salida propuesta

`E01_CANDIDATE_CONCEPT + DESIGN_LANGUAGE_CONSTRAINTS + AUDIENCE_CONTEXT`
→ `DIRECTION_SET + RATIONALES + REJECTED_ROUTES + RISKS`.

### Invariantes candidatos

- Una dirección conserva el claim y limitaciones de E01; no los fortalece.
- Diferencia estructural no equivale a cambio de color, estilo o tratamiento.
- Toda dirección debe ser reversible y expresar qué observación la reabriría.
- E02 no aprueba ni almacena aprendizaje como regla.

### Ataques de borde

- Cuatro direcciones visualmente distintas pero semánticamente idénticas.
- Una dirección más atractiva que convierte una hipótesis en hecho.
- Dirección familiar seleccionada por reconocimiento, no por task fit.
- Conflicto entre brand constraint y accesibilidad semántica.

### Gate mínimo antes de implementación

Propiedad, entrada/salida, relación con E01/E03, y rechazo de sobreclaim deben
ser revisados contra un artefacto canónico de Bloque 2.

## E03 — Design System (candidato)

### Hipótesis de responsabilidad

Ofrecer restricciones reutilizables de composición, tipografía, color,
accesibilidad y variantes, sin convertirse en autoridad sobre significado,
evidencia o decisión de E01/E02.

### Entrada / salida propuesta

`DIRECTION_SET + CHANNEL_CONSTRAINTS + ACCESSIBILITY_REQUIREMENTS`
→ `SYSTEM_CONSTRAINT_PROFILE + ALLOWED_VARIANTS + EXCEPTIONS + TEST_CASES`.

### Invariantes candidatos

- El sistema especifica opciones/constraints; no decide el argumento visual.
- Una regla de marca no puede ocultar incertidumbre ni contradicción.
- Color no es portador único de significado material.
- Excepción documentada no se convierte automáticamente en regla global.

### Ataques de borde

- Token de marca que no cumple contraste.
- Sistema que homogeneiza direcciones hasta borrar diferencias de hipótesis.
- Variante responsive que cambia la semántica de incertidumbre.
- Componente reutilizado fuera de su audiencia/decisión original.

### Gate mínimo antes de implementación

Definir autoridad sobre token, excepción, versionado y rollback, y validar que
E03 no absorba E01/E02 ni Precision.

## Dependencia y no-claims

La relación propuesta es `E01 → E02 → E03`, pero es una hipótesis de flujo,
no una dependencia aceptada. E02/E03 no se heredan de Bloque 1 ni se promueven
por la existencia del harness E01.
