@echo off
setlocal
title Telecare OS - Restaurar Intelligence
cd /d "%~dp0"

if "%~1"=="" (
  echo Arrastra una carpeta de respaldo sobre restore_intelligence.cmd.
  echo La restauracion nunca reemplaza un dossier actual.
  pause
  exit /b 1
)
if "%LOCALAPPDATA%"=="" (
  echo No se encontro LOCALAPPDATA.
  pause
  exit /b 1
)

set "PYTHONPATH=%CD%\src"
set "SICTRA_OPERATOR_STATE=%LOCALAPPDATA%\TelecareOS\Intelligence\operator"
python -m sictra_block1.operator_workspace restore "%SICTRA_OPERATOR_STATE%" "%~1"
if errorlevel 1 (
  echo.
  echo Restauracion detenida. El estado actual no fue reemplazado.
  pause
  exit /b 1
)

echo.
echo Restauracion verificada. Ya puedes iniciar Intelligence Workspace.
pause

