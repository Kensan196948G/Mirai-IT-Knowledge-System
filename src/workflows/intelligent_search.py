"""
Intelligent Search Assistant Workflow
インテリジェント検索アシスタント

自然言語での問い合わせに対して最適なナレッジを提案
"""

from typing import Dict, Any, List
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.mcp.sqlite_client import SQLiteClient
from src.mcp.context7_client import Context7Client
from src.mcp.claude_mem_client import ClaudeMemClient


class IntelligentSearchAssistant:
    """インテリジェント検索アシスタント"""

    def __init__(self):
        self.db_client = SQLiteClient()
        self.context7 = Context7Client()
        self.claude_mem = ClaudeMemClient()

    def search(self, query: str) -> Dict[str, Any]:
        """
        自然言語クエリで検索

        Args:
            query: 自然言語の質問（例: 「データベースが遅い時はどうすればいい？」）

        Returns:
            総合的な回答とナレッジ
        """
        # Step 1: 意図理解
        intent = self._understand_intent(query)

        # Step 2: 関連ナレッジ検索
        knowledge_results = self._search_knowledge(query, intent)

        # Step 3: MCP連携で補強
        enrichments = self._enrich_with_mcp(query, intent)

        # Step 4: 回答生成
        answer = self._generate_answer(query, knowledge_results, enrichments)

        return {
            'query': query,
            'intent': intent,
            'answer': answer,
            'knowledge': knowledge_results,
            'enrichments': enrichments,
            'suggestions': self._generate_suggestions(intent)
        }

    def _understand_intent(self, query: str) -> Dict[str, Any]:
        """クエリの意図を理解"""
        query_lower = query.lower()

        # 意図の分類
        intent_type = 'general'
        if any(word in query_lower for word in ['どうすれば', 'どうやって', '方法', 'やり方']):
            intent_type = 'how_to'
        elif any(word in query_lower for word in ['なぜ', 'why', '原因', '理由']):
            intent_type = 'why'
        elif any(word in query_lower for word in ['何', 'what', 'どんな']):
            intent_type = 'what'
        elif any(word in query_lower for word in ['いつ', 'when', '時期']):
            intent_type = 'when'

        # 技術要素の抽出
        technologies = []
        tech_keywords = {
            'database': ['データベース', 'db', 'mysql', 'postgresql', 'sql'],
            'web': ['web', 'ウェブ', 'apache', 'nginx', 'http'],
            'network': ['ネットワーク', 'network', 'lan', 'vpn'],
            'server': ['サーバー', 'server', 'サーバ'],
            'security': ['セキュリティ', 'security', '認証', 'auth']
        }

        for tech, keywords in tech_keywords.items():
            if any(kw in query_lower for kw in keywords):
                technologies.append(tech)

        # 問題の種類
        problem_type = 'unknown'
        if any(word in query_lower for word in ['遅い', 'slow', 'パフォーマンス']):
            problem_type = 'performance'
        elif any(word in query_lower for word in ['エラー', 'error', '障害', 'ダウン']):
            problem_type = 'error'
        elif any(word in query_lower for word in ['設定', 'config', '変更']):
            problem_type = 'configuration'

        return {
            'type': intent_type,
            'technologies': technologies,
            'problem_type': problem_type
        }

    def _search_knowledge(self, query: str, intent: Dict[str, Any]) -> List[Dict[str, Any]]:
        """ナレッジを検索"""
        # 基本検索
        results = self.db_client.search_knowledge(query=query, limit=10)

        # 意図に基づいてフィルタ・ソート
        if intent['problem_type'] == 'performance':
            # パフォーマンス関連を優先
            results = [r for r in results if 'パフォーマンス' in r.get('tags', []) or
                      'performance' in r.get('content', '').lower()][:5]

        elif intent['problem_type'] == 'error':
            # Incident/Problem を優先
            results = [r for r in results if r.get('itsm_type') in ['Incident', 'Problem']][:5]

        return results

    def _enrich_with_mcp(self, query: str, intent: Dict[str, Any]) -> Dict[str, Any]:
        """MCPで情報補強"""
        enrichments = {}

        # Context7: 技術ドキュメント
        if intent['technologies']:
            tech_docs = {}
            for tech in intent['technologies'][:2]:
                docs = self.context7.query_documentation(tech, query)
                if docs:
                    tech_docs[tech] = docs
            enrichments['technical_docs'] = tech_docs

        # Claude-Mem: 過去の記憶
        memories = self.claude_mem.search_memories(query, limit=3)
        enrichments['memories'] = memories

        return enrichments

    def _generate_answer(
        self,
        query: str,
        knowledge: List[Dict[str, Any]],
        enrichments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """回答を生成"""
        answer_parts = []

        # ナレッジベースからの回答
        if knowledge:
            answer_parts.append("### 📚 関連するナレッジ")
            for k in knowledge[:3]:
                summary = k.get('summary_non_technical') or k.get('title')
                answer_parts.append(f"- [{k['title']}](/knowledge/{k['id']}): {summary[:100]}")

        # 技術ドキュメント
        if enrichments.get('technical_docs'):
            answer_parts.append("\n### 📖 技術ドキュメント")
            for tech, docs in enrichments['technical_docs'].items():
                for doc in docs[:2]:
                    answer_parts.append(f"- [{doc['title']}]({doc.get('url', '#')})")

        # 過去の記憶
        if enrichments.get('memories'):
            answer_parts.append("\n### 🧠 過去の関連する判断・知見")
            for mem in enrichments['memories']:
                answer_parts.append(f"- {mem['title']}: {mem['content'][:100]}")

        # 即座に試せる対処法（簡易版）
        if knowledge:
            answer_parts.append("\n### ⚡ 即座に試せる対処法")
            answer_parts.append("上記のナレッジを参照して、類似の対応を試してみてください。")

        return {
            'text': '\n'.join(answer_parts),
            'knowledge_count': len(knowledge),
            'has_enrichments': bool(enrichments.get('technical_docs') or enrichments.get('memories'))
        }

    def _generate_suggestions(self, intent: Dict[str, Any]) -> List[str]:
        """関連する質問を提案"""
        suggestions = []

        if intent['problem_type'] == 'performance':
            suggestions = [
                "パフォーマンス測定の方法は？",
                "ボトルネックの特定方法は？",
                "過去の最適化事例は？"
            ]
        elif intent['problem_type'] == 'error':
            suggestions = [
                "エラーログの確認方法は？",
                "類似エラーの対応履歴は？",
                "エスカレーション基準は？"
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
        "証明書の更新手順は？"
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
        print(result['answer']['text'])
        print()
        print(f"関連ナレッジ: {result['answer']['knowledge_count']}件")
        print(f"追加情報: {'あり' if result['answer']['has_enrichments'] else 'なし'}")
        print()
        if result['suggestions']:
            print("関連する質問:")
            for sug in result['suggestions']:
                print(f"  - {sug}")
        print()
        print("=" * 80)
        print()
