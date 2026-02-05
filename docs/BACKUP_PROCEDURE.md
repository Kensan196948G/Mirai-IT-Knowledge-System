# バックアップ手順書

**システム**: Mirai IT Knowledge System v2.0
**最終更新**: 2026-02-05

## 📋 バックアップ戦略

### 目標

- **RTO** (Recovery Time Objective): 4時間
- **RPO** (Recovery Point Objective): 1時間
- **保持期間**: 日次30日、週次90日

### バックアップ対象

1. **データベース**: `db/knowledge.db`（必須）
2. **Markdownファイル**: `data/knowledge/`（重要）
3. **設定ファイル**: `.env`, `.mcp.json`（重要）
4. **ログファイル**: `logs/`（オプション）

---

## 🔄 手動バックアップ手順

### 完全バックアップ

```bash
#!/bin/bash
# scripts/backup_manual.sh

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups"
mkdir -p $BACKUP_DIR

echo "=== バックアップ開始: $TIMESTAMP ==="

# 1. データベースバックアップ（WALチェックポイント付き）
echo "1. データベースバックアップ中..."
python3 << EOF
import sqlite3
conn = sqlite3.connect('db/knowledge.db')
# WALチェックポイント
conn.execute('PRAGMA wal_checkpoint(FULL)')
# バックアップ
backup = sqlite3.connect('${BACKUP_DIR}/db_${TIMESTAMP}.db')
conn.backup(backup)
backup.close()
conn.close()
print('   ✅ データベースバックアップ完了')
EOF

# 2. Markdownファイルバックアップ
echo "2. Markdownファイルバックアップ中..."
tar -czf ${BACKUP_DIR}/knowledge_${TIMESTAMP}.tar.gz data/knowledge/
echo "   ✅ Markdownバックアップ完了"

# 3. 設定ファイルバックアップ
echo "3. 設定ファイルバックアップ中..."
tar -czf ${BACKUP_DIR}/config_${TIMESTAMP}.tar.gz .env .mcp.json db/schema.sql 2>/dev/null
echo "   ✅ 設定バックアップ完了"

# バックアップサイズ確認
echo ""
echo "=== バックアップ完了 ==="
ls -lh ${BACKUP_DIR}/*${TIMESTAMP}*

# 古いバックアップ削除（30日以上）
find ${BACKUP_DIR} -name "*.db" -mtime +30 -delete
find ${BACKUP_DIR} -name "*.tar.gz" -mtime +30 -delete
echo "古いバックアップ削除完了（30日以上）"
```

**実行**:
```bash
chmod +x scripts/backup_manual.sh
./scripts/backup_manual.sh
```

---

## ⏰ 自動バックアップ設定

### cron設定

```bash
# crontab編集
crontab -e

# 以下を追加
# 毎日3:00にバックアップ
0 3 * * * cd /mnt/LinuxHDD/Mirai-IT-Knowledge-System && ./scripts/backup_manual.sh >> logs/backup.log 2>&1

# 毎週日曜日4:00に週次バックアップ
0 4 * * 0 cd /mnt/LinuxHDD/Mirai-IT-Knowledge-System && ./scripts/backup_weekly.sh >> logs/backup.log 2>&1
```

### systemd timerによる自動バックアップ（推奨）

**Timer設定**: `/etc/systemd/system/mirai-backup.timer`
```ini
[Unit]
Description=Mirai Knowledge System Daily Backup Timer

[Timer]
OnCalendar=daily
OnCalendar=03:00
Persistent=true

[Install]
WantedBy=timers.target
```

**Service設定**: `/etc/systemd/system/mirai-backup.service`
```ini
[Unit]
Description=Mirai Knowledge System Backup

[Service]
Type=oneshot
User=mirai
WorkingDirectory=/mnt/LinuxHDD/Mirai-IT-Knowledge-System
ExecStart=/mnt/LinuxHDD/Mirai-IT-Knowledge-System/scripts/backup_manual.sh
StandardOutput=append:/mnt/LinuxHDD/Mirai-IT-Knowledge-System/logs/backup.log
StandardError=append:/mnt/LinuxHDD/Mirai-IT-Knowledge-System/logs/backup.log
```

**有効化**:
```bash
sudo systemctl daemon-reload
sudo systemctl enable mirai-backup.timer
sudo systemctl start mirai-backup.timer

# 状態確認
sudo systemctl status mirai-backup.timer
```

---

## 🔙 復元手順

### 通常復元（計画停止）

**所要時間**: 約30分

```bash
# 1. サービス停止
sudo systemctl stop mirai-knowledge

# 2. 現在のデータをバックアップ（念のため）
cp db/knowledge.db db/knowledge.db.before_restore

# 3. バックアップから復元
BACKUP_FILE="backups/db_20260205_030000.db"  # 最新を指定
cp $BACKUP_FILE db/knowledge.db

# 4. データベース整合性チェック
python3 << EOF
import sqlite3
conn = sqlite3.connect('db/knowledge.db')
result = conn.execute('PRAGMA integrity_check').fetchone()
print(f'Integrity check: {result[0]}')
assert result[0] == 'ok', 'Database integrity check failed'
conn.close()
print('✅ データベース整合性確認OK')
EOF

# 5. FTS5再構築
python3 scripts/apply_fts5_optimization.py

# 6. サービス起動
sudo systemctl start mirai-knowledge

# 7. 動作確認
sleep 5
curl http://localhost:8888/health

# 8. WebUI確認
echo "WebUIにアクセスして動作確認してください"
echo "http://192.168.0.187:8888"
```

### 緊急復元（障害時）

**所要時間**: 約15分（RTO目標: 4時間）

```bash
# 最速復元スクリプト
#!/bin/bash

set -e  # エラー時に停止

echo "=== 緊急復元開始 ==="

# 1. サービス即座停止
sudo systemctl stop mirai-knowledge || sudo pkill -9 -f "python3.*app.py"

# 2. 最新バックアップを特定
LATEST_BACKUP=$(ls -t backups/db_*.db | head -1)
echo "復元するバックアップ: $LATEST_BACKUP"

# 3. 復元
cp $LATEST_BACKUP db/knowledge.db

# 4. サービス起動
sudo systemctl start mirai-knowledge

# 5. ヘルスチェック
sleep 10
python3 scripts/health_monitor.py

echo "=== 緊急復元完了 ==="
```

---

## 📊 バックアップ検証

### 定期検証（月次推奨）

```bash
# テスト復元スクリプト
#!/bin/bash

TEST_DB="db/test_restore.db"

echo "=== バックアップ検証開始 ==="

# 最新バックアップ取得
LATEST=$(ls -t backups/db_*.db | head -1)
echo "検証対象: $LATEST"

# テストDB作成
cp $LATEST $TEST_DB

# 整合性チェック
python3 << EOF
import sqlite3
conn = sqlite3.connect('$TEST_DB')
result = conn.execute('PRAGMA integrity_check').fetchone()
print(f'Integrity: {result[0]}')

# レコード数確認
count = conn.execute('SELECT COUNT(*) FROM knowledge_entries').fetchone()[0]
print(f'ナレッジ数: {count}')

conn.close()
EOF

# クリーンアップ
rm $TEST_DB

echo "=== バックアップ検証完了 ==="
```

---

## 📈 バックアップ監視

### バックアップ成功確認

```bash
# 最新バックアップ確認
ls -lht backups/ | head -5

# バックアップサイズ確認
du -sh backups/

# バックアップログ確認
tail -50 logs/backup.log | grep "完了"
```

### アラート設定

バックアップ失敗時の通知（将来実装）:
```bash
# バックアップスクリプトに追加
if [ $? -ne 0 ]; then
    echo "バックアップ失敗" | mail -s "Alert: Backup Failed" admin@company.com
fi
```

---

## 🎯 ベストプラクティス

### 1. バックアップ前のチェック

```bash
# ディスク容量確認
df -h backups/

# データベースサイズ確認
du -sh db/knowledge.db

# WALチェックポイント
python3 -c "import sqlite3; conn = sqlite3.connect('db/knowledge.db'); conn.execute('PRAGMA wal_checkpoint(TRUNCATE)'); conn.close()"
```

### 2. 多世代バックアップ

```
backups/
├── daily/     # 日次30日分
├── weekly/    # 週次90日分
└── monthly/   # 月次1年分
```

### 3. オフサイトバックアップ

```bash
# リモートサーバーへコピー
rsync -avz backups/ backup-server:/backups/mirai-knowledge/
```

---

## 🔍 トラブルシューティング

### バックアップが大きすぎる

**対処**:
```bash
# WALファイルサイズ確認
ls -lh db/knowledge.db*

# WALチェックポイント強制実行
python3 -c "import sqlite3; conn = sqlite3.connect('db/knowledge.db'); conn.execute('PRAGMA wal_checkpoint(TRUNCATE)'); conn.close()"

# VACUUM実行（オプション、時間がかかる）
# python3 -c "import sqlite3; conn = sqlite3.connect('db/knowledge.db'); conn.execute('VACUUM'); conn.close()"
```

### バックアップ失敗

**ログ確認**:
```bash
tail -100 logs/backup.log
```

**手動で再実行**:
```bash
./scripts/backup_manual.sh
```

---

## 📞 サポート

**問題解決しない場合**:
- GitHub Issue: https://github.com/Kensan196948G/Mirai-IT-Knowledge-System/issues
- ドキュメント: docs/TROUBLESHOOTING.md

---

**最終更新**: 2026-02-05（v2.0.0）
