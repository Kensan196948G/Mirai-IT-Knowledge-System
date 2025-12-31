# 🚀 新機能ガイド

Mirai IT Knowledge Systems v2.0 で追加された新機能の詳細ガイドです。

## 📋 目次

1. [サンプルデータ生成](#1-サンプルデータ生成)
2. [ユーザーフィードバック機能](#2-ユーザーフィードバック機能)
3. [MCP連携強化](#3-mcp連携強化)
4. [高度な分析機能](#4-高度な分析機能)

---

## 1. サンプルデータ生成

### 概要
実際の運用を想定した7件のサンプルナレッジを自動生成します。

### 使い方

```bash
python3 scripts/generate_sample_data.py
```

### 生成されるサンプル

| # | タイトル | ITSMタイプ | 内容 |
|---|----------|-----------|------|
| 1 | データベース接続タイムアウトエラー | Incident | DB接続プール上限到達の障害対応 |
| 2 | DB接続数上限問題の根本原因分析 | Problem | コネクションプール設定問題の分析 |
| 3 | Webサーバー証明書の更新作業 | Change | SSL/TLS証明書更新手順 |
| 4 | APIレート制限機能のリリース | Release | 新機能リリース計画 |
| 5 | 新規ユーザーのVPNアクセス権限申請 | Request | アクセス権限申請フロー |
| 6 | バックアップサーバーのディスク容量逼迫 | Incident | ストレージ容量問題対応 |
| 7 | メール送信遅延の継続的な問題 | Problem | 継続的問題の根本原因分析 |

### 実行結果
- ✅ 各ナレッジは自動的に分析・分類されます
- ✅ 技術者向け・非技術者向け要約が生成されます
- ✅ タグ・カテゴリが自動抽出されます
- ✅ 品質スコアが算出されます

---

## 2. ユーザーフィードバック機能

### 2.1 ナレッジフィードバック

#### 機能
- 5段階評価（★1〜★5）
- フィードバックタイプ選択
  - 役立った（helpful）
  - 役立たなかった（not_helpful）
  - 内容が不正確（incorrect）
  - 情報不足（incomplete）
  - 改善提案（suggestion）
- コメント投稿

#### API使用例

```python
from src.mcp.feedback_client import FeedbackClient

client = FeedbackClient()

# フィードバック追加
client.add_knowledge_feedback(
    knowledge_id=1,
    user_id="user123",
    rating=5,
    feedback_type="helpful",
    comment="とても参考になりました"
)

# フィードバック取得
feedback = client.get_knowledge_feedback(knowledge_id=1)

# 評価サマリー取得
rating = client.get_knowledge_rating(knowledge_id=1)
# => {'avg_rating': 4.5, 'feedback_count': 10, 'helpful_count': 8}
```

#### WebUIから
1. ナレッジ詳細ページを開く
2. ページ下部の「フィードバック」フォームから投稿
3. 評価・タイプ・コメントを入力して送信

### 2.2 システムフィードバック

#### 機能
システム全体に対する改善要望・バグ報告を収集

#### カテゴリ
- UI改善（ui）
- 検索機能（search）
- ナレッジ品質（quality）
- パフォーマンス（performance）
- 機能リクエスト（feature_request）
- バグ報告（bug）
- その他（other）

#### API使用例

```python
# システムフィードバック追加
client.add_system_feedback(
    title="検索機能の改善提案",
    description="タグによる絞り込み検索を追加してほしい",
    feedback_category="search",
    priority="medium",
    user_id="user123"
)

# フィードバック一覧取得
feedbacks = client.get_system_feedback(status="new")
```

#### WebUIから
1. `/feedback` にアクセス
2. フィードバックフォームに入力
3. カテゴリ・優先度を選択して送信

### 2.3 使用統計

#### 機能
ナレッジの閲覧・利用状況を自動追跡

#### 追跡アクション
- view: 閲覧
- search_result_click: 検索結果からのクリック
- copy: コピー
- export: エクスポート
- share: 共有

#### API使用例

```python
# 使用統計記録
client.log_knowledge_usage(
    knowledge_id=1,
    action_type="view",
    user_id="user123"
)

# 統計取得
stats = client.get_knowledge_usage_stats(knowledge_id=1)
# => {
#   'view_count': 150,
#   'action_stats': {'view': 150, 'copy': 10},
#   'trend_30days': [...]
# }

# 人気のナレッジ取得
popular = client.get_popular_knowledge(limit=10, days=30)
```

### 2.4 スキーマ適用

```bash
# フィードバックスキーマを既存DBに適用
python3 scripts/apply_feedback_schema.py
```

追加されるテーブル:
- `knowledge_feedback`: ナレッジフィードバック
- `system_feedback`: システムフィードバック
- `knowledge_usage_stats`: 使用統計
- `knowledge_ratings`: 評価サマリー（ビュー）

---

## 3. MCP連携強化

### 3.1 Context7統合（技術ドキュメント参照）

#### 機能
技術ドキュメントを自動検索し、ナレッジを補強

#### 使用例

```python
from src.mcp.context7_client import Context7Client

client = Context7Client()

# 技術ドキュメント検索
docs = client.query_documentation(
    library_name="flask",
    query="routing and URL building"
)

# ナレッジ補強
enrichments = client.enrich_knowledge_with_docs(
    knowledge_content="Flaskでルーティングを設定...",
    detected_technologies=["flask", "sqlite"]
)
```

#### 対応技術
- Flask
- SQLite
- Python
- その他（拡張可能）

### 3.2 Claude-Mem統合（設計思想記憶）

#### 機能
過去の設計判断・ベストプラクティスを記憶・検索

#### 使用例

```python
from src.mcp.claude_mem_client import ClaudeMemClient

client = ClaudeMemClient()

# 過去の記憶を検索
memories = client.search_memories("データベース接続プール設定")

# 設計判断を保存
client.store_design_decision(
    knowledge_id=1,
    decision_title="接続プール設定の標準化",
    rationale="アプリケーションサーバー数とDB上限を考慮",
    alternatives_considered=["動的プール", "固定プール"],
    tags=["database", "connection-pool"]
)

# ナレッジ補強
enhancement = client.enhance_knowledge_with_memory(
    knowledge_content="...",
    itsm_type="Problem"
)
```

### 3.3 GitHub統合（バージョン管理・監査）

#### 機能
ナレッジ変更をGitHubで管理し、監査証跡を保持

#### 使用例

```python
from src.mcp.github_client import GitHubClient

client = GitHubClient(repository="mirai-it/knowledge-base")

# ナレッジをコミット
commit = client.commit_knowledge(
    knowledge_id=1,
    file_path="knowledge/00001_Incident.md",
    content="...",
    commit_message="Update incident response procedure",
    author="ops_team"
)

# 変更履歴取得
history = client.get_knowledge_history("knowledge/00001_Incident.md")

# 監査証跡取得
audit = client.get_audit_trail(knowledge_id=1)

# 変更ログ生成
changelog = client.generate_change_log(since="2025-01-01")
```

---

## 4. 高度な分析機能

### 4.1 インシデントトレンド分析

```python
from src.core.analytics import AnalyticsEngine

engine = AnalyticsEngine()

# インシデントトレンド分析
trends = engine.analyze_incident_trends(days=90)
# => {
#   'daily_counts': [...],
#   'tag_distribution': [...],
#   'recurring_incidents': [...],
#   'total_incidents': 42
# }
```

### 4.2 問題解決率分析

```python
# 問題管理の解決率
resolution = engine.analyze_problem_resolution_rate()
# => {
#   'total_problems': 10,
#   'resolved_problems': 7,
#   'resolution_rate': 70.0,
#   'avg_resolution_days': 14.5
# }
```

### 4.3 ナレッジ品質分析

```python
# 品質分析
quality = engine.analyze_knowledge_quality()
# => {
#   'length_distribution': {...},
#   'summary_coverage': 85.0,
#   'tag_distribution': [...]
# }
```

### 4.4 ITSMフロー分析

```python
# ITSM管理フロー分析
flow = engine.analyze_itsm_flow()
# => {
#   'incident_to_problem': {'total': 50, 'escalated': 15, 'rate': 30.0},
#   'problem_to_change': {'total': 15, 'escalated': 10, 'rate': 66.7},
#   'complete_flow_count': 8
# }
```

### 4.5 利用パターン分析

```python
# 利用パターン
patterns = engine.analyze_usage_patterns(days=30)
# => {
#   'popular_knowledge': [...],
#   'top_rated_knowledge': [...],
#   'search_trends': [...]
# }
```

### 4.6 総合レポート生成

```python
# 総合分析レポート
report = engine.generate_comprehensive_report(days=30)
# 全ての分析結果を統合したレポートを生成

# 改善推奨事項
recommendations = engine.generate_recommendations()
# => [
#   {
#     'category': 'incident_management',
#     'priority': 'high',
#     'recommendation': '...'
#   },
#   ...
# ]
```

### 4.7 WebUIでの分析表示

`/analytics` エンドポイントにアクセスすると、以下が表示されます:
- フィードバックサマリー
- 人気のナレッジTop10
- 評価の高いナレッジTop10
- 検索トレンド

---

## 🎯 クイックスタート

### 1. サンプルデータ生成

```bash
python3 scripts/generate_sample_data.py
```

### 2. フィードバック機能有効化

```bash
python3 scripts/apply_feedback_schema.py
```

### 3. WebUI起動

```bash
python3 src/webui/app.py
```

### 4. 新機能にアクセス

- フィードバック: http://localhost:5000/feedback
- 分析ダッシュボード: http://localhost:5000/analytics
- ナレッジ詳細（フィードバック機能付き）: http://localhost:5000/knowledge/{id}

---

## 📈 次のステップ

1. **実際のデータで運用開始**
   - サンプルデータで動作確認
   - 実際のインシデント・問題を登録
   - フィードバックを収集

2. **分析レポートの定期確認**
   - 週次でトレンド確認
   - 改善推奨事項の実施
   - KPI設定と追跡

3. **MCP連携の本格化**
   - MCPSearchツールを使用して実際のMCP連携
   - GitHub連携で変更履歴管理
   - Context7で技術情報補強

4. **カスタマイズ**
   - 分析指標の追加
   - ダッシュボードのカスタマイズ
   - アラート設定

---

## 💡 ベストプラクティス

### フィードバック収集
- ✅ ナレッジ閲覧後に評価を促す
- ✅ 定期的にフィードバックをレビュー
- ✅ 低評価ナレッジは優先的に改善

### 分析活用
- ✅ 週次レポートで傾向把握
- ✅ 再発インシデントを問題管理へ
- ✅ 人気ナレッジを参考に品質向上

### MCP活用
- ✅ 技術ナレッジにはContext7で補強
- ✅ 重要な判断はClaude-Memに記録
- ✅ 定期的にGitHubへバックアップ

---

**v2.0の新機能により、より効果的なナレッジ管理が可能になりました！** 🎉
