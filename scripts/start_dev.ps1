# ==================================================
# Mirai IT Knowledge System - Development Environment Starter
# 開発環境起動スクリプト (Windows PowerShell)
# ==================================================

# エラー時は即座に終了
$ErrorActionPreference = "Stop"

# プロジェクトルート
$PROJECT_ROOT = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $PROJECT_ROOT

Write-Host "========================================" -ForegroundColor Blue
Write-Host "🚀 Mirai IT Knowledge System" -ForegroundColor Green
Write-Host "   開発環境起動中..." -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Blue

# 環境変数設定
$env:ENVIRONMENT = "development"
$env:FLASK_ENV = "development"
$env:FLASK_APP = "src/webui/app.py"

# 環境変数ファイル読み込み
if (Test-Path ".env.development") {
    Write-Host "✅ 環境変数ファイル読み込み: .env.development" -ForegroundColor Green
    Get-Content ".env.development" | ForEach-Object {
        if ($_ -match "^\s*([^#][^=]+)\s*=\s*(.+)\s*$") {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            Set-Item -Path "env:$name" -Value $value
        }
    }
} else {
    Write-Host "⚠️  警告: .env.development が見つかりません" -ForegroundColor Yellow
}

# Pythonバージョン確認
Write-Host "`n📊 システム情報" -ForegroundColor Blue
Write-Host "   Python: $(python --version)"
Write-Host "   プロジェクトルート: $PROJECT_ROOT"
Write-Host "   環境: $env:ENVIRONMENT"

# 必要なディレクトリ作成
Write-Host "`n📁 ディレクトリ確認" -ForegroundColor Blue
New-Item -ItemType Directory -Force -Path "db" | Out-Null
New-Item -ItemType Directory -Force -Path "data/logs/dev" | Out-Null
New-Item -ItemType Directory -Force -Path "data/knowledge" | Out-Null
New-Item -ItemType Directory -Force -Path "backups/dev" | Out-Null
Write-Host "✅ ディレクトリ作成完了" -ForegroundColor Green

# データベース存在確認
if (-not (Test-Path "db/knowledge_dev.db")) {
    Write-Host "`n⚠️  開発用データベースが存在しません" -ForegroundColor Yellow
    $response = Read-Host "データベースを初期化しますか？ (y/n)"
    if ($response -match "^[yY]") {
        Write-Host "データベース初期化中..." -ForegroundColor Green
        python scripts/init_db.py --env development --with-samples
    }
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
$PORT = 8888
$portInUse = Get-NetTCPConnection -LocalPort $PORT -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Host "`n⚠️  ポート $PORT は既に使用中です" -ForegroundColor Red
    Write-Host "既存のプロセスを終了してから再度実行してください" -ForegroundColor Yellow
    Get-NetTCPConnection -LocalPort $PORT | Format-Table
    exit 1
}

# SSL証明書確認
if (-not (Test-Path "/etc/ssl/mirai-knowledge/dev-cert.pem")) {
    Write-Host "`n⚠️  SSL証明書が見つかりません" -ForegroundColor Yellow
    Write-Host "Phase 3でSSL証明書を生成してください" -ForegroundColor Blue
    Write-Host "HTTPモードで起動します（SSL無効）" -ForegroundColor Yellow
    $env:SSL_ENABLED = "False"
}

# WebUI起動
Write-Host "`n========================================" -ForegroundColor Blue
Write-Host "🌐 WebUI起動中..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Blue
Write-Host "   アクセスURL: https://192.168.0.187:8888" -ForegroundColor Green
Write-Host "   ローカル: https://localhost:8888" -ForegroundColor Green
Write-Host "   終了: Ctrl+C" -ForegroundColor Yellow
Write-Host "========================================`n" -ForegroundColor Blue

# Flask実行
python src/webui/app.py
