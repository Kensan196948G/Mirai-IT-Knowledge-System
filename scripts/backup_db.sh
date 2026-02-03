#!/bin/bash
# ==================================================
# Mirai IT Knowledge System - Database Backup
# DBバックアップスクリプト (Linux)
# ==================================================

set -e

ENVIRONMENT="development"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

ENV_FILE=".env.${ENVIRONMENT}"
if [ -f "$ENV_FILE" ]; then
    set -a
    source "$ENV_FILE"
    set +a
fi

if [ "$ENVIRONMENT" = "production" ]; then
    DB_PATH="${DATABASE_PATH:-db/knowledge.db}"
    BACKUP_DIR="${DATABASE_BACKUP_PATH:-backups/prod}"
else
    DB_PATH="${DATABASE_PATH:-db/knowledge_dev.db}"
    BACKUP_DIR="${DATABASE_BACKUP_PATH:-backups/dev}"
fi

if [ ! -f "$DB_PATH" ]; then
    echo "❌ DBが見つかりません: $DB_PATH" >&2
    exit 1
fi

mkdir -p "$BACKUP_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/knowledge_${ENVIRONMENT}_${TIMESTAMP}.db"

cp "$DB_PATH" "$BACKUP_FILE"
echo "✅ DBバックアップ完了: $BACKUP_FILE"
