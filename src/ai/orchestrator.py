#!/usr/bin/env python3
"""
AI Orchestrator - マルチAI役割分担オーケストレーター

役割分担:
- Codex (GPT-4o): 最終回答生成・統合
- GPT (GPT-4o-mini): 定型整形・FAQ処理
- Gemini: 情報収集・調査
- Perplexity: 根拠生成・エビデンス収集
"""

import os
import asyncio
import logging
from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)


class QueryType(Enum):
    """問い合わせタイプ"""
    FAQ = "faq"
    INVESTIGATION = "investigation"
    EVIDENCE = "evidence"
    GENERAL = "general"


@dataclass
class AIResult:
    """AI処理結果"""
    provider: str
    role: str
    content: str
    metadata: Dict[str, Any]
    success: bool
    error: Optional[str] = None


@dataclass
class OrchestratedResponse:
    """オーケストレーション結果"""
    answer: str
    evidence: List[Dict[str, Any]]
    sources: List[str]
    confidence: float
    query_type: QueryType
    ai_used: List[str]
    processing_time_ms: int


class AIOrchestrator:
    """
    マルチAI役割分担オーケストレーター

    処理フロー:
    1. 問い合わせタイプ判定
    2. 適切なAIへルーティング
    3. 並列処理実行
    4. Codexで統合
    5. 根拠分離出力
    """

    def __init__(self):
        # APIキー読み込み
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        self.perplexity_api_key = os.getenv('PERPLEXITY_API_KEY')

        # クライアント初期化
        self._init_clients()

        # FAQ パターン
        self.faq_patterns = [
            'パスワード', 'リセット', 'アカウント', '申請',
            '権限', 'ログイン', '作成', '削除', '変更依頼'
        ]

        # 調査パターン
        self.investigation_patterns = [
            'エラー', '障害', 'トラブル', '原因', '調査',
            '分析', '遅い', '動かない', '接続できない'
        ]

        # 根拠要求パターン
        self.evidence_patterns = [
            'なぜ', '理由', '根拠', 'ベストプラクティス',
            '推奨', '標準', 'セキュリティ'
        ]

    def _init_clients(self):
        """AIクライアントを初期化"""
        # OpenAI
        self._openai = None
        if self.openai_api_key:
            try:
                from openai import OpenAI
                self._openai = OpenAI(api_key=self.openai_api_key)
                logger.info("OpenAI クライアント初期化完了")
            except Exception as e:
                logger.warning(f"OpenAI 初期化失敗: {e}")

        # Anthropic
        self._anthropic = None
        if self.anthropic_api_key:
            try:
                import anthropic
                self._anthropic = anthropic.Anthropic(api_key=self.anthropic_api_key)
                logger.info("Anthropic クライアント初期化完了")
            except Exception as e:
                logger.warning(f"Anthropic 初期化失敗: {e}")

        # Gemini
        self._gemini = None
        if self.gemini_api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_api_key)
                # gemini-2.0-flash を使用（最新の安定版）
                self._gemini = genai.GenerativeModel('gemini-2.0-flash')
                logger.info("Gemini クライアント初期化完了")
            except Exception as e:
                logger.warning(f"Gemini 初期化失敗: {e}")

        # Perplexity (OpenAI互換API)
        self._perplexity = None
        if self.perplexity_api_key:
            try:
                from openai import OpenAI
                self._perplexity = OpenAI(
                    api_key=self.perplexity_api_key,
                    base_url="https://api.perplexity.ai"
                )
                logger.info("Perplexity クライアント初期化完了")
            except Exception as e:
                logger.warning(f"Perplexity 初期化失敗: {e}")

    def classify_query(self, query: str) -> QueryType:
        """問い合わせを分類"""
        query_lower = query.lower()

        # FAQチェック
        if any(p in query_lower for p in self.faq_patterns):
            return QueryType.FAQ

        # 根拠要求チェック
        if any(p in query_lower for p in self.evidence_patterns):
            return QueryType.EVIDENCE

        # 調査チェック
        if any(p in query_lower for p in self.investigation_patterns):
            return QueryType.INVESTIGATION

        return QueryType.GENERAL

    async def process(self, query: str, context: Optional[Dict[str, Any]] = None) -> OrchestratedResponse:
        """
        問い合わせを処理

        Args:
            query: ユーザーの問い合わせ
            context: 追加コンテキスト

        Returns:
            OrchestratedResponse
        """
        import time
        start_time = time.time()

        # 1. 問い合わせタイプ判定
        query_type = self.classify_query(query)
        logger.info(f"問い合わせタイプ: {query_type.value}")

        # 2. 並列処理タスク準備（Claude + Gemini + Perplexity構成）
        tasks = []
        ai_used = []

        # 基本情報収集（Gemini）- 調査・分析
        if self._gemini:
            tasks.append(self._gemini_investigate(query))
            ai_used.append("gemini")

        # 根拠収集（Perplexity）- 根拠要求時またはFAQ以外
        if self._perplexity and query_type in [QueryType.EVIDENCE, QueryType.INVESTIGATION]:
            tasks.append(self._perplexity_evidence(query))
            ai_used.append("perplexity")

        # 3. 並列実行
        results = []
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            results = [r for r in results if isinstance(r, AIResult) and r.success]

        # 4. Claude（Anthropic）で統合
        final_response = await self._codex_integrate(query, query_type, results)
        ai_used.append("claude")

        processing_time = int((time.time() - start_time) * 1000)

        return OrchestratedResponse(
            answer=final_response.get('answer', ''),
            evidence=final_response.get('evidence', []),
            sources=final_response.get('sources', []),
            confidence=final_response.get('confidence', 0.0),
            query_type=query_type,
            ai_used=ai_used,
            processing_time_ms=processing_time
        )

    async def _gemini_investigate(self, query: str) -> AIResult:
        """Geminiで情報収集"""
        try:
            prompt = f"""
以下のIT関連の質問について、技術的な情報を収集・整理してください。

質問: {query}

以下の形式で回答してください:
1. 問題の概要
2. 考えられる原因
3. 推奨される対処法
4. 関連する技術情報

日本語で回答してください。
"""
            response = self._gemini.generate_content(prompt)

            return AIResult(
                provider="gemini",
                role="investigation",
                content=response.text,
                metadata={"model": "gemini-2.0-flash"},
                success=True
            )
        except Exception as e:
            logger.error(f"Gemini エラー: {e}")
            return AIResult(
                provider="gemini",
                role="investigation",
                content="",
                metadata={},
                success=False,
                error=str(e)
            )

    async def _gpt_format_faq(self, query: str) -> AIResult:
        """GPTでFAQ定型処理"""
        try:
            response = self._openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """あなたはITサポートのFAQ担当です。
定型的な質問に対して、簡潔で実用的な回答を提供してください。

回答形式:
1. 回答の要約（1-2文）
2. 具体的な手順（番号付きリスト）
3. 注意点（あれば）"""
                    },
                    {"role": "user", "content": query}
                ],
                max_tokens=1000,
                temperature=0.3
            )

            return AIResult(
                provider="openai",
                role="faq",
                content=response.choices[0].message.content,
                metadata={
                    "model": "gpt-4o-mini",
                    "tokens": response.usage.total_tokens
                },
                success=True
            )
        except Exception as e:
            logger.error(f"GPT FAQ エラー: {e}")
            return AIResult(
                provider="openai",
                role="faq",
                content="",
                metadata={},
                success=False,
                error=str(e)
            )

    async def _perplexity_evidence(self, query: str) -> AIResult:
        """Perplexityで根拠収集"""
        try:
            response = self._perplexity.chat.completions.create(
                model="sonar",
                messages=[
                    {
                        "role": "system",
                        "content": """あなたは根拠・エビデンス収集の専門家です。
質問に対する根拠となる情報を収集し、信頼性の高いソースと共に提供してください。

出力形式:
1. 根拠の要約
2. 参照元（URL付き）
3. 信頼度評価"""
                    },
                    {"role": "user", "content": query}
                ],
                max_tokens=1000
            )

            return AIResult(
                provider="perplexity",
                role="evidence",
                content=response.choices[0].message.content,
                metadata={"model": "sonar"},
                success=True
            )
        except Exception as e:
            logger.error(f"Perplexity エラー: {e}")
            return AIResult(
                provider="perplexity",
                role="evidence",
                content="",
                metadata={},
                success=False,
                error=str(e)
            )

    async def _codex_integrate(
        self,
        query: str,
        query_type: QueryType,
        results: List[AIResult]
    ) -> Dict[str, Any]:
        """Claude（Anthropic）で統合（プライマリ）"""
        # Anthropicが利用不可の場合
        if not self._anthropic:
            combined = "\n\n".join([r.content for r in results if r.content])
            return {
                "answer": combined or "回答を生成できませんでした。",
                "evidence": [],
                "sources": [],
                "confidence": 0.5
            }

        # Anthropic（Claude）で統合
        result = await self._try_anthropic_integrate(query, query_type, results)
        if result:
            return result

        # 失敗時はフォールバック
        combined = "\n\n".join([r.content for r in results if r.content])
        return {
            "answer": combined or "回答を生成できませんでした。",
            "evidence": [],
            "sources": [],
            "confidence": 0.3
        }

    async def _try_openai_integrate(
        self,
        query: str,
        query_type: QueryType,
        results: List[AIResult]
    ) -> Optional[Dict[str, Any]]:
        """OpenAI (GPT-4o) で統合を試行"""
        try:
            # 収集情報をまとめる
            collected_info = ""
            for result in results:
                collected_info += f"\n【{result.role}（{result.provider}）】\n{result.content}\n"

            system_prompt = """あなたはITサポートの統合エージェントです。
収集された情報を統合し、情シス担当者向けの最終回答を生成してください。

要件:
1. 回答本文は簡潔かつ実用的に
2. 手順がある場合は番号付きリストで
3. 根拠・エビデンスは分離して出力
4. 不確実な情報は明示

出力形式（JSON）:
{
  "answer": "回答本文",
  "evidence": [{"source": "ソース名", "url": "URL", "snippet": "関連記述"}],
  "sources": ["参照URL1", "参照URL2"],
  "confidence": 0.0-1.0
}
"""

            user_content = f"""
【ユーザー質問】
{query}

【問い合わせタイプ】
{query_type.value}

【収集情報】
{collected_info}

上記を統合して、JSON形式で最終回答を生成してください。
"""

            response = self._openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                max_tokens=2000,
                temperature=0.5
            )

            # JSON抽出
            content = response.choices[0].message.content
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            try:
                return json.loads(content.strip())
            except json.JSONDecodeError:
                return {
                    "answer": response.choices[0].message.content,
                    "evidence": [],
                    "sources": [],
                    "confidence": 0.7
                }

        except Exception as e:
            logger.error(f"OpenAI統合エラー: {e}")
            return None  # フォールバックを促す

    async def _try_anthropic_integrate(
        self,
        query: str,
        query_type: QueryType,
        results: List[AIResult]
    ) -> Optional[Dict[str, Any]]:
        """Anthropic (Claude) で統合を試行"""
        try:
            # 収集情報をまとめる
            collected_info = ""
            for result in results:
                collected_info += f"\n【{result.role}（{result.provider}）】\n{result.content}\n"

            prompt = f"""あなたはITサポートの統合エージェントです。
収集された情報を統合し、情シス担当者向けの最終回答を生成してください。

要件:
1. 回答本文は簡潔かつ実用的に
2. 手順がある場合は番号付きリストで
3. 根拠・エビデンスは分離して出力
4. 不確実な情報は明示

【ユーザー質問】
{query}

【問い合わせタイプ】
{query_type.value}

【収集情報】
{collected_info}

出力形式（JSON）:
{{
  "answer": "回答本文",
  "evidence": [{{"source": "ソース名", "url": "URL", "snippet": "関連記述"}}],
  "sources": ["参照URL1", "参照URL2"],
  "confidence": 0.0-1.0
}}

JSON形式で回答してください（説明文は不要）:"""

            response = self._anthropic.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text

            # JSON抽出
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            try:
                return json.loads(content.strip())
            except json.JSONDecodeError:
                return {
                    "answer": response.content[0].text,
                    "evidence": [],
                    "sources": [],
                    "confidence": 0.7
                }

        except Exception as e:
            logger.error(f"Anthropic統合エラー: {e}")
            return None  # 全フォールバックを促す


# シングルトンインスタンス
_orchestrator: Optional[AIOrchestrator] = None


def get_orchestrator() -> AIOrchestrator:
    """オーケストレーターのシングルトンを取得"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AIOrchestrator()
    return _orchestrator


# 同期ラッパー
def process_query(query: str, context: Optional[Dict[str, Any]] = None) -> OrchestratedResponse:
    """同期的に問い合わせを処理"""
    orchestrator = get_orchestrator()
    return asyncio.run(orchestrator.process(query, context))
