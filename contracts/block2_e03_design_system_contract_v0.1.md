# Block 2 / E03 — Design System Contract v0.1

> Estado: `CANDIDATE / LOCAL BOUNDED SUT / NOT INTEGRATED / NOT ACCEPTED`  
> Alcance: convertir una dirección seleccionada externamente en restricciones y
> opciones de sistema accesibles, versionadas y trazables. No elige dirección,
> no crea evidencia, no renderiza ni administra una marca.

## Propósito y propiedad

E03 posee el **perfil de sistema visual**: tokens semánticos, roles
tipográficos, reglas de layout, opciones de componentes, motion, fallback,
excepciones y compatibilidad por canal. El dueño de la selección de dirección,
la marca, las licencias y la autoridad sigue siendo externo al motor.

## Entrada y salida

```text
E03Input = {
  envelope: DesignContextEnvelope@0.1,
  selected_direction: Direction,
  selection_record: {direction_id, selector_id, authority_reference, reason},
  brand_system_manifest: {version, token_sources[], asset_refs[], owner},
  channel_requirements: {channel, accessibility_policy_ref, viewport?, format}
}

SystemConstraintProfile = {
  profile_id, direction_id, envelope_fingerprint,
  token_bindings[], typography_roles[], layout_rules[],
  component_options[], semantic_color_map[], motion_rules[],
  accessibility_checks[], fallbacks[], exceptions[],
  source_license_refs[], compatibility_matrix, rollback_scope,
  disposition, provenance_delta
}
```

Precondiciones: envelope `CONTINUE`; selección externa con autoridad vigente;
dirección estructuralmente válida; manifest de marca versionado; cada fuente,
asset o tipografía afectante tiene `ReferenceRightsManifest`; requisitos de
canal y accesibilidad son explícitos.

## Invariantes

1. E03 no cambia el `claim_binding`, certainty, contradicciones, non-claims o
   elección de dirección ni exposición de incertidumbre; un token sólo expresa,
   no decide, significado.
2. Todo token semántico material tiene fallback no dependiente de color; todo
   motion rule material tiene alternativa estática/textual.
3. Un token de marca que choque con la política de accesibilidad no puede
   eclipsar el requisito; se declara `CONTRADICTED` o se usa fallback
   autorizado.
4. Una tipografía exacta o asset sólo se emite con licencia y scope de canal
   compatibles. Una alternativa documenta rol, no imita identidad.
5. Cada excepción indica motivo, alcance, owner, fecha de revisión y rollback.
   No se convierte en regla global por frecuencia de uso.
6. El cambio responsive/canal no puede alterar significado material sin
   `RETURN_TO_PREVIOUS` hacia E02/E01.
7. Ningún componente, token o referencia en `QUARANTINE` llega al profile.

## Disposición, recuperación y rollback

| Condición | Resultado | Recuperación |
|---|---|---|
| selección sin autoridad o direction ID distinto | `RETURN_TO_PREVIOUS` | registrar selección autorizada o reabrir E02. |
| token incompatible con accesibilidad | `CONTRADICTED` | fallback aprobado o revisión humana de política/marca. |
| fuente/asset sin licencia o vencido | `QUARANTINE_REFERENCE` | sustituir por rol autorizado o aportar licencia. |
| canal no soportado por el sistema | `UNSUPPORTED_CHANNEL` | adapter/manifest nuevo, sin degradación silenciosa. |
| excepción vencida | `RETURN_TO_PREVIOUS` | renovar con owner o recomponer sin excepción. |

Rollback revierte sólo el profile y sus excepciones al `brand_system_manifest`
versionado anterior; no altera la dirección ni licencias de origen.

## Observabilidad y oráculo independiente

Registrar versión de manifest, selección, tokens por rol, checks y fallbacks,
assets/licencias, excepciones, breakpoints/canales y reason codes. El oráculo
local separado, sin invocar al evaluador E03, comprueba que: cada token material
tiene fallback; no hay assets en cuarentena; cada excepción tiene expiración y
rollback; la selección posee autoridad; y los bindings upstream sobreviven.

## Vectores adversariales

1. Color de marca sin fallback accesible → `CONTRADICTED`.
2. Font de una captura sin licencia → `QUARANTINE_REFERENCE`.
3. Componente móvil que elimina una advertencia → `RETURN_TO_PREVIOUS`.
4. Excepción sin owner/fecha → rechazo.
5. Token que expresa `certainty_low` sólo con opacidad → rechazo.
6. Selección “automática” desde E02 sin autoridad externa → rechazo.
7. Asset con licencia válida sólo para web usado en email → rechazo.
8. Manifest más nuevo incompatible con el consumer → `UNSUPPORTED_VERSION`.

## Compatibilidad y no-claims

E03 acepta envelopes y direcciones `0.1.x`. Campos desconocidos se preservan
sin semántica; version mayor se rechaza explícitamente. Este contrato no prueba
que una marca sea legalmente usable, que contraste real haya sido medido, que
un componente haya sido renderizado o que el resultado sea accesible, integrado
o aceptado. El SUT local no sustituye el manifest completo de marca ni una
decisión jurídica: consume una decisión de rights vigente y falla cerrado si
esa vigencia fue revocada.
