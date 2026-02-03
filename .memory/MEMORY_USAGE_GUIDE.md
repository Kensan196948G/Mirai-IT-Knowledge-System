# メモリMCP使い分けガイド

## 概要

本プロジェクトでは2つのメモリMCPを使い分けて、効率的な情報管理を実現します。

---

## 1. memory（知識グラフメモリ）

**パッケージ**: `@modelcontextprotocol/server-memory`

### 用途
- **エンティティ管理**: プロジェクト、設定、コンポーネントなどの実体
- **関係管理**: エンティティ間のリレーション（uses, contains, depends_on等）
- **短期〜中期コンテキスト**: セッション間で引き継ぐプロジェクト状態
- **構造化データ**: 明確な型を持つ情報

### 保存先
```
.memory/project-memory.json
```

### 使用例
```
- プロジェクト構成情報
- MCP設定状態
- データベーススキーマ情報
- SubAgent/Hooks設定
- 現在の開発フェーズ
```

### MCPツール
| ツール | 説明 |
|--------|------|
| `create_entities` | エンティティ作成 |
| `create_relations` | 関係作成 |
| `add_observations` | 観察事項追加 |
| `search_nodes` | ノード検索 |
| `read_graph` | グラフ全体読取 |

---

## 2. claude-mem（会話履歴メモリ）

**パッケージ**: `cccmemory`

### 用途
- **会話履歴**: 過去のやり取りのセマンティック検索
- **決定追跡**: なぜその判断をしたかの記録
- **長期記憶**: プロジェクトを超えた知識の蓄積
- **Git統合**: コミットとの関連付け

### 保存先
```
.memory/claude-mem/conversations.db (SQLite)
```

### 使用例
```
- 過去に同様の問題をどう解決したか
- 設計判断の理由と経緯
- エラー対応の履歴
- 学習した教訓
```

### 特徴
- セマンティック検索（類似の会話を検索）
- 決定追跡（Decision Tracking）
- クロスプロジェクト検索
- 自動インデックス作成

---

## 使い分けフローチャート

```
情報を保存したい
    │
    ├─ 構造化されたエンティティ/関係？
    │   └─ YES → memory（知識グラフ）
    │
    ├─ 会話の文脈や決定の理由？
    │   └─ YES → claude-mem（会話履歴）
    │
    ├─ 将来検索して再利用したい？
    │   └─ YES → claude-mem（セマンティック検索）
    │
    └─ プロジェクト状態の追跡？
        └─ YES → memory（知識グラフ）
```

---

## 実装での使い分け

### SubAgent処理結果
- **memory**: SubAgentの実行ステータス、スコア
- **claude-mem**: SubAgentが出した推奨事項の理由

### ナレッジ作成
- **memory**: ナレッジID、タイプ、関連ナレッジ
- **claude-mem**: 作成時の判断プロセス、ユーザーとのやり取り

### エラー対応
- **memory**: エラーパターン、解決策のマッピング
- **claude-mem**: エラー解決の経緯、試行錯誤の記録

### 設定変更
- **memory**: 現在の設定値、依存関係
- **claude-mem**: 設定変更の理由、過去の設定履歴

---

## ベストプラクティス

### memory（知識グラフ）
1. エンティティは明確な型を持たせる（Project, Configuration, Schema等）
2. 関係は動詞形式で定義（uses, contains, depends_on）
3. 観察事項は簡潔に記述
4. 定期的に不要なエンティティを削除

### claude-mem（会話履歴）
1. 重要な決定には理由を明記
2. エラー解決時は試行過程も記録
3. 再利用可能な知識はタグ付け
4. 定期的なインデックス最適化

---

## 設定ファイル

### .mcp.json
```json
{
  "memory": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-memory"],
    "env": {
      "MEMORY_FILE_PATH": ".memory/project-memory.json"
    }
  },
  "claude-mem": {
    "command": "npx",
    "args": ["-y", "cccmemory"],
    "env": {
      "CCCMEMORY_DB_PATH": ".memory/claude-mem/conversations.db"
    }
  }
}
```

---

*Last Updated: 2026-02-03*
