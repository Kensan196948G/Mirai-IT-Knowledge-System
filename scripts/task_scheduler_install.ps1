# ==================================================
# Mirai IT Knowledge System - Task Scheduler Installer
# タスクスケジューラ登録スクリプト (Windows PowerShell)
# ==================================================

param(
    [ValidateSet('development', 'production', 'all')]
    [string]$Environment = 'production',
    [ValidateSet('backend', 'frontend', 'all')]
    [string]$Component = 'backend',
    [ValidateSet('AtStartup', 'AtLogon')]
    [string]$Trigger = 'AtStartup',
    [string]$TaskUser = 'SYSTEM'
)

$ErrorActionPreference = "Stop"

function Register-Task {
    param(
        [string]$TaskName,
        [string]$ScriptPath
    )

    $triggerArg = if ($Trigger -eq 'AtLogon') { '/SC ONLOGON' } else { '/SC ONSTART' }
    $taskAction = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`" -NonInteractive"

    schtasks.exe /Create /TN $TaskName /TR $taskAction $triggerArg /RU $TaskUser /F | Out-Null
    Write-Host "✅ タスク登録完了: $TaskName" -ForegroundColor Green
}

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

$envs = if ($Environment -eq 'all') { @('development', 'production') } else { @($Environment) }
$components = if ($Component -eq 'all') { @('backend', 'frontend') } else { @($Component) }

foreach ($env in $envs) {
    foreach ($comp in $components) {
        $scriptName = switch ($comp) {
            'backend' { if ($env -eq 'production') { 'start_backend_prod.ps1' } else { 'start_backend_dev.ps1' } }
            'frontend' { if ($env -eq 'production') { 'start_frontend_prod.ps1' } else { 'start_frontend_dev.ps1' } }
        }

        $scriptPath = Join-Path $scriptRoot $scriptName
        if (-not (Test-Path $scriptPath)) {
            Write-Host "⚠️  スクリプトが見つかりません: $scriptPath" -ForegroundColor Yellow
            continue
        }

        $taskName = "MiraiKnowledge-$comp-$env"
        Register-Task -TaskName $taskName -ScriptPath $scriptPath
    }
}
