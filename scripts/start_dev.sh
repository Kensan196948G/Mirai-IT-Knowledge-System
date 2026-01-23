#!/bin/bash
# ==================================================
# Mirai IT Knowledge System - Development Environment Starter
# 開発環境起動スクリプト (Linux)
# ==================================================

set -e  # エラー時は即座に終了

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# プロジェクトルート
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}🚀 Mirai IT Knowledge System${NC}"
echo -e "${YELLOW}   開発環境起動中...${NC}"
echo -e "${BLUE}========================================${NC}"

# 環境変数設定
export ENVIRONMENT="development"
export FLASK_ENV="development"
export FLASK_APP="src/webui/app.py"

# 環境変数ファイル読み込み
if [ -f ".env.development" ]; then
    echo -e "${GREEN}✅ 環境変数ファイル読み込み: .env.development${NC}"
    set -a
    source .env.development
    set +a
else
    echo -e "${RED}⚠️  警告: .env.development が見つかりません${NC}"
fi

# Pythonバージョン確認
echo -e "\n${BLUE}📊 システム情報${NC}"
echo -e "   Python: $(python3 --version)"
echo -e "   プロジェクトルート: $PROJECT_ROOT"
echo -e "   環境: ${ENVIRONMENT}"

# 必要なディレクトリ作成
echo -e "\n${BLUE}📁 ディレクトリ確認${NC}"
mkdir -p db
mkdir -p data/logs/dev
mkdir -p data/knowledge
mkdir -p backups/dev
echo -e "${GREEN}✅ ディレクトリ作成完了${NC}"

# データベース存在確認
if [ ! -f "db/knowledge_dev.db" ]; then
    echo -e "\n${YELLOW}⚠️  開発用データベースが存在しません${NC}"
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
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 必要なパッケージがインストールされています${NC}"
else
    echo -e "${RED}❌ 必要なパッケージがインストールされていません${NC}"
    echo -e "${YELLOW}pip install -r requirements.txt を実行してください${NC}"
    exit 1
fi

# ポート使用確認
PORT=8888
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "\n${RED}⚠️  ポート $PORT は既に使用中です${NC}"
    echo -e "${YELLOW}既存のプロセスを終了してから再度実行してください${NC}"
    lsof -Pi :$PORT -sTCP:LISTEN
    exit 1
fi

# SSL証明書確認
if [ ! -f "/etc/ssl/mirai-knowledge/dev-cert.pem" ]; then
    echo -e "\n${YELLOW}⚠️  SSL証明書が見つかりません${NC}"
    echo -e "${BLUE}Phase 3でSSL証明書を生成してください${NC}"
    echo -e "${YELLOW}HTTPモードで起動します（SSL無効）${NC}"
    export SSL_ENABLED="False"
fi

# WebUI起動
echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}🌐 WebUI起動中...${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}   アクセスURL: https://192.168.0.187:8888${NC}"
echo -e "${GREEN}   ローカル: https://localhost:8888${NC}"
echo -e "${YELLOW}   終了: Ctrl+C${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Flask実行
python3 src/webui/app.py
