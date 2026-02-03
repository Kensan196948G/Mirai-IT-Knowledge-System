# 🗺️ Mirai IT Knowledge System - 全体開発フェーズ計画

**バージョン**: 3.0
**最終更新**: 2026-01-21
**プラットフォーム**: Linux ネイティブ（メイン）、Windows 互換

---

## 📋 目次

1. [全体概要](#全体概要)
2. [開発フェーズ一覧](#開発フェーズ一覧)
3. [Phase 0: 現状分析・設計](#phase-0-現状分析設計)
4. [Phase 1: 環境分離セットアップ](#phase-1-環境分離セットアップ)
5. [Phase 2: Git Worktree構築](#phase-2-git-worktree構築)
6. [Phase 3: SSL/HTTPS設定](#phase-3-sslhttps設定)
7. [Phase 4: WebUI環境分離対応](#phase-4-webui環境分離対応)
8. [Phase 5: データベース環境分離](#phase-5-データベース環境分離)
9. [Phase 6: 自動起動設定](#phase-6-自動起動設定)
10. [Phase 7: MCP統合強化](#phase-7-mcp統合強化)
11. [Phase 8: SubAgent・Hooks最適化](#phase-8-subagent・hooks最適化)
12. [Phase 9: テスト・検証](#phase-9-テスト検証)
13. [Phase 10: 本番リリース](#phase-10-本番リリース)

---

## 🎯 全体概要

### プロジェクト目標

1. **開発環境・本番環境の完全分離**
2. **Git Worktree による並列開発環境構築**
3. **全SubAgent機能（7体）の完全活用**
4. **全Hooks機能（並列実行）の活用**
5. **全MCP機能の統合**
6. **自動起動・HTTPS対応**

### 開発期間（目安）

- **Phase 0**: 0.5日（完了）
- **Phase 1-6**: 2-3日
- **Phase 7-9**: 2-3日
- **Phase 10**: 1日
- **合計**: 約5-7日

---

## 📊 開発フェーズ一覧

| Phase | フェーズ名 | 状態 | 優先度 | 期間 |
|-------|-----------|------|--------|------|
| 0 | 現状分析・設計 | ✅ 完了 | 最高 | 0.5日 |
| 1 | 環境分離セットアップ | 🔄 進行中 | 最高 | 0.5日 |
| 2 | Git Worktree構築 | ⏳ 待機中 | 最高 | 0.5日 |
| 3 | SSL/HTTPS設定 | ⏳ 待機中 | 高 | 0.5日 |
| 4 | WebUI環境分離対応 | ⏳ 待機中 | 最高 | 1日 |
| 5 | データベース環境分離 | ⏳ 待機中 | 高 | 0.5日 |
| 6 | 自動起動設定 | ⏳ 待機中 | 高 | 0.5日 |
| 7 | MCP統合強化 | ⏳ 待機中 | 中 | 1日 |
| 8 | SubAgent・Hooks最適化 | ⏳ 待機中 | 中 | 1日 |
| 9 | テスト・検証 | ⏳ 待機中 | 最高 | 1日 |
| 10 | 本番リリース | ⏳ 待機中 | 最高 | 1日 |

---

## Phase 0: 現状分析・設計

### 🎯 目標

現状のシステム構成を把握し、全体設計を完成させる

### ✅ 完了タスク

- [x] プロジェクト構造確認
- [x] SubAgent構成確認（7体すべて実装済み）
- [x] Hooks機能確認（5種すべて実装済み）
- [x] MCP設定確認（Context7, Claude-Mem, GitHub有効）
- [x] IPアドレス・ポート番号確認
- [x] 環境分離設計書作成
- [x] 全体開発フェーズ計画作成

### 📊 成果物

- ✅ `docs/開発環境・本番環境分離設計(ENVIRONMENT_SEPARATION_DESIGN).md`
- ✅ `docs/全体開発フェーズ計画(OVERALL_DEVELOPMENT_PHASES).md`

---

## Phase 1: 環境分離セットアップ

### 🎯 目標

開発環境と本番環境のディレクトリ・設定を分離

### 📋 タスク

#### 1.1 環境変数ファイル作成

- [ ] `.env.development` 作成（開発環境設定）
- [ ] `.env.production` 作成（本番環境設定）
- [ ] 環境変数読み込み処理追加

**成果物**:
- `.env.development`
- `.env.production`
- `src/config/environment.py`（環境変数読み込みモジュール）

#### 1.2 設定ファイル分離

- [ ] `config/development.py` 作成
- [ ] `config/production.py` 作成
- [ ] 環境判定処理追加

**成果物**:
- `config/development.py`
- `config/production.py`

#### 1.3 起動スクリプト作成

- [ ] `scripts/start_dev.sh`（Linux開発環境起動）
- [ ] `scripts/start_prod.sh`（Linux本番環境起動）
- [ ] `scripts/start_dev.ps1`（Windows開発環境起動）
- [ ] `scripts/start_prod.ps1`（Windows本番環境起動）

**成果物**:
- 環境別起動スクリプト × 4

### 🧪 検証項目

- [ ] 環境変数が正しく読み込まれる
- [ ] 開発・本番で異なる設定が適用される
- [ ] 起動スクリプトが正常動作する

---

## Phase 2: Git Worktree構築

### 🎯 目標

Git Worktreeを使用した並列開発環境を構築

### 📋 タスク

#### 2.1 現在の変更をコミット

- [ ] 現在の変更をステージング
- [ ] コミット作成
- [ ] リモートにプッシュ

**コマンド**:
```bash
git add .
git commit -m "🔧 Setup: 環境分離準備完了"
git push origin main
```

#### 2.2 developブランチ作成

- [ ] developブランチを作成
- [ ] developブランチに切り替え

**コマンド**:
```bash
git checkout -b develop
git push -u origin develop
```

#### 2.3 本番環境Worktree作成

- [ ] Worktreeディレクトリ作成
- [ ] mainブランチをWorktreeに割り当て
- [ ] Worktree動作確認

**コマンド**:
```bash
git worktree add /mnt/LinuxHDD/Mirai-IT-Knowledge-System-production main
git worktree list
```

#### 2.4 Worktree管理スクリプト作成

- [ ] `scripts/worktree_setup.sh`（Worktree初期化）
- [ ] `scripts/worktree_sync.sh`（開発→本番同期）
- [ ] `scripts/worktree_status.sh`（Worktree状態確認）

**成果物**:
- Worktree管理スクリプト × 3

### 🧪 検証項目

- [ ] Worktreeが正しく作成される
- [ ] 各Worktreeで独立した変更が可能
- [ ] ブランチ間のマージが正常動作する

---

## Phase 3: SSL/HTTPS設定

### 🎯 目標

自己署名SSL証明書を使用したHTTPS通信を実現

### 📋 タスク

#### 3.1 SSL証明書ディレクトリ作成

- [ ] `/etc/ssl/mirai-knowledge/` ディレクトリ作成
- [ ] 適切な権限設定

**コマンド**:
```bash
sudo mkdir -p /etc/ssl/mirai-knowledge/
sudo chmod 755 /etc/ssl/mirai-knowledge/
```

#### 3.2 開発環境用証明書生成

- [ ] 開発環境用SSL証明書生成
- [ ] 証明書の権限設定

**コマンド**:
```bash
sudo openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout /etc/ssl/mirai-knowledge/dev-key.pem \
  -out /etc/ssl/mirai-knowledge/dev-cert.pem \
  -days 365 \
  -subj "/C=JP/ST=Tokyo/L=Tokyo/O=Mirai/OU=Development/CN=192.168.0.187"
```

#### 3.3 本番環境用証明書生成

- [ ] 本番環境用SSL証明書生成
- [ ] 証明書の権限設定

**コマンド**:
```bash
sudo openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout /etc/ssl/mirai-knowledge/prod-key.pem \
  -out /etc/ssl/mirai-knowledge/prod-cert.pem \
  -days 365 \
  -subj "/C=JP/ST=Tokyo/L=Tokyo/O=Mirai/OU=Production/CN=192.168.0.187"
```

#### 3.4 Flask HTTPS設定追加

- [ ] `app.py` にSSL設定追加（開発環境）
- [ ] `app.py` にSSL設定追加（本番環境）
- [ ] 環境変数からSSLパス読み込み

**成果物**:
- SSL対応 `src/webui/app.py`

#### 3.5 証明書管理スクリプト作成

- [ ] `scripts/generate_ssl_certs.sh`（証明書生成）
- [ ] `scripts/renew_ssl_certs.sh`（証明書更新）

**成果物**:
- SSL管理スクリプト × 2

### 🧪 検証項目

- [ ] HTTPS接続が成功する（開発環境）
- [ ] HTTPS接続が成功する（本番環境）
- [ ] ブラウザで証明書警告が表示される（自己署名）
- [ ] 証明書の有効期限が正しい

---

## Phase 4: WebUI環境分離対応

### 🎯 目標

WebUIを開発環境・本番環境で適切に分離

### 📋 タスク

#### 4.1 app.py 環境対応

- [ ] 環境変数読み込み処理追加
- [ ] 環境別設定適用
- [ ] デバッグモード切り替え

**修正ファイル**:
- `src/webui/app.py`

#### 4.2 テンプレート環境対応

- [ ] 環境表示追加（開発/本番バッジ）
- [ ] サンプルデータ表示制御
- [ ] データなし時の表示分岐

**修正ファイル**:
- `src/webui/templates/base.html`
- `src/webui/templates/index.html`
- `src/webui/templates/knowledge.html`

#### 4.3 ログ出力設定

- [ ] 開発環境ログ設定（DEBUG）
- [ ] 本番環境ログ設定（INFO）
- [ ] ログローテーション設定

**成果物**:
- `src/config/logging.py`

#### 4.4 静的ファイル環境対応

- [ ] 環境別CSS追加
- [ ] 環境別JavaScript追加

**成果物**:
- `src/webui/static/css/development.css`
- `src/webui/static/css/production.css`

### 🧪 検証項目

- [ ] 開発環境でDEBUGログが出力される
- [ ] 本番環境でDEBUGログが出力されない
- [ ] 環境バッジが正しく表示される
- [ ] サンプルデータ表示が環境で異なる

---

## Phase 5: データベース環境分離

### 🎯 目標

開発・本番で独立したデータベースを使用

### 📋 タスク

#### 5.1 データベース初期化スクリプト更新

- [ ] 環境オプション追加（`--env development|production`）
- [ ] サンプルデータ制御（`--with-samples|--no-samples`）

**修正ファイル**:
- `scripts/init_db.py`

#### 5.2 開発環境データベース初期化

- [ ] `db/knowledge_dev.db` 作成
- [ ] サンプルデータ投入
- [ ] データベース接続テスト

**コマンド**:
```bash
cd /mnt/LinuxHDD/Mirai-IT-Knowledge-System
python3 scripts/init_db.py --env development --with-samples
```

#### 5.3 本番環境データベース初期化

- [ ] `db/knowledge.db` 作成
- [ ] スキーマのみ作成（サンプルデータなし）
- [ ] データベース接続テスト

**コマンド**:
```bash
cd /mnt/LinuxHDD/Mirai-IT-Knowledge-System-production
python3 scripts/init_db.py --env production --no-samples
```

#### 5.4 データベースクライアント更新

- [ ] 環境変数からDB パス読み込み
- [ ] データなし時の表示処理追加

**修正ファイル**:
- `src/mcp/sqlite_client.py`

#### 5.5 データベースバックアップスクリプト

- [ ] `scripts/backup_db.sh`（バックアップ）
- [ ] `scripts/restore_db.sh`（リストア）

**成果物**:
- データベース管理スクリプト × 2

### 🧪 検証項目

- [ ] 開発環境DBにサンプルデータが存在する
- [ ] 本番環境DBにサンプルデータが存在しない
- [ ] 各環境で独立してデータ管理できる
- [ ] バックアップ・リストアが正常動作する

---

## Phase 6: 自動起動設定

### 🎯 目標

システム再起動後も自動的にWebUIが起動する

### 📋 タスク

#### 6.1 systemd サービスファイル作成

- [ ] `mirai-knowledge-dev.service`（開発環境）
- [ ] `mirai-knowledge-prod.service`（本番環境）

**配置先**:
- `/etc/systemd/system/mirai-knowledge-dev.service`
- `/etc/systemd/system/mirai-knowledge-prod.service`

#### 6.2 サービス有効化

- [ ] サービスファイルをリロード
- [ ] サービスを有効化
- [ ] サービスを起動

**コマンド**:
```bash
sudo systemctl daemon-reload
sudo systemctl enable mirai-knowledge-dev.service
sudo systemctl enable mirai-knowledge-prod.service
sudo systemctl start mirai-knowledge-dev.service
sudo systemctl start mirai-knowledge-prod.service
```

#### 6.3 サービス管理スクリプト作成

- [ ] `scripts/service_install.sh`（サービスインストール）
- [ ] `scripts/service_restart.sh`（サービス再起動）
- [ ] `scripts/service_logs.sh`（ログ確認）

**成果物**:
- サービス管理スクリプト × 3

### 🧪 検証項目

- [ ] サービスが起動する
- [ ] システム再起動後も自動起動する
- [ ] サービスステータスが正常
- [ ] ログが正しく出力される

---

## Phase 7: MCP統合強化

### 🎯 目標

全MCP機能を完全統合し、効果的に活用

### 📋 タスク

#### 7.1 MCP統合確認

- [ ] brave-search 動作確認
- [ ] ChromeDevTools 動作確認
- [ ] context7 動作確認
- [ ] github 動作確認
- [ ] memory 動作確認
- [ ] playwright 動作確認
- [ ] plugin:claude-mem:mem-search 動作確認
- [ ] sequential-thinking 動作確認

#### 7.2 MCP統合モジュール拡張

- [ ] Brave Search 統合（Web検索機能）
- [ ] Context7 統合強化（技術ドキュメント参照）
- [ ] GitHub 統合（自動コミット・PR作成）
- [ ] Claude-Mem 統合（長期記憶活用）

**修正ファイル**:
- `src/mcp/mcp_integration.py`

#### 7.3 MCP活用機能追加

- [ ] ナレッジ作成時にContext7参照
- [ ] 関連技術情報の自動取得
- [ ] GitHub自動バックアップ

**成果物**:
- MCP統合強化コード

### 🧪 検証項目

- [ ] すべてのMCPが動作する
- [ ] MCP経由で外部情報取得できる
- [ ] MCP統合がエラーなく動作する

---

## Phase 8: SubAgent・Hooks最適化

### 🎯 目標

SubAgent・Hooksの並列実行を最適化し、パフォーマンス向上

### 📋 タスク

#### 8.1 SubAgent並列実行最適化

- [ ] 非同期処理の最適化
- [ ] タイムアウト設定追加
- [ ] エラーハンドリング強化

**修正ファイル**:
- `src/core/workflow.py`

#### 8.2 Hooks並列実行最適化

- [ ] Hook実行順序の最適化
- [ ] 並列実行可能なHooksの同時実行
- [ ] パフォーマンス測定

**修正ファイル**:
- `src/hooks/*.py`

#### 8.3 コンフリクト防止機能強化

- [ ] Git操作前のチェック強化
- [ ] 並列開発時のロック機構
- [ ] 競合検知・自動解決

**成果物**:
- コンフリクト防止モジュール

### 🧪 検証項目

- [ ] SubAgentが並列で高速実行される
- [ ] Hooksがコンフリクトなく動作する
- [ ] 実行時間が短縮される

---

## Phase 9: テスト・検証

### 🎯 目標

全機能の統合テストと検証

### 📋 タスク

#### 9.1 単体テスト

- [ ] SubAgent個別テスト（7体）
- [ ] Hooks個別テスト（5種）
- [ ] MCP統合テスト（8種）
- [ ] データベーステスト

**成果物**:
- テストスクリプト一式

#### 9.2 統合テスト

- [ ] エンドツーエンドテスト（ナレッジ作成）
- [ ] 環境分離テスト（開発・本番）
- [ ] Git Worktreeテスト
- [ ] HTTPS通信テスト
- [ ] 自動起動テスト

#### 9.3 パフォーマンステスト

- [ ] 負荷テスト
- [ ] 並列実行テスト
- [ ] レスポンスタイム測定

#### 9.4 セキュリティテスト

- [ ] SSL証明書検証
- [ ] アクセス制御テスト
- [ ] 入力検証テスト

### 🧪 検証項目

- [ ] すべてのテストがパスする
- [ ] パフォーマンス基準を満たす
- [ ] セキュリティ基準を満たす

---

## Phase 10: 本番リリース

### 🎯 目標

本番環境への正式リリース

### 📋 タスク

#### 10.1 本番環境準備

- [ ] 本番環境データベース最終確認
- [ ] 本番環境設定最終確認
- [ ] SSL証明書最終確認

#### 10.2 ドキュメント整備

- [ ] README更新
- [ ] SETUP_GUIDE更新
- [ ] リリースノート作成

**成果物**:
- `RELEASE_NOTES_V3.md`

#### 10.3 リリース実行

- [ ] developブランチをmainにマージ
- [ ] タグ作成（v3.0.0）
- [ ] GitHubリリース作成

**コマンド**:
```bash
git checkout main
git merge develop
git tag -a v3.0.0 -m "Release v3.0.0: 環境分離・MCP統合完全版"
git push origin main --tags
```

#### 10.4 本番環境デプロイ

- [ ] 本番環境Worktreeを更新
- [ ] 本番環境サービス再起動
- [ ] 動作確認

**コマンド**:
```bash
cd /mnt/LinuxHDD/Mirai-IT-Knowledge-System-production
git pull origin main
sudo systemctl restart mirai-knowledge-prod
```

#### 10.5 監視・運用開始

- [ ] サービス監視設定
- [ ] ログ監視設定
- [ ] バックアップ設定

### 🧪 検証項目

- [ ] 本番環境が正常動作する
- [ ] HTTPSアクセスが成功する
- [ ] 自動起動が動作する
- [ ] すべての機能が正常動作する

---

## 📊 進捗管理

### 完了フェーズ

- ✅ Phase 0: 現状分析・設計（完了）

### 現在のフェーズ

- 🔄 Phase 1: 環境分離セットアップ（進行中）

### 次のフェーズ

- ⏳ Phase 2: Git Worktree構築

---

## 🎯 成功基準

### 必須要件

1. ✅ 開発・本番環境が完全に分離されている
2. ✅ Git Worktreeが正常動作している
3. ✅ HTTPS通信が機能している
4. ✅ システム再起動後も自動起動する
5. ✅ 全SubAgent（7体）が動作する
6. ✅ 全Hooks（5種）が動作する
7. ✅ 全MCP（8種）が統合されている

### オプション要件

1. ⭕ 並列実行が最適化されている
2. ⭕ パフォーマンスが向上している
3. ⭕ セキュリティが強化されている

---

## 📝 リスク管理

### 想定リスク

| リスク | 影響度 | 対策 |
|--------|--------|------|
| Git Worktree設定ミス | 高 | バックアップ取得、手順書作成 |
| SSL証明書エラー | 中 | 証明書生成スクリプト準備 |
| ポート競合 | 中 | ポート確認、代替ポート準備 |
| データベース破損 | 高 | バックアップスクリプト準備 |
| サービス起動失敗 | 高 | ログ確認手順、再起動スクリプト |

---

## ✅ 次のアクション

### 即座に実行

1. **Phase 1タスク開始**
   - 環境変数ファイル作成
   - 起動スクリプト作成

2. **Phase 2準備**
   - 現在の変更をコミット
   - Git Worktree構築準備

---

**作成日**: 2026-01-21
**責任者**: Claude Code
**承認**: ユーザー承認待ち
