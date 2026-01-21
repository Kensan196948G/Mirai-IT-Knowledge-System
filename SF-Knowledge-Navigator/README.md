# 📘 SF Knowledge Navigator

Server Fault（Stack Exchange Network）から最新の技術知識を自動収集し、日本語翻訳・分類を行い、WebUIで検索・閲覧可能にする個人向け知識基盤システムです。

## ✨ 特徴

- 🔄 **自動収集**: Server Fault の最新質問を自動取得
- 🌏 **日本語翻訳**: DeepL API による翻訳（モックモード対応）
- 🏷️ **自動分類**: 4つの技術分野への自動分類と学習タグ生成
- 🔍 **検索・閲覧**: WebUI による検索・詳細表示・エクスポート
- 📦 **運用パイプライン**: 収集→翻訳→分類のバッチ実行と失敗通知
- 🤖 **AI協調開発**: ClaudeCode SubAgent による半自律開発

## 📂 プロジェクト構成

```
SF-Knowledge-Navigator/
├─ collector/          # データ収集モジュール
├─ translator/         # 翻訳モジュール（DeepL/モック対応）
├─ tagger/             # 分類・タグ付けモジュール
├─ webui/              # WebUIモジュール（FastAPI）
├─ tests/              # テストコード
├─ data/
│  ├─ sf.db           # SQLiteデータベース
│  └─ schema.sql      # DBスキーマ定義
└─ docs/
   ├─ ARCHITECTURE.md               # アーキテクチャドキュメント
   └─ sf_knowledge_navigator_要件定義書（改訂版）.md
```

## 🚀 クイックスタート

### 1. 環境セットアップ

```bash
# リポジトリのクローン
cd SF-Knowledge-Navigator

# 依存パッケージのインストール
pip install -r requirements.txt

# データベースの初期化
python3 data/init_db.py
```

### 2. データ収集

```bash
# Server Fault から質問を収集
python3 collector/fetch_questions.py
```

### 3. 翻訳・分類

```bash
# 翻訳
python3 translator/translate.py

# 分類
python3 tagger/categorize.py
```

### 4. WebUI 起動

```bash
python3 webui/app.py
```

ブラウザで http://127.0.0.1:8000 にアクセスしてください。

### 5. 運用パイプライン実行

```bash
scripts/run_pipeline.sh
```

### 6. systemd タイマー運用

`ops/` のサービスファイルは実運用パスに合わせて設定済みです。

```bash
sudo cp ops/sfkn-pipeline.service /etc/systemd/system/
sudo cp ops/sfkn-pipeline.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now sfkn-pipeline.timer
```

確認:

```bash
systemctl status sfkn-pipeline.timer
```

### 7. (オプション) API キーの設定

Stack Exchange API キーを取得すると、レート制限が緩和されます：

```bash
export STACK_EXCHANGE_API_KEY="your_api_key_here"
```

DeepL API キーを設定すると実翻訳を行います（未設定時はモック翻訳）：

```bash
export DEEPL_API_KEY="your_deepl_api_key_here"
```

API キー取得: https://stackapps.com/apps/oauth/register / https://www.deepl.com/pro-api

### 8. .env 運用ルール

`.env` は運用用の設定を記載し、`.gitignore` の対象です。例:

```bash
# API
STACK_EXCHANGE_API_KEY=your_api_key_here
DEEPL_API_KEY=your_deepl_api_key_here

# パイプライン設定
COLLECTOR_PAGES=3
TRANSLATOR_BATCH=20
TRANSLATOR_MAX_CHARS=30000

# 失敗通知
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=mailer
SMTP_PASS=secret
SMTP_FROM=sfkn@example.com
SMTP_TO=you@example.com
```

## 📖 ドキュメント

- [アーキテクチャドキュメント](docs/ARCHITECTURE.md)
- [要件定義書](docs/sf_knowledge_navigator_要件定義書（改訂版）.md)
- [Collector モジュール README](collector/README.md)
- [Translator モジュール README](translator/README.md)
- [Tagger モジュール README](tagger/README.md)
- [WebUI README](webui/README.md)

## 🏗️ 開発状況

### ✅ 完了

- [x] プロジェクト初期セットアップ
- [x] データベーススキーマ設計
- [x] Collector モジュール実装
- [x] Translator モジュール実装（モック/DeepL対応）
- [x] Tagger モジュール実装
- [x] WebUI 実装（検索・詳細・エクスポート・ダッシュボード）

### 🚧 進行中

- [ ] 検索の高速化（FTS）
- [ ] E2E テスト整備

### 📋 今後の予定

- [ ] CI/CD パイプライン構築
- [ ] デプロイ自動化

## 🛠️ 技術スタック

- **言語**: Python 3.9+
- **データベース**: SQLite 3
- **API**:
  - Stack Exchange API v2.3
  - DeepL API v2 (予定)
- **WebUI**: FastAPI
- **テスト**: pytest, Playwright

## 🤝 開発体制（ClaudeCode SubAgent）

| SubAgent | 責務 |
|----------|------|
| @CTO | アーキテクチャ設計、仕様統制 |
| @Collector | データ収集実装 |
| @Translator | 翻訳実装 |
| @Tagger | 分類実装 |
| @WebUI | WebUI実装 |
| @QA | テスト設計・実装 |

## 📝 ライセンス

このプロジェクトは個人利用を目的としています。

## 🙏 謝辞

- Stack Exchange Network
- DeepL
- ClaudeCode by Anthropic

---

**本プロジェクトは ClaudeCode による半自律開発を前提としています。**
