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
runtime laboratory.

## Run the Intelligence Workspace

On Windows PowerShell, from the repository root:

```powershell
$env:PYTHONPATH = "src"
python -m sictra_block1.lab_web --open
```

The tool opens on `http://127.0.0.1:8765/`. It requires Python 3.11 or newer
and no third-party runtime dependencies.

## Evidence boundary

The included investigations are synthetic. The workspace does not access the
internet, ingest company data, prove source truth, provide production security,
operate Blocks 2–4, or imply global gate acceptance.
