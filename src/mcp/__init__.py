"""
MCP (Model Context Protocol) Integration Layer

各MCPサーバーとの通信を担うクライアントモジュール群:
- MCPClientBase: JSON-RPC over stdio ベースクライアント
- Context7Client: 技術ドキュメント検索
- ClaudeMemClient: 会話履歴・記憶管理
- GitHubClient: バージョン管理・監査証跡
- SQLiteClient: ローカルDB操作
- MCPIntegration: 統合マネージャー
"""

from .sqlite_client import SQLiteClient
from .mcp_client_base import MCPClientBase
from .context7_client import Context7Client
from .claude_mem_client import ClaudeMemClient
from .github_client import GitHubClient
from .mcp_integration import MCPIntegration, mcp_integration

__all__ = [
    "SQLiteClient",
    "MCPClientBase",
    "Context7Client",
    "ClaudeMemClient",
    "GitHubClient",
    "MCPIntegration",
    "mcp_integration",
]
