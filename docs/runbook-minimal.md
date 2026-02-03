# 運用Runbook（最小版）

## 1. サービス管理

### 開発環境

```bash
# 起動
sudo systemctl start mirai-knowledge-dev

# 停止
sudo systemctl stop mirai-knowledge-dev

# 再起動
sudo systemctl restart mirai-knowledge-dev

# 状態確認
sudo systemctl status mirai-knowledge-dev
```

### 本番環境

```bash
# 起動
sudo systemctl start mirai-knowledge-prod

# 停止
sudo systemctl stop mirai-knowledge-prod

# 再起動
sudo systemctl restart mirai-knowledge-prod

# 状態確認
sudo systemctl status mirai-knowledge-prod
```

## 2. ログ確認

### リアルタイムログ

```bash
# 開発環境
sudo journalctl -u mirai-knowledge-dev -f

# 本番環境
sudo journalctl -u mirai-knowledge-prod -f
```

### エラーログ抽出

```bash
# 直近100件のエラー
sudo journalctl -u mirai-knowledge-prod -p err -n 100
```

## 3. データベース

### バックアップ

```bash
# 開発DB
cp db/knowledge_dev.db backups/dev/knowledge_dev_$(date +%Y%m%d).db

# 本番DB
cp db/knowledge.db backups/prod/knowledge_$(date +%Y%m%d).db
```

### リストア

```bash
# 本番DBリストア
cp backups/prod/knowledge_YYYYMMDD.db db/knowledge.db
sudo systemctl restart mirai-knowledge-prod
```

## 4. 障害対応

### サービス応答なし

```bash
# 1. 状態確認
sudo systemctl status mirai-knowledge-prod

# 2. ログ確認
sudo journalctl -u mirai-knowledge-prod -n 50

# 3. 再起動
sudo systemctl restart mirai-knowledge-prod

# 4. 再確認
curl -k https://192.168.0.187:5000/
```

### ディスク容量不足

```bash
# 1. 容量確認
df -h

# 2. ログローテーション実行
logrotate -f /etc/logrotate.d/mirai-knowledge

# 3. 古いバックアップ削除
find backups/ -mtime +30 -delete
```

### AI API エラー

```bash
# 1. APIキー確認
cat .env.production | grep API_KEY

# 2. API疎通確認（手動）
# OpenAI
curl https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY"

# 3. フォールバック有効化
# 設定で代替AIを有効化
```

## 5. SSL証明書

### 更新

```bash
# 証明書更新スクリプト実行
sudo ./scripts/renew_ssl_certs.sh

# サービス再起動
sudo systemctl restart mirai-knowledge-prod
```

### 有効期限確認

```bash
openssl x509 -in /etc/ssl/mirai-knowledge/prod-cert.pem -noout -dates
```

## 6. アクセス情報

| 環境 | URL | ポート |
|------|-----|--------|
| 開発 | https://192.168.0.187:8888 | 8888 |
| 本番 | https://192.168.0.187:5000 | 5000 |

## 7. 連絡先

| 役割 | 連絡先 |
|------|--------|
| システム管理者 | admin@example.com |
| 緊急連絡 | 緊急電話番号 |
