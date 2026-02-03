param(
    [switch]$NonInteractive
)

$ErrorActionPreference = "Stop"
$scriptPath = Join-Path $PSScriptRoot "start_frontend.ps1"
& $scriptPath -Environment development -NonInteractive:$NonInteractive
