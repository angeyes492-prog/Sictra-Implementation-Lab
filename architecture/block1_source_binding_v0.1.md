# Block 1 — Source Binding Authorization v0.1

**Clasificación:** reparación de control de autoridad, local a E02.
**Estado:** `IMPLEMENTED CANDIDATE / LOCAL-TESTED` tras ejecutar su suite.
**Propietario semántico:** configuración gobernada de E02.

## Propósito

Una `SourceBindingAuthorization` HMAC impide que el mero constructor de
`SourceRegistration(status="BOUND")` habilite ingreso de evidencia. Vincula un
expediente de aprobación revisado con una configuración exacta y con vigencia.

## Invariantes

- La autorización está firmada por un issuer confiable de configuración.
- Vincula exactamente identidad, scope, hosts, claims y límite de contenido.
- Tiene ventana temporal; el Gateway la verifica al iniciar y en cada ingreso.
- Una decisión `REJECTED`, un token alterado, no confiable, vencido o ausente
  falla cerrado.
- El mecanismo no adquiere datos, no administra identidad de producción y no
  convierte un dato observado en verdad o gate.

## Dependencias y límites

Depende del expediente de aprobación, el candidato propuesto, primitivas DNS y
Source Gateway. HMAC local representa una autoridad de configuración acotada,
no KMS, roles corporativos, firma humana verificable ni producción.
