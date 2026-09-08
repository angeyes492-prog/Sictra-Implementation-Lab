@echo off
setlocal
title Telecare OS - Intelligence Workspace
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo No se encontro Python. Instala Python 3.11 o superior y vuelve a intentar.
  pause
  exit /b 1
)

set "PYTHONPATH=%CD%\src"
if "%LOCALAPPDATA%"=="" (
  echo No se encontro LOCALAPPDATA; no es seguro crear claves dentro del proyecto.
  pause
  exit /b 1
)
set "SICTRA_OPERATOR_STATE=%LOCALAPPDATA%\TelecareOS\Intelligence\operator"
set "SICTRA_PIPELINE_STATE=%LOCALAPPDATA%\TelecareOS\Intelligence\pipeline"
echo Verificando el estado local firmado...
python -m sictra_block1.operator_workspace init "%SICTRA_OPERATOR_STATE%"
if errorlevel 1 (
  echo.
  echo No se pudo preparar el estado protegido de Intelligence Workspace.
  pause
  exit /b 1
)
python -m sictra_block1.operator_pipeline init "%SICTRA_PIPELINE_STATE%"
if errorlevel 1 (
  echo.
  echo No se pudo preparar la cadena local de fuentes de Intelligence.
  pause
  exit /b 1
)

echo Iniciando Intelligence Workspace en modo local...
if "%~1"=="" (
  python -m sictra_block1.lab_web --operator-state "%SICTRA_OPERATOR_STATE%" --pipeline-state "%SICTRA_PIPELINE_STATE%" --open
) else (
  python -m sictra_block1.lab_web --operator-state "%SICTRA_OPERATOR_STATE%" --pipeline-state "%SICTRA_PIPELINE_STATE%" %*
)

if errorlevel 1 (
  echo.
  echo Intelligence Workspace no pudo iniciar. Revisa el mensaje anterior.
  pause
  exit /b 1
)
