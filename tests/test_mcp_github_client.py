"""
GitHubClient 単体テスト
src/mcp/github_client.py のモックテスト
現在カバレッジ0%のため優先テスト対象
"""

import pytest
from unittest.mock import MagicMock, patch
import os
from src.mcp.github_client import GitHubClient


@pytest.fixture
def disabled_client():
    """MCP無効状態のGitHubClient（デモモード）"""
    client = GitHubClient(repository="test-owner/test-repo", auto_enable=False)
    client.enabled = False
    return client


class TestGitHubClientInit:
    """初期化テスト"""

    def test_init_default_repository(self):
        """デフォルトリポジトリが設定されること"""
        client = GitHubClient(auto_enable=False)
        assert client.repository == "mirai-it/knowledge-base"

    def test_init_custom_repository(self):
        """カスタムリポジトリを設定できること"""
        client = GitHubClient(repository="owner/repo", auto_enable=False)
        assert client.repository == "owner/repo"

    def test_init_auto_commit_disabled_by_default(self):
        """auto_commitがデフォルトで無効であること"""
        client = GitHubClient(auto_enable=False)
        assert client.auto_commit_enabled is False

    def test_init_commit_cache_is_empty(self):
        """コミットキャッシュが初期状態で空であること"""
        client = GitHubClient(auto_enable=False)
        assert client._commit_cache == []

    def test_try_connect_returns_bool(self):
        """_try_connectがboolを返すこと（GITHUB_TOKEN未設定時はFalse）"""
        client = GitHubClient(auto_enable=False)
        with patch.dict("os.environ", {"GITHUB_TOKEN": ""}, clear=False):
            result = client._try_connect()
        assert isinstance(result, bool)
        assert result is False


class TestCommitKnowledge:
    """commit_knowledge メソッドテスト"""

    def test_commit_knowledge_demo_mode_returns_commit(self, disabled_client):
        """デモモードでコミット情報を返すこと"""
        result = disabled_client.commit_knowledge(
            knowledge_id=1,
            file_path="knowledge/001.md",
            content="test content",
            commit_message="Add knowledge",
        )
        assert result is not None
        assert result["message"] == "Add knowledge"
        assert result["file_path"] == "knowledge/001.md"

    def test_commit_knowledge_demo_adds_to_cache(self, disabled_client):
        """デモモードでキャッシュに追加されること"""
        disabled_client.commit_knowledge(
            knowledge_id=1,
            file_path="knowledge/001.md",
            content="content",
            commit_message="Test commit",
        )
        assert len(disabled_client._commit_cache) == 1

    def test_commit_knowledge_demo_sha_format(self, disabled_client):
        """デモモードでSHAが生成されること"""
        result = disabled_client.commit_knowledge(
            knowledge_id=5,
            file_path="knowledge/005.md",
            content="content",
            commit_message="Commit",
        )
        assert "sha" in result
        assert result["sha"] is not None

    def test_commit_knowledge_with_author(self, disabled_client):
        """authorが設定されること"""
        result = disabled_client.commit_knowledge(
            knowledge_id=1,
            file_path="knowledge/001.md",
            content="content",
            commit_message="Test",
            author="test_user",
        )
        assert result["author"] == "test_user"

    def test_commit_knowledge_default_author_is_system(self, disabled_client):
        """author未指定時にsystemが設定されること"""
        result = disabled_client.commit_knowledge(
            knowledge_id=1,
            file_path="path.md",
            content="content",
            commit_message="Test",
        )
        assert result["author"] == "system"


class TestGetKnowledgeHistory:
    """get_knowledge_history メソッドテスト"""

    def test_get_knowledge_history_empty_cache(self, disabled_client):
        """キャッシュ空の場合空リストを返すこと"""
        result = disabled_client.get_knowledge_history("knowledge/001.md")
        assert result == []

    def test_get_knowledge_history_filters_by_path(self, disabled_client):
        """指定したファイルパスでフィルタされること"""
        disabled_client._commit_cache = [
            {"file_path": "knowledge/001.md", "message": "Commit 1", "sha": "abc001", "author": "a", "timestamp": "2024-01-01"},
            {"file_path": "knowledge/002.md", "message": "Commit 2", "sha": "abc002", "author": "b", "timestamp": "2024-01-02"},
        ]
        result = disabled_client.get_knowledge_history("knowledge/001.md")
        assert len(result) == 1
        assert result[0]["file_path"] == "knowledge/001.md"


class TestCreateAuditIssue:
    """create_audit_issue メソッドテスト"""

    def test_create_audit_issue_demo_returns_issue(self, disabled_client):
        """デモモードでissue情報を返すこと"""
        result = disabled_client.create_audit_issue(
            title="Test Issue",
            description="Test description",
        )
        assert result is not None
        assert result["title"] == "Test Issue"
        assert result["state"] == "open"


class TestGetAuditTrail:
    """get_audit_trail メソッドテスト"""

    def test_get_audit_trail_empty(self, disabled_client):
        """コミットなしの監査証跡"""
        result = disabled_client.get_audit_trail(1)
        assert result["knowledge_id"] == 1
        assert result["total_commits"] == 0

    def test_get_audit_trail_with_commits(self, disabled_client):
        """コミットありの監査証跡"""
        disabled_client._commit_cache = [
            {"file_path": "knowledge/001.md", "sha": "abc001", "message": "Msg", "author": "user", "timestamp": "2024-01-01"},
        ]
        result = disabled_client.get_audit_trail(1)
        assert result["total_commits"] == 1
        assert result["latest_commit"] is not None


class TestEnableAutomatedCommits:
    """enable_automated_commits メソッドテスト"""

    def test_enable_automated_commits(self, disabled_client):
        """自動コミットを有効化できること"""
        disabled_client.enable_automated_commits(True)
        assert disabled_client.auto_commit_enabled is True

    def test_disable_automated_commits(self, disabled_client):
        """自動コミットを無効化できること"""
        disabled_client.auto_commit_enabled = True
        disabled_client.enable_automated_commits(False)
        assert disabled_client.auto_commit_enabled is False


class TestGenerateChangeLog:
    """generate_change_log メソッドテスト"""

    def test_generate_change_log_returns_string(self, disabled_client):
        """文字列を返すこと"""
        result = disabled_client.generate_change_log()
        assert isinstance(result, str)

    def test_generate_change_log_includes_commits(self, disabled_client):
        """コミット情報が含まれること"""
        disabled_client._commit_cache = [
            {"file_path": "knowledge/001.md", "sha": "abc001", "message": "Test commit", "author": "user", "timestamp": "2024-01-01T00:00:00"},
        ]
        result = disabled_client.generate_change_log()
        assert "Test commit" in result

    def test_generate_change_log_with_date_range(self, disabled_client):
        """日付範囲付きでも動作すること"""
        result = disabled_client.generate_change_log(since="2024-01-01", until="2024-12-31")
        assert "2024-01-01" in result
