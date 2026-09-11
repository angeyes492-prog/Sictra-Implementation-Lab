# Contrato ejecutable — Block 1 Source Binding Authorization v0.1

**Versión:** `0.1.0`
**Productor:** `SourceBindingIssuer` de configuración.
**Consumidor:** `SourceGateway`.
**Scope:** `intelligence`.
**Autoridad:** autorización limitada de configuración; no adquisición ni gate.

## Emisión

El issuer recibe un `SourceApprovalRecord` aprobado y un `SourceCandidate`
propuesto. El expediente debe ser apto en el instante de emisión. La
autorización firmada contiene issuer, fuente, scope, referencia de términos,
hosts, claims, límite, emisión, vencimiento y firma HMAC.

## Verificación

El verificador requiere issuer confiable, firma válida, scope, identidad,
hosts, claims y límite idénticos a `SourceRegistration`, y tiempo dentro de la
ventana. El Gateway exige exactamente una autorización por cada registro
`BOUND` y ninguna para registros no enlazados.

No se expone conversión automática desde aprobación a registro, HTTP, secretos,
credenciales, roles corporativos ni promoción de gate. HMAC local no demuestra
que el revisor sea una identidad real; ese control pertenece a una fase futura.
