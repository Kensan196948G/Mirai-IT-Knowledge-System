#!/bin/bash
# ==================================================
# Mirai IT Knowledge System - Backend Starter
# バックエンド起動スクリプト (Linux)
# ==================================================

set -e

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

ENVIRONMENT="development"
NON_INTERACTIVE=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --non-interactive)
            NON_INTERACTIVE=1
            shift
            ;;
        *)
            shift
            ;;
    esac
done

# プロジェクトルート
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

function load_env_file() {
    local env_file="$1"
    if [ -f "$env_file" ]; then
        echo -e "${GREEN}✅ 環境変数ファイル読み込み: ${env_file}${NC}"
        set -a
        source "$env_file"
        set +a
    else
        echo -e "${YELLOW}⚠️  警告: ${env_file} が見つかりません${NC}"
    fi
}

function resolve_host() {
    if [ -n "$HOST" ] && [ "$HOST" != "0.0.0.0" ] && [ "$HOST" != "localhost" ]; then
        echo "$HOST"
        return
    fi
    local ip
    ip=$(hostname -I 2>/dev/null | awk '{print $1}')
    if [ -z "$ip" ]; then
        ip="127.0.0.1"
    fi
    echo "$ip"
}

function parse_bool() {
    local value
    value=$(echo "$1" | tr '[:upper:]' '[:lower:]')
    case "$value" in
        true|1|yes|on) echo "1" ;;
        *) echo "0" ;;
    esac
}

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}🚀 Mirai IT Knowledge System${NC}"
echo -e "${YELLOW}   バックエンド起動中...${NC}"
echo -e "${BLUE}========================================${NC}"

# 環境変数設定
export ENVIRONMENT="$ENVIRONMENT"
export FLASK_ENV="$ENVIRONMENT"
export FLASK_APP="src/webui/app.py"
export PYTHONPATH="${PYTHONPATH:-$PROJECT_ROOT}"

# 環境変数ファイル読み込み
load_env_file ".env.${ENVIRONMENT}"

# HOST/PORT決定
if [ -z "$PORT" ]; then
    if [ "$ENVIRONMENT" = "production" ]; then
        PORT=5000
    else
        PORT=8888
    fi
fi
export PORT
HOST=$(resolve_host)
export HOST

# Pythonバージョン確認
echo -e "\n${BLUE}📊 システム情報${NC}"
echo -e "   Python: $(python3 --version)"
echo -e "   プロジェクトルート: $PROJECT_ROOT"
echo -e "   環境: ${ENVIRONMENT}"

# 必要なディレクトリ作成
echo -e "\n${BLUE}📁 ディレクトリ確認${NC}"
mkdir -p db
mkdir -p data/knowledge
if [ "$ENVIRONMENT" = "production" ]; then
    mkdir -p data/logs/prod
    mkdir -p backups/prod
else
    mkdir -p data/logs/dev
    mkdir -p backups/dev
fi
echo -e "${GREEN}✅ ディレクトリ作成完了${NC}"

# データベース存在確認
if [ "$ENVIRONMENT" = "production" ]; then
    DB_PATH="db/knowledge.db"
else
    DB_PATH="db/knowledge_dev.db"
fi

if [ ! -f "$DB_PATH" ]; then
    if [ "$ENVIRONMENT" = "production" ]; then
        echo -e "\n${RED}❌ 本番用データベースが存在しません${NC}"
        echo -e "${YELLOW}データベースを初期化してください:${NC}"
        echo -e "${BLUE}   python3 scripts/init_db.py --env production --no-samples${NC}"
        exit 1
    fi

    echo -e "\n${YELLOW}⚠️  開発用データベースが存在しません${NC}"
    if [ "$NON_INTERACTIVE" -eq 1 ]; then
        echo -e "${YELLOW}非対話モードのため初期化はスキップします${NC}"
        exit 1
    fi

    echo -e "${BLUE}データベースを初期化しますか？ (y/n)${NC}"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo -e "${GREEN}データベース初期化中...${NC}"
        python3 scripts/init_db.py --env development --with-samples
    fi
fi

# 依存パッケージ確認
echo -e "\n${BLUE}📦 依存パッケージ確認${NC}"
python3 -c "import flask; import dotenv" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 必要なパッケージがインストールされていません${NC}"
    echo -e "${YELLOW}pip install -r requirements.txt を実行してください${NC}"
    exit 1
fi

# ポート使用確認
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "\n${RED}⚠️  ポート $PORT は既に使用中です${NC}"
    echo -e "${YELLOW}既存のプロセスを終了してから再度実行してください${NC}"
    lsof -Pi :$PORT -sTCP:LISTEN
    exit 1
fi

# SSL証明書確認
ssl_enabled=1
if [ -n "$SSL_ENABLED" ]; then
    ssl_enabled=$(parse_bool "$SSL_ENABLED")
fi

if [ "$ssl_enabled" -eq 1 ]; then
    if [ -z "$SSL_CERT" ] || [ ! -f "$SSL_CERT" ] || [ -z "$SSL_KEY" ] || [ ! -f "$SSL_KEY" ]; then
        if [ "$ENVIRONMENT" = "production" ]; then
            echo -e "\n${RED}❌ SSL証明書が見つかりません${NC}"
            echo -e "${YELLOW}本番環境ではSSL証明書が必須です${NC}"
            exit 1
        fi
        echo -e "\n${YELLOW}⚠️  SSL証明書が見つかりません${NC}"
        echo -e "${YELLOW}HTTPモードで起動します（SSL無効）${NC}"
        ssl_enabled=0
        export SSL_ENABLED="False"
    fi
fi

# WebUI起動
if [ "$ssl_enabled" -eq 1 ]; then
    protocol="https"
else
    protocol="http"
fi

echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}🌐 WebUI起動中...${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}   アクセスURL: ${protocol}://${HOST}:${PORT}${NC}"
echo -e "${GREEN}   ローカル: ${protocol}://localhost:${PORT}${NC}"
echo -e "${YELLOW}   終了: Ctrl+C${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Flask実行
python3 src/webui/app.py
