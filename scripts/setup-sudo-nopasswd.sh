#!/bin/bash
# Mirai IT Knowledge System - sudo パスワード不要設定
# systemctlコマンドをパスワードなしで実行できるように設定

set -e

echo "=========================================="
echo "Mirai IT Knowledge System"
echo "sudo パスワード不要設定"
echo "=========================================="
echo ""

USER=$(whoami)
SUDOERS_FILE="/etc/sudoers.d/mirai-knowledge-nopasswd"

echo "📋 現在のユーザー: $USER"
echo "📝 設定ファイル: $SUDOERS_FILE"
echo ""

# sudoers設定を作成
echo "✅ sudoers設定を作成中..."
sudo tee "$SUDOERS_FILE" > /dev/null << EOF
# Mirai IT Knowledge System - sudo パスワード不要設定
# systemctlコマンドのみパスワードなしで実行可能

# mirai-knowledge-devサービスの管理
$USER ALL=(ALL) NOPASSWD: /usr/bin/systemctl start mirai-knowledge-dev
$USER ALL=(ALL) NOPASSWD: /usr/bin/systemctl stop mirai-knowledge-dev
$USER ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart mirai-knowledge-dev
$USER ALL=(ALL) NOPASSWD: /usr/bin/systemctl status mirai-knowledge-dev
$USER ALL=(ALL) NOPASSWD: /usr/bin/systemctl enable mirai-knowledge-dev
$USER ALL=(ALL) NOPASSWD: /usr/bin/systemctl disable mirai-knowledge-dev

# ログ確認
$USER ALL=(ALL) NOPASSWD: /usr/bin/journalctl -u mirai-knowledge-dev*
EOF

# パーミッション設定
sudo chmod 440 "$SUDOERS_FILE"

# 設定検証
echo ""
echo "🔍 設定を検証中..."
sudo visudo -c -f "$SUDOERS_FILE"

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ 設定完了"
    echo "=========================================="
    echo ""
    echo "📝 以下のコマンドがパスワードなしで実行可能になりました:"
    echo "  sudo systemctl start mirai-knowledge-dev"
    echo "  sudo systemctl stop mirai-knowledge-dev"
    echo "  sudo systemctl restart mirai-knowledge-dev"
    echo "  sudo systemctl status mirai-knowledge-dev"
    echo "  sudo journalctl -u mirai-knowledge-dev"
    echo ""
    echo "🧪 テスト実行:"
    echo "  sudo systemctl status mirai-knowledge-dev"
    echo ""

    # テスト実行
    sudo systemctl status mirai-knowledge-dev --no-pager -l | head -10

    echo ""
    echo "✅ パスワード不要で実行できました"
    echo ""
else
    echo ""
    echo "❌ エラー: sudoers設定が無効です"
    echo "設定ファイルを削除します..."
    sudo rm -f "$SUDOERS_FILE"
    exit 1
fi
