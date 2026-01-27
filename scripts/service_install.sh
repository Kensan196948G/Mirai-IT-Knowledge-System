#!/bin/bash
# ==================================================
# Systemd Service Installation Script
# systemdサービスインストールスクリプト
# ==================================================

set -e

# カラー定義
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}🔧 Systemdサービスインストール${NC}"
echo -e "${BLUE}========================================${NC}\n"

# root権限確認
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ このスクリプトはroot権限で実行する必要があります${NC}"
    echo -e "${YELLOW}以下のコマンドで実行してください:${NC}"
    echo -e "${BLUE}   sudo $0${NC}"
    exit 1
fi

# プロジェクトルート
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SYSTEMD_DIR="/etc/systemd/system"

# サービスファイルのコピー
echo -e "${BLUE}📁 サービスファイルをコピー中...${NC}"

# 開発環境サービス
cp "$SCRIPT_DIR/systemd/mirai-knowledge-dev.service" "$SYSTEMD_DIR/"
echo -e "${GREEN}✅ mirai-knowledge-dev.service をインストール${NC}"

# 本番環境サービス
cp "$SCRIPT_DIR/systemd/mirai-knowledge-prod.service" "$SYSTEMD_DIR/"
echo -e "${GREEN}✅ mirai-knowledge-prod.service をインストール${NC}"

# systemdリロード
echo -e "\n${BLUE}🔄 systemdをリロード中...${NC}"
systemctl daemon-reload
echo -e "${GREEN}✅ systemdリロード完了${NC}"

# サービス有効化
echo -e "\n${BLUE}🔧 サービスを有効化中...${NC}"
systemctl enable mirai-knowledge-dev.service
systemctl enable mirai-knowledge-prod.service
echo -e "${GREEN}✅ サービス有効化完了（システム起動時に自動起動）${NC}"

# サービス状態確認
echo -e "\n${BLUE}📊 サービス状態:${NC}"
echo -e "\n${YELLOW}開発環境サービス:${NC}"
systemctl status mirai-knowledge-dev.service --no-pager || true

echo -e "\n${YELLOW}本番環境サービス:${NC}"
systemctl status mirai-knowledge-prod.service --no-pager || true

# 使用方法
echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}✅ インストール完了！${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "\n${YELLOW}使用方法:${NC}"
echo -e "  ${BLUE}# 開発環境を起動${NC}"
echo -e "  sudo systemctl start mirai-knowledge-dev"
echo -e ""
echo -e "  ${BLUE}# 本番環境を起動${NC}"
echo -e "  sudo systemctl start mirai-knowledge-prod"
echo -e ""
echo -e "  ${BLUE}# サービス状態確認${NC}"
echo -e "  sudo systemctl status mirai-knowledge-dev"
echo -e "  sudo systemctl status mirai-knowledge-prod"
echo -e ""
echo -e "  ${BLUE}# ログ確認${NC}"
echo -e "  sudo journalctl -u mirai-knowledge-dev -f"
echo -e "  sudo journalctl -u mirai-knowledge-prod -f"
echo -e ""
echo -e "  ${BLUE}# サービス停止${NC}"
echo -e "  sudo systemctl stop mirai-knowledge-dev"
echo -e "  sudo systemctl stop mirai-knowledge-prod"
echo -e ""
echo -e "  ${BLUE}# サービス再起動${NC}"
echo -e "  sudo systemctl restart mirai-knowledge-dev"
echo -e "  sudo systemctl restart mirai-knowledge-prod"
echo -e ""
echo -e "  ${BLUE}# cron登録（DBバックアップ）${NC}"
echo -e "  sudo ./scripts/cron_install.sh --env production"
echo -e ""
echo -e "${BLUE}========================================${NC}\n"
