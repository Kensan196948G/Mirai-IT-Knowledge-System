# TicketClient API ドキュメント

**Phase 10.1: チケット管理クライアント**

## 概要

`TicketClient` は Mirai IT Knowledge Systems のチケット管理機能を提供するクライアントクラスです。
`SQLiteClient` を継承し、インシデント、問題、リクエスト、質問、相談などのチケットを管理します。

## クラス定義

```python
from mcp.ticket_client import TicketClient

client = TicketClient(db_path="db/knowledge_dev.db")
```

### 初期化パラメータ

| パラメータ | 型 | デフォルト | 説明 |
|-----------|---|-----------|------|
| `db_path` | str | `"db/knowledge_dev.db"` | データベースファイルパス |

## メソッド一覧

### 1. チケット作成

```python
create_ticket(
    session_id: str,
    title: str,
    description: str,
    category: str,
    priority: str = 'medium',
    created_by: str = 'ai'
) -> Dict
```

**パラメータ:**
- `session_id`: 会話セッションID
- `title`: チケットタイトル
- `description`: 詳細説明
- `category`: カテゴリ（`incident`, `problem`, `request`, `question`, `consultation`）
- `priority`: 優先度（`low`, `medium`, `high`, `critical`）
- `created_by`: 作成者名

**返却値:**
```python
{
    "success": True,
    "ticket_id": 123,
    "ticket_number": "TKT-20260205-001"
}
```

**使用例:**
```python
result = client.create_ticket(
    session_id="sess_001",
    title="VPN接続エラー",
    description="Cisco AnyConnect で認証に失敗します",
    category="incident",
    priority="high"
)
print(f"チケット番号: {result['ticket_number']}")
```

---

### 2. チケット取得（ID）

```python
get_ticket(ticket_id: int) -> Optional[Dict]
```

**パラメータ:**
- `ticket_id`: チケットID

**返却値:**
チケット情報の辞書（存在しない場合は `None`）

**使用例:**
```python
ticket = client.get_ticket(123)
if ticket:
    print(f"タイトル: {ticket['title']}")
    print(f"ステータス: {ticket['status']}")
    print(f"コメント数: {ticket['comment_count']}")
```

---

### 3. チケット取得（番号）

```python
get_ticket_by_number(ticket_number: str) -> Optional[Dict]
```

**パラメータ:**
- `ticket_number`: チケット番号（例: `TKT-20260205-001`）

**返却値:**
チケット情報の辞書（存在しない場合は `None`）

**使用例:**
```python
ticket = client.get_ticket_by_number("TKT-20260205-001")
```

---

### 4. チケット取得（セッションID）

```python
get_ticket_by_session(session_id: str) -> Optional[Dict]
```

**パラメータ:**
- `session_id`: 会話セッションID

**返却値:**
該当セッションの最新チケット情報（存在しない場合は `None`）

**使用例:**
```python
ticket = client.get_ticket_by_session("sess_001")
```

---

### 5. ステータス更新

```python
update_ticket_status(
    ticket_id: int,
    status: str,
    comment: str = None,
    updated_by: str = 'ai'
) -> bool
```

**パラメータ:**
- `ticket_id`: チケットID
- `status`: 新しいステータス（`new`, `analyzing`, `in_progress`, `pending_user`, `resolved`, `closed`, `cancelled`）
- `comment`: 更新コメント（オプション）
- `updated_by`: 更新者名

**返却値:**
成功時 `True`、失敗時 `False`

**使用例:**
```python
success = client.update_ticket_status(
    ticket_id=123,
    status='in_progress',
    comment='調査を開始しました',
    updated_by='ai'
)
```

---

### 6. コメント追加

```python
add_ticket_comment(
    ticket_id: int,
    author: str,
    content: str,
    author_type: str = 'user',
    is_internal: bool = False,
    is_solution: bool = False
) -> bool
```

**パラメータ:**
- `ticket_id`: チケットID
- `author`: 著者名
- `content`: コメント内容
- `author_type`: 著者タイプ（`user`, `ai`, `system`）
- `is_internal`: 内部コメント（ユーザーに非表示）
- `is_solution`: 解決策コメント

**返却値:**
成功時 `True`、失敗時 `False`

**使用例:**
```python
client.add_ticket_comment(
    ticket_id=123,
    author='ai',
    content='診断中: VPN証明書の有効期限を確認しています...',
    author_type='ai',
    is_internal=False
)
```

---

### 7. コメント一覧取得

```python
get_ticket_comments(
    ticket_id: int,
    include_internal: bool = False
) -> List[Dict]
```

**パラメータ:**
- `ticket_id`: チケットID
- `include_internal`: 内部コメントを含めるか

**返却値:**
コメントリスト（作成日時順）

**使用例:**
```python
comments = client.get_ticket_comments(ticket_id=123)
for comment in comments:
    print(f"[{comment['author']}] {comment['content']}")
```

---

### 8. アクティブチケット一覧

```python
get_active_tickets(
    limit: int = 20,
    category: str = None
) -> List[Dict]
```

**パラメータ:**
- `limit`: 取得件数
- `category`: カテゴリフィルタ（オプション）

**返却値:**
アクティブチケットのリスト（優先度順、作成日時順）

**使用例:**
```python
# 全カテゴリのアクティブチケット
active = client.get_active_tickets(limit=10)

# インシデントのみ
incidents = client.get_active_tickets(category='incident')
```

---

### 9. チケット解決

```python
resolve_ticket(
    ticket_id: int,
    resolution: str,
    knowledge_id: int = None,
    resolved_by: str = 'ai'
) -> bool
```

**パラメータ:**
- `ticket_id`: チケットID
- `resolution`: 解決策・対応内容
- `knowledge_id`: 関連ナレッジID（オプション）
- `resolved_by`: 解決者名

**返却値:**
成功時 `True`、失敗時 `False`

**使用例:**
```python
success = client.resolve_ticket(
    ticket_id=123,
    resolution='VPN証明書を更新することで解決しました。',
    knowledge_id=456,
    resolved_by='ai'
)
```

---

### 10. チケットクローズ

```python
close_ticket(
    ticket_id: int,
    closed_by: str = 'system'
) -> bool
```

**パラメータ:**
- `ticket_id`: チケットID
- `closed_by`: クローズ実行者

**返却値:**
成功時 `True`、失敗時 `False`

**使用例:**
```python
client.close_ticket(ticket_id=123, closed_by='system')
```

---

### 11. チケット履歴取得

```python
get_ticket_history(ticket_id: int) -> List[Dict]
```

**パラメータ:**
- `ticket_id`: チケットID

**返却値:**
履歴エントリのリスト（新しい順）

**使用例:**
```python
history = client.get_ticket_history(ticket_id=123)
for entry in history:
    print(f"{entry['action']}: {entry['from_value']} → {entry['to_value']}")
```

---

### 12. チケット統計取得

```python
get_ticket_stats() -> Dict
```

**返却値:**
統計情報の辞書

**使用例:**
```python
stats = client.get_ticket_stats()
print(f"総チケット数: {stats['total_tickets']}")
print(f"カテゴリ別: {stats['by_category']}")
print(f"ステータス別: {stats['by_status']}")
print(f"優先度別: {stats['by_priority']}")
```

---

## チケット番号形式

チケット番号は以下の形式で自動生成されます：

```
TKT-YYYYMMDD-NNN
```

- `TKT`: プレフィックス
- `YYYYMMDD`: 作成日（8桁）
- `NNN`: 同日内の連番（3桁、001から開始）

**例:**
- `TKT-20260205-001` - 2026年2月5日の1番目のチケット
- `TKT-20260205-002` - 2026年2月5日の2番目のチケット

---

## チケットステータス

| ステータス | 説明 |
|-----------|------|
| `new` | 新規作成 |
| `analyzing` | 分析中 |
| `in_progress` | 対応中 |
| `pending_user` | ユーザー待ち |
| `resolved` | 解決済み |
| `closed` | クローズ済み |
| `cancelled` | キャンセル |

---

## 優先度

| 優先度 | 説明 |
|-------|------|
| `low` | 低 |
| `medium` | 中（デフォルト） |
| `high` | 高 |
| `critical` | 緊急 |

---

## カテゴリ

| カテゴリ | 説明 |
|---------|------|
| `incident` | インシデント（障害対応） |
| `problem` | 問題（根本原因分析） |
| `request` | サービスリクエスト |
| `question` | 質問 |
| `consultation` | 相談 |

---

## エラーハンドリング

すべてのメソッドは例外を内部でキャッチし、適切な返却値を返します：

- **作成/更新系**: `{"success": False, "error": "エラーメッセージ"}` または `False`
- **取得系**: `None` または空のリスト `[]`

**使用例:**
```python
result = client.create_ticket(...)
if not result['success']:
    print(f"エラー: {result.get('error')}")
```

---

## トランザクション管理

- 全ての書き込み操作はトランザクション内で実行されます
- エラー発生時は自動的にロールバックされます
- SQLite WALモードを使用し、並行アクセスに対応しています

---

## データベーススキーマ

TicketClient は以下のテーブルを使用します：

1. **tickets** - チケット本体
2. **ticket_history** - ステータス変更履歴
3. **ticket_comments** - コメント
4. **ticket_followups** - フォローアップスケジュール
5. **ticket_stats** (VIEW) - 統計情報

詳細は `/mnt/LinuxHDD/Mirai-ticket-system/db/ticket_schema.sql` を参照してください。

---

## テスト

テストスクリプト: `/mnt/LinuxHDD/Mirai-ticket-system/test_ticket_client.py`

```bash
cd /mnt/LinuxHDD/Mirai-ticket-system
python3 test_ticket_client.py
```

---

## 使用例: 完全なワークフロー

```python
from mcp.ticket_client import TicketClient

# 初期化
client = TicketClient()

# 1. チケット作成
result = client.create_ticket(
    session_id="user_session_123",
    title="VPN接続エラー",
    description="Cisco AnyConnect で認証に失敗します",
    category="incident",
    priority="high",
    created_by="user_yamada"
)
ticket_id = result['ticket_id']

# 2. ステータス更新
client.update_ticket_status(
    ticket_id, 'analyzing',
    '問題の切り分けを開始します', 'ai'
)

# 3. 診断コメント追加
client.add_ticket_comment(
    ticket_id, 'ai',
    '証明書の有効期限を確認しています...',
    author_type='ai'
)

# 4. 解決
client.resolve_ticket(
    ticket_id,
    resolution='VPN証明書を更新して解決しました',
    knowledge_id=456,
    resolved_by='ai'
)

# 5. フォローアップ後にクローズ
client.close_ticket(ticket_id, closed_by='system')

# 6. 履歴確認
history = client.get_ticket_history(ticket_id)
for entry in history:
    print(f"{entry['created_at']}: {entry['action']}")
```

---

## 関連ドキュメント

- [チケットスキーマ](../db/ticket_schema.sql)
- [SQLiteClient API](./sqlite_client_api.md)
- [Phase 10: チケット管理システム](./phase10_design.md)

---

**作成日:** 2026-02-05
**バージョン:** 1.0.0
**ステータス:** 完成
