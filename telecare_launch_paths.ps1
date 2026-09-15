function Resolve-TelecareLaunchPaths([string]$Root, [string]$Intake, [string]$Design) {
    $configPath = Join-Path $Root 'launch-paths.json'
    $config = $null
    if (Test-Path -LiteralPath $configPath) {
        $config = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json
        if (-not $config -or (($config.PSObject.Properties.Name | Sort-Object) -join ',') -cne 'design_trace,intake_store,schema' -or $config.schema -cne 'TELECARE_LOCAL_PATHS_V1') {
            throw 'Configuración de rutas inválida. No se sustituyeron los datos.'
        }
        foreach ($value in @($config.intake_store, $config.design_trace)) {
            if ($value -isnot [string] -or -not [IO.Path]::IsPathRooted($value) -or $value -match '["\r\n]') {
                throw 'La configuración necesita rutas absolutas válidas.'
            }
        }
    }
    if (-not $Intake) { $Intake = if ($config) { $config.intake_store } else { Join-Path $Root 'research-intake.json' } }
    if (-not $Design) { $Design = if ($config) { $config.design_trace } else { Join-Path $Root 'design-console.sqlite' } }
    return @{ IntakeStore = $Intake; DesignTrace = $Design }
}
