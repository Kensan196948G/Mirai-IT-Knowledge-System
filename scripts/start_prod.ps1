# ==================================================
# Mirai IT Knowledge System - Production Environment Starter
# 本番環境起動スクリプト (Windows PowerShell)
# ==================================================

# エラー時は即座に終了
$ErrorActionPreference = "Stop"

# プロジェクトルート
$PROJECT_ROOT = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $PROJECT_ROOT

Write-Host "========================================" -ForegroundColor Blue
Write-Host "🚀 Mirai IT Knowledge System" -ForegroundColor Green
Write-Host "   本番環境起動中..." -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Blue

# 環境変数設定
$env:ENVIRONMENT = "production"
$env:FLASK_ENV = "production"
$env:FLASK_APP = "src/webui/app.py"

# 環境変数ファイル読み込み
if (Test-Path ".env.production") {
    Write-Host "✅ 環境変数ファイル読み込み: .env.production" -ForegroundColor Green
    Get-Content ".env.production" | ForEach-Object {
        if ($_ -match "^\s*([^#][^=]+)\s*=\s*(.+)\s*$") {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            Set-Item -Path "env:$name" -Value $value
        }
    }
} else {
    Write-Host "⚠️  警告: .env.production が見つかりません" -ForegroundColor Yellow
}

# Pythonバージョン確認
Write-Host "`n📊 システム情報" -ForegroundColor Blue
Write-Host "   Python: $(python --version)"
Write-Host "   プロジェクトルート: $PROJECT_ROOT"
Write-Host "   環境: $env:ENVIRONMENT"

# 必要なディレクトリ作成
Write-Host "`n📁 ディレクトリ確認" -ForegroundColor Blue
New-Item -ItemType Directory -Force -Path "db" | Out-Null
New-Item -ItemType Directory -Force -Path "data/logs/prod" | Out-Null
New-Item -ItemType Directory -Force -Path "data/knowledge" | Out-Null
New-Item -ItemType Directory -Force -Path "backups/prod" | Out-Null
Write-Host "✅ ディレクトリ作成完了" -ForegroundColor Green

# データベース存在確認
if (-not (Test-Path "db/knowledge.db")) {
    Write-Host "`n❌ 本番用データベースが存在しません" -ForegroundColor Red
    Write-Host "データベースを初期化してください:" -ForegroundColor Yellow
    Write-Host "   python scripts/init_db.py --env production --no-samples" -ForegroundColor Blue
    exit 1
}

# 依存パッケージ確認
Write-Host "`n📦 依存パッケージ確認" -ForegroundColor Blue
try {
    python -c "import flask; import dotenv" 2>$null
    Write-Host "✅ 必要なパッケージがインストールされています" -ForegroundColor Green
} catch {
    Write-Host "❌ 必要なパッケージがインストールされていません" -ForegroundColor Red
    Write-Host "pip install -r requirements.txt を実行してください" -ForegroundColor Yellow
    exit 1
}

# ポート使用確認
$PORT = 5000
$portInUse = Get-NetTCPConnection -LocalPort $PORT -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Host "`n⚠️  ポート $PORT は既に使用中です" -ForegroundColor Red
    Write-Host "既存のプロセスを終了してから再度実行してください" -ForegroundColor Yellow
    Get-NetTCPConnection -LocalPort $PORT | Format-Table
    exit 1
}

# SSL証明書確認（本番環境では必須）
if (-not (Test-Path "/etc/ssl/mirai-knowledge/prod-cert.pem")) {
    Write-Host "`n❌ SSL証明書が見つかりません" -ForegroundColor Red
    Write-Host "本番環境ではSSL証明書が必須です" -ForegroundColor Yellow
    Write-Host "Phase 3でSSL証明書を生成してください" -ForegroundColor Blue
    exit 1
}

# セキュリティチェック
if (($env:SECRET_KEY -eq "default-secret-key-change-me") -or ($env:SECRET_KEY -eq "CHANGE_THIS_TO_RANDOM_SECRET_KEY_IN_PRODUCTION")) {
    Write-Host "`n⚠️  セキュリティ警告: SECRET_KEYがデフォルト値です" -ForegroundColor Red
    Write-Host "本番環境では必ずランダムなSECRET_KEYに変更してください" -ForegroundColor Yellow
    $response = Read-Host "続行しますか？ (y/n)"
    if ($response -notmatch "^[yY]") {
        exit 1
    }
}

# WebUI起動
Write-Host "`n========================================" -ForegroundColor Blue
Write-Host "🌐 WebUI起動中..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Blue
Write-Host "   アクセスURL: https://192.168.0.187:5000" -ForegroundColor Green
Write-Host "   ローカル: https://localhost:5000" -ForegroundColor Green
Write-Host "   終了: Ctrl+C" -ForegroundColor Yellow
Write-Host "========================================`n" -ForegroundColor Blue

# Flask実行
python src/webui/app.py
