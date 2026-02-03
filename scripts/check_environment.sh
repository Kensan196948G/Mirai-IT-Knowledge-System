#!/bin/bash
# 開発環境チェックスクリプト

echo "======================================"
echo "Mirai IT Knowledge System"
echo "開発環境チェック"
echo "======================================"
echo ""

# カラー定義
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✓${NC} $1: $(command -v $1)"
        return 0
    else
        echo -e "${RED}✗${NC} $1: Not found"
        return 1
    fi
}

check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1"
        return 0
    else
        echo -e "${RED}✗${NC} $1: Not found"
        return 1
    fi
}

check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} $1"
        return 0
    else
        echo -e "${RED}✗${NC} $1: Not found"
        return 1
    fi
}

# システムコマンド
echo "📋 System Commands"
check_command python3
check_command pip
check_command node
check_command npx
check_command git
echo ""

# Python仮想環境
echo "🐍 Python Virtual Environment"
check_dir "venv"
if [ -d "venv" ]; then
    source venv/bin/activate
    echo -e "${GREEN}✓${NC} Virtual environment activated"

    # Pythonパッケージ
    echo ""
    echo "📦 Python Packages"
    for pkg in Flask PyYAML python-dotenv anthropic google-generativeai pytest; do
        if python -c "import importlib.util; exit(0 if importlib.util.find_spec('${pkg,,}') else 1)" 2>/dev/null; then
            version=$(python -c "import importlib.metadata; print(importlib.metadata.version('${pkg}'))" 2>/dev/null || echo "unknown")
            echo -e "${GREEN}✓${NC} $pkg: $version"
        else
            echo -e "${RED}✗${NC} $pkg: Not installed"
        fi
    done
fi
echo ""

# 環境設定ファイル
echo "⚙️  Configuration Files"
check_file ".env.development"
check_file ".env.production"
check_file ".mcp.json"
check_file "config/agents/subagents.yaml"
check_file "config/agents/hooks.yaml"
echo ""

# データベース
echo "🗄️  Database Files"
check_file "db/knowledge.db"
check_file "db/knowledge_dev.db"
check_file "db/schema.sql"
echo ""

# SubAgents
echo "🤖 SubAgents (7 expected)"
subagent_count=$(ls -1 src/subagents/*.py 2>/dev/null | grep -v "__init__\|base" | wc -l)
if [ "$subagent_count" -eq 7 ]; then
    echo -e "${GREEN}✓${NC} SubAgents: $subagent_count/7"
else
    echo -e "${YELLOW}⚠${NC} SubAgents: $subagent_count/7"
fi
ls -1 src/subagents/*.py 2>/dev/null | grep -v "__init__\|base" | while read f; do
    echo "  - $(basename $f .py)"
done
echo ""

# Hooks
echo "🪝 Hooks (5 expected)"
hook_count=$(ls -1 src/hooks/*.py 2>/dev/null | grep -v "__init__\|base" | wc -l)
if [ "$hook_count" -eq 5 ]; then
    echo -e "${GREEN}✓${NC} Hooks: $hook_count/5"
else
    echo -e "${YELLOW}⚠${NC} Hooks: $hook_count/5"
fi
ls -1 src/hooks/*.py 2>/dev/null | grep -v "__init__\|base" | while read f; do
    echo "  - $(basename $f .py)"
done
echo ""

# MCP Servers
echo "🔌 MCP Servers"
mcp_count=$(grep -c '"command"' .mcp.json 2>/dev/null || echo 0)
echo -e "${GREEN}✓${NC} MCP Servers configured: $mcp_count"
grep -o '"[^"]*":' .mcp.json | grep -v "mcpServers\|projectConfig\|enabledPlugins\|environments\|subagents\|hooks\|env\|args\|command\|description" | sed 's/://g' | while read server; do
    echo "  - $server"
done
echo ""

# Git状態
echo "📚 Git Repository"
if [ -d ".git" ]; then
    branch=$(git branch --show-current)
    echo -e "${GREEN}✓${NC} Current branch: $branch"
    echo -e "${GREEN}✓${NC} Recent commits:"
    git log --oneline -3 | sed 's/^/  /'
else
    echo -e "${RED}✗${NC} Not a git repository"
fi
echo ""

echo "======================================"
echo "チェック完了"
echo "======================================"
