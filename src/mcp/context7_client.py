"""
Context7 MCP Client
技術ドキュメント参照クライアント (実MCP接続対応)

Context7 MCPサーバーを使用して、ライブラリの最新ドキュメントを
検索・参照する機能を提供します。

接続フロー:
1. resolve-library-id でライブラリIDを解決
2. query-docs でドキュメントを検索
"""

import logging
from typing import Any, Dict, List, Optional

from .mcp_client_base import MCPClientBase

logger = logging.getLogger(__name__)


class Context7Client:
    """Context7連携クライアント

    Context7 MCPサーバーと実接続してドキュメント検索を行います。
    MCP未検出時はデモデータにフォールバックします。
    """

    # .mcp.json の context7 設定に準拠
    DEFAULT_COMMAND = "npx"
    DEFAULT_ARGS = ["-y", "@upstash/context7-mcp"]

    def __init__(self, auto_enable: bool = True):
        """初期化

        Args:
            auto_enable: MCP自動接続（デフォルト: True）
        """
        self._cached_docs: Dict[str, List[Dict[str, Any]]] = {}
        self._mcp_client: Optional[MCPClientBase] = None
        self.enabled = False

        if auto_enable:
            self.enabled = self._try_connect()

    def _try_connect(self) -> bool:
        """MCPサーバーへの接続を試行"""
        try:
            self._mcp_client = MCPClientBase(
                server_command=self.DEFAULT_COMMAND,
                server_args=self.DEFAULT_ARGS,
                timeout=30.0,
            )
            connected = self._mcp_client.connect()
            if connected:
                logger.info("Context7 MCP: 実接続成功")
                return True
            else:
                logger.info("Context7 MCP: 接続失敗、スタブモードで動作")
                self._mcp_client = None
                return False
        except Exception as e:
            logger.warning(f"Context7 MCP: 接続エラー ({e})、スタブモードで動作")
            self._mcp_client = None
            return False

    def disconnect(self):
        """MCP接続を切断"""
        if self._mcp_client:
            self._mcp_client.disconnect()
            self._mcp_client = None
        self.enabled = False

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
        # キャッシュチェック
        cache_key = f"{library_name}:{query}"
        if cache_key in self._cached_docs:
            return self._cached_docs[cache_key][:max_results]

        if not self.enabled or not self._mcp_client:
            return self._get_demo_results(library_name, query)

        try:
            # Step 1: ライブラリIDを解決
            library_id = self._resolve_library_id(library_name, query)
            if not library_id:
                logger.info(f"Context7: ライブラリID未解決 ({library_name})、デモデータにフォールバック")
                return self._get_demo_results(library_name, query)

            # Step 2: ドキュメント検索
            result = self._mcp_client.call_tool("query-docs", {
                "libraryId": library_id,
                "query": query,
            })

            if result is None:
                return self._get_demo_results(library_name, query)

            # 結果をフォーマット
            formatted_results = self._format_tool_result(result, max_results)

            # キャッシュに保存
            self._cached_docs[cache_key] = formatted_results
            return formatted_results

        except Exception as e:
            logger.warning(f"Context7 ドキュメント検索エラー: {e}")
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
        return self._resolve_library_id(library_name, query)

    def _resolve_library_id(self, library_name: str, query: str = "") -> Optional[str]:
        """ライブラリIDの内部解決"""
        if not self.enabled or not self._mcp_client:
            return None

        try:
            result = self._mcp_client.call_tool("resolve-library-id", {
                "libraryName": library_name,
            })

            if result is None:
                return None

            # MCP tools/call の result はcontent配列
            content_list = result.get("content", [])
            if content_list:
                # テキストコンテンツからライブラリIDを取得
                text_content = content_list[0].get("text", "")
                if text_content:
                    # Context7はライブラリIDをテキストで返す
                    return text_content.strip()

            return None
        except Exception as e:
            logger.warning(f"Context7 ライブラリID解決エラー: {e}")
            return None

    def _format_tool_result(
        self, result: Dict[str, Any], max_results: int
    ) -> List[Dict[str, Any]]:
        """MCP tools/call の結果を標準フォーマットに変換"""
        formatted = []

        content_list = result.get("content", [])
        for item in content_list[:max_results]:
            text = item.get("text", "")
            if text:
                formatted.append({
                    "title": text[:100] if len(text) > 100 else text,
                    "url": "",
                    "snippet": text[:500],
                    "source": "Context7",
                })

        return formatted

    def _get_demo_results(self, library_name: str, query: str) -> List[Dict[str, Any]]:
        """デモ用の検索結果を返す（スタブモード）"""
        demo_data = {
            "flask": [
                {
                    "title": "Flask Routing",
                    "url": "https://flask.palletsprojects.com/routing/",
                    "snippet": "Use the route() decorator to bind a function to a URL...",
                    "source": "Context7-stub",
                },
                {
                    "title": "URL Building",
                    "url": "https://flask.palletsprojects.com/quickstart/#url-building",
                    "snippet": "url_for() generates URLs to functions based on the function name...",
                    "source": "Context7-stub",
                },
            ],
            "sqlite": [
                {
                    "title": "SQLite FTS5",
                    "url": "https://www.sqlite.org/fts5.html",
                    "snippet": "FTS5 is an SQLite virtual table module for full-text search...",
                    "source": "Context7-stub",
                },
                {
                    "title": "SQLite Index",
                    "url": "https://www.sqlite.org/lang_createindex.html",
                    "snippet": "CREATE INDEX creates a new index on a table...",
                    "source": "Context7-stub",
                },
            ],
            "python": [
                {
                    "title": "Python Error Handling",
                    "url": "https://docs.python.org/3/tutorial/errors.html",
                    "snippet": "Handle exceptions with try-except blocks...",
                    "source": "Context7-stub",
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
            keywords = self._extract_tech_keywords(knowledge_content, tech)

            if keywords:
                docs = self.query_documentation(tech, " ".join(keywords))
                enrichments[tech] = {"keywords": keywords, "documentation": docs}

        return enrichments

    def _extract_tech_keywords(self, content: str, technology: str) -> List[str]:
        """技術関連のキーワードを抽出"""
        content_lower = content.lower()

        tech_keywords = {
            "flask": [
                "route", "request", "response", "session",
                "template", "blueprint",
            ],
            "sqlite": ["query", "index", "fts", "transaction", "trigger", "view"],
            "python": ["exception", "class", "function", "module", "package"],
        }

        keywords = []
        for keyword in tech_keywords.get(technology, []):
            if keyword in content_lower:
                keywords.append(keyword)

        return keywords

    def get_status(self) -> Dict[str, Any]:
        """接続ステータスを返す"""
        return {
            "enabled": self.enabled,
            "mode": "live" if self.enabled else "stub",
            "cached_queries": len(self._cached_docs),
        }


# グローバルインスタンス（オプション）
context7_client = Context7Client(auto_enable=False)
