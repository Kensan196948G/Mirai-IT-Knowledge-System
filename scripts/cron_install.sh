#!/bin/bash
# ==================================================
# Mirai IT Knowledge System - Cron Installer
# cron登録スクリプト (Linux)
# ==================================================

set -e

ENVIRONMENT="production"
SCHEDULE="0 2 * * *"
RUN_USER="root"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --schedule)
            SCHEDULE="$2"
            shift 2
            ;;
        --user)
            RUN_USER="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

if [ "$EUID" -ne 0 ]; then
    echo "❌ このスクリプトはroot権限で実行する必要があります" >&2
    echo "   sudo $0 --env ${ENVIRONMENT}" >&2
    exit 1
fi

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$PROJECT_ROOT/data/logs/${ENVIRONMENT}"
mkdir -p "$LOG_DIR"

CRON_FILE="/etc/cron.d/mirai-knowledge-${ENVIRONMENT}"
COMMAND="$PROJECT_ROOT/scripts/backup_db.sh --env ${ENVIRONMENT} >> $LOG_DIR/backup.log 2>&1"

echo "# Mirai IT Knowledge System DB Backup (${ENVIRONMENT})" > "$CRON_FILE"
echo "${SCHEDULE} ${RUN_USER} ${COMMAND}" >> "$CRON_FILE"

chmod 644 "$CRON_FILE"
echo "✅ cron登録完了: $CRON_FILE"
