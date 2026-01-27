# ==================================================
# Mirai IT Knowledge System - Production Environment Starter
# 本番環境起動スクリプト (Windows PowerShell)
# ==================================================

param(
    [switch]$NonInteractive
)

$ErrorActionPreference = "Stop"
$scriptPath = Join-Path $PSScriptRoot "start_backend.ps1"
& $scriptPath -Environment production -NonInteractive:$NonInteractive
