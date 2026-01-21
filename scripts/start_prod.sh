#!/bin/bash
# ==================================================
# Mirai IT Knowledge System - Production Environment Starter
# 本番環境起動スクリプト (Linux)
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
echo -e "${YELLOW}   本番環境起動中...${NC}"
echo -e "${BLUE}========================================${NC}"

# 環境変数設定
export ENVIRONMENT="production"
export FLASK_ENV="production"
export FLASK_APP="src/webui/app.py"

# 環境変数ファイル読み込み
if [ -f ".env.production" ]; then
    echo -e "${GREEN}✅ 環境変数ファイル読み込み: .env.production${NC}"
    set -a
    source .env.production
    set +a
else
    echo -e "${RED}⚠️  警告: .env.production が見つかりません${NC}"
fi

# Pythonバージョン確認
echo -e "\n${BLUE}📊 システム情報${NC}"
echo -e "   Python: $(python3 --version)"
echo -e "   プロジェクトルート: $PROJECT_ROOT"
echo -e "   環境: ${ENVIRONMENT}"

# 必要なディレクトリ作成
echo -e "\n${BLUE}📁 ディレクトリ確認${NC}"
mkdir -p db
mkdir -p data/logs/prod
mkdir -p data/knowledge
mkdir -p backups/prod
echo -e "${GREEN}✅ ディレクトリ作成完了${NC}"

# データベース存在確認
if [ ! -f "db/knowledge.db" ]; then
    echo -e "\n${RED}❌ 本番用データベースが存在しません${NC}"
    echo -e "${YELLOW}データベースを初期化してください:${NC}"
    echo -e "${BLUE}   python3 scripts/init_db.py --env production --no-samples${NC}"
    exit 1
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
PORT=5000
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "\n${RED}⚠️  ポート $PORT は既に使用中です${NC}"
    echo -e "${YELLOW}既存のプロセスを終了してから再度実行してください${NC}"
    lsof -Pi :$PORT -sTCP:LISTEN
    exit 1
fi

# SSL証明書確認（本番環境では必須）
if [ ! -f "/etc/ssl/mirai-knowledge/prod-cert.pem" ]; then
    echo -e "\n${RED}❌ SSL証明書が見つかりません${NC}"
    echo -e "${YELLOW}本番環境ではSSL証明書が必須です${NC}"
    echo -e "${BLUE}Phase 3でSSL証明書を生成してください:${NC}"
    echo -e "${YELLOW}   sudo openssl req -x509 -newkey rsa:4096 -nodes ...${NC}"
    exit 1
fi

# セキュリティチェック
if [ "$SECRET_KEY" == "default-secret-key-change-me" ] || [ "$SECRET_KEY" == "CHANGE_THIS_TO_RANDOM_SECRET_KEY_IN_PRODUCTION" ]; then
    echo -e "\n${RED}⚠️  セキュリティ警告: SECRET_KEYがデフォルト値です${NC}"
    echo -e "${YELLOW}本番環境では必ずランダムなSECRET_KEYに変更してください${NC}"
    echo -e "${BLUE}続行しますか？ (y/n)${NC}"
    read -r response
    if [[ ! "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        exit 1
    fi
fi

# WebUI起動
echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}🌐 WebUI起動中...${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}   アクセスURL: https://192.168.0.187:5000${NC}"
echo -e "${GREEN}   ローカル: https://localhost:5000${NC}"
echo -e "${YELLOW}   終了: Ctrl+C${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Flask実行
python3 src/webui/app.py
