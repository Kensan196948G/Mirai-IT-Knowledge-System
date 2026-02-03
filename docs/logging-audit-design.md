# ログ/監査ログ設計

## ログ種別

### 1. アプリケーションログ

#### 保存先
```
/mnt/LinuxHDD/Mirai-IT-Knowledge-System/data/logs/
├── dev/
│   └── mirai_knowledge_dev.log
└── prod/
    └── mirai_knowledge_prod.log
```

#### フォーマット
```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

#### ログレベル
| レベル | 用途 |
|--------|------|
| DEBUG | 開発時デバッグ情報 |
| INFO | 通常の処理情報 |
| WARNING | 警告（処理継続可能） |
| ERROR | エラー（処理失敗） |
| CRITICAL | 致命的エラー |

### 2. AI処理ログ

#### 保存先
```
data/logs/ai/
├── requests.log      # APIリクエスト
├── responses.log     # APIレスポンス
└── errors.log        # AIエラー
```

#### 記録内容
```json
{
  "timestamp": "2026-01-22T17:30:00Z",
  "request_id": "req_123abc",
  "ai_provider": "openai",
  "model": "gpt-4o-mini",
  "query": "パスワードリセット方法",
  "query_type": "faq",
  "tokens_used": {
    "input": 150,
    "output": 320
  },
  "latency_ms": 1250,
  "status": "success"
}
```

### 3. 監査ログ

#### 保存先
```
data/logs/audit/
└── audit.log
```

#### 記録イベント
| イベント | 説明 |
|----------|------|
| USER_QUERY | ユーザー問い合わせ |
| KNOWLEDGE_CREATE | ナレッジ作成 |
| KNOWLEDGE_UPDATE | ナレッジ更新 |
| KNOWLEDGE_DELETE | ナレッジ削除 |
| SEARCH_EXECUTE | 検索実行 |
| AI_CALL | AI API呼び出し |

#### フォーマット
```json
{
  "timestamp": "2026-01-22T17:30:00Z",
  "event_type": "KNOWLEDGE_CREATE",
  "user_id": "user123",
  "session_id": "sess_abc",
  "ip_address": "192.168.0.145",
  "details": {
    "knowledge_id": 42,
    "title": "VPN接続エラー対処法",
    "itsm_type": "Incident"
  },
  "result": "success"
}
```

## ログローテーション

### 設定
```python
LOG_MAX_BYTES = 10485760    # 10MB
LOG_BACKUP_COUNT = 5         # 5世代保持
```

### ローテーション戦略
```
app.log → app.log.1 → app.log.2 → ... → app.log.5 → 削除
```

## ログ分析

### メトリクス収集
```python
# 日次集計
metrics = {
    "total_queries": 1500,
    "ai_calls": {
        "openai": 800,
        "gemini": 500,
        "perplexity": 200
    },
    "avg_latency_ms": 1850,
    "error_rate": 0.02,
    "cache_hit_rate": 0.45
}
```

### アラート条件
| 条件 | 閾値 | アクション |
|------|------|------------|
| エラー率 | > 5% | 通知 |
| レイテンシ | > 10秒 | 警告 |
| API失敗 | 連続3回 | フォールバック |

## 保持期間

| ログ種別 | 保持期間 |
|----------|----------|
| アプリケーション | 30日 |
| AI処理 | 90日 |
| 監査 | 1年 |
