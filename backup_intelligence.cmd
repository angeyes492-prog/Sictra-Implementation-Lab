@echo off
setlocal
title Telecare OS - Backup de Intelligence
cd /d "%~dp0"

if "%LOCALAPPDATA%"=="" (
  echo No se encontro LOCALAPPDATA.
  pause
  exit /b 1
)

set "PYTHONPATH=%CD%\src"
set "SICTRA_OPERATOR_STATE=%LOCALAPPDATA%\TelecareOS\Intelligence\operator"
for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss"`) do set "SICTRA_BACKUP_STAMP=%%I"
set "SICTRA_BACKUP_TARGET=%LOCALAPPDATA%\TelecareOS\Intelligence\backups\%SICTRA_BACKUP_STAMP%"

python -m sictra_block1.operator_workspace backup "%SICTRA_OPERATOR_STATE%" "%SICTRA_BACKUP_TARGET%"
if errorlevel 1 (
  echo.
  echo No se pudo crear el respaldo. No se modifico el estado actual.
  pause
  exit /b 1
)

echo.
echo Respaldo de datos creado en:
echo %SICTRA_BACKUP_TARGET%
echo Las claves NO fueron copiadas. Conserva el estado de operador original.
pause

