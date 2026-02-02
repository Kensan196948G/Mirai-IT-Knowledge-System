"""
Intelligent Search Assistant Workflow
インテリジェント検索アシスタント

自然言語での問い合わせに対して最適なナレッジを提案
AI駆動による意図理解と根拠分離出力
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.mcp.claude_mem_client import ClaudeMemClient
from src.mcp.context7_client import Context7Client
from src.mcp.sqlite_client import SQLiteClient

logger = logging.getLogger(__name__)


class IntelligentSearchAssistant:
    """インテリジェント検索アシスタント（AI駆動版）"""

    def __init__(self):
        self.db_client = SQLiteClient()
        self.context7 = Context7Client()
        self.claude_mem = ClaudeMemClient()

        # AI Orchestrator
        self._orchestrator = None
        self._init_orchestrator()

    def _init_orchestrator(self):
        """AIオーケストレーターを初期化"""
        try:
            from src.ai.orchestrator import get_orchestrator

            self._orchestrator = get_orchestrator()
            logger.info("AIオーケストレーター初期化完了")
        except Exception as e:
            logger.warning(f"AIオーケストレーター初期化失敗: {e}")

    def search(self, query: str) -> Dict[str, Any]:
        """
        自然言語クエリで検索

        Args:
            query: 自然言語の質問（例: 「データベースが遅い時はどうすればいい？」）

        Returns:
            総合的な回答とナレッジ（根拠分離）
        """
        # Step 1: 意図理解（AI駆動）
        intent = (
            self._understand_intent_with_ai(query)
            if self._orchestrator
            else self._understand_intent(query)
        )

        # Step 2: 関連ナレッジ検索
        knowledge_results = self._search_knowledge(query, intent)

        # Step 3: MCP連携で補強
        enrichments = self._enrich_with_mcp(query, intent)

        # Step 4: AI統合回答生成（根拠分離）
        if self._orchestrator:
            answer = self._generate_answer_with_ai(
                query, knowledge_results, enrichments
            )
        else:
            answer = self._generate_answer(query, knowledge_results, enrichments)

        return {
            "query": query,
            "intent": intent,
            "answer": answer["text"],
            "evidence": answer.get("evidence", []),  # 根拠分離
            "sources": answer.get("sources", []),  # ソース分離
            "confidence": answer.get("confidence", 0.5),
            "knowledge": knowledge_results,
            "enrichments": enrichments,
            "suggestions": self._generate_suggestions(intent),
            "ai_used": answer.get("ai_used", []),
        }

    def _understand_intent_with_ai(self, query: str) -> Dict[str, Any]:
        """AIを使って意図を理解"""
        try:
            # AIオーケストレーターのクエリ分類を使用
            query_type = self._orchestrator.classify_query(query)

            # 詳細な意図分析
            intent_type = "general"
            if query_type.value == "faq":
                intent_type = "how_to"
            elif query_type.value == "evidence":
                intent_type = "why"
            elif query_type.value == "investigation":
                intent_type = "troubleshoot"

            # 技術要素の抽出（キーワードベース + 拡張）
            technologies = self._extract_technologies(query)

            # 問題の種類
            problem_type = self._classify_problem_type(query)

            return {
                "type": intent_type,
                "query_type": query_type.value,
                "technologies": technologies,
                "problem_type": problem_type,
                "ai_classified": True,
            }
        except Exception as e:
            logger.error(f"AI意図理解エラー: {e}")
            return self._understand_intent(query)

    def _extract_technologies(self, query: str) -> List[str]:
        """技術要素を抽出"""
        query_lower = query.lower()
        technologies = []
        tech_keywords = {
            "database": [
                "データベース",
                "db",
                "mysql",
                "postgresql",
                "sql",
                "oracle",
                "sqlite",
            ],
            "web": ["web", "ウェブ", "apache", "nginx", "http", "https", "html", "css"],
            "network": ["ネットワーク", "network", "lan", "vpn", "wifi", "dns", "dhcp"],
            "server": ["サーバー", "server", "サーバ", "linux", "windows", "ubuntu"],
            "security": [
                "セキュリティ",
                "security",
                "認証",
                "auth",
                "ssl",
                "tls",
                "暗号",
            ],
            "cloud": [
                "クラウド",
                "cloud",
                "aws",
                "azure",
                "gcp",
                "docker",
                "kubernetes",
            ],
            "application": [
                "アプリ",
                "application",
                "ソフトウェア",
                "software",
                "システム",
            ],
        }

        for tech, keywords in tech_keywords.items():
            if any(kw in query_lower for kw in keywords):
                technologies.append(tech)

        return technologies

    def _classify_problem_type(self, query: str) -> str:
        """問題の種類を分類"""
        query_lower = query.lower()

        if any(
            word in query_lower
            for word in ["遅い", "slow", "パフォーマンス", "重い", "タイムアウト"]
        ):
            return "performance"
        elif any(
            word in query_lower
            for word in ["エラー", "error", "障害", "ダウン", "停止", "クラッシュ"]
        ):
            return "error"
        elif any(
            word in query_lower
            for word in ["設定", "config", "変更", "セットアップ", "インストール"]
        ):
            return "configuration"
        elif any(
            word in query_lower
            for word in ["セキュリティ", "脆弱性", "攻撃", "不正", "マルウェア"]
        ):
            return "security"
        elif any(word in query_lower for word in ["なぜ", "理由", "原因", "どうして"]):
            return "investigation"
        else:
            return "general"

    def _generate_answer_with_ai(
        self, query: str, knowledge: List[Dict[str, Any]], enrichments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """AIを使って根拠分離された回答を生成"""
        try:
            # オーケストレーターで処理
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(
                    self._orchestrator.process(
                        query,
                        context={"knowledge": knowledge, "enrichments": enrichments},
                    )
                )
            finally:
                loop.close()

            return {
                "text": result.answer,
                "evidence": result.evidence,
                "sources": result.sources,
                "confidence": result.confidence,
                "ai_used": result.ai_used,
                "knowledge_count": len(knowledge),
                "has_enrichments": bool(
                    enrichments.get("technical_docs") or enrichments.get("memories")
                ),
            }
        except Exception as e:
            logger.error(f"AI回答生成エラー: {e}")
            # フォールバック
            fallback = self._generate_answer(query, knowledge, enrichments)
            return {
                "text": fallback["text"],
                "evidence": [],
                "sources": [],
                "confidence": 0.5,
                "ai_used": ["fallback"],
                "knowledge_count": fallback["knowledge_count"],
                "has_enrichments": fallback["has_enrichments"],
            }

    def _understand_intent(self, query: str) -> Dict[str, Any]:
        """クエリの意図を理解"""
        query_lower = query.lower()

        # 意図の分類
        intent_type = "general"
        if any(
            word in query_lower
            for word in ["どうすれば", "どうやって", "方法", "やり方"]
        ):
            intent_type = "how_to"
        elif any(word in query_lower for word in ["なぜ", "why", "原因", "理由"]):
            intent_type = "why"
        elif any(word in query_lower for word in ["何", "what", "どんな"]):
            intent_type = "what"
        elif any(word in query_lower for word in ["いつ", "when", "時期"]):
            intent_type = "when"

        # 技術要素の抽出
        technologies = []
        tech_keywords = {
            "database": ["データベース", "db", "mysql", "postgresql", "sql"],
            "web": ["web", "ウェブ", "apache", "nginx", "http"],
            "network": ["ネットワーク", "network", "lan", "vpn"],
            "server": ["サーバー", "server", "サーバ"],
            "security": ["セキュリティ", "security", "認証", "auth"],
        }

        for tech, keywords in tech_keywords.items():
            if any(kw in query_lower for kw in keywords):
                technologies.append(tech)

        # 問題の種類
        problem_type = "unknown"
        if any(word in query_lower for word in ["遅い", "slow", "パフォーマンス"]):
            problem_type = "performance"
        elif any(word in query_lower for word in ["エラー", "error", "障害", "ダウン"]):
            problem_type = "error"
        elif any(word in query_lower for word in ["設定", "config", "変更"]):
            problem_type = "configuration"

        return {
            "type": intent_type,
            "technologies": technologies,
            "problem_type": problem_type,
        }

    def _search_knowledge(
        self, query: str, intent: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """ナレッジを検索"""
        # 基本検索
        results = self.db_client.search_knowledge(query=query, limit=10)

        # 意図に基づいてフィルタ・ソート
        if intent["problem_type"] == "performance":
            # パフォーマンス関連を優先
            results = [
                r
                for r in results
                if "パフォーマンス" in r.get("tags", [])
                or "performance" in r.get("content", "").lower()
            ][:5]

        elif intent["problem_type"] == "error":
            # Incident/Problem を優先
            results = [
                r for r in results if r.get("itsm_type") in ["Incident", "Problem"]
            ][:5]

        return results

    def _enrich_with_mcp(self, query: str, intent: Dict[str, Any]) -> Dict[str, Any]:
        """MCPで情報補強"""
        enrichments = {}

        # Context7: 技術ドキュメント
        if intent["technologies"]:
            tech_docs = {}
            for tech in intent["technologies"][:2]:
                docs = self.context7.query_documentation(tech, query)
                if docs:
                    tech_docs[tech] = docs
            enrichments["technical_docs"] = tech_docs

        # Claude-Mem: 過去の記憶
        memories = self.claude_mem.search_memories(query, limit=3)
        enrichments["memories"] = memories

        return enrichments

    def _generate_answer(
        self, query: str, knowledge: List[Dict[str, Any]], enrichments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """回答を生成"""
        answer_parts = []

        # ナレッジベースからの回答
        if knowledge:
            answer_parts.append("### 📚 関連するナレッジ")
            for k in knowledge[:3]:
                summary = k.get("summary_non_technical") or k.get("title")
                answer_parts.append(
                    f"- [{k['title']}](/knowledge/{k['id']}): {summary[:100]}"
                )

        # 技術ドキュメント
        if enrichments.get("technical_docs"):
            answer_parts.append("\n### 📖 技術ドキュメント")
            for tech, docs in enrichments["technical_docs"].items():
                for doc in docs[:2]:
                    answer_parts.append(f"- [{doc['title']}]({doc.get('url', '#')})")

        # 過去の記憶
        if enrichments.get("memories"):
            answer_parts.append("\n### 🧠 過去の関連する判断・知見")
            for mem in enrichments["memories"]:
                answer_parts.append(f"- {mem['title']}: {mem['content'][:100]}")

        # 即座に試せる対処法（簡易版）
        if knowledge:
            answer_parts.append("\n### ⚡ 即座に試せる対処法")
            answer_parts.append(
                "上記のナレッジを参照して、類似の対応を試してみてください。"
            )

        return {
            "text": "\n".join(answer_parts),
            "knowledge_count": len(knowledge),
            "has_enrichments": bool(
                enrichments.get("technical_docs") or enrichments.get("memories")
            ),
        }

    def _generate_suggestions(self, intent: Dict[str, Any]) -> List[str]:
        """関連する質問を提案"""
        suggestions = []

        if intent["problem_type"] == "performance":
            suggestions = [
                "パフォーマンス測定の方法は？",
                "ボトルネックの特定方法は？",
                "過去の最適化事例は？",
            ]
        elif intent["problem_type"] == "error":
            suggestions = [
                "エラーログの確認方法は？",
                "類似エラーの対応履歴は？",
                "エスカレーション基準は？",
            ]

        return suggestions


# 使用例
if __name__ == "__main__":
    assistant = IntelligentSearchAssistant()

    print("🔍 インテリジェント検索アシスタント")
    print("=" * 80)
    print()

    # テストクエリ
    queries = [
        "データベースが遅い時はどうすればいい？",
        "Webサーバーの503エラーの原因は？",
        "証明書の更新手順は？",
    ]

    for query in queries:
        print(f"質問: {query}")
        print("-" * 80)

        result = assistant.search(query)

        print(f"意図: {result['intent']['type']}")
        print(f"技術: {', '.join(result['intent']['technologies'])}")
        print(f"問題種別: {result['intent']['problem_type']}")
        print()
        print("回答:")
        print(result["answer"]["text"])
        print()
        print(f"関連ナレッジ: {result['answer']['knowledge_count']}件")
        print(f"追加情報: {'あり' if result['answer']['has_enrichments'] else 'なし'}")
        print()
        if result["suggestions"]:
            print("関連する質問:")
            for sug in result["suggestions"]:
                print(f"  - {sug}")
        print()
        print("=" * 80)
        print()
