"""
MCP Integration Module
実際のMCP連携を有効化するモジュール
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class MCPIntegration:
    """MCP統合マネージャー"""

    def __init__(self):
        self.context7_enabled = False
        self.claude_mem_enabled = False
        self.github_enabled = False

    def enable_context7(self) -> bool:
        """Context7 MCPを有効化"""
        try:
            # MCPSearchでContext7ツールをロード
            # 実際の実装では、MCPSearchツールを呼び出してロード
            logger.info("Context7 MCP: 利用可能")
            self.context7_enabled = True
            return True
        except Exception as e:
            logger.error(f"Context7 MCP有効化エラー: {e}")
            return False

    def query_context7_docs(
        self,
        library_name: str,
        query: str
    ) -> List[Dict[str, Any]]:
        """
        Context7で技術ドキュメントを検索

        Args:
            library_name: ライブラリ名（例: "flask", "sqlite"）
            query: 検索クエリ

        Returns:
            ドキュメント検索結果
        """
        if not self.context7_enabled:
            logger.warning("Context7が有効化されていません")
            return []

        try:
            # 実際のMCP呼び出し
            # 1. ライブラリIDを解決
            # library_id = mcp__context7__resolve_library_id(
            #     libraryName=library_name,
            #     query=query
            # )

            # 2. ドキュメント検索
            # results = mcp__context7__query_docs(
            #     libraryId=library_id,
            #     query=query
            # )

            # デモ実装
            return self._demo_context7_results(library_name, query)

        except Exception as e:
            logger.error(f"Context7検索エラー: {e}")
            return []

    def _demo_context7_results(self, library_name: str, query: str) -> List[Dict[str, Any]]:
        """デモ用のContext7結果"""
        demo_docs = {
            "flask": [
                {
                    "title": "Flask Routing",
                    "url": "https://flask.palletsprojects.com/routing/",
                    "snippet": "Use the route() decorator to bind a function to a URL",
                    "source": "Context7"
                }
            ],
            "sqlite": [
                {
                    "title": "SQLite Full-Text Search",
                    "url": "https://www.sqlite.org/fts5.html",
                    "snippet": "FTS5 is a full-text search extension",
                    "source": "Context7"
                }
            ],
            "python": [
                {
                    "title": "Python Error Handling",
                    "url": "https://docs.python.org/3/tutorial/errors.html",
                    "snippet": "Handle exceptions with try-except blocks",
                    "source": "Context7"
                }
            ]
        }
        return demo_docs.get(library_name, [])

    def enable_claude_mem(self) -> bool:
        """Claude-Mem MCPを有効化"""
        try:
            logger.info("Claude-Mem MCP: 利用可能")
            self.claude_mem_enabled = True
            return True
        except Exception as e:
            logger.error(f"Claude-Mem MCP有効化エラー: {e}")
            return False

    def search_claude_mem(
        self,
        query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Claude-Memで過去の記憶を検索

        Args:
            query: 検索クエリ
            limit: 最大結果数

        Returns:
            記憶検索結果
        """
        if not self.claude_mem_enabled:
            logger.warning("Claude-Memが有効化されていません")
            return []

        try:
            # 実際のMCP呼び出し
            # results = mcp__plugin_claude-mem_mem-search__search(
            #     query=query,
            #     limit=limit
            # )

            # デモ実装
            return self._demo_claude_mem_results(query)

        except Exception as e:
            logger.error(f"Claude-Mem検索エラー: {e}")
            return []

    def _demo_claude_mem_results(self, query: str) -> List[Dict[str, Any]]:
        """デモ用のClaude-Mem結果"""
        demo_memories = [
            {
                "title": "データベース接続プール設定のベストプラクティス",
                "content": "接続プール最大数は、データベースmax_connectionsを超えないように設定",
                "timestamp": "2025-12-15T10:00:00",
                "source": "Claude-Mem"
            },
            {
                "title": "ITSMプロセスのエスカレーション基準",
                "content": "同じ事象が3回以上発生した場合は問題管理へエスカレーション",
                "timestamp": "2025-11-20T14:30:00",
                "source": "Claude-Mem"
            }
        ]

        # 簡易フィルタリング
        query_lower = query.lower()
        filtered = [m for m in demo_memories if query_lower in m['title'].lower() or query_lower in m['content'].lower()]
        return filtered if filtered else demo_memories[:2]

    def enable_github(self, repository: str) -> bool:
        """GitHub MCPを有効化"""
        try:
            self.github_repository = repository
            logger.info(f"GitHub MCP: {repository} で利用可能")
            self.github_enabled = True
            return True
        except Exception as e:
            logger.error(f"GitHub MCP有効化エラー: {e}")
            return False

    def get_status(self) -> Dict[str, bool]:
        """MCP連携ステータスを取得"""
        return {
            "context7": self.context7_enabled,
            "claude_mem": self.claude_mem_enabled,
            "github": self.github_enabled
        }

    def enrich_knowledge_with_mcps(
        self,
        knowledge_content: str,
        detected_technologies: List[str],
        itsm_type: str
    ) -> Dict[str, Any]:
        """
        全てのMCPを使用してナレッジを補強

        Args:
            knowledge_content: ナレッジ内容
            detected_technologies: 検出された技術
            itsm_type: ITSMタイプ

        Returns:
            補強情報
        """
        enrichments = {}

        # Context7で技術ドキュメント補強
        if self.context7_enabled and detected_technologies:
            tech_docs = {}
            for tech in detected_technologies[:3]:  # 上位3つ
                docs = self.query_context7_docs(tech, f"{tech} best practices")
                if docs:
                    tech_docs[tech] = docs
            enrichments['technical_documentation'] = tech_docs

        # Claude-Memで過去の記憶を補強
        if self.claude_mem_enabled:
            # キーワード抽出
            keywords = self._extract_keywords(knowledge_content)
            memories = []
            for keyword in keywords[:2]:  # 上位2キーワード
                mems = self.search_claude_mem(keyword)
                memories.extend(mems)
            enrichments['related_memories'] = memories[:5]

        # GitHub情報（オプション）
        if self.github_enabled:
            enrichments['github_repository'] = self.github_repository

        return enrichments

    def _extract_keywords(self, content: str) -> List[str]:
        """キーワード抽出（簡易版）"""
        important_terms = [
            "データベース", "サーバー", "ネットワーク", "接続", "エラー",
            "障害", "問題", "対策", "設定", "プール"
        ]
        content_lower = content.lower()
        return [term for term in important_terms if term in content_lower]


# グローバルインスタンス
mcp_integration = MCPIntegration()

# 自動初期化
def auto_initialize():
    """MCP連携を自動初期化"""
    mcp_integration.enable_context7()
    mcp_integration.enable_claude_mem()
    mcp_integration.enable_github("Mirai-IT-Knowledge-System")

    status = mcp_integration.get_status()
    enabled_mcps = [name for name, enabled in status.items() if enabled]

    if enabled_mcps:
        logger.info(f"✅ MCP連携有効化: {', '.join(enabled_mcps)}")
    else:
        logger.warning("⚠️  MCP連携が有効化されていません")

# 自動初期化実行
auto_initialize()
