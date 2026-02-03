#!/bin/bash
# ==================================================
# Git Worktree Status Script
# Worktree状態確認スクリプト
# ==================================================

# カラー定義
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}🌿 Git Worktree 状態確認${NC}"
echo -e "${BLUE}========================================${NC}\n"

# プロジェクトルート
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PRODUCTION_DIR="/mnt/LinuxHDD/Mirai-IT-Knowledge-System-production"

cd "$PROJECT_ROOT"

# Worktree一覧
echo -e "${BLUE}📊 Worktree一覧:${NC}"
git worktree list
echo ""

# 開発環境状態
echo -e "${BLUE}📁 開発環境 (develop):${NC}"
echo -e "   場所: $PROJECT_ROOT"
CURRENT_BRANCH=$(git branch --show-current)
echo -e "   ブランチ: $CURRENT_BRANCH"
COMMIT_HASH=$(git rev-parse --short HEAD)
echo -e "   コミット: $COMMIT_HASH"
if ! git diff-index --quiet HEAD --; then
    echo -e "   ${YELLOW}未コミット変更: あり${NC}"
else
    echo -e "   ${GREEN}未コミット変更: なし${NC}"
fi
echo ""

# 本番環境状態
if [ -d "$PRODUCTION_DIR" ]; then
    echo -e "${BLUE}📁 本番環境 (main):${NC}"
    echo -e "   場所: $PRODUCTION_DIR"
    cd "$PRODUCTION_DIR"
    PROD_BRANCH=$(git branch --show-current)
    echo -e "   ブランチ: $PROD_BRANCH"
    PROD_COMMIT=$(git rev-parse --short HEAD)
    echo -e "   コミット: $PROD_COMMIT"
    if ! git diff-index --quiet HEAD --; then
        echo -e "   ${YELLOW}未コミット変更: あり${NC}"
    else
        echo -e "   ${GREEN}未コミット変更: なし${NC}"
    fi
    cd "$PROJECT_ROOT"
else
    echo -e "${RED}❌ 本番環境Worktreeが見つかりません${NC}"
fi

echo -e "\n${BLUE}========================================${NC}\n"
