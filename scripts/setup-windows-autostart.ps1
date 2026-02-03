# Mirai IT Knowledge System - Windows自動起動設定スクリプト
# このスクリプトはWindows PowerShellで管理者権限で実行してください

$TaskName = "Mirai-Knowledge-System-AutoStart"
$Description = "Windows起動時にWSLとMirai IT Knowledge Systemサービスを自動起動"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Mirai IT Knowledge System" -ForegroundColor Green
Write-Host "Windows自動起動設定" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 既存のタスクを削除（存在する場合）
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "既存のタスクを削除中..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# タスクスケジューラのアクション
$Action = New-ScheduledTaskAction -Execute "wsl.exe" `
    -Argument "-d Ubuntu -u kensan -- bash -c 'sudo systemctl start mirai-knowledge-dev'"

# トリガー（ログオン時）
$Trigger = New-ScheduledTaskTrigger -AtLogOn

# 設定
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable `
    -DontStopOnIdleEnd

# プリンシパル（現在のユーザー）
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive

# タスク登録
Write-Host "タスクスケジューラに登録中..." -ForegroundColor Yellow
Register-ScheduledTask `
    -TaskName $TaskName `
    -Description $Description `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Principal $Principal `
    -Force

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ 設定完了" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📝 設定内容:" -ForegroundColor Yellow
Write-Host "  タスク名: $TaskName"
Write-Host "  トリガー: ユーザーログオン時"
Write-Host "  動作: WSLを起動してmirai-knowledge-devサービスを開始"
Write-Host ""
Write-Host "🔧 管理コマンド:" -ForegroundColor Yellow
Write-Host "  タスク一覧: Get-ScheduledTask -TaskName '$TaskName'"
Write-Host "  手動実行: Start-ScheduledTask -TaskName '$TaskName'"
Write-Host "  無効化: Disable-ScheduledTask -TaskName '$TaskName'"
Write-Host "  有効化: Enable-ScheduledTask -TaskName '$TaskName'"
Write-Host "  削除: Unregister-ScheduledTask -TaskName '$TaskName'"
Write-Host ""
Write-Host "⚠️ 注意事項:" -ForegroundColor Red
Write-Host "  WSL内でsudoパスワード不要の設定が必要です"
Write-Host "  詳細は setup-sudo-nopasswd.sh を実行してください"
Write-Host ""
