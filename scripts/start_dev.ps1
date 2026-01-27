# ==================================================
# Mirai IT Knowledge System - Development Environment Starter
# 開発環境起動スクリプト (Windows PowerShell)
# ==================================================

param(
    [switch]$NonInteractive
)

$ErrorActionPreference = "Stop"
$scriptPath = Join-Path $PSScriptRoot "start_backend.ps1"
& $scriptPath -Environment development -NonInteractive:$NonInteractive
