# Phase 9: プロダクション準備 - 実装計画

## 概要

**目標**: 本番運用に必要なセキュリティ、監視、運用体制を確立し、24時間365日の安定稼働を実現する

**期間**: 4週間（予定）
**優先度**: 中（Phase 7&8完了後に実施）

---

## 📋 タスク構成

### Task 9.1: セキュリティ監査とハードニング（優先度: 最高）

**工数**: 12-15時間

#### 実装内容

**1. セキュリティ脆弱性診断** (4h)
- OWASP ZAP自動スキャン実行
- SQL Injection対策検証（パラメータ化クエリ確認）
- XSS対策検証（Flask auto-escape確認）
- CSRF対策実装（Flask-WTF CSRFトークン）
- 入力検証強化

**2. 認証・認可機能実装** (6h)
- AD/LDAP統合（python-ldap3）
- セッション管理強化（Flask-Session + Redis）
- ロールベースアクセス制御（RBAC）:
  - **Admin**: 全権限（設定変更、ユーザー管理）
  - **Editor**: ナレッジ作成・編集
  - **Viewer**: 読み取りのみ

**実装ファイル**:
```python
# src/webui/auth.py（新規）
from flask_login import LoginManager, UserMixin
import ldap3

class User(UserMixin):
    def __init__(self, username, role):
        self.id = username
        self.role = role

def authenticate_ldap(username, password):
    server = ldap3.Server('ldap://ad.company.local')
    conn = ldap3.Connection(server, user=f'{username}@company.local',
                           password=password)
    return conn.bind()
```

**3. 機密情報保護** (2h)
- 環境変数暗号化（python-dotenv + secrets）
- API Key保護（環境変数化）
- ログのサニタイズ（パスワード等マスキング）

**成功基準**:
- ✅ OWASP ZAP診断で高リスク脆弱性ゼロ
- ✅ LDAP認証動作確認
- ✅ RBAC権限制御動作確認

---

### Task 9.2: 運用監視とアラート設定（優先度: 高）

**工数**: 10-12時間

#### 実装内容

**1. 監視基盤構築** (4h)
- Prometheus + Grafanaセットアップ
- メトリクス収集エンドポイント実装

**メトリクス定義**:
```python
# src/monitoring/metrics.py（新規）
from prometheus_client import Counter, Histogram, Gauge

# リクエスト数
request_count = Counter('app_requests_total', 'Total requests', ['method', 'endpoint'])

# レスポンスタイム
response_time = Histogram('app_response_time_seconds', 'Response time')

# アクティブユーザー
active_users = Gauge('app_active_users', 'Active users')

# ナレッジ数
knowledge_count = Gauge('app_knowledge_total', 'Total knowledge entries')
```

**Grafanaダッシュボード**:
- アプリケーション概要（リクエスト数、レスポンスタイム、エラー率）
- システムリソース（CPU、メモリ、ディスクI/O）
- データベース（クエリ数、接続プール使用率、FTS5検索時間）

**2. ログ集約** (3h)
- 構造化ログ（JSON形式）
- ログローテーション（logrotate）
- ログレベル制御（環境変数）

**実装**:
```python
# src/utils/logging_config.py
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName
        }
        return json.dumps(log_data, ensure_ascii=False)
```

**3. アラート設定** (3h)
- Alertmanager設定
- Slack/Email通知設定

**アラートルール**:
```yaml
groups:
- name: application
  rules:
  - alert: HighErrorRate
    expr: rate(app_errors_total[5m]) > 0.05
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Error rate > 5%"

  - alert: SlowResponse
    expr: histogram_quantile(0.95, app_response_time_seconds) > 1
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "P95 response time > 1s"
```

**成功基準**:
- ✅ Prometheusでメトリクス収集確認
- ✅ Grafanaダッシュボード表示確認
- ✅ アラート発火テスト成功

---

### Task 9.3: バックアップとディザスタリカバリ（優先度: 高）

**工数**: 8-10時間

#### 実装内容

**1. 自動バックアップシステム** (4h)

**バックアップスクリプト**:
```bash
#!/bin/bash
# scripts/backup_system.sh

BACKUP_DIR="/backups/mirai-knowledge"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# データベースバックアップ
sqlite3 db/knowledge.db ".backup ${BACKUP_DIR}/db_${TIMESTAMP}.db"

# Markdownファイルバックアップ
tar -czf ${BACKUP_DIR}/knowledge_${TIMESTAMP}.tar.gz data/knowledge/

# 古いバックアップ削除（30日以上）
find ${BACKUP_DIR} -name "*.db" -mtime +30 -delete
find ${BACKUP_DIR} -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: ${TIMESTAMP}"
```

**cron設定**:
```cron
# 毎日3:00にバックアップ
0 3 * * * /opt/mirai-knowledge/scripts/backup_system.sh

# 毎週日曜日4:00に週次バックアップ
0 4 * * 0 /opt/mirai-knowledge/scripts/backup_weekly.sh
```

**2. 復旧手順書作成** (2h)
- RTO (Recovery Time Objective): 4時間
- RPO (Recovery Point Objective): 1時間

**復旧手順**:
```
docs/DISASTER_RECOVERY.md

1. サービス停止
   systemctl stop mirai-knowledge

2. バックアップから復元
   cp /backups/mirai-knowledge/db_latest.db db/knowledge.db

3. データベース整合性チェック
   python scripts/verify_db_integrity.py

4. サービス起動
   systemctl start mirai-knowledge

5. 疎通確認
   curl http://localhost:8888/health
```

**3. DR訓練** (2h)
- 四半期ごとのDR訓練計画
- 復旧手順の検証と改善

**成功基準**:
- ✅ 自動バックアップ動作確認（日次・週次）
- ✅ 復旧手順実行成功（RTO 4時間以内）
- ✅ データ整合性確認成功

---

### Task 9.4: ドキュメント完成とユーザートレーニング（優先度: 中）

**工数**: 16-20時間

#### 実装内容

**1. 運用ドキュメント作成** (8h)

**運用手順書** (`docs/OPERATIONS_GUIDE.md`):
```markdown
# 運用ガイド

## サービス起動・停止
systemctl start mirai-knowledge
systemctl stop mirai-knowledge
systemctl status mirai-knowledge

## 設定変更
1. /opt/mirai-knowledge/.env を編集
2. systemctl restart mirai-knowledge

## トラブルシューティング
- ログ確認: journalctl -u mirai-knowledge -f
- DB確認: python scripts/health_monitor.py
- FTS5再構築: python scripts/apply_fts5_optimization.py
```

**API仕様書** (`docs/API_REFERENCE.md`):
- REST API一覧（12エンドポイント）
- SocketIO イベント
- リクエスト/レスポンス形式

**2. ユーザーマニュアル作成** (4h)
- `docs/USER_GUIDE.md` - 一般ユーザー向け
- `docs/ADMIN_GUIDE.md` - 管理者向け

**3. 開発者ドキュメント** (4h)
- `docs/DEVELOPER_GUIDE.md` - 開発者向け
- `docs/CONTRIBUTING.md` - コントリビューションガイド

**成功基準**:
- ✅ 全ドキュメント完成（レビュー承認）
- ✅ トレーニング実施完了

---

### Task 9.5: 本番環境構築とリリース（優先度: 最高）

**工数**: 12-15時間

#### 実装内容

**1. 本番環境セットアップ** (6h)

**サーバー構成**:
```
本番環境（192.168.0.187:8888）
├── Nginx (reverse proxy + SSL termination)
├── Gunicorn (4 workers)
├── SQLite (WAL mode)
└── Redis (キャッシュ - オプション)
```

**Nginx設定例**:
```nginx
server {
    listen 443 ssl http2;
    server_name knowledge.company.local;

    ssl_certificate /etc/ssl/certs/knowledge.crt;
    ssl_certificate_key /etc/ssl/private/knowledge.key;

    location / {
        proxy_pass http://localhost:8888;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /socket.io {
        proxy_pass http://localhost:8888/socket.io;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

**2. CI/CD パイプライン構築** (4h)

**GitHub Actions ワークフロー更新**:
```yaml
# .github/workflows/deploy.yml（既存を拡張）

deploy:
  name: Deploy to Production
  steps:
    - name: Deploy to server
      uses: appleboy/ssh-action@v1.0.0
      with:
        host: ${{ secrets.DEPLOY_HOST }}
        username: ${{ secrets.DEPLOY_USER }}
        key: ${{ secrets.DEPLOY_SSH_KEY }}
        script: |
          cd /opt/mirai-knowledge
          git pull origin main
          systemctl restart mirai-knowledge
          ./scripts/health_check.sh
```

**3. 本番リリース** (2h)
- リリースチェックリスト実行
- カナリアリリース（10% → 50% → 100%）
- ロールバック手順確認

**リリースチェックリスト**:
```markdown
- [ ] 全テストパス確認
- [ ] セキュリティスキャン完了
- [ ] バックアップ実行確認
- [ ] ログローテーション設定確認
- [ ] 監視ダッシュボード動作確認
- [ ] DR手順検証完了
- [ ] ドキュメント完成
- [ ] ユーザートレーニング完了
```

**成功基準**:
- ✅ 本番環境で48時間無停止稼働
- ✅ エラー率 < 0.1%
- ✅ P95レスポンスタイム < 500ms

---

## 📅 Phase 9 スケジュール

```
Week 1:  Task 9.1 (セキュリティ) + Task 9.2 (監視)
Week 2:  Task 9.3 (バックアップ) + Task 9.4 (ドキュメント)
Week 3:  Task 9.5 (本番環境構築)
Week 4:  Task 9.5 (リリース) + 安定化期間
```

---

## 🎯 Phase 9 成功基準

### 必須要件

- ✅ セキュリティ診断で高リスク脆弱性ゼロ
- ✅ 本番環境で48時間無停止稼働
- ✅ 全ドキュメント完成
- ✅ DR訓練成功（RTO/RPO達成）

### パフォーマンス要件

- ✅ P95レスポンスタイム < 500ms
- ✅ エラー率 < 0.1%
- ✅ 可用性 > 99.5%

---

## 🚧 前提条件

### Phase 7 & 8完了（✅ 達成済み）
- MCP統合完成
- 並列実行実装
- WALモード有効化
- FTS5最適化

### インフラ要件
- 本番サーバー準備完了
- ドメイン名決定
- SSL証明書取得
- AD/LDAP情報取得

---

## 📊 期待される成果

Phase 9完了後:
- ✅ プロジェクト完成度: 95% → **100%**
- ✅ 本番運用開始
- ✅ v2.0リリース
- ✅ 24時間365日運用体制確立

---

## 🎓 Phase 9 vs 早期リリース

### オプション A: Phase 9完全実施（推奨）

**メリット**:
- 完全なセキュリティ対策
- 運用監視体制整備
- DR体制確立

**デメリット**:
- 4週間の追加期間必要

### オプション B: 早期リリース（Phase 9簡略版）

Phase 9の必須項目のみ実装:
- セキュリティ基本対策（Task 9.1の一部）
- 基本的な監視（Task 9.2の一部）
- 手動バックアップ手順（Task 9.3の簡略版）

**メリット**:
- 2週間で本番リリース可能
- Phase 7&8の成果を早期に活用

**デメリット**:
- 運用体制が不完全
- DR訓練未実施

---

## 📝 現時点での推奨アクション

### 推奨: 早期リリース（Phase 9簡略版）

**理由**:
1. Phase 7&8で主要機能は完成（完成度95%）
2. 現時点で安定稼働可能
3. Phase 9は運用開始後に段階的実施可能

**実施計画**:
```
Week 1: develop → main マージ
       v2.0リリース
       基本セキュリティ対策

Week 2: ユーザー受入テスト
       フィードバック収集

Week 3-4: Phase 9簡略版実装
         （並行して本番運用継続）
```

---

## 🚀 次のステップ

Phase 9の実施方法を決定してください：

**A. Phase 9完全実施** (4週間)
- 全タスク完全実装
- 完全な運用体制確立

**B. 早期リリース + Phase 9簡略版** (2週間) - 推奨
- v2.0リリース
- 必須項目のみ実施
- 段階的に完全版へ移行

**C. Phase 9スキップ、即座にリリース**
- 今すぐv2.0リリース
- 運用しながら改善
