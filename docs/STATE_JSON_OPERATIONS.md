# state.json 運用ガイド

## 📋 概要

このドキュメントは、state.json を使用した自動エラー検知・修復システムの **運用担当者向けガイド** です。

日常的な運用タスク、トラブルシューティング、ベストプラクティスを記載しています。

---

## 🎯 対象読者

- システム運用担当者
- DevOps エンジニア
- SRE（Site Reliability Engineer）
- トラブルシューティング担当者

---

## 🚀 クイックスタート

### 1. 現在の状態を確認

```bash
# 状態表示
python scripts/state_manager_cli.py show
```

### 2. システムが正常か確認

```bash
# ヘルスステータスが "HEALTHY" ならOK
# retry_required が False ならOK
```

### 3. 統計情報を確認

```bash
# 統計表示
python scripts/state_manager_cli.py stats
```

---

## 📊 日常運用タスク

### 定期確認（毎日）

#### 朝の確認

```bash
# 1. 状態確認
python scripts/state_manager_cli.py show

# 2. 統計確認
python scripts/state_manager_cli.py stats

# 3. GitHub Actions の最新実行を確認
gh run list --workflow=auto-error-fix-continuous.yml --limit 5
```

**確認ポイント**:
- ✅ retry_required が False
- ✅ last_health_status が "healthy"
- ✅ continuous_failure_count が 0
- ✅ 修復成功率が 80% 以上

#### 夕方の確認

```bash
# 1日の統計を JSON で取得
python scripts/state_manager_cli.py stats --format json > daily_stats.json

# 分析
cat daily_stats.json | jq '{
  health: .last_health_status,
  errors: .total_errors_detected,
  success_rate: .success_rate
}'
```

---

## 🔧 運用シナリオ別ガイド

### シナリオ 1: システムが正常

**状態**:
```
retry_required: False
last_health_status: HEALTHY
continuous_failure_count: 0
```

**対応**: なし（自動監視継続）

---

### シナリオ 2: 一時的なエラー（修復済み）

**状態**:
```
retry_required: False
last_health_status: HEALTHY
total_errors_detected: 5
total_fixes_succeeded: 5
success_rate: 100%
```

**対応**:
1. エラーログを確認
   ```bash
   tail -100 logs/auto_fix.log
   ```
2. 傾向分析（同じエラーが繰り返されていないか）
3. 予防策の検討

---

### シナリオ 3: エラー継続中（修復失敗）

**状態**:
```
retry_required: True
last_health_status: DEGRADED
continuous_failure_count: 2
cooldown_until: 2026-02-02T15:00:00+09:00
```

**対応**:
1. **緊急度確認**
   ```bash
   python scripts/state_manager_cli.py show --verbose
   ```

2. **エラー詳細を確認**
   ```bash
   # 最後のエラーを確認
   grep -A 10 "$(cat state.json | jq -r .last_error_id)" logs/auto_fix.log | tail -20
   ```

3. **手動修復**
   - データベース接続エラー → DB サービス確認
   - ディスク容量不足 → 古いログ削除
   - ポート使用中 → プロセス確認

4. **修復後にリセット**
   ```bash
   python scripts/state_manager_cli.py reset --confirm
   ```

---

### シナリオ 4: Critical 状態

**状態**:
```
retry_required: True
last_health_status: CRITICAL
continuous_failure_count: 3
```

**対応**:
1. **即座に対応が必要**
   - GitHub Issue が自動作成されているか確認
   - オンコール担当者に通知

2. **ログ収集**
   ```bash
   # エラーログをまとめて収集
   tar -czf error_logs_$(date +%Y%m%d_%H%M%S).tar.gz logs/ state.json
   ```

3. **手動介入**
   - システム全体のヘルスチェック
   - 関連サービスの再起動
   - データベースの整合性確認

4. **復旧後**
   ```bash
   # スキーマ検証
   python scripts/state_manager_cli.py validate

   # リセット
   python scripts/state_manager_cli.py reset --confirm

   # 状態確認
   python scripts/state_manager_cli.py show
   ```

---

## 🛠️ トラブルシューティング

### 問題 1: state.json が見つからない

**症状**:
```
❌ state.json が存在しません
```

**原因**:
- 初回起動
- ファイルが削除された
- パスが間違っている

**解決方法**:
```bash
# 初期化
python scripts/state_manager_cli.py init
```

---

### 問題 2: state.json が壊れている

**症状**:
```
❌ JSON パースエラー
```

**原因**:
- ファイルが破損
- 手動編集ミス
- ディスク I/O エラー

**解決方法**:

```bash
# 方法 1: バックアップから復元
cp state.json.bak state.json

# 方法 2: リセットバックアップから復元
cp state.json.reset_backup state.json

# 方法 3: 初期化
python scripts/state_manager_cli.py init --force

# 検証
python scripts/state_manager_cli.py validate
```

---

### 問題 3: クールダウン期間が長すぎる

**症状**:
```
⏸️ In cooldown period until 2026-02-02T20:00:00+09:00
```

**原因**:
- 修復失敗により自動設定されたクールダウン（300秒）
- 手動修復完了後もクールダウンが残っている

**解決方法**:

```bash
# 手動修復完了後にリセット
python scripts/state_manager_cli.py reset --confirm

# または state.json を直接編集
# "cooldown_until": "" に設定
```

---

### 問題 4: 連続失敗カウントが増え続ける

**症状**:
```
continuous_failure_count: 5
last_health_status: CRITICAL
```

**原因**:
- 根本原因が解決されていない
- 自動修復では対応できない問題

**解決方法**:

1. **根本原因を特定**
   ```bash
   # エラーログ確認
   python scripts/state_manager_cli.py show --verbose

   # 最近のエラーを確認
   tail -100 logs/auto_fix.log | grep ERROR
   ```

2. **手動で根本対応**
   - システムリソース確認
   - 設定ファイル確認
   - 外部依存サービス確認

3. **対応後にリセット**
   ```bash
   python scripts/state_manager_cli.py reset --confirm
   ```

---

### 問題 5: 統計情報がおかしい

**症状**:
```
total_errors_detected: 1000
total_fixes_attempted: 0
```

**原因**:
- state.json の不整合
- 手動編集ミス

**解決方法**:

```bash
# スキーマ検証
python scripts/state_manager_cli.py validate

# 検証エラーがあればリセット
python scripts/state_manager_cli.py reset --confirm
```

---

## 📈 ベストプラクティス

### 1. 定期バックアップ

```bash
# 毎日バックアップ（cron 推奨）
0 0 * * * cp /path/to/state.json /path/to/backups/state_$(date +\%Y\%m\%d).json
```

### 2. 統計情報の記録

```bash
# 日次統計を記録
python scripts/state_manager_cli.py stats --format json >> logs/daily_stats.jsonl
```

### 3. アラート設定

```bash
# continuous_failure_count が 3 以上でアラート
FAILURE_COUNT=$(python scripts/state_manager_cli.py stats --format json | jq -r '.continuous_failure_count')

if [ "$FAILURE_COUNT" -ge 3 ]; then
  echo "🚨 Critical: 連続失敗 $FAILURE_COUNT 回" | mail -s "Auto-Fix Alert" admin@example.com
fi
```

### 4. 手動介入後の手順

```bash
# 1. 修復内容をログに記録
echo "$(date) - [MANUAL] - 手動修復完了: 詳細..." >> logs/manual_fix.log

# 2. state.json をリセット
python scripts/state_manager_cli.py reset --confirm

# 3. 動作確認
python scripts/state_manager_cli.py show

# 4. 次回実行を監視
# （5分後に自動実行される）
```

---

## 🔍 高度な使用方法

### カスタムパスの state.json

```bash
# 環境別の state.json を管理
python scripts/state_manager_cli.py --state-file /path/to/production/state.json show
python scripts/state_manager_cli.py --state-file /path/to/staging/state.json show
```

### パイプライン統合

```bash
# JSON 出力をパイプで処理
python scripts/state_manager_cli.py stats --format json | jq '.success_rate'

# CSV 出力でデータ分析
python scripts/state_manager_cli.py stats --format csv | awk -F',' '{print $1, $8}'
```

### 監視スクリプト例

```bash
#!/bin/bash
# state_monitor.sh - 定期監視スクリプト

RETRY_REQUIRED=$(python scripts/state_manager_cli.py stats --format json | jq -r '.retry_required')
HEALTH_STATUS=$(python scripts/state_manager_cli.py stats --format json | jq -r '.last_health_status')

if [ "$RETRY_REQUIRED" = "true" ] && [ "$HEALTH_STATUS" = "critical" ]; then
  echo "🚨 Critical Alert: システムが Critical 状態です"
  # 通知処理
fi
```

---

## 📞 エスカレーション基準

| 状態 | 対応レベル | 対応時間 |
|-----|----------|---------|
| **healthy** | 監視継続 | - |
| **degraded** | Level 1（運用チーム） | 1時間以内 |
| **critical** | Level 2（オンコール） | 即座 |
| **3回連続失敗** | Level 3（管理者） | 即座 |

---

## 🔗 関連ドキュメント

- [STATE_JSON_SCHEMA.md](STATE_JSON_SCHEMA.md) - スキーマ定義と技術仕様
- 統合運用設計書 - アーキテクチャと設計思想
- [health_monitor.py](../scripts/health_monitor.py) - ヘルスチェックツール

---

## 📝 よくある質問（FAQ）

### Q1: state.json はいつリセットすべきか？

**A**: 以下の場合にリセットを検討：
- 手動修復完了後
- システムアップグレード後
- 統計情報をクリアしたい時

### Q2: クールダウン期間中に強制実行したい

**A**: GitHub Actions の手動実行で `force_run: yes` を選択するか、state.json をリセット

### Q3: state.json を Git 管理すべきか？

**A**: **いいえ**。state.json は実行時の状態を保持するため、`.gitignore` で除外すべきです。

### Q4: 複数環境（dev/staging/prod）でどう管理するか？

**A**: 環境ごとに異なる state.json を使用：
```bash
--state-file /opt/app/state_production.json
--state-file /opt/app/state_staging.json
```

### Q5: state.json のバックアップ戦略は？

**A**: 推奨：
- 自動バックアップ: リセット時に `.reset_backup` が作成される
- 定期バックアップ: cron で日次バックアップ
- Artifact: GitHub Actions が 7日間保持

---

## 🎓 運用のコツ

### ヒント 1: ログと state.json を照合する

```bash
# エラー発生時刻と state.json の last_attempt_at を比較
python scripts/state_manager_cli.py show | grep last_attempt_at
grep "ERROR" logs/auto_fix.log | tail -5
```

### ヒント 2: 傾向分析

```bash
# 毎日の統計を記録
python scripts/state_manager_cli.py stats --format json >> logs/daily_state_stats.jsonl

# 週次レポート生成
cat logs/daily_state_stats.jsonl | jq -s 'map(.success_rate) | add / length'
```

### ヒント 3: プロアクティブな対応

```bash
# continuous_failure_count が 2 になったら即座に確認
# （3になる前に対応）
FAILURE_COUNT=$(python scripts/state_manager_cli.py stats --format json | jq -r '.continuous_failure_count')

if [ "$FAILURE_COUNT" -ge 2 ]; then
  echo "⚠️ Warning: 連続失敗が ${FAILURE_COUNT} 回です。確認してください。"
fi
```

---

## 🚨 緊急対応フローチャート

```
エラーアラート受信
    ↓
[状態確認]
python scripts/state_manager_cli.py show
    ↓
┌─────────────────────┐
│ last_health_status? │
└─────────────────────┘
    ↓           ↓           ↓
  healthy   degraded    critical
    ↓           ↓           ↓
  監視継続   1時間以内    即座に対応
              対応
                ↓
          [ログ確認]
          tail -100 logs/auto_fix.log
                ↓
          [手動修復]
          システム復旧作業
                ↓
          [リセット]
          python scripts/state_manager_cli.py reset --confirm
                ↓
          [確認]
          python scripts/state_manager_cli.py show
```

---

## 📝 運用チェックリスト

### 日次チェックリスト

- [ ] state.json の状態確認（`show`）
- [ ] 統計情報の確認（`stats`）
- [ ] GitHub Actions の実行履歴確認
- [ ] エラーログの確認（`logs/auto_fix.log`）
- [ ] ヘルスステータスが healthy か確認

### 週次チェックリスト

- [ ] 統計情報の傾向分析
- [ ] state.json のバックアップ確認
- [ ] エラーパターンの見直し（`scripts/error_patterns.json`）
- [ ] 修復成功率が 80% 以上か確認
- [ ] 不要なログファイルの削除

### 月次チェックリスト

- [ ] 自動修復システム全体のレビュー
- [ ] error_patterns.json の最適化
- [ ] 新しいエラーパターンの追加検討
- [ ] バックアップの整理（30日以上古いものを削除）
- [ ] 運用ドキュメントの更新

---

## 🎯 パフォーマンス指標（KPI）

### 推奨目標値

| 指標 | 目標値 | 警告閾値 | Critical 閾値 |
|-----|-------|---------|--------------|
| **修復成功率** | 90% 以上 | 70% 未満 | 50% 未満 |
| **連続失敗回数** | 0 | 2 | 3 |
| **ヘルスステータス** | healthy | degraded | critical |
| **1日あたりのエラー数** | 5 未満 | 10 以上 | 20 以上 |

### モニタリング方法

```bash
# 週次レポート生成例
cat << 'EOF' > weekly_report.sh
#!/bin/bash
STATS=$(python scripts/state_manager_cli.py stats --format json)

echo "## 週次レポート ($(date +%Y-%m-%d))"
echo ""
echo "| 指標 | 値 |"
echo "|------|-----|"
echo "| 修復成功率 | $(echo $STATS | jq -r .success_rate)% |"
echo "| 総エラー数 | $(echo $STATS | jq -r .total_errors_detected) |"
echo "| ヘルスステータス | $(echo $STATS | jq -r .last_health_status) |"
EOF

chmod +x weekly_report.sh
```

---

## 🔐 セキュリティ考慮事項

### 1. アクセス制御

```bash
# state.json のパーミッション設定
chmod 644 state.json
chown www-data:www-data state.json
```

### 2. ログのマスキング

state.json の `last_error_summary` には機密情報を含めない：
- API キー → マスキング
- パスワード → マスキング
- 個人情報 → マスキング

### 3. バックアップの保護

```bash
# バックアップディレクトリの権限
chmod 700 backups/
```

---

## 📞 サポート

### 問題が解決しない場合

1. **ログを収集**
   ```bash
   tar -czf support_$(date +%Y%m%d_%H%M%S).tar.gz \
     logs/ \
     state.json \
     scripts/error_patterns.json
   ```

2. **GitHub Issue を作成**
   - ログファイルを添付
   - state.json の内容（機密情報除く）
   - 発生時刻と再現手順

3. **エスカレーション**
   - Level 1: 運用チーム
   - Level 2: DevOps チーム
   - Level 3: 開発チーム

---

## 変更履歴

| バージョン | 日付 | 変更内容 |
|----------|------|---------|
| 1.0.0 | 2026-02-02 | 初版作成 |

---

**📚 関連ドキュメント**: [STATE_JSON_SCHEMA.md](STATE_JSON_SCHEMA.md) | [統合運用設計書](#)
