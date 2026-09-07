# Telecare OS — Implementation Lab

This repository hosts versioned implementation artifacts for Telecare OS. Its
first block is SICTrA / Intelligence.

## System model

Telecare OS is composed of four blocks: Intelligence, Design, Precision, and a
Master Orchestrator that will govern their eventual collaboration. See
[`architecture/telecare_os_block_model_v1.md`](architecture/telecare_os_block_model_v1.md).

## Current scope

Block 1 includes a bounded E01–E08 runtime and a local Intelligence Workspace
for field-testing the logistics research workflow. The workspace exposes
global, regional, and local synthetic investigations; an Evidence Spine;
multi-objective strategy comparison; 7/30/90 watchlists; and the adversarial
runtime laboratory. It now also includes governed source readiness, the
Global → Segment → Account interpretation model, and a weekly Editorial Engine
with evidence eligibility, Pareto shortlist, reasoned human selection,
explicit abstention, and a bounded Block 2 handoff candidate.
The backend also has a read-only bridge for durable signed dossiers. The
ordinary Windows launcher initializes its ignored single-user key/store layout;
this is local integrity configuration, not production secret management.

## Run the Intelligence Workspace

### Windows — sin usar comandos

1. Abre la carpeta del proyecto.
2. Haz doble clic en `start_intelligence.cmd`.
3. La primera ejecución crea claves locales aleatorias fuera del proyecto, en
   `%LOCALAPPDATA%\TelecareOS\Intelligence\operator`; no las compartas.
4. Espera a que el navegador abra `http://127.0.0.1:8765/`.
5. Entra en **Dossiers** para comprobar el lector firmado. Un almacén válido
   pero vacío es el resultado esperado hasta registrar dos versiones.
6. Entra en **Mesa editorial** para revisar la lista corta sintética.
7. Escribe tu razonamiento y elige una pieza insignia, o registra que ninguna
   debe avanzar esa semana.
8. Entra en **Investigaciones** para guardar una pregunta propia como
   **borrador local**. No pegues secretos ni datos personales: la referencia
   opcional no se consulta ni se convierte en evidencia.

Mantén abierta la ventana de inicio mientras utilizas la herramienta. Para
detenerla, ciérrala o presiona `Ctrl+C`.

### Respaldo y restauración local

1. Cierra Intelligence Workspace antes de respaldar.
2. Haz doble clic en `backup_intelligence.cmd`; se crea una carpeta fechada en
   `%LOCALAPPDATA%\TelecareOS\Intelligence\backups`.
3. El respaldo contiene el ledger de dossiers y su digest, nunca las claves.
4. Para restaurar después de perder únicamente `dossiers.json`, arrastra la
   carpeta fechada sobre `restore_intelligence.cmd`.

La restauración no reemplaza datos actuales y solo funciona con las claves
originales. Por eso es recuperación local ante pérdida accidental, no un
respaldo de desastre ni recuperación de claves.

### PowerShell

On Windows PowerShell, from the repository root:

```powershell
$env:PYTHONPATH = "src"
python -m sictra_block1.lab_web --open
```

The tool opens on `http://127.0.0.1:8765/`. It requires Python 3.11 or newer
and no third-party runtime dependencies.

## Evidence boundary

The included investigations are synthetic. The Workspace can persist a local
operator-declared research question, but it does not access the internet,
ingest company data, prove source truth, provide production security, operate
Blocks 2–4, or imply global gate acceptance.
