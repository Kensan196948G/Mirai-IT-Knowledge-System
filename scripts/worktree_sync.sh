#!/bin/bash
# ==================================================
# Git Worktree Sync Script
# 開発環境から本番環境への同期スクリプト
# ==================================================

set -e

# カラー定義
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}🔄 Git Worktree 同期${NC}"
echo -e "${YELLOW}   開発環境 → 本番環境${NC}"
echo -e "${BLUE}========================================${NC}\n"

# プロジェクトルート
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PRODUCTION_DIR="/mnt/LinuxHDD/Mirai-IT-Knowledge-System-production"

cd "$PROJECT_ROOT"

# developブランチにいるか確認
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "develop" ]; then
    echo -e "${RED}❌ 現在のブランチがdevelopではありません${NC}"
    echo -e "${YELLOW}現在: $CURRENT_BRANCH${NC}"
    echo -e "${BLUE}developブランチに切り替えてください:${NC}"
    echo -e "${BLUE}   git checkout develop${NC}"
    exit 1
fi

# 未コミットの変更を確認
if ! git diff-index --quiet HEAD --; then
    echo -e "${YELLOW}⚠️  未コミットの変更があります${NC}"
    echo -e "${BLUE}変更をコミットしますか？ (y/n)${NC}"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        git add .
        echo -e "${BLUE}コミットメッセージを入力してください:${NC}"
        read -r commit_message
        git commit -m "$commit_message"
    else
        echo -e "${RED}同期を中止します${NC}"
        exit 1
    fi
fi

# リモートにプッシュ
echo -e "\n${BLUE}📤 リモートにプッシュ中...${NC}"
git push origin develop

# mainブランチに切り替え
echo -e "\n${BLUE}🔀 mainブランチにマージ中...${NC}"
git checkout main
git merge develop

# リモートにプッシュ
echo -e "\n${BLUE}📤 mainブランチをプッシュ中...${NC}"
git push origin main

# developブランチに戻る
git checkout develop

# 本番環境Worktreeを更新
if [ -d "$PRODUCTION_DIR" ]; then
    echo -e "\n${BLUE}🔄 本番環境Worktreeを更新中...${NC}"
    cd "$PRODUCTION_DIR"
    git pull origin main
    cd "$PROJECT_ROOT"
fi

echo -e "\n${GREEN}✅ 同期完了！${NC}"
echo -e "${BLUE}========================================${NC}"
git worktree list
echo -e "${BLUE}========================================${NC}\n"
