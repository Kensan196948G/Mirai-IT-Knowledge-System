#!/bin/bash
# GitHub リポジトリセットアップスクリプト

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                              ║"
echo "║              🐙 GitHub リポジトリセットアップ 🐙                             ║"
echo "║                                                                              ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# リポジトリ情報
GITHUB_USER="Kensan196948G"
REPO_NAME="Mirai-IT-Knowledge-System"
REPO_URL="https://github.com/${GITHUB_USER}/${REPO_NAME}"

echo "📦 リポジトリ情報"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ユーザー名   : ${GITHUB_USER}"
echo "  リポジトリ名 : ${REPO_NAME}"
echo "  URL         : ${REPO_URL}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ステップ1: GitHubでリポジトリを作成
echo "📝 ステップ1: GitHubでリポジトリを作成"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "以下のURLにアクセスして、新しいリポジトリを作成してください:"
echo ""
echo "   👉 https://github.com/new"
echo ""
echo "設定項目:"
echo "  - リポジトリ名: ${REPO_NAME}"
echo "  - 説明: AI-assisted Internal IT Knowledge Management System powered by Claude Code Workflow"
echo "  - Public/Private: お好みで選択"
echo "  - 「Add a README file」: チェックしない（既にREADME.mdがあります）"
echo "  - 「Add .gitignore」: None（既に.gitignoreがあります）"
echo "  - 「Choose a license」: なし（後で追加可能）"
echo ""
echo "作成したら Enter を押してください..."
read -r

# ステップ2: リモートリポジトリの確認
echo ""
echo "📡 ステップ2: リモートリポジトリの確認"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
git remote -v

# ステップ3: プッシュ実行
echo ""
echo "🚀 ステップ3: GitHubにプッシュします"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "プッシュを実行しますか？ (y/N): "
read -r response

if [ "$response" = "y" ] || [ "$response" = "Y" ]; then
    echo ""
    echo "📤 プッシュ中..."

    # メインブランチ名を確認
    BRANCH=$(git branch --show-current)
    echo "   ブランチ: ${BRANCH}"

    # プッシュ実行
    git push -u origin ${BRANCH}

    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ プッシュ成功！"
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "🎉 GitHubリポジトリのセットアップが完了しました！"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "   リポジトリURL: ${REPO_URL}"
        echo ""
        echo "   ブラウザでアクセスして確認してください:"
        echo "   👉 ${REPO_URL}"
        echo ""
    else
        echo ""
        echo "❌ プッシュに失敗しました"
        echo ""
        echo "💡 トラブルシューティング:"
        echo ""
        echo "1. GitHubで正しくリポジトリが作成されているか確認"
        echo "   → ${REPO_URL}"
        echo ""
        echo "2. 認証情報が正しいか確認"
        echo "   Personal Access Token を使用する場合:"
        echo "   - Username: ${GITHUB_USER}"
        echo "   - Password: Personal Access Token"
        echo ""
        echo "3. SSHキーを使用する場合:"
        echo "   - リモートURLを変更: git remote set-url origin git@github.com:${GITHUB_USER}/${REPO_NAME}.git"
        echo "   - SSH接続テスト: ssh -T git@github.com"
        echo ""
        echo "詳細は docs/GITHUB_SETUP.md を参照してください"
        echo ""
    fi
else
    echo ""
    echo "ℹ️  プッシュをスキップしました"
    echo ""
    echo "後でプッシュする場合:"
    echo "   git push -u origin main"
    echo ""
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
