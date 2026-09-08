@echo off
setlocal
title Telecare OS - Importar fuente Eurostat
cd /d "%~dp0"

if "%~1"=="" (
  echo Arrastra un archivo XLSX de Eurostat sobre este archivo.
  echo Solo procesa la seleccion aprobada tran_r_mago_nm; no descarga nada de internet.
  pause
  exit /b 1
)
if "%LOCALAPPDATA%"=="" (
  echo No se encontro LOCALAPPDATA; no es seguro crear claves dentro del proyecto.
  pause
  exit /b 1
)

set "PYTHONPATH=%CD%\src"
set "SICTRA_PIPELINE_STATE=%LOCALAPPDATA%\TelecareOS\Intelligence\pipeline"
python -m sictra_block1.operator_pipeline init "%SICTRA_PIPELINE_STATE%"
if errorlevel 1 exit /b 1
python -m sictra_block1.operator_pipeline ingest "%SICTRA_PIPELINE_STATE%" "%~1" --geo-level COUNTRY
if errorlevel 1 (
  echo.
  echo La importacion fue detenida. No se publico ningun contenido.
  pause
  exit /b 1
)

echo.
echo Importacion terminada. Una linea base no es un insight ni un dossier.
pause
