# Mirai IT Knowledge System - 運用ガイド

**バージョン**: v2.0.0
**最終更新**: 2026-02-05

## 📋 目次

1. [サービス管理](#サービス管理)
2. [設定変更](#設定変更)
3. [データベース管理](#データベース管理)
4. [バックアップ](#バックアップ)
5. [監視とメンテナンス](#監視とメンテナンス)
6. [トラブルシューティング](#トラブルシューティング)

---

## サービス管理

### 起動方法

#### 開発環境
```bash
cd /mnt/LinuxHDD/Mirai-IT-Knowledge-System
./start.sh

# または手動起動
python3 src/webui/app.py
```

#### 本番環境（systemd）
```bash
# サービス起動
sudo systemctl start mirai-knowledge

# サービス停止
sudo systemctl stop mirai-knowledge

# サービス再起動
sudo systemctl restart mirai-knowledge

# 状態確認
sudo systemctl status mirai-knowledge

# 自動起動設定
sudo systemctl enable mirai-knowledge
```

### ログ確認

```bash
# リアルタイムログ（systemd）
sudo journalctl -u mirai-knowledge -f

# アプリケーションログ
tail -f logs/app.log

# エラーログのみ
grep ERROR logs/app.log
```

---

## 設定変更

### 環境変数設定

設定ファイル: `.env` または環境変数

```bash
# データベース設定
export DATABASE_PATH="db/knowledge.db"
export DB_BACKUP_PATH="backups/"

# アプリケーション設定
export FLASK_ENV="production"
export HOST="0.0.0.0"
export PORT="8888"

# MCP設定
export MCP_AUTO_INIT="True"
export MCP_CLAUDE_MEM_ENABLED="True"
export MCP_CONTEXT7_ENABLED="True"
export MCP_GITHUB_ENABLED="False"  # オプション

# ログ設定
export LOG_LEVEL="INFO"  # DEBUG, INFO, WARNING, ERROR
export LOG_PATH="logs/"
export LOG_FILE="app.log"
```

### 設定反映

```bash
# 設定変更後は再起動
sudo systemctl restart mirai-knowledge

# または開発環境
pkill -f "python3 src/webui/app.py"
./start.sh
```

---

## データベース管理

### データベース初期化

```bash
# 開発環境DBの初期化
python3 scripts/init_db.py --env development

# サンプルデータ付き
python3 scripts/init_db.py --env development --with-samples

# 本番環境DB（注意: 既存データ削除）
python3 scripts/init_db.py --env production --force
```

### FTS5最適化

```bash
# FTS5インデックス最適化
python3 scripts/apply_fts5_optimization.py

# パフォーマンステスト付き
python3 scripts/apply_fts5_optimization.py --test
```

### WALモード確認

```bash
# WALモード確認
python3 -c "import sqlite3; conn = sqlite3.connect('db/knowledge.db'); print('Journal mode:', conn.execute('PRAGMA journal_mode').fetchone()[0])"

# 期待される出力: Journal mode: wal
```

### データベースバックアップ

```bash
# SQLiteバックアップ（オンライン）
python3 -c "
import sqlite3
conn = sqlite3.connect('db/knowledge.db')
backup = sqlite3.connect('backups/knowledge_$(date +%Y%m%d_%H%M%S).db')
conn.backup(backup)
backup.close()
conn.close()
print('Backup completed')
"
```

---

## バックアップ

### 手動バックアップ

**データベース**:
```bash
# WALチェックポイント実行
python3 -c "import sqlite3; conn = sqlite3.connect('db/knowledge.db'); conn.execute('PRAGMA wal_checkpoint(FULL)'); conn.close()"

# バックアップ作成
cp db/knowledge.db backups/knowledge_$(date +%Y%m%d_%H%M%S).db
```

**Markdownファイル**:
```bash
tar -czf backups/knowledge_$(date +%Y%m%d_%H%M%S).tar.gz data/knowledge/
```

**設定ファイル**:
```bash
tar -czf backups/config_$(date +%Y%m%d_%H%M%S).tar.gz .env .mcp.json
```

### 復元手順

```bash
# 1. サービス停止
sudo systemctl stop mirai-knowledge

# 2. バックアップから復元
cp backups/knowledge_YYYYMMDD_HHMMSS.db db/knowledge.db

# 3. データベース整合性チェック
python3 -c "import sqlite3; conn = sqlite3.connect('db/knowledge.db'); conn.execute('PRAGMA integrity_check').fetchone()"

# 4. サービス起動
sudo systemctl start mirai-knowledge

# 5. 動作確認
curl http://localhost:8888/health
```

---

## 監視とメンテナンス

### ヘルスチェック

```bash
# システムヘルスチェック
python3 scripts/health_monitor.py

# JSON形式
python3 scripts/health_monitor.py --json
```

**ヘルスチェックエンドポイント**:
```bash
curl http://localhost:8888/health
```

**期待される応答**:
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "database": "connected",
  "uptime": "24h 15m"
}
```

### 定期メンテナンス

**日次**:
```bash
# ログローテーション確認
ls -lh logs/

# ディスク使用量確認
df -h db/
```

**週次**:
```bash
# FTS5最適化
python3 scripts/apply_fts5_optimization.py

# データベースVACUUM（オプション、WALモードでは不要）
# python3 -c "import sqlite3; conn = sqlite3.connect('db/knowledge.db'); conn.execute('VACUUM'); conn.close()"
```

**月次**:
```bash
# 古いログファイル削除
find logs/ -name "*.log.*" -mtime +30 -delete

# 古いバックアップ削除
find backups/ -name "*.db" -mtime +30 -delete
```

---

## トラブルシューティング

### サービスが起動しない

**確認項目**:
```bash
# 1. ポート使用確認
lsof -i:8888

# 2. ログ確認
tail -50 logs/app.log

# 3. Python環境確認
python3 --version
pip3 list | grep -i flask

# 4. データベース確認
ls -la db/knowledge.db
```

**対処**:
```bash
# ポートが使用中の場合
sudo kill $(lsof -t -i:8888)

# 依存関係再インストール
pip3 install -r requirements.txt

# データベース再作成
python3 scripts/init_db.py --env production
```

### データベース接続エラー

**症状**: `database is locked` エラー

**対処**:
```bash
# WALモード確認
python3 -c "import sqlite3; conn = sqlite3.connect('db/knowledge.db'); print(conn.execute('PRAGMA journal_mode').fetchone())"

# WALモードでない場合は有効化
python3 -c "import sqlite3; conn = sqlite3.connect('db/knowledge.db'); conn.execute('PRAGMA journal_mode = WAL'); conn.close()"

# サービス再起動
sudo systemctl restart mirai-knowledge
```

### 検索が遅い

**対処**:
```bash
# FTS5最適化実行
python3 scripts/apply_fts5_optimization.py

# インデックス確認
python3 -c "
import sqlite3
conn = sqlite3.connect('db/knowledge.db')
cursor = conn.execute(\"SELECT name FROM sqlite_master WHERE type='index'\")
for row in cursor:
    print(row[0])
"
```

### メモリ不足

**確認**:
```bash
# メモリ使用量
free -h

# プロセスメモリ
ps aux | grep python3 | grep app.py
```

**対処**:
```bash
# キャッシュサイズ削減（SQLite）
# .envに追加
export SQLITE_CACHE_SIZE="-32000"  # 32MBに削減（デフォルト64MB）

# サービス再起動
sudo systemctl restart mirai-knowledge
```

---

## 緊急時対応

### サービス停止

```bash
# 即座に停止
sudo systemctl stop mirai-knowledge

# または強制終了
sudo pkill -9 -f "python3 src/webui/app.py"
```

### ロールバック

```bash
# 1. サービス停止
sudo systemctl stop mirai-knowledge

# 2. 前バージョンに戻す
git checkout v1.x.x  # 前のバージョンタグ

# 3. サービス起動
sudo systemctl start mirai-knowledge
```

---

## 連絡先

**システム管理者**: IT部門
**緊急連絡先**: xxx-xxxx-xxxx
**GitHub**: https://github.com/Kensan196948G/Mirai-IT-Knowledge-System

---

**最終更新**: 2026-02-05（v2.0.0リリース時）
