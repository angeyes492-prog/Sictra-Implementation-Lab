# Bloque 2 / E01 — Preflight Contract v0.1

> Estado: `CANDIDATE / BOUNDED SUT`; autoridad local de E01. No es contrato
> común, producción, validación perceptual ni aceptación arquitectónica.

## Propósito

Clasificar un fixture de comparación visual **antes** de exponerlo a un
observador. El contrato sólo puede devolver `READY_FOR_OBSERVATION`,
`RETURN_UPSTREAM`, `INVALID_TRIAL` o `UNSUPPORTED_COMBINATION`.

`READY_FOR_OBSERVATION` no es una observación, evidencia empírica, preferencia,
resultado de diseño ni promoción de memoria.

## Entradas obligatorias

- Identidad/procedencia/evidence status/authority/audience/decisión del objeto
  upstream.
- Claim con Target, Action, Scope, versión y audit de leakage.
- Dos candidatos con igualdad en contenido, tarea, etiquetas, escala,
  incertidumbre, anotación, contexto, atención y carga de implementación.
- Perfil de observador con independencia revisada y control de orden.
- Registro de confounders y composición de claims, si existe.

## Invariantes y rechazo

- Entrada upstream incompleta: `RETURN_UPSTREAM`.
- Fuga, desigualdad semántica, observador contaminado, orden no controlado o
  confounder material: `INVALID_TRIAL`.
- Combinación de claims sin prueba de interacción: `UNSUPPORTED_COMBINATION`.
- Los motivos y claims en cuarentena se conservan; no se borran ni se reducen a
  un score.
- Un fixture limpio no puede convertirse en `A_SUPPORTED` ni `B_SUPPORTED`.

## Límites conocidos

No analiza píxeles, no infiere leakage desde lenguaje natural, no certifica
independencia humana y no mide sensibilidad nula. Es un guard estructural para
hacer explícita la revisión humana/independiente pendiente.
