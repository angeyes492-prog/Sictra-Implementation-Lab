$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '../telecare_launch_paths.ps1')
$scratch = Join-Path ([IO.Path]::GetTempPath()) ('telecare-launch-test-' + [guid]::NewGuid())
$null = New-Item -ItemType Directory -Path $scratch
try {
    $resolved = Resolve-TelecareLaunchPaths $scratch '' ''
    if ($resolved.IntakeStore -ne (Join-Path $scratch 'research-intake.json')) { throw 'Default path mismatch' }
    $intake = Join-Path $scratch 'legacy input.json'
    $design = Join-Path $scratch 'legacy trace.sqlite'
    $configPath = Join-Path $scratch 'launch-paths.json'
    @{schema='TELECARE_LOCAL_PATHS_V1';intake_store=$intake;design_trace=$design} | ConvertTo-Json | Set-Content -LiteralPath $configPath
    $resolved = Resolve-TelecareLaunchPaths $scratch '' ''
    if ($resolved.IntakeStore -ne $intake -or $resolved.DesignTrace -ne $design) { throw 'Legacy paths not preserved' }
    $override = Join-Path $scratch 'explicit.json'
    if ((Resolve-TelecareLaunchPaths $scratch $override '').IntakeStore -ne $override) { throw 'Explicit path ignored' }
    foreach ($bad in @('{"schema":"UNKNOWN"}', '{"schema":"TELECARE_LOCAL_PATHS_V1","intake_store":"relative","design_trace":"relative"}', 'broken-json')) {
        Set-Content -LiteralPath $configPath -Value $bad
        $rejected = $false
        try { $null = Resolve-TelecareLaunchPaths $scratch '' '' } catch { $rejected = $true }
        if (-not $rejected) { throw 'Invalid configuration silently fell back to new data' }
    }
    Write-Output 'PASS: default, legacy preservation, explicit override, invalid schema, relative paths, corrupt configuration'
} finally {
    # Delete only this test's explicitly created, validated temporary directory.
    $target = [IO.Path]::GetFullPath($scratch)
    $parent = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
    if ($target.StartsWith($parent) -and [IO.Path]::GetFileName($target).StartsWith('telecare-launch-test-')) {
        Remove-Item -LiteralPath $target -Recurse -Force
    }
}
