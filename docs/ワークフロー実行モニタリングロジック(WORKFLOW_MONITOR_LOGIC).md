# ワークフロー実行モニタリング ロジック (WORKFLOW_MONITOR_LOGIC)

## 概要
`/workflows/monitor` はワークフローの直近実行を一覧表示し、詳細APIでサブエージェント/フックのログを確認できる画面です。

## 対象画面 / API
- 画面: `/workflows/monitor`
- API:
  - `/api/workflows/recent`
  - `/api/workflows/<execution_id>`

## 主要ロジック
### 1) 画面表示
- `SQLiteClient.get_recent_workflow_executions(limit=20)` を呼び出し、最新の実行を表示
- テンプレート: `workflow_monitor.html`

### 2) 詳細取得API
- `get_workflow_execution(execution_id)` で実行概要
- `get_subagent_logs(execution_id)` でサブエージェントのログ
- `get_hook_logs(execution_id)` でフックのログ
- 上記をJSONとして返却

## 参照テーブル（DB）
- `workflow_executions`
- `subagent_logs`
- `hook_logs`

## 関連ファイル
- `src/webui/app.py`
  - `workflow_monitor()`
  - `api_recent_workflows()`
  - `api_workflow_detail()`
- `src/mcp/sqlite_client.py`
  - `get_recent_workflow_executions()`
  - `get_workflow_execution()`
  - `get_subagent_logs()`
  - `get_hook_logs()`
- `src/webui/templates/workflow_monitor.html`

## 注意点
- 取得件数は `limit` で制御（デフォルト20件）
- ログの並び順は作成時刻/トリガー時刻基準

## 拡張案
- 実行時間のヒストグラム表示
- 失敗率の可視化
- 期間フィルタや担当者フィルタの追加
