# 📋 Mirai IT Knowledge System - 次の開発ステップ

**更新日**: 2026-02-03
**現在フェーズ**: Phase 5 - テスト・品質保証

---

## ✅ 完了済み環境整備

### インストール済み
- ✅ Python 3.12.3 仮想環境 (venv)
- ✅ Flask 3.1.2
- ✅ Anthropic SDK 0.77.0
- ✅ Google Generative AI 0.8.6
- ✅ pytest 9.0.2
- ✅ 全依存パッケージ

### 設定完了
- ✅ SubAgents: 7つ実装 (Architect, KnowledgeCurator, ITSMExpert, DevOps, QA, Coordinator, Documenter)
- ✅ Hooks: 5つ実装 (PreTask, PostTask, DuplicateCheck, DeviationCheck, AutoSummary)
- ✅ MCP: 9サーバー設定 (github, sqlite-dev, sqlite-prod, brave-search, context7, memory, claude-mem, sequential-thinking, playwright)
- ✅ データベース: knowledge_dev.db, knowledge.db (11テーブル)
- ✅ 環境設定ファイル: .env.development, .env.production

---

## ⚠️ 要設定項目（ユーザー操作必要）

### 1. APIキー設定

`.env.development` を編集してAPIキーを設定：

```bash
# ファイル編集
nano .env.development

# 設定が必要な項目
ANTHROPIC_API_KEY=sk-ant-xxxxx...
GEMINI_API_KEY=xxxxx...
PERPLEXITY_API_KEY=xxxxx...
GITHUB_TOKEN=ghp_xxxxx...
```

### 2. SSL証明書生成（HTTPS対応）

```bash
# 証明書生成スクリプト実行
sudo bash scripts/generate_ssl_certs.sh

# または手動生成
sudo mkdir -p /etc/ssl/mirai-knowledge
sudo openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout /etc/ssl/mirai-knowledge/dev-key.pem \
  -out /etc/ssl/mirai-knowledge/dev-cert.pem \
  -days 365 \
  -subj "/CN=192.168.0.187"
```

---

## 🎯 次の開発ステップ（優先順位付き）

### 🔴 Phase 5.1: 即時実行推奨（HIGH Priority）

#### ステップ 1: WebUI起動テスト

```bash
# 仮想環境有効化
source venv/bin/activate

# 開発サーバー起動
python3 src/webui/app.py
```

**期待結果:**
- サーバー起動: https://192.168.0.187:8888
- アクセス可能な画面:
  - `/` - ホーム（統計・最近のナレッジ）
  - `/knowledge/search` - 検索
  - `/knowledge/create` - ナレッジ作成
  - `/analytics` - 分析ダッシュボード
  - `/dashboard` - ワークフロー監視

**確認項目:**
- [ ] サーバーが起動する
- [ ] WebUIにアクセスできる
- [ ] データベース接続が正常
- [ ] 既存ナレッジ（1件）が表示される

---

#### ステップ 2: ワークフロー統合テスト

```bash
source venv/bin/activate
python3 scripts/test_workflow.py
```

**期待結果:**
- Incident/Problemケースのテスト成功
- 実行時間: 1.4〜1.6秒
- 品質スコア: 67-80%
- 7つのSubAgentすべて実行
- 5つのHooksすべて実行

**確認項目:**
- [ ] SubAgent並列実行成功
- [ ] Hooks動作確認
- [ ] データベース保存確認
- [ ] Markdownファイル生成確認

---

#### ステップ 3: SubAgent個別テスト

```bash
source venv/bin/activate

# 全SubAgentテスト
pytest tests/test_subagent_*.py -v

# 個別実行例
pytest tests/test_subagent_architect.py -v
pytest tests/test_subagent_itsm_expert.py -v
```

**期待結果:**
- 7つのSubAgentテストすべて成功
- エラーなし

---

### 🟡 Phase 5.2: 品質保証（MEDIUM Priority）

#### ステップ 4: Hooks詳細テスト

```bash
pytest tests/test_hooks_detailed.py -v
```

**確認項目:**
- [ ] 重複検知精度（類似度85%閾値）
- [ ] ITSM逸脱検知精度
- [ ] 自動要約生成品質

---

#### ステップ 5: MCP統合動作確認

**claude-mem テスト:**
```bash
# 現在の会話をインデックス
# Claude Code内から以下を実行
mcp__claude-mem__index_conversations
```

**context7 テスト:**
```bash
# ライブラリドキュメント取得テスト
# 例: Flaskのドキュメント検索
```

**github テスト:**
```bash
# リポジトリ情報取得
mcp__github__get_file_contents
```

---

#### ステップ 6: パフォーマンステスト

```bash
# ストレステストデータ生成
python3 scripts/generate_stress_test_data.py

# パフォーマンス計測
pytest tests/test_performance.py -v
```

**確認項目:**
- [ ] 100件のナレッジ作成時間
- [ ] 検索レスポンス時間
- [ ] メモリ使用量

---

### 🟢 Phase 5.3: ドキュメント・コード品質（LOW Priority）

#### ステップ 7: テストカバレッジ向上

```bash
# カバレッジ計測
pytest --cov=src --cov-report=html tests/

# レポート確認
open htmlcov/index.html
```

**目標:**
- [ ] テストカバレッジ 80%以上
- [ ] クリティカルパスは100%カバレッジ

---

#### ステップ 8: ドキュメント更新

**更新が必要なドキュメント:**
- [ ] API仕様書 (`docs/API_SPEC.md`)
- [ ] 運用マニュアル (`docs/OPERATIONS.md`)
- [ ] トラブルシューティングガイド (`docs/TROUBLESHOOTING.md`)

---

### 🚀 Phase 6: 本番展開準備

#### ステップ 9: 本番環境デプロイ

```bash
# Worktreeで本番ブランチ作成
bash scripts/worktree_setup.sh

# 本番環境起動
bash scripts/start_prod.sh
```

**確認項目:**
- [ ] 本番DBへの移行
- [ ] SSL証明書設定
- [ ] systemdサービス登録
- [ ] ログローテーション設定

---

#### ステップ 10: 監視・運用設定

```bash
# ヘルスモニター起動
python3 scripts/health_monitor.py

# Auto-repair デーモン起動
python3 scripts/auto_fix_daemon.py
```

**設定項目:**
- [ ] ログ監視
- [ ] エラー通知（メール/Slack）
- [ ] バックアップスケジュール
- [ ] パフォーマンス監視

---

## 📊 開発進捗サマリー

```
Phase 1: ✅ 完了 - 基盤構築
Phase 2: ✅ 完了 - AIエージェント統合
Phase 3: ✅ 完了 - AI対話機能強化
Phase 4: ✅ 完了 - AI検索機能強化
Phase 5: 🔄 70% - テスト・品質保証
Phase 6: 📋 0% - 本番展開準備
```

**全体進捗**: 約85%完了

---

## 🎬 クイックスタートコマンド

### 1. 開発サーバー起動

```bash
source venv/bin/activate
python3 src/webui/app.py
```

### 2. テスト実行

```bash
source venv/bin/activate
pytest tests/ -v
```

### 3. 環境チェック

```bash
bash scripts/check_environment.sh
```

---

## 📞 サポート・トラブルシューティング

### よくある問題

**Q: WebUIが起動しない**
```bash
# ポート使用状況確認
lsof -i:8888

# プロセス確認
ps aux | grep "app.py"
```

**Q: APIエラーが発生する**
```bash
# APIキー確認
source venv/bin/activate
python3 -c "import os; from dotenv import load_dotenv; load_dotenv('.env.development'); print('ANTHROPIC_API_KEY:', os.getenv('ANTHROPIC_API_KEY')[:10] if os.getenv('ANTHROPIC_API_KEY') else 'Not set')"
```

**Q: データベースエラー**
```bash
# データベース再初期化（注意: データ消去）
source venv/bin/activate
python3 scripts/init_db.py --force --env development
```

---

## 🎯 推奨実行順序

1. **今すぐ**: APIキー設定 → WebUI起動テスト
2. **次に**: ワークフロー統合テスト → SubAgent個別テスト
3. **その後**: MCP統合確認 → パフォーマンステスト
4. **最後に**: ドキュメント整備 → 本番展開準備

---

**作成日**: 2026-02-03
**作成者**: Claude Code Workflow
**プロジェクト**: Mirai IT Knowledge System v2.0
