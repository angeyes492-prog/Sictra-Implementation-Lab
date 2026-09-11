# Block 2 / E02 — Creative Direction Contract v0.1

> Estado: `CANDIDATE / NOT IMPLEMENTED / NOT ACCEPTED`  
> Alcance: divergencia creativa trazable desde una tesis visual válida. No es un
> selector de ganador, moodboard, renderer, generador de imagen ni sistema de
> memoria.

## Propósito, productor y consumidor

E02 transforma un `VisualThesisSet` admisible de E01 en un `DirectionSet` de
dos o tres estrategias de comunicación materialmente distintas. Su propiedad
es la **dirección creativa**: marco conceptual, arquitectura de información,
encoding, secuencia e intención de canal. No adquiere hechos, evidencia,
certainty, autoridad, tokens de marca ni aceptación.

| Rol | Entidad | Límite |
|---|---|---|
| Productor | E02 | añade direcciones y razones, sin modificar `upstream_binding`. |
| Consumer inmediato | E03 | usa una dirección seleccionada por una autoridad externa. |
| Consumer de revisión | futuro E07 | evalúa hipótesis/riesgos; no selecciona por E02. |
| Dueño de selección | revisión humana o policy autorizada futura | elige, rechaza o solicita reabrir; fuera de E02. |

## Entrada

```text
E02Input = {
  envelope: DesignContextEnvelope@0.1,
  visual_thesis_set: {
    thesis_id, claim_bindings[], hierarchy, semantic_tension,
    visual_metaphor, encoding_hypotheses[], uncertainty_exposure,
    assumptions[], risks[], return_conditions[]
  },
  direction_brief: {target_channel, permitted_axes[], required_accessibility[],
                    max_directions, prohibited_adaptations[]}
}
```

Precondiciones:

1. El envelope tiene disposición `CONTINUE`, temporalidad `CURRENT` y no ha
   sufrido mutación de upstream.
2. La tesis tiene al menos un `claim_binding`, conserva contradicciones y
   declara cómo expone incertidumbre material.
3. `target_channel` está autorizado y no requiere un adapter no contratado.
4. Las referencias usadas por la tesis poseen manifest válido o están limitadas
   a restricciones abstractas permitidas.

De no cumplirse (1) se responde `RETURN_UPSTREAM`; de no cumplirse (2) o (4),
`RETURN_TO_PREVIOUS`/`QUARANTINE_REFERENCE`; de no cumplirse (3),
`UNSUPPORTED_CHANNEL`.

## Salida

```text
DirectionSet = {
  direction_set_id, parent_thesis_id, envelope_fingerprint,
  directions[2..3], pairwise_difference_matrix,
  shared_claim_bindings[], rejected_routes[], disposition,
  provenance_delta
}

Direction = {
  direction_id, conceptual_frame,
  structural_axes: {
    visual_metaphor, information_architecture, encoding,
    reading_sequence, interaction_or_motion
  },
  channel_intent, accessibility_intent,
  claim_bindings[], uncertainty_exposure,
  tradeoffs[], risk_register[],
  disconfirming_observation, reopen_target
}
```

`pairwise_difference_matrix` registra por cada par de direcciones los ejes
que difieren, por qué importan para la tarea y si la diferencia es verificable.

## Invariantes

1. Cada dirección preserva exactamente los claim bindings, certainty,
   contradicciones y non-claims heredados; puede hacerlos visibles, no
   atenuarlos ni elevarlos.
2. Dos direcciones son materialmente distintas sólo si difieren en **dos o más
   ejes estructurales permitidos** y cada diferencia cambia la comprensión,
   carga cognitiva, accesibilidad o estrategia de lectura de forma declarada.
3. Cambio de paleta, ornamento, imagen decorativa o microcopy por sí solo no
   cuenta como diferencia estructural.
4. Cada dirección define una observación que podría invalidarla y el motor al
   que retornaría; no afirma que dicha observación ya ocurrió.
5. La adaptación de audiencia usa únicamente restricciones explícitas de
   lenguaje, densidad, canal y accesibilidad. No infiere atributos sensibles,
   intención o preferencia desde proxies no autorizados.
6. `max_directions` no puede producir diversidad ficticia: si sólo hay una ruta
   admisible, E02 devuelve `RETURN_TO_PREVIOUS` con `INSUFFICIENT_DIVERGENCE`.
7. E02 no selecciona un ganador, no emite `ACCEPTED`, no actualiza memoria y no
   pasa una dirección a E03 sin una selección registrada fuera de E02.

## Matriz de diferencia estructural

Cada par debe anotar `SAME`, `DIFFERENT_MATERIAL`, `DIFFERENT_COSMETIC` o
`UNSPECIFIED` para los cinco ejes. Es admisible sólo si el conteo
`DIFFERENT_MATERIAL >= 2` y no existe cambio prohibido.

Ejemplo abstracto válido:

| Eje | Dirección A | Dirección B | Tipo |
|---|---|---|---|
| metáfora | progresión | comparación de escenarios | `DIFFERENT_MATERIAL` |
| arquitectura | secuencia causal | matriz de decisiones | `DIFFERENT_MATERIAL` |
| encoding | hitos y etiquetas | comparación con notas de incertidumbre | `DIFFERENT_MATERIAL` |
| color | sobrio | contrastado | `DIFFERENT_COSMETIC` |

El ejemplo no prescribe una solución real ni permite copiar una referencia.

## Rechazo, recuperación y rollback

| Condición | Disposición | Recuperación |
|---|---|---|
| upstream incompleto/stale | `RETURN_UPSTREAM` | reparar el objeto de Intelligence y emitir un nuevo envelope. |
| tesis sin binding o incertidumbre oculta | `RETURN_TO_PREVIOUS` | E01 corrige tesis o exposición de límite. |
| referencia de identidad protegida | `QUARANTINE_REFERENCE` | retirar dependencia y proponer una restricción abstracta autorizada. |
| rutas duplicadas | `RETURN_TO_PREVIOUS` | E02 replantea ejes o declara que no hay divergencia honesta. |
| marca versus accesibilidad incompatibles | `CONTRADICTED` | revisión humana del conflicto; E02 no arbitra. |
| canal fuera de contrato | `UNSUPPORTED_CHANNEL` | contratar/autorizar adapter o escoger canal permitido. |

El rollback descarta el `DirectionSet` y sus deltas. No altera la tesis ni el
envelope padre; el nuevo intento referencia al mismo padre o a una versión
explícitamente actualizada.

## Observabilidad

Por cada run registrar: IDs de tesis/dirección, fingerprint padre, ejes
materiales por par, claims y contradicciones conservados, elementos decorativos
excluidos, rutas descartadas, risks, reasons de disposición, derechos de
referencia, versión y timestamp lógico. Métricas candidatas: `material_delta`
por par, duplicados rechazados, bindings preservados, returns por causa y
direcciones con fallback accesible.

## Oráculo independiente especificado

El oráculo futuro recibe un `DirectionSet` serializado y, sin llamar al
evaluador de E02 ni compartir helpers, verifica:

1. igualdad exacta entre metadata upstream de entrada/salida;
2. cada binding presente en tesis está presente en las direcciones;
3. toda contradicción/non-claim material sobrevive;
4. cada par tiene al menos dos `DIFFERENT_MATERIAL`;
5. ningún eje prohibido ni asset en cuarentena aparece como dependencia;
6. ninguna dirección tiene estado de selección, publicación o aceptación.

El acuerdo con este oráculo será evidencia diferencial acotada, no prueba de
creatividad, percepción, derechos reales ni validación global.

## Vectores de validación y red-team

1. Dos rutas que sólo cambian color/ornamento → `INSUFFICIENT_DIVERGENCE`.
2. Una ruta cambia metáfora y arquitectura → diferencia material admisible.
3. Tesis `PLAUSIBLE` convertida en headline `VERIFIED` → rechazo.
4. Contradicción conservada en A y omitida en B → rechazo total del set.
5. Captura con fuente/logotipo no licenciado → cuarentena, no ruta de imitación.
6. Adaptación basada en atributo sensible no autorizado → rechazo.
7. `max_directions=3` con una sola ruta honesta → retorno, no tercera variante.
8. Selección automática de “mejor dirección” → rechazo de alcance.
9. Mutación de `message_id` o fingerprint padre → `IdentityCollision`/rechazo.
10. Canal email sin versión de accesibilidad prevista → retorno a dirección o
    `UNSUPPORTED_CHANNEL` según contrato de canal.

## Compatibilidad y no-claims

E02 acepta `DesignContextEnvelope@0.1.x` y una tesis compatible. Campos
desconocidos se preservan sin semántica. Versión mayor produce
`UNSUPPORTED_VERSION`; no hay coerción silenciosa.

Conformidad no prueba que una dirección sea preferida, comprensible, efectiva,
accesible para una población real, legalmente segura, renderizada, integrada,
ejecutada, validada o aceptada.

