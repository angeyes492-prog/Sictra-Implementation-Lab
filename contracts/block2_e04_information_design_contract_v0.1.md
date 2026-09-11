# Block 2 / E04 — Information Design Contract v0.1

> Estado: `CANDIDATE / LOCAL BOUNDED SUT / NOT INTEGRATED / NOT ACCEPTED`  
> Alcance: blueprint de composición informativa para un canal autorizado. No
> investiga, inventa contenido, renderiza, envía newsletters ni publica assets.

## Propósito y propiedad

E04 posee la **composición de información**: orden de lectura, secciones,
encodings, densidad, rutas de audiencia, atribución y fallbacks. No posee la
dirección creativa, los tokens, hechos/evidencia, el contenido fuente ni la
producción final.

## Entrada y salida

```text
E04Input = {
  envelope: DesignContextEnvelope@0.1,
  system_constraint_profile: SystemConstraintProfile,
  information_payload: {claims[], evidence_refs[], approved_copy[],
                        attributions[], limitations[]},
  channel_target: {artifact_type, channel, locale?, format, audience_path}
}

InformationCompositionBlueprint = {
  blueprint_id, profile_id, envelope_fingerprint, artifact_type, channel,
  audience_path, reading_order[], sections[], claim_to_element_map[],
  encoding_plan[], content_density_budget, responsive_plan,
  accessibility_fallbacks[], source_attribution_plan,
  validation_prompts[], unsupported_capabilities[],
  disposition, provenance_delta
}
```

`approved_copy` es contenido autorizado; E04 no amplía facts ni transforma una
limitación en una afirmación. Cada `claim_to_element_map` une un elemento con
claim, evidence reference o marca explícita `decorative`.

## Precondiciones e invariantes

1. Profile válido, no vencido y compatible con el canal; payload con claims,
   evidencia/atribución y limitaciones necesarias; canal contratado.
2. Todo elemento material del blueprint tiene mapa a claim/evidence/restricción.
   Decoración no puede introducir inferencias o modificar la lectura de un
   claim.
3. Orden de lectura conserva relación entre decisión/CTA, evidencia y sus
   limitaciones. Un CTA no puede separar ni ocultar la incertidumbre material.
4. Encodings mantienen unidades, escala, polaridad, incertidumbre y
   atribución; E04 no invierte causalidad o comparación para mejorar impacto.
5. Cada significado esencial dispone de fallback accesible. Para newsletter se
   exige plan de versión texto plano; para multimedia, transcript y descripción
   de información material; para gráfico, texto alternativo y leyenda.
6. Adaptar de un canal a otro requiere volver a validar `claim_to_element_map`.
   Si se pierde, se emite `UNSUPPORTED_CHANNEL`/`RETURN_TO_PREVIOUS`.
7. `InformationCompositionBlueprint` nunca contiene bytes de imagen, HTML,
   PDF, email enviado, vídeo generado ni estado de publicación.
8. La visualización se selecciona por relación informativa, no por ornamento:
   línea para tendencia; barras/dot para comparación; histogram/box/violin
   para distribución; scatter para correlación; y encodings específicos para
   flujo, red, geografía y objetivo. Se rechazan 3D, doble eje, color como único
   portador de significado y barras sin cero. Pie se limita a cinco series.
9. Las identidades de claim, elemento y encoding son únicas; los duplicados no
   se colapsan ni resuelven por orden de llegada.

## Disposición y recuperación

| Condición | Resultado | Recuperación |
|---|---|---|
| facts/evidence/atribución ausentes | `RETURN_UPSTREAM` | reparar el payload en su owner. |
| profile incompatible o significado cambiado | `RETURN_TO_PREVIOUS` | reabrir E03/E02 con razón exacta. |
| canal/fallback no contratado | `UNSUPPORTED_CHANNEL` | restringir el blueprint o autorizar adapter. |
| licencia/asset revocado | `QUARANTINE_REFERENCE` | recomponer desde profile sin dependencia revocada. |
| densidad y accesibilidad incompatibles | `CONTRADICTED` | revisión humana; no reducir contexto silenciosamente. |

Rollback descarta el blueprint, conserva el profile y los padres para auditoría,
y crea una nueva versión de blueprint al reintentar.

## Observabilidad y oráculo independiente

Registrar fingerprint de envelope/profile, canal, orden, secciones, densidad,
mapa claim→element, fallbacks, atribuciones, capability gaps y reason codes.
El oráculo local separado no invoca E04 y verifica: cobertura de cada claim material;
presencia de limits junto a CTA/claim relevante; fallback por tipo de canal;
ausencia de output ejecutable/publicado; y preservación de unidades/polaridad.

## Vectores adversariales

1. Gráfico con claim sin leyenda/atribución → `RETURN_UPSTREAM`.
2. Newsletter con CTA sin límite de claim material → rechazo.
3. Conversión de brief a email que borra contradicción → `RETURN_TO_PREVIOUS`.
4. Imagen sin alt text que expresa información esencial → rechazo.
5. Video blueprint sin transcript → `UNSUPPORTED_CHANNEL`.
6. Infografía que invierte escala/polaridad respecto del payload → rechazo.
7. Elemento decorativo presentado como evidencia → rechazo.
8. Intento de incluir HTML, PNG o estado `PUBLISHED` → rechazo de alcance.

## Compatibilidad y no-claims

E04 acepta `0.1.x` de envelope/profile/payload. Versiones mayores producen
`UNSUPPORTED_VERSION`; campos no conocidos se preservan sin efecto. Conformidad
no prueba comprensión, conversión, aprendizaje, accesibilidad real, delivery,
integración con software, derechos finales, ejecución, validación humana ni
aceptación.
