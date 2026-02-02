# 🤖 自動エラー検知・修復システム
# Auto Error Detection & Repair System

## 📋 概要

本システムは、ClaudeCode（Linuxネイティブ）とGitHub Actionsを組み合わせた、
自動エラー検知・修復ループシステムです。

### アーキテクチャ

```
┌──────────────────────────────────────────────┐
│ GitHub Actions（制御レイヤ）                │
│                                              │
│ ・schedule / workflow_dispatch               │
│ ・Run 単位で最大15回ループ                   │
│ ・state.json による Run 間状態管理           │
│ ・再実行 or 停止の判断                       │
└───────────────┬────────────────────────────┘
                │ 呼び出し
                ▼
┌──────────────────────────────────────────────┐
│ ClaudeCode（Linuxネイティブ）                │
│ auto_fix_daemon.py（修復レイヤ）             │
│                                              │
│ ・ヘルスチェック                             │
│ ・ログスキャン                               │
│ ・エラーパターン照合                         │
│ ・自動修復アクション実行                     │
│ ・クールダウン制御（300秒）                  │
└──────────────────────────────────────────────┘
```

## 🎯 設計原則

### レイヤ分離

| レイヤ | 役割 | 原則 |
|------|------|------|
| 制御レイヤ | 実行管理・判断 | 考えない・常駐しない・必ず終わる |
| 修復レイヤ | 検知・修復実行 | 考える・直す・判断しない |

### GitHub Actions の責務（制御レイヤ）

✅ **やること**
- Workflow の起動（cron / 手動）
- 1 Run あたり最大15回の修復ループ制御
- テスト成功／失敗の判定
- state.json への状態保存
- Run を必ず終了させる

❌ **やらないこと**
- エラー内容の解釈
- 修復方法の判断
- sleep / wait による常駐
- 無限ループ処理

### ClaudeCode / auto_fix_daemon の責務（修復レイヤ）

✅ **やること**
- ログ・テスト結果の読解
- error_patterns.json に基づくエラー検知
- ヘルスチェック（DB / Redis / Disk / HTTP 等）
- 自動修復アクション実行
- クールダウン管理（同一エラー300秒）
- 修復ログ出力

❌ **やらないこと**
- 実行回数管理
- 継続／停止判断
- 無限実行
- Run 間制御

## 📁 ファイル構成

```
.
├── .github/
│   └── workflows/
│       └── auto_repair.yml          # GitHub Actions ワークフロー（制御レイヤ）
├── config/
│   └── error_patterns.json          # エラーパターン定義
├── data/
│   ├── state.json                   # Run間の状態管理
│   └── repair_log.json              # 修復ログ（自動生成）
└── scripts/
    └── auto_fix_daemon.py           # 自動修復デーモン（修復レイヤ）
```

## 🔧 設定ファイル

### error_patterns.json

エラーパターンと修復アクションを定義します。

```json
{
  "patterns": [
    {
      "id": "database_connection_error",
      "name": "Database Connection Error",
      "patterns": ["sqlite3.OperationalError", "database is locked"],
      "severity": "critical",
      "auto_repair": true,
      "actions": [
        {
          "type": "restart_service",
          "service": "database",
          "wait_seconds": 5
        }
      ],
      "cooldown_seconds": 300
    }
  ],
  "health_checks": [
    {
      "name": "database",
      "type": "file_exists",
      "path": "db/knowledge.db",
      "required": true
    }
  ]
}
```

#### サポートされているアクションタイプ

1. **restart_service**: サービスの再起動
2. **check_file_permissions**: ファイル権限の確認
3. **cleanup_temp_files**: 一時ファイルのクリーンアップ
4. **rotate_logs**: ログローテーション
5. **install_dependencies**: 依存関係のインストール
6. **wait_and_retry**: 待機してリトライ

### state.json

Run間の状態を管理します（GitHub Actionsが自動更新）。

```json
{
  "retry_required": false,
  "run_count": 0,
  "last_error_id": null,
  "last_error_summary": null,
  "last_attempt_at": null,
  "cooldown_until": null,
  "last_run_at": null,
  "last_run_result": null,
  "last_iterations": 0,
  "last_repairs_made": 0
}
```

## 🚀 使用方法

### 自動実行（推奨）

GitHub Actionsのスケジュール機能により、5分間隔で自動実行されます。

```yaml
on:
  schedule:
    - cron: '*/5 * * * *'
```

### 手動実行

GitHub Actionsの画面から手動でワークフローを実行できます。

1. GitHub リポジトリの「Actions」タブを開く
2. 「Auto Error Detection & Repair Loop」を選択
3. 「Run workflow」をクリック
4. オプション：`max_iterations`（デフォルト: 15）を設定
5. 「Run workflow」をクリックして実行

### ローカルでのテスト

```bash
# テスト出力をパイプ
python3 scripts/test_workflow.py 2>&1 | python3 scripts/auto_fix_daemon.py

# ファイルから読み込み
python3 scripts/auto_fix_daemon.py --test-output test_output.txt

# 直接文字列として渡す
python3 scripts/auto_fix_daemon.py --test-output "ModuleNotFoundError: No module named 'flask'"
```

## 🔄 実行フロー

### 1 Run 内の流れ

```
1. Workflow 起動
   ↓
2. テスト実行
   ↓
3. 成功？ → Run 終了 ✅
   ↓ 失敗
4. ClaudeCode 呼び出し（エラー検知・修復）
   ↓
5. 修復成功？
   ↓ Yes
6. 再テスト（最大15回まで繰り返し）
   ↓ No / 上限到達
7. state.json 更新 → Run 終了 ⏸️
```

### 疑似無限ループの仕組み

```
Run #1（最大15回修復）→ 終了
   ↓（5分後）
Run #2（最大15回修復）→ 終了
   ↓（5分後）
Run #3（最大15回修復）→ 終了
   ...
```

- 無限に見えるが **Run は必ず短時間で終了**
- GitHub Actions の実行モデルとして健全
- テストが成功すれば自動的に停止

## 📊 監視とログ

### GitHub Actions Summary

各Run終了後、以下の情報がサマリーに表示されます：

- Run Count: 実行回数
- Iterations: イテレーション数
- Repairs Made: 修復回数
- Final Status: 最終ステータス
- Current State: 現在の状態（state.json）
- Recent Repairs: 最近の修復履歴

### 修復ログ

`data/repair_log.json` に修復履歴が記録されます（最新100件を保持）。

```json
[
  {
    "timestamp": "2026-02-02T06:00:00+00:00",
    "action": {
      "error_id": "database_connection_error",
      "error_name": "Database Connection Error",
      "action": {...},
      "result": {
        "success": true,
        "message": "Service database restarted successfully"
      }
    }
  }
]
```

## 🔐 セキュリティ考慮事項

### 安全な修復アクション

- ファイル削除は `/tmp` 配下のみ
- システムコマンドは制限された範囲で実行
- 依存関係のインストールは `requirements.txt` のみ

### クールダウン機構

同一エラーに対して連続して修復アクションを実行しないよう、
デフォルトで300秒（5分）のクールダウン期間を設けています。

## 🛠️ カスタマイズ

### 新しいエラーパターンの追加

`config/error_patterns.json` に新しいパターンを追加：

```json
{
  "id": "custom_error",
  "name": "Custom Error Name",
  "patterns": ["error pattern regex"],
  "severity": "high",
  "auto_repair": true,
  "actions": [
    {
      "type": "custom_action",
      ...
    }
  ],
  "cooldown_seconds": 300
}
```

### ヘルスチェックの追加

```json
{
  "name": "custom_check",
  "type": "file_exists",
  "path": "path/to/file",
  "required": true
}
```

### スケジュールの変更

`.github/workflows/auto_repair.yml` の cron 式を変更：

```yaml
on:
  schedule:
    # 例：10分間隔
    - cron: '*/10 * * * *'
```

## 🔄 systemd との棲み分け

| 実行環境 | 正解モデル |
|--------|-----------|
| 本番サーバ | systemd + auto_fix_daemon --continuous |
| GitHub Actions | Run 単発 + state.json 連携 |

**重要**: GitHub Actions では `--continuous` モードは使用しません。

## 🐛 トラブルシューティング

### ワークフローが起動しない

- リポジトリの Actions が有効になっているか確認
- cron スケジュールが正しいか確認
- GitHub Actions の実行制限に達していないか確認

### 修復が動作しない

- `error_patterns.json` のパターンが正しいか確認
- クールダウン期間中でないか確認（`state.json`）
- `auto_repair: true` が設定されているか確認

### 無限ループが止まらない

- 正常な動作です（Run は必ず終了します）
- テストが成功すれば自動的に停止します
- 手動で停止する場合は、ワークフローを無効化してください

## 📚 参考資料

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [ITSM Best Practices](https://www.itil.org/)
- ISO/IEC 20000 - IT Service Management

## 📝 ライセンス

このシステムは Mirai IT Knowledge System の一部として提供されます。

---

**最終更新**: 2026-02-02
**バージョン**: 1.0.0
