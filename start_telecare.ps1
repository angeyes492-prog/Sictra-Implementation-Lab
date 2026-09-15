param([int]$Port = 8768, [switch]$NoBrowser,
    [string]$StatePath, [string]$IntakeStore, [string]$DesignTrace)
$ErrorActionPreference = 'Stop'
if ($Port -ne 8768) { throw 'La suite federada usa los puertos 8765–8768. Usa 8768 para conservar la navegación interna.' }
if (-not $env:LOCALAPPDATA) { throw 'LOCALAPPDATA no disponible.' }
$projectPath = $PSScriptRoot
$statePath = if ($StatePath) { [IO.Path]::GetFullPath($StatePath) } else { Join-Path $env:LOCALAPPDATA 'TelecareOS\Operations' }
if (-not $IntakeStore) { $IntakeStore = Join-Path $statePath 'research-intake.json' }
if (-not $DesignTrace) { $DesignTrace = Join-Path $statePath 'design-console.sqlite' }
$pythonPath = (Get-Command python -ErrorAction Stop).Source
$env:PYTHONPATH = Join-Path $projectPath 'src'
& $pythonPath -m sictra_block4_orchestrator.operations --state $statePath init
if ($LASTEXITCODE -ne 0) { throw 'No se pudo verificar el estado local.' }
function Start-VerifiedBlock([int]$BlockPort, [string[]]$Arguments, [string]$HtmlPath, [string]$LogName) {
    $expected = [IO.File]::ReadAllText((Join-Path $projectPath $HtmlPath))
    $listener = Get-NetTCPConnection -LocalPort $BlockPort -State Listen -ErrorAction SilentlyContinue
    if (-not $listener) {
        Start-Process -FilePath $pythonPath -ArgumentList $Arguments -WorkingDirectory $projectPath -WindowStyle Hidden -RedirectStandardOutput (Join-Path $statePath "$LogName.stdout.log") -RedirectStandardError (Join-Path $statePath "$LogName.stderr.log")
    }
    $ready = $false
    for ($attempt = 0; $attempt -lt 20; $attempt++) {
        try { $page = Invoke-WebRequest "http://127.0.0.1:$BlockPort/" -TimeoutSec 2; $ready = $true; break } catch { Start-Sleep -Milliseconds 250 }
    }
    if (-not $ready) { throw "El bloque en $BlockPort no respondió. Revisa $statePath\$LogName.stderr.log" }
    if ($page.Content -cne $expected) { throw "Otra versión ocupa el puerto $BlockPort. No se abrió una interfaz antigua: actualiza o reinicia ese bloque desde esta misma instalación." }
}
Start-VerifiedBlock $Port @('-m','sictra_block4_orchestrator.operations','--state',('"'+$statePath+'"'),'serve','--port',$Port) 'src/sictra_block4_orchestrator/command_center/index.html' 'service'
Start-VerifiedBlock 8765 @('-m','sictra_block1.lab_web','--port','8765','--intake-store',('"'+$IntakeStore+'"'),'--pipeline-state',('"'+(Join-Path $statePath 'pipeline')+'"')) 'src/sictra_block1/web/index.html' 'intelligence'
Start-VerifiedBlock 8766 @('-m','sictra_block2_design.design_console_web','--port','8766','--trace-db',('"'+$DesignTrace+'"'),'--operations-state',('"'+$statePath+'"')) 'src/sictra_block2_design/design_console/index.html' 'design'
Start-VerifiedBlock 8767 @('-m','sictra_block3_precision.precision_console_web','--port','8767','--operations-state',('"'+$statePath+'"')) 'src/sictra_block3_precision/precision_console/index.html' 'precision'
$currentService = Invoke-RestMethod "http://127.0.0.1:$Port/api/operations" -TimeoutSec 5
if ($currentService.scope -ne 'LABORATORY_INTERNAL_SUPERVISED') { throw 'Servicio fuera del alcance local.' }
if ($currentService.watch_directory -ne (Join-Path $statePath 'dropbox')) { throw 'El servicio abierto usa otra carpeta de datos. No se mezclaron los estados.' }
$intelligenceHealth = Invoke-RestMethod 'http://127.0.0.1:8765/health' -TimeoutSec 5
if ($intelligenceHealth.pipeline_reader -ne 'AVAILABLE') { throw 'Intelligence no tiene la cadena retenida conectada. Revisa su arranque --pipeline-state.' }
foreach ($readerPort in @(8766,8767)) {
    $projection = Invoke-RestMethod "http://127.0.0.1:$readerPort/api/review-artifacts" -TimeoutSec 10
    if ($projection.status -ne 'AVAILABLE') { throw "El lector de artefactos en $readerPort no está conectado." }
}
if (-not $NoBrowser) { Start-Process "http://127.0.0.1:$Port/" }
Write-Output "Telecare OS disponible: http://127.0.0.1:$Port/"
