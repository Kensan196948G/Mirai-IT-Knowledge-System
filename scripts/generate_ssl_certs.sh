#!/bin/bash
# ==================================================
# SSL Certificate Generation Script
# SSL証明書生成スクリプト
# ==================================================

set -e

# カラー定義
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}🔒 SSL証明書生成${NC}"
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

# ディレクトリ作成
echo -e "${BLUE}📁 証明書ディレクトリ作成:${NC} $CERT_DIR"
mkdir -p "$CERT_DIR"

# 開発環境用証明書生成
echo -e "\n${BLUE}🔧 開発環境用証明書生成中...${NC}"
openssl req -x509 -newkey rsa:4096 -nodes \
    -keyout "$CERT_DIR/dev-key.pem" \
    -out "$CERT_DIR/dev-cert.pem" \
    -days 365 \
    -subj "/C=JP/ST=Tokyo/L=Tokyo/O=Mirai/OU=Development/CN=192.168.0.187"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 開発環境用証明書生成完了${NC}"
else
    echo -e "${RED}❌ 開発環境用証明書生成失敗${NC}"
    exit 1
fi

# 本番環境用証明書生成
echo -e "\n${BLUE}🔧 本番環境用証明書生成中...${NC}"
openssl req -x509 -newkey rsa:4096 -nodes \
    -keyout "$CERT_DIR/prod-key.pem" \
    -out "$CERT_DIR/prod-cert.pem" \
    -days 365 \
    -subj "/C=JP/ST=Tokyo/L=Tokyo/O=Mirai/OU=Production/CN=192.168.0.187"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 本番環境用証明書生成完了${NC}"
else
    echo -e "${RED}❌ 本番環境用証明書生成失敗${NC}"
    exit 1
fi

# 権限設定
echo -e "\n${BLUE}🔐 証明書の権限設定中...${NC}"
chmod 600 "$CERT_DIR"/*.pem
chown $SUDO_USER:$SUDO_USER "$CERT_DIR"/*.pem

# 証明書情報表示
echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}✅ SSL証明書生成完了！${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "\n${GREEN}📄 生成された証明書:${NC}"
ls -lh "$CERT_DIR"

echo -e "\n${BLUE}🔍 証明書情報:${NC}"
echo -e "\n${YELLOW}開発環境用証明書:${NC}"
openssl x509 -in "$CERT_DIR/dev-cert.pem" -text -noout | grep -E "(Subject:|Not Before|Not After)"

echo -e "\n${YELLOW}本番環境用証明書:${NC}"
openssl x509 -in "$CERT_DIR/prod-cert.pem" -text -noout | grep -E "(Subject:|Not Before|Not After)"

echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}💡 証明書の有効期限: 365日${NC}"
echo -e "${YELLOW}⚠️  自己署名証明書のため、ブラウザで警告が表示されます${NC}"
echo -e "${BLUE}   セキュリティ例外を追加して続行してください${NC}"
echo -e "${BLUE}========================================${NC}\n"
