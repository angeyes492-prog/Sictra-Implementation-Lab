param([int]$Port = 8768, [switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
if (-not $env:LOCALAPPDATA) { throw 'LOCALAPPDATA no disponible.' }
$projectPath = $PSScriptRoot
$statePath = Join-Path $env:LOCALAPPDATA 'TelecareOS\Operations'
$pythonPath = (Get-Command python -ErrorAction Stop).Source
$env:PYTHONPATH = Join-Path $projectPath 'src'
& $pythonPath -m sictra_block4_orchestrator.operations --state $statePath init
if ($LASTEXITCODE -ne 0) { throw 'No se pudo verificar el estado local.' }
try {
    $currentService = Invoke-RestMethod "http://127.0.0.1:$Port/api/operations" -TimeoutSec 3
    if ($currentService.scope -ne 'LABORATORY_INTERNAL_SUPERVISED') { throw 'Servicio desconocido en el puerto.' }
} catch {
    $listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($listener) { throw "El puerto $Port está ocupado. Cierra la consola anterior o elige otro puerto con -Port." }
    $arguments = @('-m', 'sictra_block4_orchestrator.operations', '--state', ('"' + $statePath + '"'), 'serve', '--port', $Port)
    Start-Process -FilePath $pythonPath -ArgumentList $arguments -WorkingDirectory $projectPath -WindowStyle Hidden -RedirectStandardOutput (Join-Path $statePath 'service.stdout.log') -RedirectStandardError (Join-Path $statePath 'service.stderr.log')
    $ready = $false
    for ($attempt = 0; $attempt -lt 20; $attempt++) {
        Start-Sleep -Milliseconds 500
        try { $check = Invoke-RestMethod "http://127.0.0.1:$Port/api/operations" -TimeoutSec 2; $ready = $true; break } catch { }
    }
    if (-not $ready) { throw "El servicio no respondió. Revisa $statePath\service.stderr.log" }
}
if (-not $NoBrowser) { Start-Process "http://127.0.0.1:$Port/" }
Write-Output "Telecare OS disponible: http://127.0.0.1:$Port/"
