"""
Context7 MCP Client
技術ドキュメント参照クライアント
"""

from typing import Any, Dict, List, Optional


class Context7Client:
    """Context7連携クライアント

    Context7 MCPを使用して技術ドキュメントを検索・参照する機能を提供

    Note: 実際のMCP連携には、MCPSearchツールを使用して
    mcp__context7__* ツールをロードする必要があります
    """

    def __init__(self):
        """初期化"""
        self.enabled = False  # MCP利用可能かどうか
        self._cached_docs = {}  # ドキュメントキャッシュ

    def query_documentation(
        self, library_name: str, query: str, max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        技術ドキュメントを検索

        Args:
            library_name: ライブラリ名（例: "python", "flask", "sqlite"）
            query: 検索クエリ
            max_results: 最大結果数

        Returns:
            検索結果のリスト

        Example:
            results = client.query_documentation(
                library_name="flask",
                query="routing and URL building"
            )
        """
        # 実際のMCP連携実装
        # この関数は、MCPSearchでmcp__context7__query-docsをロードして使用する

        # デモ実装（実際はMCP経由）
        if not self.enabled:
            return self._get_demo_results(library_name, query)

        # TODO: 実際のMCP呼び出し
        # results = mcp_call("mcp__context7__query-docs", {
        #     "library": library_name,
        #     "query": query,
        #     "max_results": max_results
        # })

        return []

    def resolve_library_id(self, library_name: str) -> Optional[str]:
        """
        ライブラリIDを解決

        Args:
            library_name: ライブラリ名

        Returns:
            ライブラリID（見つからない場合はNone）
        """
        # TODO: 実際のMCP呼び出し
        # library_id = mcp_call("mcp__context7__resolve-library-id", {
        #     "library_name": library_name
        # })

        return None

    def _get_demo_results(self, library_name: str, query: str) -> List[Dict[str, Any]]:
        """デモ用の検索結果を返す"""
        demo_data = {
            "flask": [
                {
                    "title": "Flask Routing",
                    "url": "https://flask.palletsprojects.com/routing/",
                    "snippet": "Use the route() decorator to bind a function to a URL...",
                },
                {
                    "title": "URL Building",
                    "url": "https://flask.palletsprojects.com/quickstart/#url-building",
                    "snippet": "url_for() generates URLs to functions based on the function name...",
                },
            ],
            "sqlite": [
                {
                    "title": "SQLite FTS5",
                    "url": "https://www.sqlite.org/fts5.html",
                    "snippet": "FTS5 is an SQLite virtual table module for full-text search...",
                },
                {
                    "title": "SQLite Index",
                    "url": "https://www.sqlite.org/lang_createindex.html",
                    "snippet": "CREATE INDEX creates a new index on a table...",
                },
            ],
            "python": [
                {
                    "title": "Python Error Handling",
                    "url": "https://docs.python.org/3/tutorial/errors.html",
                    "snippet": "Handle exceptions with try-except blocks...",
                }
            ],
        }

        return demo_data.get(library_name, [])

    def enrich_knowledge_with_docs(
        self, knowledge_content: str, detected_technologies: List[str]
    ) -> Dict[str, Any]:
        """
        ナレッジ内容を技術ドキュメントで補強

        Args:
            knowledge_content: ナレッジ内容
            detected_technologies: 検出された技術（例: ["flask", "sqlite"]）

        Returns:
            補強情報
        """
        enrichments = {}

        for tech in detected_technologies:
            # 技術に関連するキーワードを抽出
            keywords = self._extract_tech_keywords(knowledge_content, tech)

            if keywords:
                # 各キーワードでドキュメント検索
                docs = self.query_documentation(tech, " ".join(keywords))
                enrichments[tech] = {"keywords": keywords, "documentation": docs}

        return enrichments

    def _extract_tech_keywords(self, content: str, technology: str) -> List[str]:
        """技術関連のキーワードを抽出"""
        content_lower = content.lower()

        tech_keywords = {
            "flask": [
                "route",
                "request",
                "response",
                "session",
                "template",
                "blueprint",
            ],
            "sqlite": ["query", "index", "fts", "transaction", "trigger", "view"],
            "python": ["exception", "class", "function", "module", "package"],
        }

        keywords = []
        for keyword in tech_keywords.get(technology, []):
            if keyword in content_lower:
                keywords.append(keyword)

        return keywords


# グローバルインスタンス（オプション）
context7_client = Context7Client()
