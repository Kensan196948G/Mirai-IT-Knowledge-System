#!/bin/bash
# ==================================================
# SSL Certificate Renewal Script
# SSL証明書更新スクリプト
# ==================================================

set -e

# カラー定義
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}🔄 SSL証明書更新${NC}"
echo -e "${BLUE}========================================${NC}\n"

# 証明書ディレクトリ
CERT_DIR="/etc/ssl/mirai-knowledge"

# sudo権限確認
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ このスクリプトはroot権限で実行する必要があります${NC}"
    echo -e "${YELLOW}以下のコマンドで実行してください:${NC}"
    echo -e "${BLUE}   sudo $0${NC}"
    exit 1
fi

# 証明書の有効期限確認
echo -e "${BLUE}🔍 現在の証明書有効期限確認:${NC}\n"

if [ -f "$CERT_DIR/dev-cert.pem" ]; then
    echo -e "${YELLOW}開発環境用証明書:${NC}"
    openssl x509 -in "$CERT_DIR/dev-cert.pem" -noout -enddate
else
    echo -e "${RED}開発環境用証明書が見つかりません${NC}"
fi

if [ -f "$CERT_DIR/prod-cert.pem" ]; then
    echo -e "${YELLOW}本番環境用証明書:${NC}"
    openssl x509 -in "$CERT_DIR/prod-cert.pem" -noout -enddate
else
    echo -e "${RED}本番環境用証明書が見つかりません${NC}"
fi

# 更新確認
echo -e "\n${BLUE}証明書を更新しますか？ (y/n)${NC}"
read -r response
if [[ ! "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo -e "${YELLOW}更新を中止します${NC}"
    exit 0
fi

# 古い証明書をバックアップ
echo -e "\n${BLUE}📦 古い証明書をバックアップ中...${NC}"
BACKUP_DIR="$CERT_DIR/backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
if [ -f "$CERT_DIR/dev-cert.pem" ]; then
    cp "$CERT_DIR"/dev-*.pem "$BACKUP_DIR/" 2>/dev/null || true
fi
if [ -f "$CERT_DIR/prod-cert.pem" ]; then
    cp "$CERT_DIR"/prod-*.pem "$BACKUP_DIR/" 2>/dev/null || true
fi
echo -e "${GREEN}✅ バックアップ完了: $BACKUP_DIR${NC}"

# 新しい証明書生成
echo -e "\n${BLUE}🔧 新しい証明書を生成中...${NC}"

# 開発環境用証明書
openssl req -x509 -newkey rsa:4096 -nodes \
    -keyout "$CERT_DIR/dev-key.pem" \
    -out "$CERT_DIR/dev-cert.pem" \
    -days 365 \
    -subj "/C=JP/ST=Tokyo/L=Tokyo/O=Mirai/OU=Development/CN=192.168.0.187"

# 本番環境用証明書
openssl req -x509 -newkey rsa:4096 -nodes \
    -keyout "$CERT_DIR/prod-key.pem" \
    -out "$CERT_DIR/prod-cert.pem" \
    -days 365 \
    -subj "/C=JP/ST=Tokyo/L=Tokyo/O=Mirai/OU=Production/CN=192.168.0.187"

# 権限設定
chmod 600 "$CERT_DIR"/*.pem
chown $SUDO_USER:$SUDO_USER "$CERT_DIR"/*.pem

echo -e "\n${GREEN}✅ 証明書更新完了！${NC}"

# 新しい証明書情報表示
echo -e "\n${BLUE}🔍 新しい証明書の有効期限:${NC}\n"
echo -e "${YELLOW}開発環境用:${NC}"
openssl x509 -in "$CERT_DIR/dev-cert.pem" -noout -enddate
echo -e "${YELLOW}本番環境用:${NC}"
openssl x509 -in "$CERT_DIR/prod-cert.pem" -noout -enddate

echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}💡 サービスの再起動が必要な場合があります${NC}"
echo -e "${BLUE}   開発環境: sudo systemctl restart mirai-knowledge-dev${NC}"
echo -e "${BLUE}   本番環境: sudo systemctl restart mirai-knowledge-prod${NC}"
echo -e "${BLUE}========================================${NC}\n"
