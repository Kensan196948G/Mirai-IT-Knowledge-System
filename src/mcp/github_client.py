"""
GitHub MCP Client
バージョン管理・監査証跡クライアント
"""

from datetime import datetime
from typing import Any, Dict, List, Optional


class GitHubClient:
    """GitHub連携クライアント

    ナレッジの変更履歴をGitHubで管理し、監査証跡を保持する機能を提供

    Note: 実際のMCP連携には、MCPSearchツールを使用して
    mcp__github__* ツールをロードする必要があります
    """

    def __init__(self, repository: Optional[str] = None, auto_enable: bool = True):
        """
        初期化

        Args:
            repository: GitHubリポジトリ名（例: "owner/repo"）
            auto_enable: MCP自動有効化（デフォルト: True）
        """
        self.repository = repository or "mirai-it/knowledge-base"
        self._commit_cache = []
        self.auto_commit_enabled = False
        self.enabled = auto_enable and self._check_mcp_available()

    def _check_mcp_available(self) -> bool:
        """MCP利用可能性をチェック"""
        try:
            import sys
            tool = globals().get('mcp__github__create_or_update_file') or \
                   getattr(sys.modules.get('__main__', {}), 'mcp__github__create_or_update_file', None)
            return tool is not None
        except Exception:
            return False

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
        if not self.enabled:
            # デモ実装
            commit = {
                "sha": f"abc{knowledge_id:04d}",
                "message": commit_message,
                "author": author or "system",
                "timestamp": datetime.now().isoformat(),
                "file_path": file_path,
            }
            self._commit_cache.append(commit)
            return commit

        try:
            # 実際のMCP呼び出し
            from ..tools import mcp__github__create_or_update_file

            owner, repo = self.repository.split('/')

            result = mcp__github__create_or_update_file(
                owner=owner,
                repo=repo,
                path=file_path,
                content=content,
                message=commit_message,
                branch="main"
            )

            commit = {
                "sha": result.get("commit", {}).get("sha", ""),
                "message": commit_message,
                "author": author or "system",
                "timestamp": datetime.now().isoformat(),
                "file_path": file_path,
                "url": result.get("content", {}).get("html_url", "")
            }

            self._commit_cache.append(commit)
            return commit

        except Exception as e:
            print(f"Warning: GitHub commit failed: {e}")
            return None

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
        if not self.enabled:
            # デモ実装
            return [c for c in self._commit_cache if c["file_path"] == file_path][:limit]

        try:
            # 実際のMCP呼び出し
            from ..tools import mcp__github__list_commits

            owner, repo = self.repository.split('/')

            commits_result = mcp__github__list_commits(
                owner=owner,
                repo=repo,
                perPage=limit
            )

            # ファイルパスでフィルタリング
            commits = []
            for commit in commits_result.get("commits", []):
                commit_files = commit.get("files", [])
                if any(f.get("filename") == file_path for f in commit_files):
                    commits.append({
                        "sha": commit.get("sha", ""),
                        "message": commit.get("commit", {}).get("message", ""),
                        "author": commit.get("commit", {}).get("author", {}).get("name", ""),
                        "timestamp": commit.get("commit", {}).get("author", {}).get("date", ""),
                        "file_path": file_path
                    })

            return commits[:limit]

        except Exception as e:
            print(f"Warning: GitHub history retrieval failed: {e}")
            return [c for c in self._commit_cache if c["file_path"] == file_path][:limit]

    def create_audit_issue(
        self, title: str, description: str, labels: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        監査用issueを作成

        Args:
            title: issueタイトル
            description: issue説明
            labels: ラベル

        Returns:
            issue情報
        """
        if not self.enabled:
            # デモ実装
            return {
                "number": len(self._commit_cache) + 1,
                "title": title,
                "state": "open",
                "created_at": datetime.now().isoformat(),
            }

        try:
            # 実際のMCP呼び出し
            from ..tools import mcp__github__create_issue

            owner, repo = self.repository.split('/')

            issue = mcp__github__create_issue(
                owner=owner,
                repo=repo,
                title=title,
                body=description,
                labels=labels or ["audit", "knowledge-system"]
            )

            return {
                "number": issue.get("number", 0),
                "title": issue.get("title", ""),
                "state": issue.get("state", "open"),
                "created_at": issue.get("created_at", ""),
                "html_url": issue.get("html_url", "")
            }

        except Exception as e:
            print(f"Warning: GitHub issue creation failed: {e}")
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
        if not self.enabled:
            return None

        try:
            # 実際のMCP呼び出し
            from ..tools import mcp__github__get_file_contents

            owner, repo = self.repository.split('/')

            result = mcp__github__get_file_contents(
                owner=owner,
                repo=repo,
                path=file_path,
                branch=ref
            )

            # Base64デコード（GitHubは内容をBase64エンコードして返す）
            import base64
            content = result.get("content", "")
            if content:
                decoded = base64.b64decode(content).decode('utf-8')
                return decoded

            return None

        except Exception as e:
            print(f"Warning: GitHub file content retrieval failed: {e}")
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
        if not self.enabled:
            # デモ実装
            return {
                "number": 42,
                "title": title,
                "state": "open",
                "html_url": f"https://github.com/{self.repository}/pull/42",
            }

        try:
            # 実際のMCP呼び出し
            from ..tools import mcp__github__create_branch, mcp__github__push_files, mcp__github__create_pull_request

            owner, repo = self.repository.split('/')

            # 1. ブランチ作成
            mcp__github__create_branch(
                owner=owner,
                repo=repo,
                branch=branch_name,
                from_branch="main"
            )

            # 2. ファイル追加/更新
            mcp__github__push_files(
                owner=owner,
                repo=repo,
                branch=branch_name,
                files=files_changed,
                message=f"Knowledge update: {title}"
            )

            # 3. PR作成
            pr = mcp__github__create_pull_request(
                owner=owner,
                repo=repo,
                title=title,
                body=description,
                head=branch_name,
                base="main"
            )

            return {
                "number": pr.get("number", 0),
                "title": pr.get("title", ""),
                "state": pr.get("state", "open"),
                "html_url": pr.get("html_url", "")
            }

        except Exception as e:
            print(f"Warning: GitHub PR creation failed: {e}")
            return None

    def enable_automated_commits(self, enabled: bool = True):
        """
        自動コミット機能の有効/無効

        Args:
            enabled: 有効化するかどうか
        """
        self.auto_commit_enabled = enabled

    def get_audit_trail(self, knowledge_id: int) -> Dict[str, Any]:
        """
        監査証跡を取得

        Args:
            knowledge_id: ナレッジID

        Returns:
            監査証跡情報
        """
        commits = [c for c in self._commit_cache if str(knowledge_id) in c["file_path"]]

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
        """
        変更ログを生成

        Args:
            since: 開始日時
            until: 終了日時

        Returns:
            変更ログ（Markdown形式）
        """
        # TODO: コミット履歴から変更ログを生成

        changelog = f"# ナレッジ変更ログ\n\n"
        changelog += f"期間: {since or '開始'} 〜 {until or '現在'}\n\n"

        for commit in self._commit_cache:
            changelog += f"## {commit['timestamp'][:10]}\n"
            changelog += f"- {commit['message']} (by {commit['author']})\n"
            changelog += f"  - ファイル: {commit['file_path']}\n\n"

        return changelog


# グローバルインスタンス（オプション）
github_client = GitHubClient()
