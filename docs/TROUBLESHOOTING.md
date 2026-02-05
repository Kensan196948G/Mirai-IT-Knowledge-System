# トラブルシューティングガイド

**バージョン**: v2.0.0
**対象**: Mirai IT Knowledge System

## 🔍 問題別対応ガイド

### 1. サービス起動失敗

#### 症状
```
systemctl start mirai-knowledge
→ Failed to start mirai-knowledge.service
```

#### 原因と対処

**原因1: ポート8888が使用中**
```bash
# 確認
lsof -i:8888

# 対処
sudo kill $(lsof -t -i:8888)
sudo systemctl start mirai-knowledge
```

**原因2: Python依存関係不足**
```bash
# 確認
python3 -c "import flask; import flask_socketio"

# 対処
pip3 install -r requirements.txt
sudo systemctl start mirai-knowledge
```

**原因3: データベースファイル権限エラー**
```bash
# 確認
ls -la db/knowledge.db

# 対処
chmod 644 db/knowledge.db
chown $USER:$USER db/knowledge.db
```

---

### 2. データベース関連

#### DB lockエラー

**症状**: `database is locked`

**原因**: WALモードが無効（v2.0ではほぼ発生しない）

**対処**:
```bash
# WALモード確認
python3 << EOF
import sqlite3
conn = sqlite3.connect('db/knowledge.db')
mode = conn.execute('PRAGMA journal_mode').fetchone()[0]
print(f'Current mode: {mode}')
if mode != 'wal':
    conn.execute('PRAGMA journal_mode = WAL')
    print('WAL mode enabled')
conn.close()
EOF

# サービス再起動
sudo systemctl restart mirai-knowledge
```

#### FTS5検索エラー

**症状**: `no such table: knowledge_fts`

**対処**:
```bash
# スキーマ確認
python3 -c "
import sqlite3
conn = sqlite3.connect('db/knowledge.db')
cursor = conn.execute(\"SELECT name FROM sqlite_master WHERE name='knowledge_fts'\")
if not cursor.fetchone():
    print('FTS5テーブルが存在しません')
    print('スキーマを再適用してください')
conn.close()
"

# スキーマ再適用
python3 scripts/init_db.py --env production

# または
python3 scripts/apply_fts5_optimization.py
```

---

### 3. パフォーマンス問題

#### ナレッジ作成が遅い

**症状**: 30秒以上かかる

**原因**: DB最適化未実施

**対処**:
```bash
# FTS5最適化
python3 scripts/apply_fts5_optimization.py

# パフォーマンステスト
python3 scripts/benchmark_parallel_execution.py
```

#### 検索が遅い

**症状**: 検索に1秒以上かかる

**対処**:
```bash
# インデックス確認
python3 -c "
import sqlite3
conn = sqlite3.connect('db/knowledge.db')
cursor = conn.execute(\"SELECT name FROM sqlite_master WHERE type='index' ORDER BY name\")
print('インデックス一覧:')
for row in cursor:
    print(f'  - {row[0]}')
conn.close()
"

# FTS5再構築
python3 scripts/apply_fts5_optimization.py
```

---

### 4. WebUI接続問題

#### ページが表示されない

**確認**:
```bash
# サービス稼働確認
curl http://localhost:8888/

# ポート確認
netstat -tlnp | grep 8888

# ファイアウォール確認（Ubuntu）
sudo ufw status
```

**対処**:
```bash
# ファイアウォール許可
sudo ufw allow 8888/tcp

# サービス再起動
sudo systemctl restart mirai-knowledge
```

#### WebSocket接続エラー

**症状**: リアルタイム更新が動作しない

**対処**:
```bash
# Flask-SocketIOバージョン確認
pip3 show flask-socketio

# 再インストール
pip3 install --upgrade flask-socketio python-socketio
```

---

### 5. MCP統合問題

#### MCP Clientが有効にならない

**確認**:
```bash
# MCP設定確認
cat .mcp.json | jq '.mcpServers | keys'

# Claude-Mem DB確認
ls -la .memory/claude-mem/conversations.db
```

**対処**:
```bash
# MCP無効化して動作確認（フォールバック）
export MCP_AUTO_INIT="False"
python3 src/webui/app.py

# MCP設定修正後
export MCP_AUTO_INIT="True"
sudo systemctl restart mirai-knowledge
```

---

## 📊 ヘルスチェック

### システムヘルス確認

```bash
python3 scripts/health_monitor.py
```

**確認項目**:
- ✅ データベース接続
- ✅ ディスク容量
- ✅ メモリ使用量
- ✅ ポート疎通
- ✅ ディレクトリ書き込み権限

**正常な出力例**:
```
Overall Status: healthy

Checks:
  ✅ SQLite接続: OK
  ✅ ディスク容量: 45.2 GB 利用可能
  ✅ メモリ: 2.1 GB / 8.0 GB (26%)
  ✅ HTTPポート: 8888 使用中
  ✅ ログディレクトリ: 書き込み可能
```

---

## 🔧 定期メンテナンス

### 日次タスク

```bash
#!/bin/bash
# scripts/daily_maintenance.sh

# ログ確認
tail -100 logs/app.log | grep ERROR

# ディスク使用量確認
df -h | grep -E "(Filesystem|/mnt/LinuxHDD)"

# ヘルスチェック
python3 scripts/health_monitor.py
```

### 週次タスク

```bash
#!/bin/bash
# scripts/weekly_maintenance.sh

# FTS5最適化
python3 scripts/apply_fts5_optimization.py

# バックアップ
python3 -c "
import sqlite3
import datetime
backup_name = f'backups/weekly_{datetime.date.today()}.db'
conn = sqlite3.connect('db/knowledge.db')
backup = sqlite3.connect(backup_name)
conn.backup(backup)
print(f'Backup created: {backup_name}')
"

# 古いログ削除（30日以上）
find logs/ -name "*.log.*" -mtime +30 -delete
```

---

## 🆘 緊急時対応

### サービス完全停止が必要な場合

```bash
# 1. サービス停止
sudo systemctl stop mirai-knowledge

# 2. プロセス確認
ps aux | grep "python3.*app.py"

# 3. 強制終了（必要なら）
sudo pkill -9 -f "python3 src/webui/app.py"

# 4. ポート解放確認
lsof -i:8888  # 何も表示されなければOK
```

### データベース破損時

```bash
# 1. 整合性チェック
python3 -c "
import sqlite3
conn = sqlite3.connect('db/knowledge.db')
result = conn.execute('PRAGMA integrity_check').fetchone()
print(f'Integrity: {result[0]}')
conn.close()
"

# 2. 破損している場合
#    バックアップから復元
cp backups/knowledge_LATEST.db db/knowledge.db

# 3. FTS5再構築
python3 scripts/apply_fts5_optimization.py
```

---

## 📞 エスカレーション

### レベル1: 自己解決
- 本ガイドのトラブルシューティング実施
- ログ確認
- サービス再起動

### レベル2: システム管理者
- 上記で解決しない場合
- データベース復元が必要な場合

### レベル3: 開発者
- コード修正が必要な場合
- GitHub Issue作成

---

## 🔗 関連ドキュメント

- **運用ガイド**: 本ドキュメント
- **バックアップ手順**: docs/BACKUP_PROCEDURE.md
- **パフォーマンスチューニング**: docs/PHASE7_PERFORMANCE_TUNING.md
- **GitHub Issues**: https://github.com/Kensan196948G/Mirai-IT-Knowledge-System/issues

---

**最終更新**: 2026-02-05
