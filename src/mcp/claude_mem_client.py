"""
Claude-Mem MCP Client
設計思想・判断記憶クライアント
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


class ClaudeMemClient:
    """Claude-Mem連携クライアント

    設計思想、判断理由、過去の決定事項を記憶・検索する機能を提供

    Note: 実際のMCP連携には、MCPSearchツールを使用して
    mcp__plugin_claude-mem_mem-search__* ツールをロードする必要があります
    """

    def __init__(self):
        """初期化"""
        self.enabled = False  # MCP利用可能かどうか
        self._memory_cache = []  # メモリキャッシュ

    def search_memories(
        self,
        query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        過去の記憶を検索

        Args:
            query: 検索クエリ
            limit: 最大結果数

        Returns:
            検索結果のリスト

        Example:
            memories = client.search_memories("データベース接続プール設定")
        """
        # TODO: 実際のMCP呼び出し
        # results = mcp_call("mcp__plugin_claude-mem_mem-search__search", {
        #     "query": query,
        #     "limit": limit
        # })

        # デモ実装
        return self._get_demo_memories(query)

    def get_context_timeline(
        self,
        context_type: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        コンテキストのタイムラインを取得

        Args:
            context_type: コンテキストタイプ
            days: 取得日数

        Returns:
            タイムラインデータ
        """
        # TODO: 実際のMCP呼び出し
        # timeline = mcp_call("mcp__plugin_claude-mem_mem-search__get_context_timeline", {
        #     "context_type": context_type,
        #     "days": days
        # })

        return []

    def store_design_decision(
        self,
        knowledge_id: int,
        decision_title: str,
        rationale: str,
        alternatives_considered: Optional[List[str]] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """
        設計判断を記憶

        Args:
            knowledge_id: ナレッジID
            decision_title: 判断のタイトル
            rationale: 判断理由
            alternatives_considered: 検討した代替案
            tags: タグ

        Returns:
            成功したかどうか
        """
        memory = {
            "knowledge_id": knowledge_id,
            "decision_title": decision_title,
            "rationale": rationale,
            "alternatives": alternatives_considered or [],
            "tags": tags or [],
            "timestamp": datetime.now().isoformat()
        }

        # TODO: 実際のMCP呼び出しでメモリに保存

        # デモ実装
        self._memory_cache.append(memory)
        return True

    def get_related_decisions(
        self,
        knowledge_id: int
    ) -> List[Dict[str, Any]]:
        """
        関連する過去の判断を取得

        Args:
            knowledge_id: ナレッジID

        Returns:
            関連判断のリスト
        """
        # デモ実装
        return [m for m in self._memory_cache if m.get('knowledge_id') == knowledge_id]

    def _get_demo_memories(self, query: str) -> List[Dict[str, Any]]:
        """デモ用のメモリデータ"""
        demo_memories = [
            {
                "title": "データベース接続プール設定のベストプラクティス",
                "content": "各アプリケーションサーバーの接続プール最大数は、データベース側の max_connections を超えないように設定する必要がある。",
                "timestamp": "2025-12-15T10:00:00",
                "tags": ["database", "connection-pool", "best-practice"]
            },
            {
                "title": "ITSMプロセスにおけるインシデント→問題管理の移行判断",
                "content": "同じ事象が3回以上発生した場合、または根本原因が不明な場合は、問題管理プロセスへエスカレーションする。",
                "timestamp": "2025-11-20T14:30:00",
                "tags": ["itsm", "incident", "problem", "escalation"]
            },
            {
                "title": "証明書更新作業の標準手順",
                "content": "SSL/TLS証明書の更新は、期限の2週間前から計画し、ステージング環境で事前検証を行う。",
                "timestamp": "2025-10-05T09:00:00",
                "tags": ["security", "certificate", "procedure"]
            }
        ]

        # クエリに基づいた簡易フィルタリング
        query_lower = query.lower()
        filtered = [
            m for m in demo_memories
            if query_lower in m['title'].lower() or query_lower in m['content'].lower()
        ]

        return filtered if filtered else demo_memories[:2]

    def enhance_knowledge_with_memory(
        self,
        knowledge_content: str,
        itsm_type: str
    ) -> Dict[str, Any]:
        """
        ナレッジを過去の記憶で補強

        Args:
            knowledge_content: ナレッジ内容
            itsm_type: ITSMタイプ

        Returns:
            補強情報
        """
        # キーワード抽出（簡易版）
        keywords = self._extract_keywords(knowledge_content)

        # 各キーワードで記憶を検索
        all_memories = []
        for keyword in keywords[:3]:  # 上位3キーワード
            memories = self.search_memories(keyword, limit=2)
            all_memories.extend(memories)

        # 重複除去
        unique_memories = []
        seen_titles = set()
        for memory in all_memories:
            title = memory.get('title', '')
            if title not in seen_titles:
                unique_memories.append(memory)
                seen_titles.add(title)

        return {
            "related_memories": unique_memories[:5],
            "keywords_used": keywords[:3]
        }

    def _extract_keywords(self, content: str) -> List[str]:
        """キーワード抽出（簡易版）"""
        # 重要な技術用語を抽出
        important_terms = [
            "データベース", "サーバー", "ネットワーク", "証明書", "バックアップ",
            "接続", "プール", "エラー", "障害", "問題", "変更", "リリース",
            "セキュリティ", "パフォーマンス", "監視", "アラート"
        ]

        content_lower = content.lower()
        found_keywords = []

        for term in important_terms:
            if term in content_lower:
                found_keywords.append(term)

        return found_keywords[:5]


# グローバルインスタンス（オプション）
claude_mem_client = ClaudeMemClient()
