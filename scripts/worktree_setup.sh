#!/bin/bash
# ==================================================
# Git Worktree Setup Script
# Git Worktree初期化スクリプト
# ==================================================

set -e

# カラー定義
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}🌿 Git Worktree セットアップ${NC}"
echo -e "${BLUE}========================================${NC}\n"

# プロジェクトルート
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PRODUCTION_DIR="/mnt/LinuxHDD/Mirai-IT-Knowledge-System-production"

cd "$PROJECT_ROOT"

# 現在のWorktree確認
echo -e "${BLUE}📊 現在のWorktree状態:${NC}"
git worktree list

# 本番環境Worktreeが存在するか確認
if [ -d "$PRODUCTION_DIR" ]; then
    echo -e "\n${YELLOW}⚠️  本番環境Worktreeは既に存在します${NC}"
    echo -e "${BLUE}場所: $PRODUCTION_DIR${NC}"
    exit 0
fi

# developブランチが存在するか確認
if ! git rev-parse --verify develop >/dev/null 2>&1; then
    echo -e "\n${RED}❌ developブランチが存在しません${NC}"
    echo -e "${YELLOW}先にdevelopブランチを作成してください:${NC}"
    echo -e "${BLUE}   git checkout -b develop${NC}"
    echo -e "${BLUE}   git push -u origin develop${NC}"
    exit 1
fi

# 本番環境Worktree作成
echo -e "\n${BLUE}🔧 本番環境Worktreeを作成中...${NC}"
git worktree add "$PRODUCTION_DIR" main

echo -e "\n${GREEN}✅ Worktree作成完了！${NC}"
echo -e "${BLUE}========================================${NC}"
git worktree list
echo -e "${BLUE}========================================${NC}\n"

echo -e "${GREEN}📁 ディレクトリ構成:${NC}"
echo -e "   開発環境: $PROJECT_ROOT (develop)"
echo -e "   本番環境: $PRODUCTION_DIR (main)"

echo -e "\n${YELLOW}💡 使い方:${NC}"
echo -e "   開発作業: cd $PROJECT_ROOT"
echo -e "   本番確認: cd $PRODUCTION_DIR"
