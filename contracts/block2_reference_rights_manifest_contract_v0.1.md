# Block 2 / Reference Rights Manifest Contract v0.1

> Estado: `CANDIDATE / NOT IMPLEMENTED / NOT LEGAL ADVICE`  
> Alcance: clasificar si una referencia puede ser consultada, resumida o usada
> como restricción de diseño. No determina propiedad intelectual ni otorga una
> licencia por sí mismo.

## Propósito y frontera

El manifest evita que una referencia pública sea tratada como permiso de copia,
entrenamiento, redistribución o imitación. Es un control transversal candidato
para E01–E04; no es E05 ni un sistema de entrenamiento.

La decisión está separada por activo: texto, imagen, vídeo, fuente, audio,
logo/marca, código y archivo de proyecto. Una licencia de página, metadata o
software no se transfiere automáticamente a sus assets incrustados.

## Forma lógica

```text
ReferenceRightsManifest = {
  manifest_id, version, source_id, canonical_url, publisher, retrieved_at,
  content_hash?, license_snapshot_ref?, terms_snapshot_ref?,
  asset_records[],
  access_decision, decision_basis[], reviewer?, review_due_at?,
  provenance, uncertainty[], non_claims[]
}

AssetRecord = {
  asset_id, asset_type, rights_holder?, license_ref?, usage_scope[],
  restrictions[], origin_confidence, tdm_status?,
  allow_index, allow_rag_storage, allow_finetune,
  allow_asset_training, allow_redistribution,
  style_similarity_risk, decision
}
```

`asset_type` acepta solamente `TEXT`, `IMAGE`, `VIDEO`, `FONT`, `AUDIO`,
`LOGO_OR_TRADE_DRESS`, `CODE` o `PROJECT_FILE`. Los booleanos de permiso sólo
son `true` con evidencia de alcance aplicable; `UNKNOWN` se representa como
`false` para toda acción que copie, entrene, redistribuya o reproduzca.

## Decisiones permitidas

| Decisión | Uso permitido | Uso expresamente bloqueado |
|---|---|---|
| `ALLOW_CONSTRAINT_ONLY` | extraer principios abstractos, por ejemplo densidad o rol tipográfico. | copiar activos, reproducción distintiva o entrenamiento. |
| `ALLOW_LICENSED_ASSET` | usar el asset en el scope, canal y periodo de licencia registrados. | usos fuera de scope o derivados no autorizados. |
| `ALLOW_METADATA_INDEX` | indexar metadatos y URL. | almacenar/citar contenido no permitido. |
| `QUARANTINE` | conservar ID, riesgo y razón sin usar el activo. | copia, estilo, prompt de imitación, RAG o entrenamiento. |
| `REVOKED` | ninguna reutilización; dispara invalidación descendiente. | todo uso futuro o distribución. |

No existe una decisión implícita `ALLOW`.

## Precondiciones y autoridad

Cada manifest requiere fuente canónica, timestamp de recuperación, clase de
activo y una decisión con base registrable. `ALLOW_LICENSED_ASSET` requiere
rights holder o licencia verificable, scope, restricciones, vigencia y la
identidad/autoridad del revisor cuando la política lo exija. Una captura de
pantalla sin datos de licencia es `QUARANTINE`, aunque E01 pueda describir de
forma abstracta su jerarquía sin reproducirla.

El manifest no puede invalidar reglas protegidas, derechos de terceros, una
revocación de fuente ni la exigencia de revisión legal externa cuando aplique.

## Invariantes

1. Público, accesible o indexable no implica reutilizable.
2. La decisión más restrictiva domina para un asset y sus derivados.
3. `ALLOW_CONSTRAINT_ONLY` no permite especificar una fuente exacta, logo,
   composición distintiva o prompt que solicite imitación identificable.
4. Un asset sin `license_ref` verificable no puede pasar a
   `ALLOW_LICENSED_ASSET`.
5. Una fuente o asset `REVOKED` invalida outputs que lo incorporen desde su
   `provenance` y exige recomposición.
6. El manifest conserva hashes/snapshots cuando existan; una página cambiada no
   borra la decisión histórica.
7. Ningún engine puede alterar `access_decision`; sólo un owner de derechos
   autorizado puede emitir una versión nueva.

## Interacción con E01–E04

| Motor | Puede leer | Debe hacer |
|---|---|---|
| E01 | `ALLOW_CONSTRAINT_ONLY`, `ALLOW_LICENSED_ASSET` | ligar una tesis a restricciones abstractas y reportar riesgo de similitud. |
| E02 | decisiones y restricciones | evitar direcciones que dependan de identidad protegida o clonación. |
| E03 | assets/fuentes con scope explícito | usar sólo tokens/activos permitidos y declarar fallback. |
| E04 | atribución y restricciones de canal | incluir atribución, texto alternativo y exclusiones en blueprint. |

## Rechazo, recuperación y observabilidad

Origen ausente, asset ambiguo, licencia no verificable, scope vencido,
restricciones contradictorias o intento de entrenamiento producen
`QUARANTINE`. La recuperación consiste en aportar documentación de derechos,
reclasificar bajo nuevo manifest o sustituir por un recurso autorizado. No hay
retry automático ni inferencia desde la marca, popularidad o disponibilidad de
una web.

Registrar: manifest/asset IDs, hash y timestamp, decisión, reason codes,
scope, restricciones, risk score, lineage de outputs afectados y versión de
revocación. El score no reemplaza la decisión ni una revisión humana.

## Vectores de validación requeridos

1. Página pública sin licencia de imagen → imagen `QUARANTINE`.
2. Metadata con licencia permisiva e imagen sin licencia → sólo
   `ALLOW_METADATA_INDEX`.
3. Fuente con licencia por canal limitado → E03 bloquea export fuera de canal.
4. Asset permitido pero `allow_finetune=false` → entrenamiento rechazado.
5. Captura como referencia de jerarquía → `ALLOW_CONSTRAINT_ONLY`, sin fuente
   exacta ni composición clonada.
6. Revocación posterior → outputs dependientes quedan invalidables y no se
   redistribuyen.
7. Dos decisiones conflictivas → domina `QUARANTINE` y se expone contradicción.
8. Prompt que solicita copiar la marca/referencia → rechazo aunque el asset sea
   visible públicamente.

## No-claims

Este manifest es una herramienta de control técnico y de trazabilidad; no
otorga derechos, sustituye asesoría jurídica, verifica por sí mismo una licencia
ni prueba que una salida no sea sustancialmente similar a una referencia.

