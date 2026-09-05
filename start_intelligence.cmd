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
if "%~1"=="" (
  echo Iniciando Intelligence Workspace en modo local...
  python -m sictra_block1.lab_web --open
) else (
  python -m sictra_block1.lab_web %*
)

if errorlevel 1 (
  echo.
  echo Intelligence Workspace no pudo iniciar. Revisa el mensaje anterior.
  pause
  exit /b 1
)
