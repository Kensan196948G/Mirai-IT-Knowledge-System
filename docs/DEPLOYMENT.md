# 🚀 デプロイメントガイド

## GitHub へのプッシュ

### 前提条件

GitHubリポジトリを作成してください:
- リポジトリ名: `Mirai-IT-Knowledge-System`
- URL: https://github.com/Kensan196948G/Mirai-IT-Knowledge-System

### プッシュ手順

```bash
cd /mnt/LinuxHDD/Mirai-IT-Knowledge-Systems

# リモートリポジトリの確認
git remote -v
# => origin https://github.com/Kensan196948G/Mirai-IT-Knowledge-System.git

# プッシュ実行
git push -u origin main
```

**注意**: 初回プッシュ時にGitHub認証が必要です。

### 認証方法

#### オプション1: Personal Access Token（推奨）

1. GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. "Generate new token (classic)" をクリック
3. スコープ: `repo` を選択
4. トークンを生成してコピー
5. プッシュ時に入力:
   - Username: `Kensan196948G`
   - Password: `生成したトークン`

#### オプション2: SSH Key

```bash
# SSH キー生成
ssh-keygen -t ed25519 -C "kensan196948g@users.noreply.github.com"

# 公開鍵をコピー
cat ~/.ssh/id_ed25519.pub

# GitHubに追加
# Settings → SSH and GPG keys → New SSH key

# リモートURLをSSHに変更
git remote set-url origin git@github.com:Kensan196948G/Mirai-IT-Knowledge-System.git

# プッシュ
git push -u origin main
```

---

## 📦 現在の状態

### コミット情報
- **コミットID**: 2d64565
- **ファイル数**: 70ファイル
- **総行数**: 10,722行
- **ナレッジ**: 16件（サンプル含む）

### ディレクトリ構成
```
✅ src/ - 28 Pythonファイル
✅ db/ - 2 SQLスキーマ
✅ data/knowledge/ - 16 Markdownナレッジ
✅ scripts/ - 4 ユーティリティスクリプト
✅ docs/ - 4 ドキュメント
✅ .github/ - GitHub設定（ワークフロー、Issue テンプレート）
```

---

## 🌐 WebUI アクセス

### 起動

```bash
python3 src/webui/app.py
```

### アクセスURL

- **ネットワーク**: http://192.168.0.187:5000
- **ローカル**: http://localhost:5000

### 利用可能なページ

| URL | 機能 |
|-----|------|
| `/` | ホーム（統計・最近のナレッジ） |
| `/knowledge/search` | 検索 |
| `/knowledge/create` | 新規作成 |
| `/knowledge/<id>` | 詳細表示 |
| `/feedback` | システムフィードバック |
| `/analytics` | 分析ダッシュボード |
| `/dashboard` | 管理ダッシュボード |

---

## 🔄 継続的デプロイメント

### GitHub Actions 自動バックアップ

`.github/workflows/backup.yml` により:
- 毎日午前2時（JST）に自動バックアップ
- データベースを `backups/` に保存
- 自動的にGitHubにコミット・プッシュ

### 手動バックアップ

```bash
# データベースバックアップ
mkdir -p backups
cp db/knowledge.db backups/knowledge-$(date +%Y%m%d-%H%M%S).db

# Gitにコミット
git add backups/
git commit -m "🔄 Manual backup $(date +%Y-%m-%d)"
git push
```

---

## 📊 デプロイ後の確認

### 1. WebUI動作確認

```bash
# WebUI起動
python3 src/webui/app.py &

# 動作確認（別ターミナル）
curl http://192.168.0.187:5000/api/statistics
```

### 2. データベース確認

```bash
# ナレッジ数を確認
python3 -c "
from src.mcp.sqlite_client import SQLiteClient
client = SQLiteClient()
stats = client.get_statistics()
print(f'総ナレッジ: {stats[\"total_knowledge\"]}件')
for itsm_type, count in stats['by_itsm_type'].items():
    print(f'  {itsm_type}: {count}件')
"
```

### 3. MCP連携確認

```bash
python3 -c "
from src.mcp.mcp_integration import mcp_integration
status = mcp_integration.get_status()
print('MCP連携ステータス:')
for mcp, enabled in status.items():
    print(f'  {mcp}: {\"✅ 有効\" if enabled else \"❌ 無効\"}')
"
```

---

## 🎯 GitHub リポジトリの設定

リポジトリ作成後、以下を設定:

### 1. About セクション

- **Description**: AI-assisted Internal IT Knowledge Management System powered by Claude Code Workflow
- **Website**: http://192.168.0.187:5000
- **Topics**: `knowledge-management`, `itsm`, `ai-assisted`, `claude-code`, `python`, `flask`

### 2. Settings

- **Features**:
  - ✅ Issues
  - ✅ Discussions（推奨）
  - ✅ Projects（推奨）

### 3. Secrets（GitHub Actions用）

必要に応じて設定:
- データベースバックアップの暗号化キー
- 外部サービス連携用トークン

---

## 📝 運用開始チェックリスト

- [ ] GitHubリポジトリ作成完了
- [ ] 初回プッシュ完了
- [ ] WebUIが起動し、`192.168.0.187:5000` でアクセス可能
- [ ] データベースにサンプルデータあり（16件）
- [ ] 新規ナレッジ作成テスト成功
- [ ] フィードバック機能動作確認
- [ ] 分析ダッシュボード表示確認
- [ ] MCP連携ステータス確認
- [ ] GitHub Actions ワークフロー有効化
- [ ] チームメンバーへの案内完了

---

## 🔧 次のステップ

### すぐに実行

```bash
# GitHubにプッシュ
git push -u origin main

# WebUI起動
python3 src/webui/app.py
```

### 運用フロー確立

1. **日次**: ナレッジ作成・更新
2. **週次**: 分析レポート確認
3. **月次**: フィードバックレビュー
4. **四半期**: システム改善計画

---

## 📞 トラブルシューティング

### プッシュエラー

```bash
# GitHubで先にリポジトリを作成してから再度プッシュ
git push -u origin main
```

### WebUI接続エラー

```bash
# ファイアウォール確認
sudo ufw status
sudo ufw allow 5000/tcp

# 別ポートで起動
python3 -c "
from src.webui.app import app
app.run(host='0.0.0.0', port=8080)
"
```

---

**デプロイ完了後、システムが本格稼働します！** 🚀
