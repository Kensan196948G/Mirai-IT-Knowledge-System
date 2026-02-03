# 分析ダッシュボード ロジック (ANALYTICS_LOGIC)

## 概要
WebUIの「分析」画面は、`FeedbackClient` とDBの集計結果を表示する軽量ダッシュボードです。
高度な分析は `src/core/analytics.py` の `AnalyticsEngine` に実装されていますが、現状の `/analytics` 画面では直接使用していません。

## 対象画面 / エンドポイント
- 画面: `/analytics`
- API: `/api/knowledge/<id>/stats`

## 主要ロジック
### 1) フィードバックサマリー
- 取得元: `FeedbackClient.get_feedback_summary()`
- 対象テーブル: `knowledge_feedback`, `system_feedback`
- 取得値:
  - 総フィードバック件数
  - 平均評価
  - フィードバックが付いたナレッジ件数
  - システムフィードバック件数
  - フィードバック種別別件数

### 2) 人気ナレッジ
- 取得元: `FeedbackClient.get_popular_knowledge(limit=10, days=30)`
- 参照: `knowledge_usage_stats`（view / click など）

### 3) 高評価ナレッジ
- 取得元: `FeedbackClient.get_top_rated_knowledge(limit=10)`
- 参照: `knowledge_feedback` → `knowledge_ratings`（VIEW）
- 条件: feedback_count >= 3

### 4) ナレッジ統計API
- `/api/knowledge/<id>/stats`
  - 使用統計: `get_knowledge_usage_stats`
  - 評価サマリー: `get_knowledge_rating`

## 関連ファイル
- `src/webui/app.py`
  - `analytics()`
  - `api_knowledge_stats()`
- `src/mcp/feedback_client.py`
- `db/feedback_schema.sql`
- `src/core/analytics.py`（高度分析エンジン）

## 注意点
- 画面側はDB集計の結果をそのまま表示するだけです。
- 高度分析（トレンドや相関）は `AnalyticsEngine` を呼び出す必要があります。

## 拡張案
- `AnalyticsEngine` の結果をAPI化して `/analytics` に統合
- 日次/週次の集計キャッシュ
- 組織/システム単位のドリルダウン
