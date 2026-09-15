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

Respalda conjuntamente `block4-journal.sqlite` y su clave original sólo dentro
del límite local autorizado. Una copia sin la misma clave debe fallar cerrada.
