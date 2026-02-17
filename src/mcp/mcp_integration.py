"""
MCP Integration Module
実際のMCP連携を有効化する統合モジュール

各MCPクライアント（Context7/GitHub/Claude-Mem/SQLite）を
統合的に管理し、ナレッジ補強パイプラインを提供します。

接続戦略:
- 各MCPサーバーへの接続を個別に試行
- 接続失敗時はスタブモードにフォールバック
- 少なくとも1つが成功すれば「有効」と見なす
"""

import logging
import os
from typing import Any, Dict, List, Optional

from .context7_client import Context7Client
from .claude_mem_client import ClaudeMemClient
from .github_client import GitHubClient

logger = logging.getLogger(__name__)


class MCPIntegration:
    """MCP統合マネージャー

    全MCPクライアントのライフサイクル管理と、
    ナレッジ補強パイプラインを提供します。
    """

    def __init__(self, auto_connect: bool = False):
        """
        Args:
            auto_connect: 自動接続するか (デフォルト: False)
                          Trueにすると、各MCPサーバーへの接続を即座に試行
        """
        self._context7: Optional[Context7Client] = None
        self._claude_mem: Optional[ClaudeMemClient] = None
        self._github: Optional[GitHubClient] = None

        # 後方互換性のフラグ
        self.context7_enabled = False
        self.claude_mem_enabled = False
        self.github_enabled = False

        if auto_connect:
            self.connect_all()

    # =========================================
    # 接続管理
    # =========================================

    def connect_all(self) -> Dict[str, bool]:
        """全MCPサーバーへの接続を試行

        Returns:
            各MCPの接続結果
        """
        results = {}
        results["context7"] = self.enable_context7()
        results["claude_mem"] = self.enable_claude_mem()
        results["github"] = self.enable_github()

        enabled_count = sum(1 for v in results.values() if v)
        if enabled_count > 0:
            logger.info(f"MCP統合: {enabled_count}/3 接続成功")
        else:
            logger.info("MCP統合: 全てスタブモードで動作")

        return results

    def disconnect_all(self):
        """全MCP接続を切断"""
        if self._context7:
            self._context7.disconnect()
        if self._claude_mem:
            self._claude_mem.disconnect()
        if self._github:
            self._github.disconnect()

        self.context7_enabled = False
        self.claude_mem_enabled = False
        self.github_enabled = False

    def enable_context7(self) -> bool:
        """Context7 MCPを有効化"""
        try:
            self._context7 = Context7Client(auto_enable=True)
            self.context7_enabled = self._context7.enabled
            if self.context7_enabled:
                logger.info("Context7 MCP: 実接続で有効化")
            else:
                logger.info("Context7 MCP: スタブモードで有効化")
            return self.context7_enabled
        except Exception as e:
            logger.error(f"Context7 MCP有効化エラー: {e}")
            # スタブモードで有効化
            self._context7 = Context7Client(auto_enable=False)
            self.context7_enabled = False
            return False

    def enable_claude_mem(self) -> bool:
        """Claude-Mem MCPを有効化"""
        try:
            self._claude_mem = ClaudeMemClient(auto_enable=True)
            self.claude_mem_enabled = self._claude_mem.enabled
            if self.claude_mem_enabled:
                logger.info("Claude-Mem MCP: 実接続で有効化")
            else:
                logger.info("Claude-Mem MCP: スタブモードで有効化")
            return self.claude_mem_enabled
        except Exception as e:
            logger.error(f"Claude-Mem MCP有効化エラー: {e}")
            self._claude_mem = ClaudeMemClient(auto_enable=False)
            self.claude_mem_enabled = False
            return False

    def enable_github(self, repository: Optional[str] = None) -> bool:
        """GitHub MCPを有効化"""
        try:
            repo = repository or os.environ.get(
                "GITHUB_REPOSITORY", "mirai-it/knowledge-base"
            )
            self._github = GitHubClient(repository=repo, auto_enable=True)
            self.github_enabled = self._github.enabled
            if self.github_enabled:
                self.github_repository = repo
                logger.info(f"GitHub MCP: 実接続で有効化 ({repo})")
            else:
                self.github_repository = repo
                logger.info("GitHub MCP: スタブモードで有効化")
            return self.github_enabled
        except Exception as e:
            logger.error(f"GitHub MCP有効化エラー: {e}")
            self._github = GitHubClient(auto_enable=False)
            self.github_enabled = False
            return False

    # =========================================
    # クライアントアクセサ
    # =========================================

    @property
    def context7(self) -> Context7Client:
        """Context7クライアントを取得"""
        if self._context7 is None:
            self._context7 = Context7Client(auto_enable=False)
        return self._context7

    @property
    def claude_mem(self) -> ClaudeMemClient:
        """Claude-Memクライアントを取得"""
        if self._claude_mem is None:
            self._claude_mem = ClaudeMemClient(auto_enable=False)
        return self._claude_mem

    @property
    def github(self) -> GitHubClient:
        """GitHubクライアントを取得"""
        if self._github is None:
            self._github = GitHubClient(auto_enable=False)
        return self._github

    # =========================================
    # ナレッジ補強パイプライン
    # =========================================

    def query_context7_docs(
        self, library_name: str, query: str
    ) -> List[Dict[str, Any]]:
        """Context7でドキュメント検索 (後方互換API)"""
        return self.context7.query_documentation(library_name, query)

    def search_claude_mem(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Claude-Memで記憶検索 (後方互換API)"""
        return self.claude_mem.search_memories(query, limit=limit)

    def enrich_knowledge_with_mcps(
        self, knowledge_content: str, detected_technologies: List[str], itsm_type: str
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
        enrichments: Dict[str, Any] = {}

        # Context7で技術ドキュメント補強
        if detected_technologies:
            tech_docs = {}
            for tech in detected_technologies[:3]:
                docs = self.context7.query_documentation(tech, f"{tech} best practices")
                if docs:
                    tech_docs[tech] = docs
            if tech_docs:
                enrichments["technical_documentation"] = tech_docs

        # Claude-Memで過去の記憶を補強
        keywords = self._extract_keywords(knowledge_content)
        memories = []
        for keyword in keywords[:2]:
            mems = self.claude_mem.search_memories(keyword)
            memories.extend(mems)
        if memories:
            enrichments["related_memories"] = memories[:5]

        # GitHub情報（オプション）
        if self._github:
            enrichments["github_repository"] = getattr(self, "github_repository", "")

        return enrichments

    # =========================================
    # ステータス
    # =========================================

    def get_status(self) -> Dict[str, Any]:
        """MCP連携ステータスを取得"""
        return {
            "context7": self.context7_enabled,
            "claude_mem": self.claude_mem_enabled,
            "github": self.github_enabled,
            "context7_mode": "live" if self.context7_enabled else "stub",
            "claude_mem_mode": "live" if self.claude_mem_enabled else "stub",
            "github_mode": "live" if self.github_enabled else "stub",
        }

    def get_detailed_status(self) -> Dict[str, Any]:
        """詳細なMCP連携ステータスを取得"""
        status = self.get_status()
        if self._context7:
            status["context7_detail"] = self._context7.get_status()
        if self._claude_mem:
            status["claude_mem_detail"] = self._claude_mem.get_status()
        if self._github:
            status["github_detail"] = self._github.get_status()
        return status

    def health_check(self) -> Dict[str, Any]:
        """全MCPクライアントのヘルスチェック

        Returns:
            各MCPの健全性レポート
        """
        report: Dict[str, Any] = {
            "overall": "healthy",
            "live_count": 0,
            "stub_count": 0,
            "error_count": 0,
            "clients": {},
        }

        # Context7
        if self._context7 and self._context7._mcp_client:
            ctx_health = self._context7._mcp_client.health_check()
            report["clients"]["context7"] = ctx_health
            if ctx_health.get("connected"):
                report["live_count"] += 1
            else:
                report["stub_count"] += 1
        else:
            report["clients"]["context7"] = {"connected": False, "mode": "stub"}
            report["stub_count"] += 1

        # Claude-Mem
        if self._claude_mem and self._claude_mem._mcp_client:
            mem_health = self._claude_mem._mcp_client.health_check()
            report["clients"]["claude_mem"] = mem_health
            if mem_health.get("connected"):
                report["live_count"] += 1
            else:
                report["stub_count"] += 1
        else:
            report["clients"]["claude_mem"] = {"connected": False, "mode": "stub"}
            report["stub_count"] += 1

        # GitHub
        if self._github and self._github._mcp_client:
            gh_health = self._github._mcp_client.health_check()
            report["clients"]["github"] = gh_health
            if gh_health.get("connected"):
                report["live_count"] += 1
            else:
                report["stub_count"] += 1
        else:
            report["clients"]["github"] = {"connected": False, "mode": "stub"}
            report["stub_count"] += 1

        if report["live_count"] == 0:
            report["overall"] = "all_stub"
        elif report["live_count"] < 3:
            report["overall"] = "partial"

        return report

    def generate_connection_report(self) -> str:
        """接続確認レポートを生成

        Returns:
            Markdownフォーマットのレポート
        """
        health = self.health_check()
        lines = [
            "# MCP接続確認レポート",
            "",
            f"## 総合ステータス: {health['overall']}",
            f"- 実接続: {health['live_count']}/3",
            f"- スタブ: {health['stub_count']}/3",
            "",
            "## 各MCP詳細",
            "",
        ]

        for name, client_health in health["clients"].items():
            mode = "LIVE" if client_health.get("connected") else "STUB"
            lines.append(f"### {name} [{mode}]")
            if client_health.get("server_info"):
                info = client_health["server_info"]
                lines.append(f"- サーバー: {info.get('server_name', 'N/A')} v{info.get('server_version', 'N/A')}")
                lines.append(f"- プロトコル: {info.get('protocol_version', 'N/A')}")
            if client_health.get("available_tools") is not None:
                lines.append(f"- 利用可能ツール数: {client_health['available_tools']}")
                tool_names = client_health.get("tool_names", [])
                if tool_names:
                    lines.append(f"- ツール: {', '.join(tool_names[:10])}")
            if client_health.get("last_error"):
                lines.append(f"- 最後のエラー: {client_health['last_error']}")
            lines.append("")

        return "\n".join(lines)

    def _extract_keywords(self, content: str) -> List[str]:
        """キーワード抽出（簡易版）"""
        important_terms = [
            "データベース", "サーバー", "ネットワーク",
            "接続", "エラー", "障害", "問題", "対策", "設定", "プール",
        ]
        content_lower = content.lower()
        return [term for term in important_terms if term in content_lower]


# グローバルインスタンス (遅延初期化)
mcp_integration = MCPIntegration(auto_connect=False)


def auto_initialize(connect: bool = False):
    """MCP連携を初期化

    Args:
        connect: 実MCPサーバーに接続するか (デフォルト: False)
                 Falseの場合、各クライアントはスタブモードで初期化
    """
    if connect:
        results = mcp_integration.connect_all()
        enabled_mcps = [name for name, enabled in results.items() if enabled]
        if enabled_mcps:
            logger.info(f"MCP連携有効化 (実接続): {', '.join(enabled_mcps)}")
        else:
            logger.info("MCP連携: 全てスタブモードで動作")
    else:
        # スタブモードで初期化 (MCPサーバー不要)
        mcp_integration.enable_context7()
        mcp_integration.enable_claude_mem()
        mcp_integration.enable_github()
        logger.info("MCP連携: スタブモードで初期化完了")
