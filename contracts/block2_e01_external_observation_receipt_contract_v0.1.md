# Block 2 / E01 — External Observation Receipt Contract v0.1

> Estado: `CANDIDATE / LOCAL RECEIPT VALIDATOR / NOT ACCEPTED`.

## Propósito

El recibo registra una observación humana de un único fixture E01 que ya pasó
preflight. Vincula fixture, objeto upstream, autoridad, revisor, orden de
exposición, evidencia y resultado; no ejecuta el ensayo ni declara una regla
de diseño. La salida `OBSERVATION_RECORDED` conserva una observación atómica y
siempre lleva `NOT_PROMOTED / NOT_ACCEPTED`.

## Invariantes

1. `fixture_id` y SHA-256 del fixture deben coincidir con el fixture preflighted
   exacto; sustitución de candidatos, tarea o confounders es `INVALID_TRIAL`.
2. El objeto upstream y la autoridad deben coincidir; temporalidad distinta de
   `CURRENT` es `RETURN_UPSTREAM`.
3. La identidad del autor vive dentro del fixture y está cubierta por el hash;
   el recibo debe repetirla exactamente. El reviewer no puede ser ese autor,
   debe ser externo, tener independencia revisada y aportar evidencia
   atribuible. Una sustitución de autor invalida el ensayo.
4. Fuga material, exposición de tesis antes de la respuesta o confounder
   material hacen el ensayo `INVALID_TRIAL`.
5. Un preflight `RETURN_UPSTREAM` domina la recepción; un preflight no listo
   nunca produce observación.
6. Resultados admitidos: `A_SUPPORTED`, `B_SUPPORTED` o `NO_DISCRIMINATION`.
   Ninguno prueba causalidad, reproduce un efecto, cambia E01 ni alimenta E08
   sin los gates correspondientes.

## Límite y autoridad

El recibo es una interfaz para que un revisor humano independiente entregue
evidencia verificable. Una fixture de test y un recibo sintético sólo prueban
la lógica local. La validez perceptual, identidad real del revisor, derechos,
MAR y aceptación humana permanecen fuera del módulo.
