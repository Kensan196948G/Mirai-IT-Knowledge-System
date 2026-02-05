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

    def __init__(self, auto_enable: bool = True):
        """初期化

        Args:
            auto_enable: MCP自動有効化（デフォルト: True）
        """
        self._cached_docs = {}  # ドキュメントキャッシュ
        self.enabled = auto_enable and self._check_mcp_available()

    def _check_mcp_available(self) -> bool:
        """MCP利用可能性をチェック"""
        try:
            # Context7 MCPツールの存在を確認
            import sys
            tool = globals().get('mcp__context7__query_docs') or \
                   getattr(sys.modules.get('__main__', {}), 'mcp__context7__query_docs', None)
            return tool is not None
        except Exception:
            return False

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

        try:
            # 実際のMCP呼び出し
            from ..tools import mcp__context7__resolve_library_id, mcp__context7__query_docs

            # まずライブラリIDを解決
            library_resolution = mcp__context7__resolve_library_id(
                libraryName=library_name,
                query=query
            )

            library_id = library_resolution.get("library_id")
            if not library_id:
                return self._get_demo_results(library_name, query)

            # ドキュメントを検索
            doc_results = mcp__context7__query_docs(
                libraryId=library_id,
                query=query
            )

            # 結果をフォーマット
            formatted_results = []
            for doc in doc_results.get("results", [])[:max_results]:
                formatted_results.append({
                    "title": doc.get("title", ""),
                    "url": doc.get("url", ""),
                    "snippet": doc.get("snippet", ""),
                    "relevance": doc.get("score", 0.0)
                })

            # キャッシュに保存
            cache_key = f"{library_name}:{query}"
            self._cached_docs[cache_key] = formatted_results

            return formatted_results

        except Exception as e:
            print(f"Warning: Context7 documentation search failed: {e}")
            return self._get_demo_results(library_name, query)

    def resolve_library_id(self, library_name: str, query: str = "") -> Optional[str]:
        """
        ライブラリIDを解決

        Args:
            library_name: ライブラリ名
            query: 検索コンテキスト（オプション）

        Returns:
            ライブラリID（見つからない場合はNone）
        """
        if not self.enabled:
            return None

        try:
            # 実際のMCP呼び出し
            from ..tools import mcp__context7__resolve_library_id

            result = mcp__context7__resolve_library_id(
                libraryName=library_name,
                query=query or f"Documentation for {library_name}"
            )

            return result.get("library_id")

        except Exception as e:
            print(f"Warning: Library ID resolution failed: {e}")
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
