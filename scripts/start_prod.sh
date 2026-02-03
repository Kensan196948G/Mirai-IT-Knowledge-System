#!/bin/bash
# ==================================================
# Mirai IT Knowledge System - Production Environment Starter
# 本番環境起動スクリプト (Linux)
# ==================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"$SCRIPT_DIR/start_backend.sh" --env production "$@"
