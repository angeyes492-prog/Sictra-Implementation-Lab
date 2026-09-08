@echo off
setlocal
title Telecare OS - Restaurar cadena Eurostat
cd /d "%~dp0"

if "%~1"=="" (
  echo Arrastra una carpeta de respaldo sobre restore_eurostat_pipeline.cmd.
  echo La restauracion se niega a reemplazar cualquier ledger actual.
  pause
  exit /b 1
)
if "%LOCALAPPDATA%"=="" (
  echo No se encontro LOCALAPPDATA.
  pause
  exit /b 1
)

set "PYTHONPATH=%CD%\src"
set "SICTRA_PIPELINE_STATE=%LOCALAPPDATA%\TelecareOS\Intelligence\pipeline"
python -m sictra_block1.operator_pipeline restore "%SICTRA_PIPELINE_STATE%" "%~1"
if errorlevel 1 (
  echo.
  echo Restauracion detenida. Ningun ledger actual fue reemplazado.
  pause
  exit /b 1
)

echo.
echo Restauracion verificada. Abre Intelligence Workspace para revisar el estado.
pause
