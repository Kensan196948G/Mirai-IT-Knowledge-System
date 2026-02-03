# ==================================================
# Mirai IT Knowledge System - Backend Starter
# バックエンド起動スクリプト (Windows PowerShell)
# ==================================================

param(
    [ValidateSet('development', 'production')]
    [string]$Environment = 'development',
    [switch]$NonInteractive
)

$ErrorActionPreference = "Stop"

function Load-EnvFile {
    param([string]$Path)
    if (Test-Path $Path) {
        Write-Host "✅ 環境変数ファイル読み込み: $Path" -ForegroundColor Green
        Get-Content $Path | ForEach-Object {
            if ($_ -match "^\s*([^#][^=]+)\s*=\s*(.+)\s*$") {
                $name = $matches[1].Trim()
                $value = $matches[2].Trim()
                Set-Item -Path "env:$name" -Value $value
            }
        }
    } else {
        Write-Host "⚠️  警告: $Path が見つかりません" -ForegroundColor Yellow
    }
}

function Get-PrimaryIPv4 {
    $ip = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
        Where-Object { $_.IPAddress -notlike '169.254*' -and $_.IPAddress -ne '127.0.0.1' } |
        Select-Object -First 1
    if ($ip) { return $ip.IPAddress }
    return '127.0.0.1'
}

# プロジェクトルート
$PROJECT_ROOT = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $PROJECT_ROOT

Write-Host "========================================" -ForegroundColor Blue
Write-Host "🚀 Mirai IT Knowledge System" -ForegroundColor Green
Write-Host "   バックエンド起動中..." -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Blue

# 環境変数設定
$env:ENVIRONMENT = $Environment
$env:FLASK_ENV = $Environment
$env:FLASK_APP = "src/webui/app.py"
if (-not $env:PYTHONPATH) {
    $env:PYTHONPATH = $PROJECT_ROOT
}

# 環境変数ファイル読み込み
$envFile = ".env.$Environment"
Load-EnvFile $envFile

# HOST/PORTの決定
if (-not $env:PORT) {
    $env:PORT = if ($Environment -eq 'production') { "5000" } else { "8888" }
}
if (-not $env:HOST -or $env:HOST -eq '0.0.0.0' -or $env:HOST -eq 'localhost') {
    $env:HOST = Get-PrimaryIPv4
}

$PORT = [int]$env:PORT
$HOSTNAME = $env:HOST

# Pythonバージョン確認
Write-Host "`n📊 システム情報" -ForegroundColor Blue
Write-Host "   Python: $(python --version)"
Write-Host "   プロジェクトルート: $PROJECT_ROOT"
Write-Host "   環境: $env:ENVIRONMENT"

# 必要なディレクトリ作成
Write-Host "`n📁 ディレクトリ確認" -ForegroundColor Blue
New-Item -ItemType Directory -Force -Path "db" | Out-Null
New-Item -ItemType Directory -Force -Path "data/knowledge" | Out-Null
if ($Environment -eq 'production') {
    New-Item -ItemType Directory -Force -Path "data/logs/prod" | Out-Null
    New-Item -ItemType Directory -Force -Path "backups/prod" | Out-Null
} else {
    New-Item -ItemType Directory -Force -Path "data/logs/dev" | Out-Null
    New-Item -ItemType Directory -Force -Path "backups/dev" | Out-Null
}
Write-Host "✅ ディレクトリ作成完了" -ForegroundColor Green

# データベース存在確認
$dbPath = if ($Environment -eq 'production') { "db/knowledge.db" } else { "db/knowledge_dev.db" }
if (-not (Test-Path $dbPath)) {
    if ($Environment -eq 'production') {
        Write-Host "`n❌ 本番用データベースが存在しません" -ForegroundColor Red
        Write-Host "データベースを初期化してください:" -ForegroundColor Yellow
        Write-Host "   python scripts/init_db.py --env production --no-samples" -ForegroundColor Blue
        exit 1
    }

    Write-Host "`n⚠️  開発用データベースが存在しません" -ForegroundColor Yellow
    if ($NonInteractive) {
        Write-Host "非対話モードのため初期化はスキップします" -ForegroundColor Yellow
        exit 1
    }

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
$portInUse = Get-NetTCPConnection -LocalPort $PORT -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Host "`n⚠️  ポート $PORT は既に使用中です" -ForegroundColor Red
    Write-Host "既存のプロセスを終了してから再度実行してください" -ForegroundColor Yellow
    Get-NetTCPConnection -LocalPort $PORT | Format-Table
    exit 1
}

# SSL証明書確認
$sslEnabled = $true
if ($env:SSL_ENABLED) {
    $sslEnabled = $env:SSL_ENABLED.ToLower() -in @('true', '1', 'yes', 'on')
}

$sslCert = $env:SSL_CERT
$sslKey = $env:SSL_KEY
if ($sslEnabled) {
    if (-not $sslCert -or -not (Test-Path $sslCert) -or -not $sslKey -or -not (Test-Path $sslKey)) {
        if ($Environment -eq 'production') {
            Write-Host "`n❌ SSL証明書が見つかりません" -ForegroundColor Red
            Write-Host "本番環境ではSSL証明書が必須です" -ForegroundColor Yellow
            exit 1
        }
        Write-Host "`n⚠️  SSL証明書が見つかりません" -ForegroundColor Yellow
        Write-Host "HTTPモードで起動します（SSL無効）" -ForegroundColor Yellow
        $sslEnabled = $false
        $env:SSL_ENABLED = "False"
    }
}

# WebUI起動
$protocol = if ($sslEnabled) { "https" } else { "http" }
Write-Host "`n========================================" -ForegroundColor Blue
Write-Host "🌐 WebUI起動中..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Blue
Write-Host ("   アクセスURL: {0}://{1}:{2}" -f $protocol, $HOSTNAME, $PORT) -ForegroundColor Green
Write-Host ("   ローカル: {0}://localhost:{1}" -f $protocol, $PORT) -ForegroundColor Green
Write-Host "   終了: Ctrl+C" -ForegroundColor Yellow
Write-Host "========================================`n" -ForegroundColor Blue

# Flask実行
python src/webui/app.py
