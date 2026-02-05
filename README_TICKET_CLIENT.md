# TicketClient - Quick Start Guide

**Mirai IT Knowledge Systems - Phase 10.1**

## 🚀 クイックスタート

### インストール

すでにプロジェクトに統合されています。インポートするだけです。

```python
from mcp.ticket_client import TicketClient

client = TicketClient()
```

### 基本的な使い方

```python
# チケット作成
result = client.create_ticket(
    session_id="session_001",
    title="VPN接続エラー",
    description="Cisco AnyConnect で認証失敗",
    category="incident",
    priority="high"
)

ticket_id = result['ticket_id']
ticket_number = result['ticket_number']  # TKT-20260205-001

# チケット取得
ticket = client.get_ticket(ticket_id)
print(f"ステータス: {ticket['status']}")

# ステータス更新
client.update_ticket_status(ticket_id, 'in_progress', '調査開始')

# コメント追加
client.add_ticket_comment(ticket_id, 'ai', '診断中...', 'ai')

# 解決
client.resolve_ticket(ticket_id, '証明書を更新して解決')

# クローズ
client.close_ticket(ticket_id)
```

## 📊 主要メソッド

| メソッド | 用途 |
|---------|------|
| `create_ticket()` | チケット新規作成 |
| `get_ticket()` | ID でチケット取得 |
| `get_ticket_by_number()` | 番号でチケット取得 |
| `get_ticket_by_session()` | セッションからチケット取得 |
| `update_ticket_status()` | ステータス変更 |
| `add_ticket_comment()` | コメント追加 |
| `get_ticket_comments()` | コメント一覧 |
| `get_active_tickets()` | アクティブチケット一覧 |
| `resolve_ticket()` | チケット解決 |
| `close_ticket()` | チケットクローズ |
| `get_ticket_history()` | 変更履歴取得 |
| `get_ticket_stats()` | 統計情報取得 |

## 📝 チケットステータス

```
new → analyzing → in_progress → resolved → closed
                      ↓
                  pending_user
                      ↓
                  cancelled
```

## 🏷️ カテゴリと優先度

### カテゴリ
- `incident` - インシデント（障害対応）
- `problem` - 問題（根本原因分析）
- `request` - サービスリクエスト
- `question` - 質問
- `consultation` - 相談

### 優先度
- `critical` - 緊急
- `high` - 高
- `medium` - 中（デフォルト）
- `low` - 低

## 🧪 テスト実行

```bash
cd /mnt/LinuxHDD/Mirai-ticket-system
python3 test_ticket_client.py
```

期待される出力:
```
======================================================================
✅ 全テスト成功!
======================================================================
```

## 📖 詳細ドキュメント

- **完全なAPIリファレンス**: `docs/ticket_client_api.md`
- **実装完了レポート**: `docs/phase10.1_completion_report.md`
- **データベーススキーマ**: `db/ticket_schema.sql`

## 🔧 トラブルシューティング

### データベースファイルが見つからない

```python
# デフォルトパスを使用
client = TicketClient()  # db/knowledge_dev.db

# カスタムパス
client = TicketClient(db_path="path/to/your/db.sqlite")
```

### スキーマが適用されていない

```bash
python3 -c "import sqlite3; conn = sqlite3.connect('db/knowledge_dev.db'); \
conn.executescript(open('db/ticket_schema.sql').read()); conn.close()"
```

## 💡 ベストプラクティス

### 1. エラーチェック

```python
result = client.create_ticket(...)
if result['success']:
    ticket_id = result['ticket_id']
else:
    print(f"エラー: {result.get('error')}")
```

### 2. トランザクション

全てのメソッドは内部でトランザクション管理されています。明示的な `commit()` は不要です。

### 3. コメントの使い分け

```python
# ユーザー向けコメント
client.add_ticket_comment(ticket_id, 'ai', '診断中...', 'ai', is_internal=False)

# 内部メモ（ユーザーに非表示）
client.add_ticket_comment(ticket_id, 'ai', 'デバッグ情報...', 'ai', is_internal=True)

# 解決策コメント
client.add_ticket_comment(ticket_id, 'ai', '解決策...', 'ai', is_solution=True)
```

## 🎯 実装済み機能

- ✅ チケットCRUD操作
- ✅ ステータス管理と履歴追跡
- ✅ コメントシステム
- ✅ 自動番号生成（TKT-YYYYMMDD-NNN）
- ✅ 統計・分析機能
- ✅ エラーハンドリング
- ✅ WALモード最適化
- ✅ JSONフィールド対応

## 🔜 今後の拡張（Phase 10.2+）

- 問題切り分けエンジン統合
- 自動フォローアップ
- 会話コンテキスト永続化
- Web UI 統合

## 📞 サポート

問題が発生した場合は、以下を確認してください：

1. データベースファイルが存在するか
2. スキーマが適用されているか
3. テストが通るか (`python3 test_ticket_client.py`)

---

**バージョン:** 1.0.0
**更新日:** 2026-02-05
**ステータス:** Production Ready ✅
