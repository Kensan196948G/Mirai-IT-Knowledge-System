# 🚀 自動修復システム クイックスタート
# Auto-Repair System Quick Start Guide

## 📖 はじめに

このガイドでは、自動エラー検知・修復システムを素早くセットアップして動作確認する手順を説明します。

## ⚡ クイックスタート（5分）

### 1. システムの有効化

GitHub Actionsは自動的に有効化されます。以下を確認してください：

```bash
# リポジトリをクローン（既に完了している場合はスキップ）
git clone https://github.com/Kensan196948G/Mirai-IT-Knowledge-System.git
cd Mirai-IT-Knowledge-System

# ファイルの存在確認
ls -la .github/workflows/auto_repair.yml
ls -la scripts/auto_fix_daemon.py
ls -la config/error_patterns.json
ls -la data/state.json
```

### 2. ローカルでのテスト

```bash
# 依存関係のインストール
pip install -r requirements.txt

# ヘルスチェックのテスト
echo "Test output" | python3 scripts/auto_fix_daemon.py

# エラー検知のテスト
echo "ModuleNotFoundError: No module named 'test'" | python3 scripts/auto_fix_daemon.py
```

### 3. GitHub Actionsでの実行

#### 手動実行（推奨：最初のテスト）

1. GitHubリポジトリページを開く
2. **「Actions」** タブをクリック
3. **「Auto Error Detection & Repair Loop」** を選択
4. **「Run workflow」** をクリック
5. ブランチを選択し、**「Run workflow」** を実行

#### 自動実行の確認

スケジュールされた実行は5分間隔で自動的に開始されます：

```yaml
# .github/workflows/auto_repair.yml
on:
  schedule:
    - cron: '*/5 * * * *'  # 5分ごと
```

### 4. 実行結果の確認

#### GitHub Actions画面で確認

1. **「Actions」** タブを開く
2. 最新のワークフロー実行をクリック
3. **Summary** セクションで結果を確認：
   - Run Count（実行回数）
   - Iterations（イテレーション数）
   - Repairs Made（修復回数）
   - Final Status（最終ステータス）

#### ローカルで確認

```bash
# 状態ファイルの確認
cat data/state.json

# 修復ログの確認
cat data/repair_log.json

# 最新の修復履歴（最後の5件）
cat data/repair_log.json | python3 -m json.tool | tail -30
```

## 🔧 基本的な設定

### エラーパターンのカスタマイズ

`config/error_patterns.json` を編集して、プロジェクト固有のエラーパターンを追加：

```json
{
  "patterns": [
    {
      "id": "my_custom_error",
      "name": "My Custom Error",
      "patterns": ["CustomError:", "My specific error pattern"],
      "severity": "high",
      "auto_repair": true,
      "actions": [
        {
          "type": "install_dependencies",
          "file": "requirements.txt"
        }
      ],
      "cooldown_seconds": 300
    }
  ]
}
```

### スケジュールの調整

実行頻度を変更する場合は `.github/workflows/auto_repair.yml` を編集：

```yaml
on:
  schedule:
    # 10分ごとに変更する例
    - cron: '*/10 * * * *'
```

## 📊 モニタリング

### リアルタイム監視

```bash
# 状態ファイルをウォッチ（変更を監視）
watch -n 5 cat data/state.json

# 修復ログをリアルタイムで確認
tail -f data/repair_log.json
```

### GitHub Actions のメール通知

GitHub Actionsの設定でワークフローの失敗時に通知を受け取ることができます：

1. GitHubアカウント設定 → **Notifications**
2. **Actions** セクションで通知を有効化

## 🐛 トラブルシューティング

### よくある問題と解決方法

#### ❌ ワークフローが実行されない

**原因**: GitHub Actionsが無効化されている

**解決方法**:
```
1. リポジトリの「Settings」→「Actions」→「General」
2. 「Allow all actions and reusable workflows」を選択
3. 「Save」をクリック
```

#### ❌ 修復が動作しない

**原因**: クールダウン期間中

**解決方法**:
```bash
# 状態をリセット
cat > data/state.json << 'EOF'
{
  "retry_required": false,
  "run_count": 0,
  "last_error_id": null,
  "last_error_summary": null,
  "last_attempt_at": null,
  "cooldown_until": null
}
EOF

git add data/state.json
git commit -m "Reset auto-repair state"
git push
```

#### ❌ テストが常に失敗する

**原因**: 修復できないエラー

**解決方法**:
1. エラーログを確認: `cat data/repair_log.json`
2. `config/error_patterns.json` に適切なパターンを追加
3. 必要に応じて手動で修正

## 🎯 次のステップ

### 詳細ドキュメント

より詳しい情報は以下を参照：

- [AUTO_REPAIR_SYSTEM.md](AUTO_REPAIR_SYSTEM.md) - システム全体の詳細設計
- [error_patterns.json](../config/error_patterns.json) - エラーパターン定義
- [auto_fix_daemon.py](../scripts/auto_fix_daemon.py) - 修復デーモンのソースコード

### カスタマイズ例

#### 1. データベースエラーの修復

```json
{
  "id": "db_error",
  "name": "Database Error",
  "patterns": ["sqlite3.OperationalError"],
  "severity": "critical",
  "auto_repair": true,
  "actions": [
    {
      "type": "check_file_permissions",
      "path": "db/knowledge.db"
    }
  ],
  "cooldown_seconds": 300
}
```

#### 2. ディスク容量不足の対応

```json
{
  "id": "disk_full",
  "name": "Disk Space Full",
  "patterns": ["No space left on device"],
  "severity": "critical",
  "auto_repair": true,
  "actions": [
    {
      "type": "cleanup_temp_files",
      "paths": ["/tmp"]
    }
  ],
  "cooldown_seconds": 600
}
```

## 📚 参考リソース

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Python unittest Documentation](https://docs.python.org/3/library/unittest.html)
- [YAML Syntax](https://yaml.org/spec/1.2/spec.html)

## 💬 サポート

問題が発生した場合は、GitHubのIssuesでお問い合わせください。

---

**最終更新**: 2026-02-02
