# Bloque 4 — operación local supervisada

El Command Center usa solo loopback y un journal/clave fuera de Git. No inicia
una fuente remota, no acepta paquetes sin firma y no publica resultados.

```powershell
$env:PYTHONPATH = (Resolve-Path .\src).Path
New-Item -ItemType Directory -Force .\.runtime | Out-Null
python -m sictra_block4_orchestrator.web `
  --store .\.runtime\block4-journal.sqlite `
  --integrity-key-file .\.runtime\block4-integrity.key `
  --bootstrap-demo --port 8768
```

Abre `http://127.0.0.1:8768/`. El demo genera un paquete marcado como prueba
sintética y lo detiene en `HUMAN_REVIEW_REQUIRED`. Para una entrada real de
laboratorio se requiere el adaptador firmado de Block 1 aprobado por el MAR;
no copies ni reutilices claves de otro bloque.

Verificación local:

```powershell
Invoke-RestMethod http://127.0.0.1:8768/health
Invoke-RestMethod http://127.0.0.1:8768/api/cases
```

## Controles de operación local

El Command Center puede pausar, reanudar, detener e iniciar **sólo** el
procesamiento local de Block 4. Cada cambio se registra en el mismo journal
HMAC, se recupera después de reiniciar y no publica, entrega, aprueba ni envía
un mandato a los otros bloques.

La interfaz muestra únicamente las acciones admitidas por el estado actual.
Para diagnosticar sin cambiar estado, usa **Verificar journal**. Para una
operación automatizada local, envía únicamente JSON desde loopback con un ID de
solicitud único y uno de los motivos permitidos:

```powershell
$body = @{
  action = 'PAUSE'
  request_id = 'operator-pause-0001'
  reason = 'REVIEW_REQUIRED'
} | ConvertTo-Json -Compress
Invoke-RestMethod http://127.0.0.1:8768/api/controls -Method Post -ContentType 'application/json' -Body $body
```

`PAUSE` sólo parte de `RUNNING`; `RESUME` sólo de `PAUSED`; `STOP` parte de
`RUNNING` o `PAUSED`; y `START` sólo de `STOPPED`. Un `RETRY_CASE` requiere
además un `case_id` retornable, un runtime `RUNNING` y menos de tres reintentos.
Repetir exactamente la misma solicitud es idempotente; reutilizar su ID con un
contenido distinto se rechaza. Un journal alterado, origen no local, acción
desconocida o transición insegura se rechazan sin efecto descendente.

Respalda conjuntamente `block4-journal.sqlite` y su clave original sólo dentro
del límite local autorizado. Una copia sin la misma clave debe fallar cerrada.
