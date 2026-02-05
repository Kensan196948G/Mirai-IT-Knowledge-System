# Phase 11: ナレッジ収集・FAQ強化 & ベストプラクティス実装

**策定日**: 2026-02-05
**優先度**: 最高
**期間**: 3-4週間

---

## 📋 Phase 11 概要

### 目標

ナレッジ収集・FAQ取得のAI活用ベストプラクティスを実装し、**エンタープライズ級ヘルプデスクシステム**を実現する。

### 背景

Phase 10までで基本的なAI対話システムは完成。Phase 11では、業界のベストプラクティスに基づいた以下を実装：

1. **戦略的KPI管理**（自動化率、削減率の可視化）
2. **高度なRAGアーキテクチャ**（ハイブリッド検索、チャンク最適化）
3. **FAQ収集・管理システム**（自動抽出、バージョン管理）
4. **継続改善フロー**（評価分析、ナレッジ棚卸し）
5. **組織・セキュリティ強化**（ナレッジオーナー、アクセス制御）

---

## 🎯 Phase 11 タスク構成

### Task 11.1: KPIダッシュボード実装（優先度: 最高）

**工数**: 10-12時間

#### 実装内容

**1. KPI定義とメトリクス収集** (4h)

```python
# src/analytics/kpi_metrics.py（新規）

class KPIMetrics:
    """KPIメトリクス管理"""

    def calculate_automation_rate(self, start_date, end_date) -> float:
        """一次応答自動化率"""
        # (AI完結件数) / (総問い合わせ件数) * 100

    def calculate_reduction_rate(self, period: str) -> Dict:
        """問い合わせ件数削減率"""
        # 前月比、前年同月比

    def calculate_resolution_time(self) -> Dict:
        """平均対応時間"""
        # AI回答時間、人間介入時間、総対応時間

    def calculate_user_satisfaction(self) -> float:
        """ユーザー満足度"""
        # 評価スコア平均（1-5）
```

**KPI項目**:
- **一次応答自動化率**: AI完結 / 総問い合わせ × 100%（目標: 70%）
- **問い合わせ件数削減率**: 前月比・前年比（目標: 20%削減）
- **平均対応時間**: AI応答時間（目標: <5秒）、総対応時間（目標: 30%短縮）
- **解決率**: AI完結率（目標: 60%）、人間介入後の解決率
- **ユーザー満足度**: 評価平均（目標: 4.0/5.0）
- **FAQ活用率**: FAQ参照回数 / 問い合わせ数
- **エスカレーション率**: 人間介入が必要だった割合

**2. ダッシュボードUI実装** (4h)

```html
<!-- templates/kpi_dashboard.html（新規） -->
<div class="kpi-dashboard">
    <div class="kpi-grid">
        <!-- 一次応答自動化率 -->
        <div class="kpi-card">
            <h3>一次応答自動化率</h3>
            <div class="kpi-value">{{ automation_rate }}%</div>
            <div class="kpi-trend">▲ {{ trend }}% vs 前月</div>
            <div class="kpi-target">目標: 70%</div>
        </div>

        <!-- 問い合わせ削減率 -->
        <div class="kpi-card">
            <h3>問い合わせ削減率</h3>
            <div class="kpi-value">{{ reduction_rate }}%</div>
            <div class="kpi-trend">▼ {{ count }} 件減少</div>
        </div>

        <!-- その他KPI... -->
    </div>

    <!-- グラフ（Chart.js使用） -->
    <div class="charts">
        <canvas id="automationTrendChart"></canvas>
        <canvas id="categoryDistChart"></canvas>
    </div>
</div>
```

**3. リアルタイム集計** (2h)

- WebSocketでリアルタイム更新
- 日次・週次・月次集計
- エクスポート機能（CSV/Excel）

**4. API実装** (2h)

```python
@app.route("/api/kpi/automation-rate")
def get_automation_rate():
    """自動化率取得"""

@app.route("/api/kpi/trends")
def get_kpi_trends():
    """KPIトレンド取得"""

@app.route("/api/kpi/export")
def export_kpi_data():
    """KPIデータエクスポート"""
```

---

### Task 11.2: RAGアーキテクチャ強化（優先度: 最高）

**工数**: 12-15時間

#### 実装内容

**1. ハイブリッド検索実装** (5h)

```python
# src/search/hybrid_search.py（新規）

class HybridSearchEngine:
    """ハイブリッド検索エンジン"""

    def __init__(self):
        self.fts5 = FTS5Engine()          # キーワード検索
        self.vector = VectorEngine()       # ベクトル検索

    async def search(self, query: str, top_k: int = 10) -> List[Result]:
        """ハイブリッド検索"""
        # 並列実行
        keyword_results, vector_results = await asyncio.gather(
            self.fts5.search(query, top_k),
            self.vector.search(query, top_k)
        )

        # RRF（Reciprocal Rank Fusion）でマージ
        merged = self._rrf_merge(keyword_results, vector_results)
        return merged

    def _rrf_merge(self, results1, results2, k=60) -> List:
        """RRFアルゴリズムでマージ"""
        # score = 1/(k + rank1) + 1/(k + rank2)
```

**2. チャンク最適化** (4h)

```python
# src/search/chunking.py（新規）

class SmartChunker:
    """スマートチャンク分割"""

    def chunk_document(self, document: str,
                      chunk_size: int = 500,
                      overlap: int = 50) -> List[Chunk]:
        """ドキュメントをチャンク分割"""
        # 段落・見出し・箇条書きを考慮
        # オーバーラップ付きスライディングウィンドウ

    def semantic_chunking(self, document: str) -> List[Chunk]:
        """意味的チャンク分割（AIベース）"""
        # Claude/Geminiで意味の区切りを判定
```

**チャンク戦略**:
- **FAQ**: 1Q&A = 1チャンク
- **マニュアル**: 段落単位（300-800文字）
- **手順書**: ステップ単位
- **オーバーラップ**: 50-100文字（コンテキスト保持）

**3. ベクトルDB統合** (3h)

```python
# src/search/vector_store.py（新規）

# オプション1: ChromaDB（ローカル）
import chromadb

# オプション2: FAISS（高速）
import faiss

# オプション3: SQLite-VSS（既存DB統合）
```

**4. 検索品質評価** (3h)

- Precision@K, Recall@K, MRR（Mean Reciprocal Rank）
- A/Bテスト機能（キーワード vs ハイブリッド）
- ユーザーフィードバックによる継続改善

---

### Task 11.3: FAQ収集・管理システム（優先度: 高）

**工数**: 10-12時間

#### 実装内容

**1. FAQ自動抽出エンジン** (4h)

```python
# src/faq/auto_extraction.py（新規）

class FAQAutoExtractor:
    """FAQ自動抽出エンジン"""

    async def extract_from_logs(self, ticket_logs: List[Dict]) -> List[FAQCandidate]:
        """チケットログからFAQ候補を抽出"""
        # 1. 頻出パターン検出（TF-IDF, クラスタリング）
        # 2. AIで質問文を生成（Claude）
        # 3. 回答を要約（Gemini）
        # 4. 信頼度評価（Perplexity で検証）

    async def extract_from_conversations(self, sessions: List[Dict]) -> List[FAQCandidate]:
        """会話履歴からFAQ候補を抽出"""
        # 解決に至った会話をAIで要約
```

**2. FAQバージョン管理** (3h)

```sql
-- FAQ管理テーブル
CREATE TABLE IF NOT EXISTS faq_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    faq_number TEXT UNIQUE NOT NULL,        -- FAQ-001, FAQ-002
    category TEXT NOT NULL,                  -- アカウント、ネットワーク、PC等
    question TEXT NOT NULL,                  -- 質問文
    question_variations TEXT,                -- 類似質問（JSON array）
    answer TEXT NOT NULL,                    -- 回答文
    answer_format TEXT DEFAULT 'structured', -- structured/conversational

    -- バージョン管理
    version INTEGER DEFAULT 1,
    effective_date DATE,                     -- 有効開始日
    expiry_date DATE,                        -- 有効期限
    is_active BOOLEAN DEFAULT 1,

    -- オーナーシップ
    owner_department TEXT,                   -- 責任部署
    reviewer TEXT,                           -- レビュー担当者
    last_reviewed_at DATE,                   -- 最終レビュー日
    next_review_date DATE,                   -- 次回レビュー予定

    -- メタデータ
    target_users TEXT,                       -- 対象ユーザー（全社/特定部門）
    difficulty_level TEXT,                   -- easy/medium/hard
    related_faqs TEXT,                       -- 関連FAQ（JSON array）
    tags TEXT,                               -- タグ

    -- 統計
    view_count INTEGER DEFAULT 0,
    helpful_count INTEGER DEFAULT 0,
    not_helpful_count INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- FAQ変更履歴
CREATE TABLE IF NOT EXISTS faq_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    faq_id INTEGER NOT NULL,
    version INTEGER NOT NULL,
    question TEXT,
    answer TEXT,
    changed_by TEXT,
    change_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (faq_id) REFERENCES faq_items(id)
);
```

**3. FAQ管理UI** (3h)

- `/faq/manage` - FAQ一覧・編集
- `/faq/create` - FAQ作成
- `/faq/candidates` - AI抽出候補レビュー

**4. FAQ検索API** (2h)

```python
@app.route("/api/faq/search")
def search_faq():
    """FAQ検索（ハイブリッド）"""

@app.route("/api/faq/suggest")
def suggest_faq():
    """関連FAQ提案"""

@app.route("/api/faq/extract-candidates")
def extract_faq_candidates():
    """FAQ候補自動抽出"""
```

---

### Task 11.4: 評価・フィードバックシステム強化（優先度: 高）

**工数**: 8-10時間

#### 実装内容

**1. 多段階評価システム** (3h)

```python
# 既存のfeedbackシステムを拡張

# 評価レベル
FEEDBACK_LEVELS = {
    "immediate": {  # 即座の評価
        "type": "thumbs",  # 👍/👎
        "timing": "after_answer"
    },
    "detailed": {   # 詳細評価
        "type": "rating",  # 1-5 stars
        "questions": [
            "回答は正確でしたか？",
            "問題は解決しましたか？",
            "説明は分かりやすかったですか？"
        ]
    },
    "follow_up": {  # フォローアップ
        "type": "survey",
        "timing": "24h_after",
        "questions": [
            "その後問題は再発していませんか？",
            "他に困っていることはありませんか？"
        ]
    }
}
```

**2. 低評価回答の自動抽出** (2h)

```python
async def extract_low_rated_answers(threshold: float = 2.0) -> List[Dict]:
    """低評価回答を抽出（週次レビュー用）"""
    # rating < 2.0 の回答を抽出
    # AIで原因分析（Claude）
    # 改善提案生成
```

**3. レビューワークフロー** (3h)

- 低評価回答の週次レビュー画面
- 改善アクション（FAQ更新、ナレッジ追加）
- レビュー完了トラッキング

---

### Task 11.5: ナレッジオーナー・権限管理（優先度: 中）

**工数**: 8-10時間

#### 実装内容

**1. ナレッジオーナーシップ** (4h)

```sql
-- ナレッジオーナー管理
CREATE TABLE IF NOT EXISTS knowledge_owners (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    knowledge_id INTEGER NOT NULL,
    owner_type TEXT CHECK(owner_type IN ('department', 'user')),
    owner_id TEXT NOT NULL,              -- 部署コードまたはユーザーID
    role TEXT CHECK(role IN ('owner', 'reviewer', 'contributor')),
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (knowledge_id) REFERENCES knowledge_entries(id)
);

-- 部門マスタ
CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dept_code TEXT UNIQUE NOT NULL,
    dept_name TEXT NOT NULL,
    parent_dept_code TEXT,
    knowledge_manager TEXT              -- ナレッジ責任者
);
```

**2. アクセス制御** (3h)

```python
# src/auth/access_control.py（新規）

class AccessControl:
    """アクセス制御"""

    def can_view_knowledge(self, user: User, knowledge_id: int) -> bool:
        """閲覧権限チェック"""
        # 公開範囲（全社/部門/個人）をチェック

    def can_edit_knowledge(self, user: User, knowledge_id: int) -> bool:
        """編集権限チェック"""
        # オーナーまたはレビュアーのみ

    def filter_search_results(self, results: List, user: User) -> List:
        """検索結果を権限フィルタ"""
```

**公開範囲**:
- `public`: 全社公開
- `department`: 特定部門のみ
- `confidential`: 機密（オーナーのみ）

**3. レビュースケジュール** (3h)

```python
# src/workflows/knowledge_review.py（新規）

# 定期レビュー機能
- 四半期ごとのナレッジ棚卸し
- 古いナレッジの自動検出（6ヶ月更新なし）
- レビュー期限通知
- レビュー完了トラッキング
```

---

### Task 11.6: ナレッジ更新パイプライン（優先度: 中）

**工数**: 6-8時間

#### 実装内容

**1. 変更検知・自動インデックス更新** (3h)

```python
# scripts/knowledge_pipeline.py（新規）

class KnowledgePipeline:
    """ナレッジ更新パイプライン"""

    def watch_knowledge_changes(self):
        """ナレッジ変更を監視"""
        # ファイルシステム監視（watchdog）
        # Git commit フック

    async def update_indexes(self, knowledge_id: int):
        """インデックス更新"""
        # 1. FTS5インデックス更新
        # 2. ベクトルインデックス更新
        # 3. キャッシュクリア

    async def validate_knowledge(self, knowledge_id: int) -> ValidationResult:
        """ナレッジ検証"""
        # AIで内容チェック
        # リンク切れチェック
        # フォーマット検証
```

**2. 未解決質問からのFAQ候補抽出** (3h)

```python
async def extract_unsolved_questions() -> List[FAQCandidate]:
    """未解決質問を抽出"""
    # 1. 解決しなかった会話セッションを抽出
    # 2. AIで質問を要約（Claude）
    # 3. 類似質問をグルーピング
    # 4. 頻度でランキング
    # 5. FAQ候補キューに追加
```

**3. 自動品質チェック** (2h)

- ナレッジ作成時のAI品質チェック
- 古い情報の検出
- 重複コンテンツ検出

---

### Task 11.7: エスカレーション・ガードレール（優先度: 高）

**工数**: 6-8時間

#### 実装内容

**1. エスカレーションルール** (3h)

```python
# src/ai/guardrails.py（新規）

class Guardrails:
    """ガードレール（安全装置）"""

    ESCALATION_KEYWORDS = [
        "セキュリティインシデント", "情報漏えい", "不正アクセス",
        "システムダウン", "緊急", "訴訟", "個人情報", "パワハラ"
    ]

    def should_escalate(self, message: str, context: Dict) -> EscalationDecision:
        """エスカレーション判定"""
        # キーワードチェック
        # AIで重要度判定
        # ルールベース判定

        if self._contains_sensitive_keywords(message):
            return EscalationDecision(
                should_escalate=True,
                reason="sensitive_keyword",
                urgency="high",
                suggested_contact="security_team"
            )
```

**2. 禁止表現チェック** (2h)

```python
def validate_ai_response(response: str) -> ValidationResult:
    """AI回答の検証"""
    # 個人情報が含まれていないか
    # 不適切表現がないか
    # 社内機密情報が漏れていないか
```

**3. 安全な有人引き継ぎ** (3h)

```python
async def escalate_to_human(ticket_id: int, reason: str):
    """人間へエスカレーション"""
    # 1. チケットステータス更新
    # 2. 会話ログ添付
    # 3. 担当者割り当て
    # 4. 通知送信（メール/Slack）
    # 5. ユーザーへ案内
```

---

### Task 11.8: Teams/Slack連携準備（優先度: 中）

**工数**: 8-10時間

#### 実装内容

**1. Webhook受信** (3h)

```python
@app.route("/api/webhook/slack", methods=["POST"])
def slack_webhook():
    """Slack Webhook受信"""

@app.route("/api/webhook/teams", methods=["POST"])
def teams_webhook():
    """Teams Webhook受信"""
```

**2. ボットメッセージフォーマット** (2h)

```python
# src/integrations/slack_formatter.py（新規）

def format_for_slack(ai_response: Dict) -> Dict:
    """Slack Block Kit形式に変換"""
    return {
        "blocks": [
            {"type": "section", "text": {"type": "mrkdwn", "text": answer}},
            {"type": "actions", "elements": [
                {"type": "button", "text": "👍", "action_id": "helpful"},
                {"type": "button", "text": "👎", "action_id": "not_helpful"}
            ]}
        ]
    }
```

**3. 双方向連携** (3h)

- Slackからの質問→AI回答
- Teams会議でのリアルタイム質問
- チケット作成通知
- 解決通知

---

## 📅 Phase 11 スケジュール

```
Week 1: Task 11.1 (KPI) + Task 11.2 (RAG強化)
Week 2: Task 11.3 (FAQ管理) + Task 11.4 (評価強化)
Week 3: Task 11.5 (権限管理) + Task 11.6 (パイプライン)
Week 4: Task 11.7 (ガードレール) + Task 11.8 (Teams/Slack)
       統合テスト・最終調整
```

---

## 🎯 成功基準

### 機能要件
- ✅ 一次応答自動化率70%達成
- ✅ FAQ自動抽出機能動作
- ✅ KPIダッシュボード実装
- ✅ ハイブリッド検索精度90%以上
- ✅ エスカレーションルール動作

### パフォーマンス要件
- ✅ ハイブリッド検索 < 200ms
- ✅ FAQ抽出処理 < 30秒/100会話
- ✅ KPI集計 < 3秒

### 品質要件
- ✅ FAQ候補精度 > 80%
- ✅ ユーザー満足度 > 4.0/5.0
- ✅ エスカレーション適切性 > 95%

---

## 🔧 使用技術

### AIモデル役割分担

| 機能 | 主AI | 副AI | 用途 |
|------|------|------|------|
| FAQ抽出 | Claude | Gemini | 質問要約・回答生成 |
| RAG検索 | - | Claude | 結果統合 |
| 品質評価 | Gemini | Perplexity | 検証 |
| ガードレール | Claude | - | 判定 |
| KPI分析 | Gemini | - | データ分析 |

### 開発ツール
- **SubAgent並列実行**: FAQ抽出、検索、評価を並列処理
- **Git WorkTree**: 各機能を並行開発
- **MCP統合**: Claude-Mem（過去事例）、Context7（技術参照）

---

## 📈 期待される効果

### ビフォー（Phase 10）
```
問い合わせ → AI対話 → チケット作成 → 解決
自動化率: 推定40%
```

### アフター（Phase 11）
```
問い合わせ → FAQ即座提示（自動収集）
          ↓（解決しない）
          AI対話（RAG強化）
          ↓（解決しない）
          エスカレーション（ガードレール）

自動化率: 目標70%
FAQ活用率: 50%
ナレッジ鮮度: 常に最新（自動更新）
```

---

## 🚀 Phase 11 実装準備

次のステップ:
1. 開発フェーズ全体図更新
2. Phase 11タスク登録
3. WorkTree環境構築
4. KPIダッシュボード実装開始

実装開始の承認をお願いします。
