# Red-team — Account Knowledge Fabric v0.1

| Vector | Resultado | Evidencia |
|---|---|---|
| SSRF loopback / puerto no aprobado | bloqueado | `test_private_network_fetch_target_is_rejected_before_request` |
| link externo, `mailto:` o `javascript:` | sin fetch / degradación visible | `test_stays_within_official_domain...`, `test_malformed_and_non_http_links...` |
| robots indisponible o redirigido fuera de dominio | fail closed | `test_robots_unavailable...`, `test_robots_redirect...` |
| prompt injection en contenido web | cuarentena, no llega a M05 | `test_instruction_like_web_content...` |
| evidencia de otro tenant | rechazada en el dossier | `test_cross_tenant_evidence...` |
| alteración, borrado de cola o trigger SQLite | detectado antes de lectura | pruebas `tampering`, `terminal_record_deletion`, `unapproved_sqlite_trigger` |
| eliminación de tombstone | detectada por head autenticado | `test_tombstone_deletion...` |
| promoción web a fact o delivery | sin ruta | adaptador `HYPOTHESIS` y modelo Wolfram |

## Resultado

`PASS` en SUT local acotado. La defensa por patrones contra inyección no es
completa frente a contenido adversarial; el contenido se mantiene como dato no
confiable y no se conecta a herramientas de acción.
