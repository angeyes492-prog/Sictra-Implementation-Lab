param([int]$Port = 8768)
$ErrorActionPreference = 'Stop'
$launcher = Join-Path $PSScriptRoot 'start_telecare.ps1'
if (-not (Test-Path -LiteralPath $launcher)) { throw 'No se encontro el iniciador de Telecare OS.' }
$taskName = 'TelecareOS-LocalOperations'
$existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
$argument = '-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "' + $launcher + '" -NoBrowser -Port ' + $Port
if ($existing -and ($existing.Actions.Arguments -notcontains $argument)) {
    throw 'Ya existe una tarea con otra configuracion. No se sobrescribio.'
}
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument $argument -WorkingDirectory $PSScriptRoot
$trigger = New-ScheduledTaskTrigger -AtLogOn -User ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name)
$principal = New-ScheduledTaskPrincipal -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit (New-TimeSpan -Minutes 5)
if (-not $existing) {
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description 'Inicia el servicio local supervisado de Telecare OS al entrar a Windows. No publica ni contacta.' | Out-Null
}
Start-ScheduledTask -TaskName $taskName
Get-ScheduledTask -TaskName $taskName | Select-Object TaskName, State
