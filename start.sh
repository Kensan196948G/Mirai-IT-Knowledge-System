#!/bin/bash
# Mirai IT Knowledge Systems - クイックスタートスクリプト

echo "🌸 Mirai IT Knowledge Systems v2.0"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# カレントディレクトリ確認
if [ ! -f "src/webui/app.py" ]; then
    echo "❌ エラー: プロジェクトルートで実行してください"
    exit 1
fi

# データベース確認
if [ ! -f "db/knowledge.db" ]; then
    echo "📦 データベースが存在しません。初期化します..."
    python3 scripts/init_db.py
    python3 scripts/apply_feedback_schema.py
    python3 scripts/apply_conversation_schema.py
    echo ""
fi

# 追加スキーマの適用（既存DB向け）
python3 scripts/apply_feedback_schema.py
python3 scripts/apply_conversation_schema.py

# サンプルデータ確認
echo "📊 データベース状態を確認中..."
KNOWLEDGE_COUNT=$(python3 -c "
from src.mcp.sqlite_client import SQLiteClient
client = SQLiteClient()
stats = client.get_statistics()
print(stats['total_knowledge'])
" 2>/dev/null)

if [ "$KNOWLEDGE_COUNT" = "0" ] || [ -z "$KNOWLEDGE_COUNT" ]; then
    echo "📝 サンプルデータがありません。生成しますか？ (y/N): "
    read -r response
    if [ "$response" = "y" ] || [ "$response" = "Y" ]; then
        python3 scripts/generate_sample_data.py
    fi
    echo ""
fi

# 環境変数読み込み（開発環境想定）
if [ -f ".env.development" ]; then
    set -a
    source .env.development
    set +a
fi

# IPアドレス取得
IP_ADDRESS="${HOST:-}"
if [ -z "$IP_ADDRESS" ] || [ "$IP_ADDRESS" = "0.0.0.0" ] || [ "$IP_ADDRESS" = "localhost" ]; then
    IP_ADDRESS=$(hostname -I | awk '{print $1}')
fi

PORT="${PORT:-8888}"
SSL_FLAG="${SSL_ENABLED:-False}"
if [[ "${SSL_FLAG,,}" == "true" || "${SSL_FLAG,,}" == "1" || "${SSL_FLAG,,}" == "yes" || "${SSL_FLAG,,}" == "on" ]]; then
    PROTOCOL="https"
else
    PROTOCOL="http"
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 WebUIを起動します..."
echo ""
echo "   ネットワークアクセス: ${PROTOCOL}://${IP_ADDRESS}:${PORT}"
echo "   ローカルアクセス    : ${PROTOCOL}://localhost:${PORT}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "終了するには Ctrl+C を押してください"
echo ""

# WebUI起動
python3 src/webui/app.py
