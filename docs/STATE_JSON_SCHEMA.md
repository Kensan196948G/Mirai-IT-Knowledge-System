# state.json スキーマ定義書

## 概要

`state.json` は、GitHub Actions（制御レイヤ）と ClaudeCode（修復レイヤ）の間で Run 間の状態を共有するための **申し送りファイル** です。

## 設計原則

### レイヤ分離

| レイヤ | 読み取り | 書き込み | 判断 |
|-------|---------|---------|------|
| **GitHub Actions（制御レイヤ）** | ✅ | ❌ | ✅ retry_required を見て Run 継続/停止を判断 |
| **ClaudeCode（修復レイヤ）** | ✅ | ✅ | ❌ 状態を更新するだけ、判断しない |

### ファイル配置

```
<project_root>/state.json
```

- リポジトリルートに配置
- `.gitignore` に追加（Git管理外）
- GitHub Actions の Artifact として保存・復元

---

## スキーマ定義

### JSON Structure

```json
{
  "retry_required": boolean,
  "run_count": integer,
  "last_error_id": string,
  "last_error_summary": string,
  "last_attempt_at": string (ISO 8601),
  "cooldown_until": string (ISO 8601),
  "total_errors_detected": integer,
  "total_fixes_attempted": integer,
  "total_fixes_succeeded": integer,
  "last_health_status": string,
  "continuous_failure_count": integer,
  "created_at": string (ISO 8601),
  "updated_at": string (ISO 8601)
}
```

### フィールド詳細

#### 必須フィールド

| フィールド | 型 | 説明 | 例 |
|----------|-----|------|-----|
| **retry_required** | boolean | 次回 Run が必要か（GitHub Actions が判断に使用） | `true` |
| **run_count** | integer | 累積 Run 実行回数 | `5` |
| **last_error_id** | string | 最後に検出されたエラーID | `"database_connection_error"` |
| **last_error_summary** | string | エラーの要約 | `"PostgreSQL connection refused"` |
| **last_attempt_at** | string | 最後の修復試行日時（ISO 8601） | `"2026-02-02T20:15:00+09:00"` |
| **cooldown_until** | string | クールダウン終了日時（ISO 8601） | `"2026-02-02T20:20:00+09:00"` |

#### 統計フィールド

| フィールド | 型 | 説明 | 例 |
|----------|-----|------|-----|
| **total_errors_detected** | integer | 累積検出エラー数 | `23` |
| **total_fixes_attempted** | integer | 累積修復試行数 | `18` |
| **total_fixes_succeeded** | integer | 累積修復成功数 | `15` |
| **last_health_status** | string | 最後のヘルスチェック結果 | `"degraded"` |
| **continuous_failure_count** | integer | 連続失敗回数（3回で critical） | `2` |

#### メタデータフィールド

| フィールド | 型 | 説明 | 例 |
|----------|-----|------|-----|
| **created_at** | string | 初回作成日時（ISO 8601） | `"2026-02-02T10:00:00+09:00"` |
| **updated_at** | string | 最終更新日時（ISO 8601） | `"2026-02-02T20:15:00+09:00"` |

---

## 初期状態（テンプレート）

```json
{
  "retry_required": false,
  "run_count": 0,
  "last_error_id": "",
  "last_error_summary": "",
  "last_attempt_at": "",
  "cooldown_until": "",
  "total_errors_detected": 0,
  "total_fixes_attempted": 0,
  "total_fixes_succeeded": 0,
  "last_health_status": "unknown",
  "continuous_failure_count": 0,
  "created_at": "2026-02-02T00:00:00+09:00",
  "updated_at": "2026-02-02T00:00:00+09:00"
}
```

---

## 状態遷移パターン

### パターン 1: 正常（エラーなし）

```
Run #1: エラーなし
  → retry_required = false
  → Run 終了

（5分後）

Run #2: スキップ（retry_required = false）
```

### パターン 2: エラー検出 → 修復成功

```
Run #1: エラー検出
  → ClaudeCode が修復
  → retry_required = false
  → Run 終了

（5分後）

Run #2: 正常確認
  → retry_required = false
```

### パターン 3: エラー検出 → 修復失敗 → クールダウン

```
Run #1: エラー検出
  → ClaudeCode が修復試行
  → 失敗
  → retry_required = true
  → cooldown_until = 現在時刻 + 300秒
  → Run 終了

（5分後）

Run #2: クールダウン中
  → retry_required = true (変更なし)
  → Run 終了

（5分後）

Run #3: クールダウン解除
  → 再修復試行
```

### パターン 4: 連続失敗 → Critical

```
Run #1: エラー → 修復失敗
  → continuous_failure_count = 1
  → retry_required = true

Run #2: エラー → 修復失敗
  → continuous_failure_count = 2
  → retry_required = true

Run #3: エラー → 修復失敗
  → continuous_failure_count = 3
  → last_health_status = "critical"
  → GitHub Issue 自動作成
  → retry_required = false (手動対応待ち)
```

---

## GitHub Actions での使用例

```yaml
- name: Load state
  id: load_state
  run: |
    if [ -f state.json ]; then
      retry_required=$(jq -r '.retry_required' state.json)
      run_count=$(jq -r '.run_count' state.json)
      echo "retry_required=$retry_required" >> $GITHUB_OUTPUT
      echo "run_count=$run_count" >> $GITHUB_OUTPUT
    else
      echo "retry_required=false" >> $GITHUB_OUTPUT
      echo "run_count=0" >> $GITHUB_OUTPUT
    fi

- name: Check if retry needed
  if: steps.load_state.outputs.retry_required == 'false'
  run: |
    echo "No retry required, skipping..."
    exit 0
```

---

## ClaudeCode での使用例

```python
from pathlib import Path
import json
from datetime import datetime, timedelta

class StateManager:
    def __init__(self, state_file: str = "state.json"):
        self.state_file = Path(state_file)

    def load_state(self) -> dict:
        """状態を読み込み"""
        if not self.state_file.exists():
            return self._get_initial_state()

        with open(self.state_file, 'r') as f:
            return json.load(f)

    def save_state(self, state: dict):
        """状態を保存"""
        state['updated_at'] = datetime.now().isoformat()
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

    def update_after_fix(self, error_id: str, success: bool):
        """修復後の状態更新"""
        state = self.load_state()
        state['run_count'] += 1
        state['last_error_id'] = error_id
        state['total_fixes_attempted'] += 1

        if success:
            state['retry_required'] = False
            state['total_fixes_succeeded'] += 1
            state['continuous_failure_count'] = 0
        else:
            state['retry_required'] = True
            state['continuous_failure_count'] += 1
            state['cooldown_until'] = (
                datetime.now() + timedelta(seconds=300)
            ).isoformat()

        self.save_state(state)
```

---

## セキュリティ考慮事項

### ⚠️ 注意事項

1. **機密情報を含めない**
   - API キー、パスワード、トークンは絶対に保存しない
   - エラーメッセージに機密情報が含まれる場合はマスキング

2. **Git管理から除外**
   ```gitignore
   # .gitignore
   state.json
   state.json.bak
   ```

3. **GitHub Actions Artifact として保存**
   - Run 間で状態を引き継ぐため、Artifact として保存・復元
   - retention-days: 7 で自動削除

---

## トラブルシューティング

### state.json が壊れた場合

```bash
# バックアップから復元
cp state.json.bak state.json

# 初期化
echo '{
  "retry_required": false,
  "run_count": 0,
  "last_error_id": "",
  "last_error_summary": "",
  "last_attempt_at": "",
  "cooldown_until": "",
  "total_errors_detected": 0,
  "total_fixes_attempted": 0,
  "total_fixes_succeeded": 0,
  "last_health_status": "unknown",
  "continuous_failure_count": 0,
  "created_at": "'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'",
  "updated_at": "'"$(date -u +%Y-%m-%dT%H:%M:%SZ)"'"
}' > state.json
```

---

## 変更履歴

| バージョン | 日付 | 変更内容 |
|----------|------|---------|
| 1.0.0 | 2026-02-02 | 初版作成 |

---

**このドキュメントは統合運用設計書に基づいて作成されました**
