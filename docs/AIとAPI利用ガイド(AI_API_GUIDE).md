# 🤖 AI API 選定ガイド

Mirai IT Knowledge Systems の AI対話・AI検索機能で使用するAPIの選定ガイド

---

## 📋 AI対話・AI検索で必要なAPI

### 現在の実装状態

**重要**: 現在の実装は**APIキー不要**で動作します。

- **AI対話機能** (`/chat`): ルールベースの質問フロー（APIキー不要）
- **AI検索機能** (`/search/intelligent`): キーワードマッチング（APIキー不要）

### なぜAPIが必要になるか？

より高度な機能を実現する場合にAIモデルAPIが必要になります：

| 機能 | 現在の実装 | API使用時 |
|------|-----------|----------|
| **対話生成** | 固定質問フロー | 文脈理解した自然な対話 |
| **意図理解** | キーワードマッチ | 深い意味理解 |
| **要約生成** | テンプレート | 高品質な要約 |
| **推奨事項** | ルールベース | コンテキスト理解した提案 |

---

## 🔍 推奨AI API比較

### 1. **Anthropic Claude API** ⭐⭐⭐⭐⭐ 【最推奨】

#### 特徴
- **長文理解**: 最大200K tokens（Claude 3.5 Sonnet）
- **日本語性能**: 非常に高い
- **推論能力**: 優れた文脈理解
- **安全性**: エンタープライズグレード

#### 推奨モデル
```python
# Claude 3.5 Sonnet（バランス型）
model = "claude-3-5-sonnet-20241022"
# 用途: 対話、検索、要約、全般

# Claude 3.5 Haiku（高速・低コスト）
model = "claude-3-5-haiku-20241022"
# 用途: 簡易検索、タグ抽出
```

#### 料金（2025年12月時点）
- **Claude 3.5 Sonnet**: 入力$3/M tokens、出力$15/M tokens
- **Claude 3.5 Haiku**: 入力$0.25/M tokens、出力$1.25/M tokens

#### 月間コスト試算（社内500ユーザー）
```
想定利用:
- AI対話: 50件/日（1件=2K tokens）
- AI検索: 200件/日（1件=1K tokens）

月間tokens: (50×2K + 200×1K) × 30 = 9M tokens

月間コスト:
  Sonnet: 9M × $3/M = $27（入力のみ）
  Haiku: 9M × $0.25/M = $2.25（入力のみ）

→ 混合利用で月額 $10-20程度
```

#### メリット
- ✅ 本システムとの親和性が最高（Claude Code Workflowで開発）
- ✅ 長文ナレッジの理解に優れる
- ✅ 日本語の品質が高い
- ✅ 安全性・信頼性が高い

#### デメリット
- コストは中程度

---

### 2. **OpenAI GPT-4** ⭐⭐⭐⭐

#### 特徴
- **実績**: 最も広く使われている
- **性能**: 高品質
- **エコシステム**: 豊富

#### 推奨モデル
```python
# GPT-4 Turbo（バランス型）
model = "gpt-4-turbo-preview"

# GPT-3.5 Turbo（低コスト）
model = "gpt-3.5-turbo"
```

#### 料金
- **GPT-4 Turbo**: 入力$10/M、出力$30/M
- **GPT-3.5 Turbo**: 入力$0.5/M、出力$1.5/M

#### メリット
- ✅ 実績が豊富
- ✅ ドキュメントが充実
- ✅ 多くの統合ツール

#### デメリット
- 長文理解はClaudeに劣る
- コストが高め（GPT-4）

---

### 3. **DeepSeek** ⭐⭐⭐⭐ 【コスパ重視】

#### 特徴
- **超低コスト**: 他の1/10以下
- **性能**: 意外と高品質
- **オープン性**: 透明性が高い

#### 推奨モデル
```python
# DeepSeek V3
model = "deepseek-chat"
```

#### 料金
- **DeepSeek V3**: 入力$0.27/M、出力$1.10/M
  （OpenRouter経由の場合）

#### 月間コスト試算
```
同じ9M tokens使用で:
月額: $2.43（入力のみ）

→ 非常に低コスト！
```

#### メリット
- ✅ 圧倒的な低コスト
- ✅ 十分な性能
- ✅ 推論能力が高い

#### デメリット
- 日本語は少し劣る
- 企業利用の実績が少ない

---

### 4. **OpenRouter** ⭐⭐⭐⭐⭐ 【柔軟性重視】

#### 特徴
- **複数モデル対応**: 1つのAPIで全モデル利用可能
- **料金比較**: リアルタイムで最安モデル選択
- **切り替え容易**: モデル変更が簡単

#### 利用可能モデル（一例）
```python
models = [
    "anthropic/claude-3.5-sonnet",
    "openai/gpt-4-turbo",
    "deepseek/deepseek-chat",
    "google/gemini-pro",
    # 40以上のモデル
]
```

#### メリット
- ✅ 1つのAPIで複数モデル
- ✅ 用途に応じて使い分け可能
- ✅ コスト最適化しやすい

#### 実装例
```python
# 用途別の使い分け
if task == "long_context":
    model = "anthropic/claude-3.5-sonnet"
elif task == "quick_search":
    model = "deepseek/deepseek-chat"
elif task == "complex_reasoning":
    model = "openai/gpt-4-turbo"
```

---

## 🎯 推奨構成

### パターンA: 品質重視（大企業向け）

```yaml
primary_api: Anthropic Claude
models:
  - claude-3-5-sonnet-20241022  # メイン
  - claude-3-5-haiku-20241022   # 補助

月額コスト: $15-30
品質: 最高
```

### パターンB: コスパ重視（中小企業向け）

```yaml
primary_api: OpenRouter
models:
  - deepseek/deepseek-chat      # メイン（格安）
  - anthropic/claude-3.5-haiku  # 重要タスク用

月額コスト: $5-10
品質: 高
```

### パターンC: ハイブリッド（推奨）

```yaml
primary_api: OpenRouter
strategy: 用途別使い分け

routing:
  long_documents: anthropic/claude-3.5-sonnet
  search: deepseek/deepseek-chat
  summaries: anthropic/claude-3.5-haiku
  chat: deepseek/deepseek-chat

月額コスト: $10-20
品質: 最適化
```

---

## 💻 実装方法

### 設定ファイルの追加

```yaml
# config/ai_config.yaml

ai_provider: openrouter  # または anthropic, openai

# Anthropic直接使用の場合
anthropic:
  api_key: ${ANTHROPIC_API_KEY}
  model: claude-3-5-sonnet-20241022
  max_tokens: 4096

# OpenRouter使用の場合
openrouter:
  api_key: ${OPENROUTER_API_KEY}
  models:
    chat: deepseek/deepseek-chat
    search: anthropic/claude-3.5-haiku
    analysis: anthropic/claude-3.5-sonnet

# コスト制御
limits:
  max_tokens_per_request: 4096
  max_requests_per_day: 1000
  alert_threshold_usd: 50.0
```

### Python実装

```python
# src/ai/client.py

from anthropic import Anthropic
# または
import openai
# または
import requests  # OpenRouter

class AIClient:
    def __init__(self, provider="anthropic"):
        self.provider = provider
        if provider == "anthropic":
            self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        elif provider == "openai":
            self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        elif provider == "openrouter":
            self.api_key = os.getenv("OPENROUTER_API_KEY")
            self.base_url = "https://openrouter.ai/api/v1"

    def generate_response(self, prompt, model=None):
        if self.provider == "anthropic":
            response = self.client.messages.create(
                model=model or "claude-3-5-sonnet-20241022",
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        # 他のプロバイダーの実装...
```

---

## 🔐 セキュリティ

### APIキーの管理

```bash
# .env ファイル（Gitには含めない）
ANTHROPIC_API_KEY=sk-ant-xxx
OPENAI_API_KEY=sk-xxx
OPENROUTER_API_KEY=sk-or-xxx
DEEPSEEK_API_KEY=sk-xxx
```

```python
# python-dotenv 使用
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("ANTHROPIC_API_KEY")
```

### .gitignore に追加

```
.env
.env.local
config/ai_config.yaml  # APIキーを含む場合
```

---

## 📊 コスト管理

### モニタリング

```python
# コスト追跡
class CostTracker:
    def log_usage(self, tokens_in, tokens_out, model):
        cost = self.calculate_cost(tokens_in, tokens_out, model)
        # データベースに記録
        # 閾値超過でアラート
```

### 最適化戦略

1. **キャッシング**: 同じクエリは再利用
2. **モデル選択**: 簡単なタスクは小モデル
3. **バッチ処理**: 複数リクエストをまとめる
4. **プロンプト最適化**: 必要最小限の情報

---

## 🎯 本システムでの推奨

### **OpenRouter + Claude & DeepSeek のハイブリッド**

#### 理由

1. **柔軟性**: 1つのAPIで複数モデル
2. **コスト最適化**: 用途別に使い分け
3. **品質**: Claude で高品質な処理
4. **スピード**: DeepSeek で高速処理

#### 実装優先順位

```
Phase 1: OpenRouter統合（1週間）
  - APIクライアント実装
  - 設定画面追加
  - コスト追跡

Phase 2: モデル最適化（1週間）
  - 用途別モデル選択
  - キャッシング実装

Phase 3: 高度化（2週間）
  - ストリーミング応答
  - バッチ処理
  - コスト最適化
```

---

## 📝 次のステップ

1. **設定画面の実装** ← 次に実装
2. **APIクライアントの実装**
3. **AI対話の高度化**
4. **コスト管理機能**

---

**推奨**: OpenRouter を使用して、用途に応じて Claude と DeepSeek を使い分ける構成が最適です！

次に設定画面を実装します。
