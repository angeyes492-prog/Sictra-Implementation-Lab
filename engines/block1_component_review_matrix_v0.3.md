# Matriz de Revisión Operacional por Componente v0.3

| Componente | Ataque principal | Mecanismo de cierre | Evidencia requerida |
|---|---|---|---|
| Common Envelope | canonicalización ambigua, versión, mutabilidad | JSON estricto, deep-freeze, SemVer cerrado | contract negatives |
| E01 | input no acotado, identidad ambigua | 1,000 fuentes máximo, task+run namespace | límites/tipos |
| E02 | provenance fabricada, stale/synthetic/foreign | atestación HMAC + scope/clase/tiempo | mutations |
| E03 | completed confundido con validated, sustitución post-handoff | metadata + evidence/outcome fingerprint + HMAC + NOT_VALIDATED | determinismo/mutation |
| E04 | race, topology bypass, replay | lock, allowlist, audit de reject, bounded cache | concurrency |
| E05 | correlación/contradicción circular, outcome falsificado | grafo root/correlation + claims gobernados + verificación E03 | independent/mutation |
| E06 | write antes de auth, mutabilidad, bypass E08 | atestación E08 + reautorización actual + transacción + hash chain | restart/concurrency/tamper |
| E07 | false-green | execution + observations + cero uncertainty + store health | future/stale/gaps/outage |
| E08 | autoridad autocertificada, TOCTOU, action confusion | verifier HMAC, binding exacto y acción registrada | forged/binding/action |
| Runtime | partial failure y duplicate effects | dispatch allowlist + transacción terminal/efecto + journal | replay/fault injection |

Los revisores independientes son agentes distintos del constructor. La primera
pasada bloqueó el gate; la segunda encontró defectos de atomicidad y dispatch.
La promoción requiere una tercera pasada independiente sobre el SHA exacto,
sin hallazgos críticos o altos dentro del perfil operacional acotado.

