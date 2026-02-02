# 変更履歴 (CHANGELOG)

Mirai IT Knowledge Systemsプロジェクトの変更履歴を記録します。

## 変更履歴の記録方法

すべての設定変更、機能追加、バグ修正は以下の形式で記録してください：

```markdown
## [バージョン] - YYYY-MM-DD

### 追加 (Added)
- 新機能の説明

### 変更 (Changed)
- 既存機能の変更内容

### 修正 (Fixed)
- バグ修正の内容

### 削除 (Removed)
- 削除された機能

### 設定変更 (Configuration)
- 設定ファイルの変更内容
- 変更前: [旧設定値]
- 変更後: [新設定値]
- 理由: [変更理由]
- 影響範囲: [影響を受けるコンポーネント]
```

---

## [2.2.0] - 2026-02-02

### 追加 (Added)
- **state.json Run間状態管理システム**
  - `StateManager` クラス追加（`scripts/auto_fix_daemon.py`）
  - Run間で状態を永続化し、GitHub Actions と連携
  - クールダウン管理（300秒）、連続失敗カウント機能
  - リトライ判定機能（retry_required フラグ）

- **state_manager_cli.py - CLI 管理ツール**
  - `scripts/state_manager_cli.py` - 運用担当者向け CLI ツール
  - 5つの主要コマンド（init, show, reset, stats, validate）
  - カラフルな出力で視認性向上
  - 3つの出力フォーマット（text, json, csv）
  - 統合テスト 12種類（100% 成功）

- **ドキュメント整備**
  - `docs/STATE_JSON_SCHEMA.md` - スキーマ定義と技術仕様（7.8KB）
  - `docs/STATE_JSON_OPERATIONS.md` - 運用ガイド（完全版）
  - `docs/INDEX.md` - 新ドキュメント追加

- **テストスイート**
  - `scripts/test_state_management.py` - StateManager 統合テスト（10種類）
  - `scripts/test_state_manager_cli.py` - CLI ツール統合テスト（12種類）
  - テスト成功率: 100% (22/22 passed)

### 変更 (Changed)
- `auto_fix_daemon.py` に StateManager クラスを統合（209行追加）
- エラー検出時・修復後に自動的に state.json を更新
- `.gitignore` に state.json を追加（Git管理外）

### 設定変更 (Configuration)
- **state.json 管理**
  - 変更前: Run間の状態管理なし
  - 変更後: state.json による永続化
  - 理由: GitHub Actions（制御レイヤ）との連携強化
  - 影響範囲: auto_fix_daemon.py, GitHub Actions ワークフロー

---

## [2.1.0] - 2026-01-20

### 追加 (Added)
- **WebUI-Sample**: 完全なデモWebUIを作成
  - HTML 5ページ（index, search, create, detail, sf-browser）
  - CSS 4ファイル（base, components, layout, responsive）
  - JavaScript 5ファイル（storage, mockData, itsmClassifier, search, ui）
  - README.md（使い方ガイド）
  - 合計約5,000行のコード

- **開発管理ドキュメント**: 新規作成
  - `開発状況総合レポート_2026-01-20.md` - 包括的な現状分析
  - `変更履歴(CHANGELOG).md` - 本ファイル
  - `開発フェーズ定義(DEVELOPMENT_PHASES).md` - 開発フェーズ管理
  - `開発ステップ管理(DEVELOPMENT_STEPS).md` - ステップバイステップガイド

### 変更 (Changed)
- **docsフォルダ構造**: ファイル名を日本語名（英語名）形式に統一
  - 従来: 英語名のみ（例: `DEPLOYMENT.md`）
  - 変更後: 日本語名（英語名）形式（例: `デプロイメントガイド(DEPLOYMENT).md`）
  - 理由: 日本語環境での可読性向上
  - 影響範囲: docsフォルダ内の全ドキュメント

### 設定変更 (Configuration)
- なし（本バージョンでは設定変更なし）

---

## [2.0.0] - 2025-12-31

### 追加 (Added)
- **ユーザーフィードバック機能**
  - ナレッジフィードバック（5段階評価、コメント）
  - システムフィードバック
  - 使用統計記録（view, use, share）
  - データベーステーブル: `knowledge_feedback`, `system_feedback`, `knowledge_usage_stats`

- **高度な分析機能**
  - トレンド分析
  - 人気ナレッジランキング（過去30日間）
  - 評価の高いナレッジ表示
  - フィードバックサマリー

- **AI対話機能**
  - WebSocket対応チャットUI（`/chat`）
  - 対話的なナレッジ作成
  - セッション管理
  - 対話履歴の保存

- **インテリジェント検索**
  - 自然言語理解
  - 意図分析
  - 高度な検索結果表示

- **設定機能**
  - システム設定変更UI（`/settings`）
  - 簡易認証機能（admin/admin123）
  - 設定履歴記録

- **MCP統合基盤**
  - Context7クライアント（スタブ）
  - Claude-Memクライアント（スタブ）
  - GitHubクライアント（スタブ）
  - MCPIntegrationクラス（デモモード）

- **ワークフロー監視機能**
  - ワークフロー実行モニタリング（`/workflows/monitor`）
  - SubAgentログ表示
  - Hookログ表示

### 変更 (Changed)
- **データベーススキーマ拡張**
  - テーブル数: 10個 → 20個
  - 新規テーブル: フィードバック系3個、設定系4個、対話系2個、検索系1個

- **WebUIテンプレート拡張**
  - テンプレート数: 6個 → 13個
  - 新規ページ: analytics.html, chat.html, settings.html, intelligent_search.html, system_feedback.html, workflow_monitor.html

- **REST API拡張**
  - エンドポイント数: 4個 → 12個

### 修正 (Fixed)
- FTS5全文検索の同期問題を修正
  - トリガーを追加してknowledge_entriesとknowledge_ftsを自動同期

### 設定変更 (Configuration)
- **データベーススキーマ**: フィードバック機能、設定機能を追加
  - 追加ファイル: `db/feedback_schema.sql`, `db/settings_schema.sql`
  - 影響範囲: データベース全体

---

## [1.0.0] - 2025-12-31 (初回リリース)

### 追加 (Added)
- **コアワークフローエンジン**
  - `src/core/workflow.py` - メインワークフローオーケストレーター
  - `src/core/knowledge_generator.py` - ナレッジ生成
  - `src/core/itsm_classifier.py` - ITSM自動分類

- **SubAgents（7個）**
  - Architect - 設計整合性チェック（242行）
  - KnowledgeCurator - タグ・カテゴリ分類（229行）
  - ITSMExpert - ITSM妥当性・逸脱検知（321行）
  - DevOps - 技術分析・自動化提案（264行）
  - QA - 品質保証・重複検知（337行）
  - Coordinator - 全体調整・抜け漏れ確認（130行）
  - Documenter - 要約生成・フォーマット（384行）

- **Hooks（5個）**
  - PreTaskHook - 入力検証、SubAgent推奨（117行）
  - DuplicateCheckHook - 重複検知（89行）
  - DeviationCheckHook - ITSM逸脱検知（89行）
  - AutoSummaryHook - 3行要約検証（70行）
  - PostTaskHook - 統合レビュー（156行）

- **WebUI（Flask）**
  - ホームページ（`/`）
  - 検索機能（`/knowledge/search`）
  - ナレッジ作成（`/knowledge/create`）
  - ナレッジ詳細（`/knowledge/<id>`）
  - ダッシュボード（`/dashboard`）
  - REST API（4エンドポイント）

- **データベース**
  - SQLiteデータベース（`db/knowledge.db`）
  - メインスキーマ（`db/schema.sql`）
  - テーブル数: 10個
  - FTS5全文検索対応
  - インデックス: 18個

- **MCP統合**
  - SQLiteClient - 完全実装（510行）

- **ドキュメント**
  - README.md - プロジェクト概要と使い方
  - ARCHITECTURE.md - アーキテクチャ設計
  - SETUP_GUIDE.md - セットアップガイド
  - PROJECT_SUMMARY.md - プロジェクトサマリー
  - CONTRIBUTING.md - 貢献ガイド
  - RELEASE_NOTES_V2.md - リリースノート

- **スクリプト**
  - `scripts/init_db.py` - データベース初期化
  - `scripts/test_workflow.py` - ワークフローE2Eテスト
  - `scripts/generate_sample_data.py` - サンプルデータ生成

- **設定ファイル**
  - `requirements.txt` - Python依存パッケージ
  - `start.sh` - 起動スクリプト
  - `.gitignore` - Git除外設定

### 設定変更 (Configuration)
- **初期設定**: プロジェクト全体の初期設定
  - Python 3.8以上を要求
  - Flask, Flask-SocketIOを依存関係に追加
  - ポート: 8888（デフォルト）
  - データベースパス: `db/knowledge.db`
  - ナレッジ保存先: `data/knowledge/`

---

## 変更履歴の管理ルール

### 1. バージョニング規則

**セマンティックバージョニング（Semantic Versioning）を採用**:
- **メジャーバージョン（X.0.0）**: 破壊的変更、大規模なアーキテクチャ変更
- **マイナーバージョン（0.X.0）**: 新機能追加、下位互換性のある変更
- **パッチバージョン（0.0.X）**: バグ修正、小さな改善

### 2. 記録タイミング

以下の場合に必ず記録してください：
- ✅ 新機能の追加
- ✅ 既存機能の変更
- ✅ バグ修正
- ✅ 設定ファイルの変更
- ✅ データベーススキーマの変更
- ✅ APIエンドポイントの変更
- ✅ 依存パッケージの追加・更新
- ✅ ドキュメントの大幅な更新

### 3. 設定変更の記録フォーマット

```markdown
### 設定変更 (Configuration)
- **[設定項目名]**: [変更内容の概要]
  - 変更ファイル: `path/to/config/file`
  - 変更前: `旧設定値`
  - 変更後: `新設定値`
  - 理由: [変更理由の説明]
  - 影響範囲: [影響を受けるコンポーネント、機能のリスト]
  - マイグレーション: [必要な場合、手動での対応手順]
```

### 4. 記録例

#### 例1: データベーススキーマ変更
```markdown
### 設定変更 (Configuration)
- **データベーススキーマ**: knowledge_entriesテーブルにstatus列を追加
  - 変更ファイル: `db/schema.sql`
  - 変更前: status列なし
  - 変更後: `status TEXT DEFAULT 'active' CHECK(status IN ('active', 'archived', 'draft'))`
  - 理由: ナレッジのライフサイクル管理を実装するため
  - 影響範囲:
    - `src/mcp/sqlite_client.py` - CRUDメソッドにstatus処理を追加
    - `src/webui/app.py` - 検索時にstatusフィルタを追加
  - マイグレーション:
    ```sql
    ALTER TABLE knowledge_entries ADD COLUMN status TEXT DEFAULT 'active' CHECK(status IN ('active', 'archived', 'draft'));
    ```
```

#### 例2: 設定ファイル変更
```markdown
### 設定変更 (Configuration)
- **WebUIポート番号**: デフォルトポートを8888から5000に変更
  - 変更ファイル: `src/webui/app.py`
  - 変更前: `app.run(host='0.0.0.0', port=8888)`
  - 変更後: `app.run(host='0.0.0.0', port=5000)`
  - 理由: 標準的なFlaskポートに統一
  - 影響範囲:
    - `README.md` - アクセスURL更新
    - `start.sh` - 起動スクリプトの説明更新
  - マイグレーション: ブラウザで http://localhost:5000 にアクセス
```

---

## 次のバージョン予定

### [2.2.0] - 予定日未定

#### 計画中の追加機能
- [ ] MCP統合の実稼働化（Context7, Claude-Mem, GitHub）
- [ ] 単体テスト実装（カバレッジ80%以上）
- [ ] CI/CDパイプライン構築（GitHub Actions）
- [ ] SF-Knowledge-Navigator軽量版統合（WebUI-Sampleベース）

#### 計画中の改善
- [ ] パフォーマンス最適化（1,000件以上のナレッジでの負荷テスト）
- [ ] エラーハンドリング強化
- [ ] ローディング表示改善

---

**最終更新日**: 2026-01-20
**次回更新予定**: 機能追加または設定変更時
