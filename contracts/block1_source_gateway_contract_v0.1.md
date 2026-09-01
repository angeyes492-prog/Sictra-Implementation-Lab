# Contrato ejecutable — Block 1 Source Gateway v0.1

**Versión:** `0.1.0`  
**Productor:** Source Gateway (límite local de E02)  
**Consumidor:** `EvidenceVerifier` de Block 1 y luego E02  
**Compatibilidad:** salida de evidencia `0.3.0`; no cambia ese contrato.

## Registro de fuente

Un `SourceRegistration` admite: `source_id`, `publisher`, `scope`, `allowed_hosts`, `claim_keys`, `status` y `max_content_bytes`.

- `source_id` es único dentro del Gateway.
- `allowed_hosts` contiene nombres DNS normalizados, no IPs ni localhost.
- `claim_keys` es un conjunto no vacío de claims canónicos que la fuente está autorizada a aportar.
- Sólo `status=BOUND` permite emitir. `PROPOSED`, `SUSPENDED` o `RETIRED` se rechazan.
- Cada `BOUND` exige una `SourceBindingAuthorization` HMAC vigente, emitida por
  un issuer confiable y que coincida exactamente en `source_id`, scope, hosts,
  claims y límite de contenido. Una aprobación o configuración no firmada no
  habilita la fuente.
- La capacidad inicial es 50 registros; el registro 51 se rechaza.

## Paquete manual admisible

El objeto de entrada contiene exactamente: `source_id`, `source_url`, `content`, `observed_at`, `claim_key`, `polarity`, `correlation_id`.

- URL: HTTPS, host incluido en `allowed_hosts`, sin usuario, contraseña, puerto, fragmento ni IP/local host.
- `content`: texto no vacío y dentro del límite UTF-8 de la fuente.
- `observed_at`: entero no booleano, no negativo ni futuro respecto al reloj inyectado.
- `claim_key`: incluido en `claim_keys`; `polarity`: `-1` o `1`; correlación: texto no vacío.

## Salida

La salida firmada contiene los campos requeridos por `EvidenceVerifier`: `source_id`, `content`, `observed_at`, `root_provenance`, `evidence_class=OBSERVED`, `scope`, `correlation_id`, `claim_key`, `polarity`, `schema_version`, issuer y atestación.

También incluye `source_url`, `publisher`, `content_sha256`, `ingestion_method=MANUAL_SOURCE_BUNDLE` y `gateway_version=0.1.0`; todos forman parte del material HMAC.

`root_provenance` es `gateway-source:<source_id>`. Por diseño conservador, dos artefactos de la misma fuente registrada no cuentan como raíces independientes sólo por tener contenido o correlación diferentes.

`SourceRegistration` nace `PROPOSED`. Pasar un estado `BOUND` sin autorización,
con autorización expirada, ausente, alterada o que amplíe la configuración se
rechaza antes de ingresar un paquete.

## Rechazos y no-claims

Todo incumplimiento provoca `ContractViolation` sin salida. Una atestación válida prueba únicamente que el Gateway configurado recibió y normalizó el paquete; no prueba verdad, licencia, frescura más allá de la ventana del verificador, independencia, utilidad ni aceptación de un insight.
