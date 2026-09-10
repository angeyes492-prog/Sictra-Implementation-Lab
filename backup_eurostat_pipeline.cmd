@echo off
setlocal
title Telecare OS - Respaldo de cadena Eurostat
cd /d "%~dp0"

if "%LOCALAPPDATA%"=="" (
  echo No se encontro LOCALAPPDATA.
  pause
  exit /b 1
)

set "PYTHONPATH=%CD%\src"
set "SICTRA_PIPELINE_STATE=%LOCALAPPDATA%\TelecareOS\Intelligence\pipeline"
for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss"`) do set "SICTRA_BACKUP_STAMP=%%I"
set "SICTRA_BACKUP_TARGET=%LOCALAPPDATA%\TelecareOS\Intelligence\backups\pipeline-%SICTRA_BACKUP_STAMP%"

python -m sictra_block1.operator_pipeline backup "%SICTRA_PIPELINE_STATE%" "%SICTRA_BACKUP_TARGET%"
if errorlevel 1 (
  echo.
  echo No se pudo crear el respaldo. El estado actual no fue modificado.
  pause
  exit /b 1
)

echo.
echo Respaldo creado en:
echo %SICTRA_BACKUP_TARGET%
echo No incluye claves ni historial SQLite de ejecucion. Conserva el estado original.
pause
