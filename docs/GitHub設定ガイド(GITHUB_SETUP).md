# GitHub連携セットアップガイド

## 📋 概要

Mirai IT Knowledge SystemsをGitHubリポジトリと連携し、ナレッジの変更履歴管理と自動バックアップを実現します。

## 🔧 セットアップ手順

### 1. GitHubリポジトリの作成

#### オプションA: GitHub WebUIで作成（推奨）

1. https://github.com/new にアクセス
2. リポジトリ名: `Mirai-IT-Knowledge-System`
3. 説明: `AI-assisted Internal IT Knowledge Management System powered by Claude Code Workflow`
4. Public/Private を選択
5. "Initialize this repository with a README" をチェック
6. "Create repository" をクリック

#### オプションB: GitHub CLIで作成

```bash
# GitHub CLIがインストールされている場合
gh repo create Mirai-IT-Knowledge-System \
  --public \
  --description "AI-assisted Internal IT Knowledge Management System" \
  --clone=false
```

### 2. ローカルリポジトリとリモートの接続

```bash
cd /mnt/LinuxHDD/Mirai-IT-Knowledge-Systems

# リモートリポジトリを追加（あなたのGitHubユーザー名に置き換え）
git remote add origin https://github.com/YOUR_USERNAME/Mirai-IT-Knowledge-System.git

# または SSH を使用（推奨）
git remote add origin git@github.com:YOUR_USERNAME/Mirai-IT-Knowledge-System.git

# リモート確認
git remote -v
```

### 3. 初回コミットとプッシュ

```bash
# Gitユーザー情報設定（まだの場合）
git config user.name "Your Name"
git config user.email "your.email@example.com"

# ステージング
git add .

# コミット
git commit -m "🎉 Initial commit: Mirai IT Knowledge Systems v2.0

- Complete ITSM knowledge management system
- 6 SubAgents (Architect, Curator, ITSM Expert, DevOps, QA, Documenter)
- 5 Hooks for quality assurance
- User feedback collection
- MCP integration (Context7, Claude-Mem, GitHub)
- Advanced analytics
- WebUI with search and dashboard

🤖 Generated with Claude Code Workflow"

# プッシュ
git push -u origin main
# または master ブランチの場合
# git push -u origin master
```

### 4. GitHub Actions ワークフローの有効化

リポジトリに `.github/workflows/backup.yml` が既に含まれています。

**機能:**
- 毎日自動的にデータベースをバックアップ
- 日付付きバックアップファイルを保存
- GitHub Actions で自動実行

**有効化:**
1. GitHubリポジトリの "Actions" タブにアクセス
2. ワークフローを確認・有効化
3. 必要に応じて実行

## 🔐 認証設定

### SSH キーの設定（推奨）

```bash
# SSH キーを生成（まだの場合）
ssh-keygen -t ed25519 -C "your.email@example.com"

# 公開鍵をコピー
cat ~/.ssh/id_ed25519.pub

# GitHubに公開鍵を追加
# 1. GitHub Settings → SSH and GPG keys
# 2. "New SSH key" をクリック
# 3. 公開鍵を貼り付けて保存
```

### Personal Access Token（HTTPS使用時）

```bash
# 1. GitHub Settings → Developer settings → Personal access tokens
# 2. "Generate new token (classic)"
# 3. repo スコープを選択
# 4. トークンをコピー

# Git に保存
git config credential.helper store
# 次回pushで Username と Password（トークン）を入力
```

## 📦 ナレッジのバージョン管理

### 自動コミット

ナレッジが作成・更新されるたびに自動的にGitHubにコミットする場合:

```python
from src.mcp.github_client import GitHubClient

github = GitHubClient("YOUR_USERNAME/Mirai-IT-Knowledge-System")
github.enable_automated_commits(True)
```

### 手動コミット

```bash
# ナレッジファイルの変更をコミット
cd /mnt/LinuxHDD/Mirai-IT-Knowledge-Systems
git add data/knowledge/
git commit -m "📝 Update knowledge: [タイトル]"
git push
```

## 🔄 自動バックアップ設定

### 毎日自動バックアップ

`.github/workflows/backup.yml` により以下が自動実行されます:
- 毎日午前2時（JST）にバックアップ実行
- `db/knowledge.db` を `backups/` ディレクトリにコピー
- 日付付きファイル名で保存
- 自動的にGitHubにプッシュ

### 手動バックアップ

```bash
# GitHub Actions から手動実行
# リポジトリの Actions タブ → "Knowledge Base Backup" → "Run workflow"
```

## 📊 変更履歴の確認

### コマンドライン

```bash
# コミット履歴を表示
git log --oneline --graph

# 特定ファイルの履歴
git log data/knowledge/00001_Incident.md

# 差分を表示
git diff HEAD~1 data/knowledge/00001_Incident.md
```

### WebUI

GitHubリポジトリで直接確認:
- コミット履歴
- ファイル変更履歴
- ブランチ・タグ

## 🎯 ベストプラクティス

### コミットメッセージ規約

```
📝 ナレッジ追加/更新
🐛 バグ修正
✨ 新機能追加
🔧 設定変更
📊 データベース更新
🔄 バックアップ
```

### ブランチ戦略

```bash
# 機能開発用ブランチ
git checkout -b feature/new-analytics

# ナレッジ更新用ブランチ
git checkout -b knowledge/update-incident-procedure

# 変更をマージ
git checkout main
git merge feature/new-analytics
```

### .gitignore 設定

既に以下が除外されています:
- `__pycache__/`
- `*.db`（オプション: バックアップ方針による）
- `*.log`
- 仮想環境

## 🔧 トラブルシューティング

### リモートが既に存在する場合

```bash
git remote remove origin
git remote add origin git@github.com:YOUR_USERNAME/Mirai-IT-Knowledge-System.git
```

### プッシュが拒否される場合

```bash
# リモートの変更を取得
git pull origin main --rebase

# 再度プッシュ
git push origin main
```

### 認証エラー

```bash
# SSHキーの確認
ssh -T git@github.com

# HTTPSの場合はトークンを再生成
git config credential.helper store
```

## 📖 参考リンク

- [GitHub公式ドキュメント](https://docs.github.com/)
- [Git基本操作](https://git-scm.com/doc)
- [GitHub Actions](https://docs.github.com/actions)

---

**セットアップ完了後、ナレッジの変更が自動的にGitHubで管理されます！** 🎉
