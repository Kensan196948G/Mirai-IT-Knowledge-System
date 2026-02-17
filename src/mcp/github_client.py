"""
GitHub MCP Client
バージョン管理・監査証跡クライアント (実MCP接続対応)

GitHub MCPサーバーを使用して、ナレッジの変更履歴をGitHubで管理し、
監査証跡を保持する機能を提供します。

主な機能:
- ナレッジファイルのコミット管理
- Issue/PR操作
- 変更履歴の追跡・監査証跡
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from .mcp_client_base import MCPClientBase

logger = logging.getLogger(__name__)


class GitHubClient:
    """GitHub連携クライアント

    GitHub MCPサーバーと実接続してリポジトリ操作を行います。
    MCP未検出時はデモデータにフォールバックします。
    """

    # .mcp.json の github 設定に準拠
    DEFAULT_COMMAND = "npx"
    DEFAULT_ARGS = ["-y", "@modelcontextprotocol/server-github"]

    def __init__(self, repository: Optional[str] = None, auto_enable: bool = True):
        """
        初期化

        Args:
            repository: GitHubリポジトリ名（例: "owner/repo"）
            auto_enable: MCP自動接続（デフォルト: True）
        """
        self.repository = repository or "mirai-it/knowledge-base"
        self._commit_cache: List[Dict[str, Any]] = []
        self.auto_commit_enabled = False
        self._mcp_client: Optional[MCPClientBase] = None
        self.enabled = False

        if auto_enable:
            self.enabled = self._try_connect()

    def _try_connect(self) -> bool:
        """MCPサーバーへの接続を試行"""
        github_token = os.environ.get("GITHUB_TOKEN", "")
        if not github_token:
            logger.info("GitHub MCP: GITHUB_TOKEN未設定、スタブモードで動作")
            return False

        try:
            self._mcp_client = MCPClientBase(
                server_command=self.DEFAULT_COMMAND,
                server_args=self.DEFAULT_ARGS,
                env={"GITHUB_TOKEN": github_token},
                timeout=30.0,
            )
            connected = self._mcp_client.connect()
            if connected:
                logger.info(f"GitHub MCP: 実接続成功 (repo: {self.repository})")
                return True
            else:
                logger.info("GitHub MCP: 接続失敗、スタブモードで動作")
                self._mcp_client = None
                return False
        except Exception as e:
            logger.warning(f"GitHub MCP: 接続エラー ({e})、スタブモードで動作")
            self._mcp_client = None
            return False

    def disconnect(self):
        """MCP接続を切断"""
        if self._mcp_client:
            self._mcp_client.disconnect()
            self._mcp_client = None
        self.enabled = False

    def _parse_repo(self) -> tuple:
        """リポジトリ名をowner/repoに分割"""
        parts = self.repository.split("/")
        if len(parts) == 2:
            return parts[0], parts[1]
        return "", self.repository

    def commit_knowledge(
        self,
        knowledge_id: int,
        file_path: str,
        content: str,
        commit_message: str,
        author: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        ナレッジをGitHubにコミット

        Args:
            knowledge_id: ナレッジID
            file_path: ファイルパス
            content: ファイル内容
            commit_message: コミットメッセージ
            author: 作成者

        Returns:
            コミット情報
        """
        if not self.enabled or not self._mcp_client:
            commit = {
                "sha": f"stub_{knowledge_id:04d}",
                "message": commit_message,
                "author": author or "system",
                "timestamp": datetime.now().isoformat(),
                "file_path": file_path,
                "mode": "stub",
            }
            self._commit_cache.append(commit)
            return commit

        try:
            owner, repo = self._parse_repo()
            result = self._mcp_client.call_tool("create_or_update_file", {
                "owner": owner,
                "repo": repo,
                "path": file_path,
                "content": content,
                "message": commit_message,
                "branch": "main",
            })

            if result is None:
                return self._stub_commit(knowledge_id, file_path, commit_message, author)

            commit = {
                "sha": self._extract_text(result)[:40],
                "message": commit_message,
                "author": author or "system",
                "timestamp": datetime.now().isoformat(),
                "file_path": file_path,
                "mode": "live",
            }
            self._commit_cache.append(commit)
            return commit

        except Exception as e:
            logger.warning(f"GitHub commit failed: {e}")
            return self._stub_commit(knowledge_id, file_path, commit_message, author)

    def get_knowledge_history(
        self, file_path: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        ナレッジの変更履歴を取得

        Args:
            file_path: ファイルパス
            limit: 最大取得件数

        Returns:
            コミット履歴のリスト
        """
        if not self.enabled or not self._mcp_client:
            return [c for c in self._commit_cache if c.get("file_path") == file_path][:limit]

        try:
            owner, repo = self._parse_repo()
            result = self._mcp_client.call_tool("list_commits", {
                "owner": owner,
                "repo": repo,
                "perPage": limit,
            })

            if result is None:
                return [c for c in self._commit_cache if c.get("file_path") == file_path][:limit]

            # MCP結果をパース
            commits = []
            text = self._extract_text(result)
            if text:
                commits.append({
                    "sha": "",
                    "message": text[:200],
                    "author": "",
                    "timestamp": "",
                    "file_path": file_path,
                })

            return commits[:limit]

        except Exception as e:
            logger.warning(f"GitHub history retrieval failed: {e}")
            return [c for c in self._commit_cache if c.get("file_path") == file_path][:limit]

    def create_audit_issue(
        self, title: str, description: str, labels: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        監査用Issueを作成

        Args:
            title: Issueタイトル
            description: Issue説明
            labels: ラベル

        Returns:
            Issue情報
        """
        if not self.enabled or not self._mcp_client:
            return {
                "number": len(self._commit_cache) + 1,
                "title": title,
                "state": "open",
                "created_at": datetime.now().isoformat(),
                "mode": "stub",
            }

        try:
            owner, repo = self._parse_repo()
            result = self._mcp_client.call_tool("create_issue", {
                "owner": owner,
                "repo": repo,
                "title": title,
                "body": description,
                "labels": labels or ["audit", "knowledge-system"],
            })

            if result is None:
                return {
                    "number": 0,
                    "title": title,
                    "state": "error",
                    "created_at": datetime.now().isoformat(),
                }

            return {
                "number": 0,
                "title": title,
                "state": "open",
                "created_at": datetime.now().isoformat(),
                "result_text": self._extract_text(result)[:200],
                "mode": "live",
            }

        except Exception as e:
            logger.warning(f"GitHub issue creation failed: {e}")
            return None

    def get_file_content(self, file_path: str, ref: str = "main") -> Optional[str]:
        """
        ファイル内容を取得

        Args:
            file_path: ファイルパス
            ref: ブランチ/タグ名

        Returns:
            ファイル内容
        """
        if not self.enabled or not self._mcp_client:
            return None

        try:
            owner, repo = self._parse_repo()
            result = self._mcp_client.call_tool("get_file_contents", {
                "owner": owner,
                "repo": repo,
                "path": file_path,
                "branch": ref,
            })

            if result is None:
                return None

            return self._extract_text(result)

        except Exception as e:
            logger.warning(f"GitHub file content retrieval failed: {e}")
            return None

    def create_knowledge_pr(
        self,
        branch_name: str,
        title: str,
        description: str,
        files_changed: List[Dict[str, str]],
    ) -> Optional[Dict[str, Any]]:
        """
        ナレッジ変更のPRを作成

        Args:
            branch_name: ブランチ名
            title: PRタイトル
            description: PR説明
            files_changed: 変更ファイルリスト

        Returns:
            PR情報
        """
        if not self.enabled or not self._mcp_client:
            return {
                "number": 42,
                "title": title,
                "state": "open",
                "html_url": f"https://github.com/{self.repository}/pull/42",
                "mode": "stub",
            }

        try:
            owner, repo = self._parse_repo()

            # 1. ブランチ作成
            self._mcp_client.call_tool("create_branch", {
                "owner": owner,
                "repo": repo,
                "branch": branch_name,
                "from_branch": "main",
            })

            # 2. ファイルプッシュ
            self._mcp_client.call_tool("push_files", {
                "owner": owner,
                "repo": repo,
                "branch": branch_name,
                "files": files_changed,
                "message": f"Knowledge update: {title}",
            })

            # 3. PR作成
            result = self._mcp_client.call_tool("create_pull_request", {
                "owner": owner,
                "repo": repo,
                "title": title,
                "body": description,
                "head": branch_name,
                "base": "main",
            })

            return {
                "number": 0,
                "title": title,
                "state": "open",
                "result_text": self._extract_text(result) if result else "",
                "mode": "live",
            }

        except Exception as e:
            logger.warning(f"GitHub PR creation failed: {e}")
            return None

    def enable_automated_commits(self, enabled: bool = True):
        """自動コミット機能の有効/無効"""
        self.auto_commit_enabled = enabled

    def get_audit_trail(self, knowledge_id: int) -> Dict[str, Any]:
        """
        監査証跡を取得

        Args:
            knowledge_id: ナレッジID

        Returns:
            監査証跡情報
        """
        commits = [c for c in self._commit_cache if str(knowledge_id) in c.get("file_path", "")]

        return {
            "knowledge_id": knowledge_id,
            "total_commits": len(commits),
            "first_commit": commits[-1] if commits else None,
            "latest_commit": commits[0] if commits else None,
            "all_commits": commits,
        }

    def generate_change_log(
        self, since: Optional[str] = None, until: Optional[str] = None
    ) -> str:
        """変更ログを生成"""
        changelog = "# ナレッジ変更ログ\n\n"
        changelog += f"期間: {since or '開始'} 〜 {until or '現在'}\n\n"

        for commit in self._commit_cache:
            changelog += f"## {commit.get('timestamp', '')[:10]}\n"
            changelog += f"- {commit.get('message', '')} (by {commit.get('author', '')})\n"
            changelog += f"  - ファイル: {commit.get('file_path', '')}\n\n"

        return changelog

    def get_status(self) -> Dict[str, Any]:
        """接続ステータスを返す"""
        return {
            "enabled": self.enabled,
            "mode": "live" if self.enabled else "stub",
            "repository": self.repository,
            "cached_commits": len(self._commit_cache),
        }

    def _stub_commit(
        self, knowledge_id: int, file_path: str, commit_message: str, author: Optional[str]
    ) -> Dict[str, Any]:
        """スタブコミットを作成"""
        commit = {
            "sha": f"stub_{knowledge_id:04d}",
            "message": commit_message,
            "author": author or "system",
            "timestamp": datetime.now().isoformat(),
            "file_path": file_path,
            "mode": "stub",
        }
        self._commit_cache.append(commit)
        return commit

    def _extract_text(self, result: Dict[str, Any]) -> str:
        """MCP tools/call結果からテキストを抽出"""
        content_list = result.get("content", [])
        if content_list:
            return content_list[0].get("text", "")
        return ""


# グローバルインスタンス（オプション）
github_client = GitHubClient(auto_enable=False)
