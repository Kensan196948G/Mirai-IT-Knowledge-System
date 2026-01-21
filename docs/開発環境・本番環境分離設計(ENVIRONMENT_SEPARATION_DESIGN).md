# 🏗️ 開発環境・本番環境分離設計書

**プロジェクト名**: Mirai IT Knowledge System
**バージョン**: 3.0
**最終更新**: 2026-01-21
**プラットフォーム**: Linux ネイティブ（メイン）、Windows 互換

---

## 📋 目次

1. [概要](#概要)
2. [環境構成](#環境構成)
3. [ディレクトリ構造](#ディレクトリ構造)
4. [ネットワーク設定](#ネットワーク設定)
5. [データベース設計](#データベース設計)
6. [Git Worktree 戦略](#git-worktree-戦略)
7. [自動起動設定](#自動起動設定)
8. [SSL/HTTPS設定](#sslhttps設定)
9. [MCP統合設定](#mcp統合設定)
10. [SubAgent・Hooks設定](#subagent・hooks設定)

---

## 📊 概要

本システムは、開発環境と本番環境を完全に分離し、並列開発とコンフリクト防止を実現します。

### 設計原則

1. **環境完全分離**: 開発・本番で独立したディレクトリ、データベース、設定
2. **Git Worktree活用**: ブランチごとに物理ディレクトリを分離
3. **並列開発対応**: 複数開発者が同時作業可能
4. **コンフリクト防止**: Hooks機能による自動チェック
5. **自動起動**: systemd によるシステム起動時の自動開始

---

## 🏢 環境構成

### 1. 開発環境（Development）

| 項目 | 設定値 |
|------|--------|
| **環境名** | Development（開発） |
| **ブランチ** | `develop` |
| **ディレクトリ** | `/mnt/LinuxHDD/Mirai-IT-Knowledge-System` |
| **IPアドレス** | `192.168.0.187` |
| **ポート番号** | `8888` |
| **アクセスURL** | `https://192.168.0.187:8888` |
| **ブックマーク** | `[開発] Mirai Knowledge System` |
| **データベース** | `db/knowledge_dev.db` |
| **サンプルデータ** | **保持する**（開発用サンプルデータ） |
| **ログレベル** | `DEBUG` |
| **Flaskデバッグ** | `True` |

### 2. 本番環境（Production）

| 項目 | 設定値 |
|------|--------|
| **環境名** | Production（本番） |
| **ブランチ** | `main` |
| **ディレクトリ** | `/mnt/LinuxHDD/Mirai-IT-Knowledge-System-production` |
| **IPアドレス** | `192.168.0.187` |
| **ポート番号** | `5000` |
| **アクセスURL** | `https://192.168.0.187:5000` |
| **ブックマーク** | `[本番] Mirai Knowledge System` |
| **データベース** | `db/knowledge.db` |
| **サンプルデータ** | **削除する**（○○データなし表示） |
| **ログレベル** | `INFO` |
| **Flaskデバッグ** | `False` |

---

## 📁 ディレクトリ構造

```
/mnt/LinuxHDD/
├── Mirai-IT-Knowledge-System/          # 開発環境（developブランチ）
│   ├── .git/                            # Git管理ディレクトリ（メイン）
│   ├── db/
│   │   └── knowledge_dev.db            # 開発用データベース
│   ├── data/
│   │   ├── knowledge/                  # ナレッジファイル（開発）
│   │   └── logs/                       # ログ（開発）
│   ├── src/
│   │   ├── subagents/                  # SubAgent実装
│   │   ├── hooks/                      # Hooks実装
│   │   ├── webui/
│   │   │   └── app.py                  # WebUI（開発設定）
│   │   └── ...
│   ├── scripts/
│   │   ├── start_dev.sh                # 開発環境起動スクリプト（Linux）
│   │   ├── start_dev.ps1               # 開発環境起動スクリプト（Windows）
│   │   └── ...
│   ├── .env.development                # 開発環境変数
│   └── requirements.txt
│
└── Mirai-IT-Knowledge-System-production/  # 本番環境（mainブランチ）
    ├── .git → ../Mirai-IT-Knowledge-System/.git/worktrees/production
    ├── db/
    │   └── knowledge.db                # 本番用データベース
    ├── data/
    │   ├── knowledge/                  # ナレッジファイル（本番）
    │   └── logs/                       # ログ（本番）
    ├── src/
    │   ├── subagents/                  # SubAgent実装
    │   ├── hooks/                      # Hooks実装
    │   ├── webui/
    │   │   └── app.py                  # WebUI（本番設定）
    │   └── ...
    ├── scripts/
    │   ├── start_prod.sh               # 本番環境起動スクリプト（Linux）
    │   ├── start_prod.ps1              # 本番環境起動スクリプト（Windows）
    │   └── ...
    ├── .env.production                 # 本番環境変数
    └── requirements.txt
```

---

## 🌐 ネットワーク設定

### IPアドレス割り当て

**メインIPアドレス**: `192.168.0.187`

### ポート番号割り当て

| 環境 | ポート | 使用状況 | 備考 |
|------|--------|---------|------|
| 開発 | 8888 | 未使用 → 割り当て | 他プロジェクトと競合なし |
| 本番 | 5000 | 未使用 → 割り当て | Flask デフォルト |
| （参考）| 3000 | 使用中 | 他プロジェクト使用中 |
| （参考）| 8000 | 使用中 | 他プロジェクト使用中 |

**重要**: ポート番号は開発途中で変更しない

### アクセスURL

- **開発環境**: `https://192.168.0.187:8888`
- **本番環境**: `https://192.168.0.187:5000`

### ブックマーク設定

Webブラウザのブックマークに以下を登録：

- `[開発] Mirai Knowledge System - https://192.168.0.187:8888`
- `[本番] Mirai Knowledge System - https://192.168.0.187:5000`

---

## 🗄️ データベース設計

### 開発環境データベース

**ファイル**: `db/knowledge_dev.db`

- サンプルデータ: **保持**
- 初期データ: 7件のリアルなサンプルナレッジ
- テストデータ: 自由に追加・削除可能

### 本番環境データベース

**ファイル**: `db/knowledge.db`

- サンプルデータ: **削除**
- 初期データ: スキーマのみ
- データなし時の表示: 「○○データなし」と表示

### データベース初期化スクリプト

#### 開発環境
```bash
# 開発環境データベース初期化（サンプルデータ込み）
cd /mnt/LinuxHDD/Mirai-IT-Knowledge-System
python3 scripts/init_db.py --env development --with-samples
```

#### 本番環境
```bash
# 本番環境データベース初期化（スキーマのみ）
cd /mnt/LinuxHDD/Mirai-IT-Knowledge-System-production
python3 scripts/init_db.py --env production --no-samples
```

---

## 🌿 Git Worktree 戦略

### Worktree 構成

```
メインリポジトリ（開発環境）
├── develop ブランチ → /mnt/LinuxHDD/Mirai-IT-Knowledge-System
└── Worktree
    └── main ブランチ → /mnt/LinuxHDD/Mirai-IT-Knowledge-System-production
```

### Worktree セットアップコマンド

```bash
# 1. 現在の変更をコミット（開発環境）
cd /mnt/LinuxHDD/Mirai-IT-Knowledge-System
git add .
git commit -m "🔧 Setup: 開発環境・本番環境分離前の準備"

# 2. developブランチを作成
git checkout -b develop

# 3. 本番環境用Worktreeを作成（mainブランチ）
git worktree add ../Mirai-IT-Knowledge-System-production main

# 4. Worktree 確認
git worktree list
```

### 開発フロー

#### 機能開発（developブランチ）

```bash
# 開発環境で作業
cd /mnt/LinuxHDD/Mirai-IT-Knowledge-System
git checkout develop

# 機能開発
# ... コーディング ...

# コミット
git add .
git commit -m "✨ Feature: 新機能追加"

# プッシュ
git push origin develop
```

#### 本番リリース（mainブランチ）

```bash
# 開発環境でテスト完了後
cd /mnt/LinuxHDD/Mirai-IT-Knowledge-System
git checkout develop
git pull origin develop

# mainブランチにマージ
git checkout main
git merge develop
git push origin main

# 本番環境に反映
cd /mnt/LinuxHDD/Mirai-IT-Knowledge-System-production
git pull origin main

# 本番環境再起動
sudo systemctl restart mirai-knowledge-prod
```

---

## 🚀 自動起動設定

### systemd サービスファイル

#### 開発環境サービス

**ファイル**: `/etc/systemd/system/mirai-knowledge-dev.service`

```ini
[Unit]
Description=Mirai IT Knowledge System - Development Environment
After=network.target

[Service]
Type=simple
User=kensan
WorkingDirectory=/mnt/LinuxHDD/Mirai-IT-Knowledge-System
Environment="FLASK_ENV=development"
Environment="FLASK_APP=src/webui/app.py"
ExecStart=/usr/bin/python3 /mnt/LinuxHDD/Mirai-IT-Knowledge-System/src/webui/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 本番環境サービス

**ファイル**: `/etc/systemd/system/mirai-knowledge-prod.service`

```ini
[Unit]
Description=Mirai IT Knowledge System - Production Environment
After=network.target

[Service]
Type=simple
User=kensan
WorkingDirectory=/mnt/LinuxHDD/Mirai-IT-Knowledge-System-production
Environment="FLASK_ENV=production"
Environment="FLASK_APP=src/webui/app.py"
ExecStart=/usr/bin/python3 /mnt/LinuxHDD/Mirai-IT-Knowledge-System-production/src/webui/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### サービス有効化コマンド

```bash
# サービスファイルをリロード
sudo systemctl daemon-reload

# サービスを有効化（システム起動時に自動起動）
sudo systemctl enable mirai-knowledge-dev.service
sudo systemctl enable mirai-knowledge-prod.service

# サービスを開始
sudo systemctl start mirai-knowledge-dev.service
sudo systemctl start mirai-knowledge-prod.service

# ステータス確認
sudo systemctl status mirai-knowledge-dev.service
sudo systemctl status mirai-knowledge-prod.service
```

---

## 🔒 SSL/HTTPS設定

### 自己署名SSL証明書の生成

#### 証明書ディレクトリ作成

```bash
# 証明書格納ディレクトリ
sudo mkdir -p /etc/ssl/mirai-knowledge/
cd /etc/ssl/mirai-knowledge/
```

#### 開発環境用証明書

```bash
# 開発環境用証明書生成
sudo openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout dev-key.pem \
  -out dev-cert.pem \
  -days 365 \
  -subj "/C=JP/ST=Tokyo/L=Tokyo/O=Mirai/OU=Development/CN=192.168.0.187"
```

#### 本番環境用証明書

```bash
# 本番環境用証明書生成
sudo openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout prod-key.pem \
  -out prod-cert.pem \
  -days 365 \
  -subj "/C=JP/ST=Tokyo/L=Tokyo/O=Mirai/OU=Production/CN=192.168.0.187"
```

#### 権限設定

```bash
sudo chmod 600 /etc/ssl/mirai-knowledge/*.pem
sudo chown kensan:kensan /etc/ssl/mirai-knowledge/*.pem
```

### Flask HTTPS設定

開発環境・本番環境の `app.py` に以下を追加：

```python
# 開発環境（app.py）
if __name__ == '__main__':
    app.run(
        host='192.168.0.187',
        port=8888,
        debug=True,
        ssl_context=('/etc/ssl/mirai-knowledge/dev-cert.pem',
                    '/etc/ssl/mirai-knowledge/dev-key.pem')
    )

# 本番環境（app.py）
if __name__ == '__main__':
    app.run(
        host='192.168.0.187',
        port=5000,
        debug=False,
        ssl_context=('/etc/ssl/mirai-knowledge/prod-cert.pem',
                    '/etc/ssl/mirai-knowledge/prod-key.pem')
    )
```

---

## 🔌 MCP統合設定

### 利用可能なMCP

1. **brave-search** - Web検索
2. **ChromeDevTools** - ブラウザ自動化
3. **context7** - 技術ドキュメント検索
4. **github** - GitHub連携
5. **memory** - 長期記憶
6. **playwright** - E2Eテスト
7. **plugin:claude-mem:mem-search** - Claude記憶検索
8. **sequential-thinking** - 順次思考

### MCP設定確認

```python
from src.mcp.mcp_integration import mcp_integration

# ステータス確認
status = mcp_integration.get_status()
print(status)
# => {'context7': True, 'claude_mem': True, 'github': True}
```

---

## 🤖 SubAgent・Hooks設定

### SubAgent構成（7体）

全環境で共通の7つのSubAgentを使用：

1. **Architect** - 設計整合性チェック
2. **KnowledgeCurator** - タグ・カテゴリ分類
3. **ITSMExpert** - ITSM妥当性・逸脱検知
4. **DevOps** - 技術分析・自動化提案
5. **QA** - 品質保証・重複検知
6. **Coordinator** - 全体調整・抜け漏れ確認
7. **Documenter** - 要約生成・フォーマット

### Hooks機能（並列実行対応）

5つのHooksで品質保証：

1. **PreTaskHook** - 入力検証・SubAgent割り当て
2. **PostTaskHook** - 統合レビュー
3. **DuplicateCheckHook** - 重複検知
4. **DeviationCheckHook** - ITSM逸脱検知
5. **AutoSummaryHook** - 3行要約生成

### 並列実行設定

`src/core/workflow.py` で並列実行が有効化されています：

```python
# 並列SubAgent実行（7体同時）
subagent_results = await asyncio.gather(
    architect.analyze(...),
    knowledge_curator.analyze(...),
    itsm_expert.analyze(...),
    devops.analyze(...),
    qa.analyze(...),
    coordinator.analyze(...),
    documenter.analyze(...)
)
```

---

## 📝 環境変数設定

### 開発環境（.env.development）

```bash
# 環境
FLASK_ENV=development
FLASK_DEBUG=True
ENVIRONMENT=development

# ネットワーク
HOST=192.168.0.187
PORT=8888

# データベース
DATABASE_PATH=db/knowledge_dev.db

# ログ
LOG_LEVEL=DEBUG
LOG_PATH=data/logs/dev

# SSL
SSL_CERT=/etc/ssl/mirai-knowledge/dev-cert.pem
SSL_KEY=/etc/ssl/mirai-knowledge/dev-key.pem

# サンプルデータ
USE_SAMPLE_DATA=True
```

### 本番環境（.env.production）

```bash
# 環境
FLASK_ENV=production
FLASK_DEBUG=False
ENVIRONMENT=production

# ネットワーク
HOST=192.168.0.187
PORT=5000

# データベース
DATABASE_PATH=db/knowledge.db

# ログ
LOG_LEVEL=INFO
LOG_PATH=data/logs/prod

# SSL
SSL_CERT=/etc/ssl/mirai-knowledge/prod-cert.pem
SSL_KEY=/etc/ssl/mirai-knowledge/prod-key.pem

# サンプルデータ
USE_SAMPLE_DATA=False
```

---

## ✅ セットアップチェックリスト

### 環境分離

- [ ] Git Worktree 作成完了
- [ ] 開発環境ディレクトリ確認
- [ ] 本番環境ディレクトリ確認
- [ ] 環境変数ファイル作成

### ネットワーク

- [ ] IPアドレス確認（192.168.0.187）
- [ ] 開発環境ポート確認（8888）
- [ ] 本番環境ポート確認（5000）
- [ ] ブックマーク登録

### データベース

- [ ] 開発環境DB初期化（サンプルデータ込み）
- [ ] 本番環境DB初期化（スキーマのみ）
- [ ] データベース接続テスト

### SSL/HTTPS

- [ ] 開発環境証明書生成
- [ ] 本番環境証明書生成
- [ ] Flask SSL設定追加
- [ ] HTTPS接続テスト

### 自動起動

- [ ] systemdサービスファイル作成（開発）
- [ ] systemdサービスファイル作成（本番）
- [ ] サービス有効化
- [ ] サービス起動確認
- [ ] 自動起動テスト（再起動後確認）

### MCP・SubAgent・Hooks

- [ ] MCP統合確認
- [ ] SubAgent（7体）動作確認
- [ ] Hooks（5種）動作確認
- [ ] 並列実行テスト

---

## 🚀 次のステップ

1. **Phase 1**: 環境分離セットアップ
2. **Phase 2**: SSL/HTTPS設定
3. **Phase 3**: 自動起動設定
4. **Phase 4**: 機能開発・テスト
5. **Phase 5**: 本番リリース

---

**作成日**: 2026-01-21
**更新履歴**: 初版作成
