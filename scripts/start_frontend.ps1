# ==================================================
# Mirai IT Knowledge System - Frontend Starter
# フロントエンド起動スクリプト (Windows PowerShell)
# ==================================================

param(
    [ValidateSet('development', 'production')]
    [string]$Environment = 'development',
    [switch]$NonInteractive
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "start_backend.ps1"
Write-Host "🖥️  フロントエンドはWebUI（Flask）で提供されます" -ForegroundColor Yellow
Write-Host "    バックエンド起動によりフロントエンドも利用可能です" -ForegroundColor Yellow
& $scriptPath -Environment $Environment -NonInteractive:$NonInteractive
