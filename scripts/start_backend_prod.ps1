param(
    [switch]$NonInteractive
)

$ErrorActionPreference = "Stop"
$scriptPath = Join-Path $PSScriptRoot "start_backend.ps1"
& $scriptPath -Environment production -NonInteractive:$NonInteractive
