# AIロジック詳細 (AI_LOGIC)

## 概要
本システムのAIロジックは以下3系統で構成されています。
1. **AIオーケストレーター**: Claude/Gemini/Perplexity を役割分担で統合
2. **AI検索アシスタント**: 自然言語検索 + 根拠分離
3. **対話型ナレッジ生成**: 収集項目を段階的に埋める対話フロー

---

## 1. AIオーケストレーター（`src/ai/orchestrator.py`）
### 目的
- 問い合わせを分類し、複数AIで並列処理 → 最終統合

### 主要フロー
1. **一次判断（Claude）**: FAQ/調査/根拠/一般に分類
2. **並列処理**: Gemini/Perplexity 等の役割別処理
3. **Claude統合**: 回答本文と根拠を分離して生成
4. **キャッシュ**: query_type別TTLキャッシュ

### キャッシュ
- FAQ: 24h
- 調査: 1h
- 根拠: 2h
- 一般: 1h

### 主な出力
- `answer` / `evidence` / `sources`
- `confidence` / `processing_time_ms` / `ai_used`

---

## 2. AI検索アシスタント（`src/workflows/intelligent_search.py`）
### 処理ステップ
1. **意図理解**（AI優先 / フォールバックあり）
2. **ナレッジ検索**（DB）
3. **MCP拡張**（Context7 / Claude Mem）
4. **AI統合回答**（根拠分離）

### 意図理解
- `how_to`, `why`, `what`, `when`, `general`
- 技術要素抽出（database/web/network 等）
- 問題種別分類（performance/error/configuration 等）

### 返却構造（抜粋）
- `intent`, `answer`, `evidence`, `sources`, `confidence`
- `knowledge`（DB検索結果）
- `enrichments`（外部知識）
- `suggestions`（関連質問）

---

## 3. 対話型ナレッジ生成（`src/workflows/interactive_knowledge_creation.py`）
### 目的
- インシデント情報を **段階的に収集** してナレッジ化

### 収集フィールド
- title / when / system / symptom / impact / response / cause / measures

### 質問生成
- 未収集の項目に応じて **柔軟な質問文** を返す
- 「不明」でも進められる設計

### AI抽出
- Anthropic / OpenAI が利用可能な場合はJSON抽出
- 失敗時はキーワードベースにフォールバック

---

## WebUIでの使用箇所
- `/search/intelligent` → AI検索アシスタント
- `/chat` → 対話型ナレッジ生成（段階的質問）
- `/api/chat/ai-answer` → AIオーケストレーター単体回答

---

## 主要関連ファイル
- `src/ai/orchestrator.py`
- `src/workflows/intelligent_search.py`
- `src/workflows/interactive_knowledge_creation.py`
- `src/webui/app.py`

---

## 今後の拡張案
- 役割別のAI選定を環境設定で切替可能にする
- 結果の根拠ソースの保存・監査
- クエリタイプ別のUI表示最適化
