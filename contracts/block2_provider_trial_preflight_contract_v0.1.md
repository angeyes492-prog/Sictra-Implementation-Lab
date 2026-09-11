# Block 2 — Provider Trial Preflight Contract v0.1

> Estado: `CANDIDATE / LOCAL NON-OPERATIONAL PREFLIGHT / MAR REQUIRED`.

## Propósito

Clasificar si el paquete de gobierno para un futuro trial de provider está
declarado sin resolver secretos, invocar red ni habilitar producción. Cubre las
lanes candidatas `GENERATIVE_MEDIA` y `DESIGN_PLATFORM`; no modifica la lane
determinista existente.

## Invariantes

1. El registro conserva provider, snapshot, lane, handle no secreto, términos,
   política de datos, hash de rights, presupuesto, autoridad de trial y
   referencia MAR.
2. El handle debe usar `vault://` y cualquier forma que parezca secreto/API key
   se rechaza estructuralmente. El vault es quien resuelve el handle; este
   contrato nunca recibe la credencial.
3. Credencial ausente/expirada/revocada, preflight vencido o scopes mínimos
   ausentes devuelve `RETURN_UPSTREAM` con razones.
4. `PRECONDITIONS_DECLARED` significa sólo que la declaración local está
   completa. Mantiene `execution_authorized=false` y `NOT_ACCEPTED`; no prueba
   que el vault, MAR, términos ni provider real hayan sido verificados.
5. La integración con un adapter remoto requiere un contrato posterior,
   verificación independiente de cada referencia y MAR. No existe fallback ni
   llamada implícita desde este módulo.

## Scopes mínimos

| Lane | Scopes declarados |
|---|---|
| `GENERATIVE_MEDIA` | `IMAGE_GENERATION` |
| `DESIGN_PLATFORM` | `DESIGN_CREATE`, `DESIGN_EXPORT` |

## No-claims

Fixtures de este contrato no son credenciales reales, aceptación de términos,
ejecución contra OpenAI/Canva/Figma, seguridad del vault, prueba de billing ni
aceptación global.
