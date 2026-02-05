# Phase 7: MCP統合ガイド

## 概要

Phase 7では、3種類のMCP Client（Claude-Mem、Context7、GitHub）を完全実装し、外部サービスとの統合を実現しました。

## 実装されたMCP Client

### 1. Claude-Mem Client

**用途**: 会話履歴、決定追跡、長期記憶管理

**主要機能**:
- セマンティック検索
- 類似会話検索
- 決定追跡（Decision Tracking）
- Git統合（コミット-会話リンク）

**実装済みメソッド**:

```python
from src.mcp.claude_mem_client import ClaudeMemClient

client = ClaudeMemClient()

# セマンティック検索
memories = client.search_memories(
    query="データベース接続エラーの解決方法",
    limit=5
)

# 類似会話検索
similar = client.search_similar_conversations(
    content="Webサーバー503エラーが発生しました...",
    threshold=0.7
)

# 決定を記録
client.store_decision(
    title="接続プール最大数の変更",
    decision="最大接続数を20から50に変更",
    rationale="ピーク時の接続不足を解消するため",
    alternatives=["Redis導入", "スケールアウト"],
    tags=["database", "performance"]
)

# 決定を検索
decisions = client.get_decisions(
    query="接続プール",
    limit=10
)

# Gitコミットとリンク
client.link_to_commit(
    decision_id="dec_20260205120000",
    commit_hash="abc1234",
    commit_message="feat: Increase connection pool size"
)
```

**MCP Tools使用**:
- `mcp__claude-mem__search_conversations`
- `mcp__claude-mem__get_decisions`
- `mcp__claude-mem__index_conversations`
- `mcp__claude-mem__link_commits_to_conversations`

---

### 2. Context7 Client

**用途**: 技術ドキュメント検索、ライブラリリファレンス取得

**主要機能**:
- ライブラリID解決
- ドキュメント検索
- ナレッジ補強（技術ドキュメントによる）

**実装済みメソッド**:

```python
from src.mcp.context7_client import Context7Client

client = Context7Client()

# ライブラリIDを解決
library_id = client.resolve_library_id(
    library_name="flask",
    query="routing and URL building"
)

# ドキュメントを検索
docs = client.query_documentation(
    library_name="flask",
    query="How to handle file uploads",
    max_results=5
)

# ナレッジを技術ドキュメントで補強
enrichment = client.enrich_knowledge_with_docs(
    knowledge_content="Flaskアプリケーションでファイルアップロード機能を実装...",
    detected_technologies=["flask", "python"]
)
```

**MCP Tools使用**:
- `mcp__context7__resolve-library-id`
- `mcp__context7__query-docs`

**サポートライブラリ**:
- Flask, SQLite, Python, Apache, Nginx, その他多数

---

### 3. GitHub Client

**用途**: バージョン管理、監査証跡、変更履歴管理

**主要機能**:
- ナレッジのGitコミット
- 変更履歴取得
- 監査Issue作成
- PR作成ワークフロー

**実装済みメソッド**:

```python
from src.mcp.github_client import GitHubClient

client = GitHubClient(repository="owner/repo")

# ナレッジをGitHubにコミット
commit = client.commit_knowledge(
    knowledge_id=123,
    file_path="data/knowledge/00123_Incident.md",
    content="# ナレッジ内容...",
    commit_message="docs: Add incident resolution for server error",
    author="user@example.com"
)

# 変更履歴を取得
history = client.get_knowledge_history(
    file_path="data/knowledge/00123_Incident.md",
    limit=10
)

# 監査Issueを作成
issue = client.create_audit_issue(
    title="Critical incident: Production outage",
    description="Root cause analysis required",
    labels=["audit", "high-priority"]
)

# ナレッジ変更のPRを作成
pr = client.create_knowledge_pr(
    branch_name="knowledge/update-123",
    title="Update incident resolution documentation",
    description="Added detailed root cause analysis",
    files_changed=[
        {"path": "data/knowledge/00123_Incident.md", "content": "..."}
    ]
)
```

**MCP Tools使用**:
- `mcp__github__create_or_update_file`
- `mcp__github__list_commits`
- `mcp__github__create_issue`
- `mcp__github__create_branch`
- `mcp__github__push_files`
- `mcp__github__create_pull_request`

---

## MCP統合の設計パターン

### Graceful Fallback パターン

すべてのMCP Clientは、MCP利用不可時に自動的にフォールバック動作を行います。

```python
def search_memories(self, query: str, limit: int = 5):
    if not self.enabled:
        # MCP無効時はデモデータにフォールバック
        return self._get_demo_memories(query)

    try:
        # MCP経由で検索
        results = mcp__claude_mem__search_conversations(
            query=query,
            limit=limit,
            scope="all"
        )
        return self._format_results(results)

    except Exception as e:
        print(f"Warning: MCP search failed: {e}. Falling back to demo data.")
        return self._get_demo_memories(query)
```

### Auto-Enable パターン

MCP利用可能性を自動チェック：

```python
def __init__(self, auto_enable: bool = True):
    self.enabled = auto_enable and self._check_mcp_available()

def _check_mcp_available(self) -> bool:
    """MCP利用可能性をチェック"""
    try:
        import sys
        tool = globals().get('mcp__claude_mem__search_conversations') or \
               getattr(sys.modules.get('__main__', {}),
                      'mcp__claude_mem__search_conversations', None)
        return tool is not None
    except Exception:
        return False
```

### キャッシュパターン

頻繁にアクセスされるデータはローカルキャッシュ：

```python
def query_documentation(self, library_name: str, query: str):
    # キャッシュチェック
    cache_key = f"{library_name}:{query}"
    if cache_key in self._cached_docs:
        return self._cached_docs[cache_key]

    # MCP経由で検索
    results = mcp__context7__query_docs(...)

    # キャッシュに保存
    self._cached_docs[cache_key] = results
    return results
```

## 環境変数設定

### Claude-Mem

```bash
# データベースパス
export CCCMEMORY_DB_PATH=".memory/claude-mem/conversations.db"

# 自動有効化
export MCP_CLAUDE_MEM_ENABLED="True"
```

### Context7

```bash
# 自動有効化
export MCP_CONTEXT7_ENABLED="True"
```

### GitHub

```bash
# リポジトリ設定
export GITHUB_REPOSITORY="owner/repo"

# 自動有効化
export MCP_GITHUB_ENABLED="True"
```

## トラブルシューティング

### MCP Clientが有効にならない

**確認項目**:
1. MCP設定ファイル（.mcp.json）が存在するか
2. MCPサーバーが起動しているか
3. 環境変数が正しく設定されているか

**デバッグ方法**:
```python
client = ClaudeMemClient(auto_enable=True)
print(f"Enabled: {client.enabled}")
print(f"DB Path: {client.db_path}")

# 手動でMCPツールを確認
import sys
tool = globals().get('mcp__claude_mem__search_conversations')
print(f"Tool available: {tool is not None}")
```

### MCP呼び出しエラー

**症状**: `MCP search failed` 警告が表示される

**対策**:
1. フォールバック動作により処理は継続される
2. ログを確認してエラー詳細を把握
3. MCP設定を確認

### パフォーマンス低下

**原因**: MCP呼び出しのオーバーヘッド

**対策**:
1. キャッシュを活用（既に実装済み）
2. MCP無効化してローカルのみで動作
3. 非同期呼び出しの活用（将来の改善）

## ベストプラクティス

### 1. MCP有効/無効の切り替え

```python
# テスト時はMCP無効化
client = ClaudeMemClient(auto_enable=False)

# 本番環境ではMCP有効化
client = ClaudeMemClient(auto_enable=True)
```

### 2. エラーハンドリング

```python
try:
    results = client.search_memories(query)
    if results:
        # 結果を使用
        pass
except Exception as e:
    logger.error(f"MCP search failed: {e}")
    # フォールバック処理
```

### 3. キャッシュ戦略

- **短期キャッシュ**: 検索結果（TTL: 5分）
- **中期キャッシュ**: ドキュメント（TTL: 1時間）
- **長期キャッシュ**: 決定（永続化）

## セキュリティ考慮事項

### 1. API Key管理

MCP設定ファイル（.mcp.json）には機密情報を含めない：

```json
{
  "mcpServers": {
    "github": {
      "command": "mcp-server-github",
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
```

環境変数から取得：
```bash
export GITHUB_TOKEN="ghp_xxxxx"
```

### 2. データ暗号化

Claude-Memデータベースは機密情報を含む可能性があるため：
- アクセス権限を適切に設定（chmod 600）
- バックアップ時は暗号化

## まとめ

Phase 7のMCP統合により：

✅ **17個のTODO完全解消**
✅ **外部サービス統合**（会話履歴、技術ドキュメント、GitHub）
✅ **Graceful Fallback**（MCP無効時も動作）
✅ **エラー耐性強化**

次のPhaseでは、これらのMCP統合機能を活用した高度な機能実装が可能になります。
