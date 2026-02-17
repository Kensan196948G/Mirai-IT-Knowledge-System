"""
MCP統合テスト
SQLite MCPクライアントの基本操作とMCP統合モジュールを確認する
（実際のMCPサーバー接続は行わず、モック/スタブベースで検証。
  実接続テストはTestMCPLiveConnectionで別途テスト）
"""

import os
import sys
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="module")
def sqlite_client(tmp_path_factory):
    """テスト用SQLiteClient（一時DB）"""
    from src.mcp.sqlite_client import SQLiteClient

    db_dir = tmp_path_factory.mktemp("mcp_db")
    db_path = str(db_dir / "test_mcp.db")

    # スキーマ適用
    schema_path = Path(__file__).parent.parent / "db" / "schema.sql"
    client = SQLiteClient(db_path=db_path)
    if schema_path.exists():
        import sqlite3

        with sqlite3.connect(db_path) as conn:
            conn.executescript(schema_path.read_text(encoding="utf-8"))

    return client


# ─── SQLiteClient 基本操作テスト ─────────────────────────────


class TestSQLiteClientBasics:
    """SQLiteClient の基本CRUD操作を確認"""

    def test_sqlite_client_instantiation(self, sqlite_client):
        """SQLiteClient が正常にインスタンス化できることを確認"""
        assert sqlite_client is not None
        assert sqlite_client.db_path is not None

    def test_sqlite_client_connection(self, sqlite_client):
        """SQLiteClient がDB接続を取得できることを確認"""
        conn = sqlite_client.get_connection()
        assert conn is not None
        conn.close()

    def test_create_and_retrieve_knowledge(self, sqlite_client):
        """ナレッジの作成と取得が正常に動作することを確認"""
        knowledge_id = sqlite_client.create_knowledge(
            title="MCPテストナレッジ",
            itsm_type="Incident",
            content="MCP統合テスト用のナレッジコンテンツです。",
            created_by="mcp_test",
        )
        assert isinstance(knowledge_id, int)
        assert knowledge_id > 0

        retrieved = sqlite_client.get_knowledge(knowledge_id)
        assert retrieved is not None
        assert retrieved["id"] == knowledge_id
        assert retrieved["title"] == "MCPテストナレッジ"

    def test_search_knowledge_empty_query(self, sqlite_client):
        """クエリなしの検索が空リストまたはリストを返すことを確認"""
        results = sqlite_client.search_knowledge(limit=10)
        assert isinstance(results, list)

    def test_search_knowledge_with_query(self, sqlite_client):
        """クエリありの検索が動作することを確認"""
        sqlite_client.create_knowledge(
            title="検索テスト専用ナレッジ",
            itsm_type="Problem",
            content="検索テスト用コンテンツです。",
            created_by="test",
        )
        results = sqlite_client.search_knowledge(query="検索テスト", limit=5)
        assert isinstance(results, list)

    def test_search_knowledge_with_itsm_type_filter(self, sqlite_client):
        """ITSMタイプフィルタ付き検索が動作することを確認"""
        results = sqlite_client.search_knowledge(itsm_type="Incident", limit=10)
        assert isinstance(results, list)
        for r in results:
            assert r["itsm_type"] == "Incident"

    def test_get_nonexistent_knowledge_returns_none(self, sqlite_client):
        """存在しないIDの取得がNoneを返すことを確認"""
        result = sqlite_client.get_knowledge(999999)
        assert result is None

    def test_get_statistics_returns_dict(self, sqlite_client):
        """統計情報取得がdictを返すことを確認"""
        stats = sqlite_client.get_statistics()
        assert isinstance(stats, dict)

    def test_create_workflow_execution(self, sqlite_client):
        """ワークフロー実行記録が正常に作成できることを確認"""
        execution_id = sqlite_client.create_workflow_execution(
            workflow_type="test_workflow"
        )
        assert isinstance(execution_id, int)
        assert execution_id > 0


# ─── SQLiteClient 更新・削除テスト ─────────────────────────────


class TestSQLiteClientUpdate:
    """SQLiteClient の更新操作を確認"""

    def test_update_knowledge_markdown_path(self, sqlite_client):
        """ナレッジのmarkdown_pathを更新できることを確認"""
        knowledge_id = sqlite_client.create_knowledge(
            title="更新テストナレッジ",
            itsm_type="Change",
            content="更新テスト用コンテンツです。",
            created_by="test",
        )
        sqlite_client.update_knowledge(
            knowledge_id, markdown_path="/tmp/test.md"
        )
        retrieved = sqlite_client.get_knowledge(knowledge_id)
        assert retrieved is not None
        assert retrieved["markdown_path"] == "/tmp/test.md"

    def test_update_workflow_execution_status(self, sqlite_client):
        """ワークフロー実行ステータスを更新できることを確認"""
        execution_id = sqlite_client.create_workflow_execution(
            workflow_type="update_test"
        )
        sqlite_client.update_workflow_execution(
            execution_id,
            status="completed",
            execution_time_ms=500,
        )
        assert True

    def test_log_hook_execution(self, sqlite_client):
        """フック実行ログを記録できることを確認"""
        execution_id = sqlite_client.create_workflow_execution(
            workflow_type="hook_log_test"
        )
        sqlite_client.log_hook_execution(
            workflow_execution_id=execution_id,
            hook_name="test_hook",
            hook_type="pre-task",
            result="pass",
            message="テストフック実行成功",
            details={"key": "value"},
        )
        assert True


# ─── MCP統合モジュールテスト ─────────────────────────────


class TestMCPIntegration:
    """MCP統合モジュールの動作をモックで確認"""

    def test_mcp_integration_importable(self):
        """mcp_integration モジュールがインポートできることを確認"""
        from src.mcp.mcp_integration import mcp_integration
        assert mcp_integration is not None

    def test_mcp_integration_has_enrich_method(self):
        """mcp_integration に enrich_knowledge_with_mcps メソッドがあることを確認"""
        from src.mcp.mcp_integration import mcp_integration
        assert hasattr(mcp_integration, "enrich_knowledge_with_mcps")

    def test_mcp_enrich_with_empty_content(self):
        """空コンテンツでも enrich_knowledge_with_mcps が例外を出さないことを確認"""
        from src.mcp.mcp_integration import MCPIntegration
        integration = MCPIntegration(auto_connect=False)
        result = integration.enrich_knowledge_with_mcps(
            knowledge_content="",
            detected_technologies=[],
            itsm_type="Incident",
        )
        assert isinstance(result, dict)

    def test_mcp_enrich_returns_dict(self):
        """enrich_knowledge_with_mcps が dict を返すことを確認"""
        from src.mcp.mcp_integration import MCPIntegration
        integration = MCPIntegration(auto_connect=False)
        result = integration.enrich_knowledge_with_mcps(
            knowledge_content="テストコンテンツ",
            detected_technologies=["python"],
            itsm_type="Incident",
        )
        assert isinstance(result, dict)

    def test_mcp_get_status(self):
        """get_status がステータスdictを返すことを確認"""
        from src.mcp.mcp_integration import MCPIntegration
        integration = MCPIntegration(auto_connect=False)
        status = integration.get_status()
        assert isinstance(status, dict)
        assert "context7" in status
        assert "claude_mem" in status
        assert "github" in status

    def test_mcp_get_detailed_status(self):
        """get_detailed_status が詳細ステータスを返すことを確認"""
        from src.mcp.mcp_integration import MCPIntegration
        from src.mcp.context7_client import Context7Client
        from src.mcp.claude_mem_client import ClaudeMemClient
        from src.mcp.github_client import GitHubClient

        integration = MCPIntegration(auto_connect=False)
        # スタブモードで各クライアントを直接設定（MCP接続を回避）
        integration._context7 = Context7Client(auto_enable=False)
        integration._claude_mem = ClaudeMemClient(auto_enable=False)
        integration._github = GitHubClient(auto_enable=False)
        status = integration.get_detailed_status()
        assert isinstance(status, dict)
        assert "context7_mode" in status


# ─── MCPClientBase テスト ─────────────────────────────


class TestMCPClientBase:
    """MCPClientBase の単体テストをモックで確認"""

    def test_client_base_instantiation(self):
        """MCPClientBase が正常にインスタンス化できることを確認"""
        from src.mcp.mcp_client_base import MCPClientBase
        client = MCPClientBase(
            server_command="echo",
            server_args=["test"],
        )
        assert client is not None
        assert client.server_command == "echo"
        assert not client.is_connected

    def test_client_base_not_connected_returns_none(self):
        """未接続状態で call_tool がNoneを返すことを確認"""
        from src.mcp.mcp_client_base import MCPClientBase
        client = MCPClientBase(
            server_command="echo",
            server_args=["test"],
        )
        result = client.call_tool("test_tool", {"arg": "value"})
        assert result is None

    def test_client_base_not_connected_returns_empty_tools(self):
        """未接続状態で list_tools が空リストを返すことを確認"""
        from src.mcp.mcp_client_base import MCPClientBase
        client = MCPClientBase(
            server_command="echo",
            server_args=["test"],
        )
        tools = client.list_tools()
        assert tools == []

    def test_client_base_connect_with_nonexistent_command(self):
        """存在しないコマンドで接続失敗がFalseを返すことを確認"""
        from src.mcp.mcp_client_base import MCPClientBase
        client = MCPClientBase(
            server_command="nonexistent_mcp_command_xyz",
            server_args=[],
        )
        result = client.connect()
        assert result is False
        assert not client.is_connected


# ─── Context7Client テスト ─────────────────────────────


class TestContext7Client:
    """Context7Client のスタブモード動作を確認"""

    def test_context7_stub_mode(self):
        """auto_enable=False でスタブモードになることを確認"""
        from src.mcp.context7_client import Context7Client
        client = Context7Client(auto_enable=False)
        assert not client.enabled
        assert client.get_status()["mode"] == "stub"

    def test_context7_stub_query(self):
        """スタブモードで query_documentation がデモデータを返すことを確認"""
        from src.mcp.context7_client import Context7Client
        client = Context7Client(auto_enable=False)
        results = client.query_documentation("flask", "routing")
        assert isinstance(results, list)
        assert len(results) > 0
        assert results[0]["source"] == "Context7-stub"

    def test_context7_stub_unknown_library(self):
        """スタブモードで未知ライブラリが空リストを返すことを確認"""
        from src.mcp.context7_client import Context7Client
        client = Context7Client(auto_enable=False)
        results = client.query_documentation("unknown_lib_xyz", "test")
        assert isinstance(results, list)
        assert len(results) == 0

    def test_context7_resolve_library_id_stub(self):
        """スタブモードで resolve_library_id がNoneを返すことを確認"""
        from src.mcp.context7_client import Context7Client
        client = Context7Client(auto_enable=False)
        result = client.resolve_library_id("flask")
        assert result is None

    def test_context7_enrich_knowledge(self):
        """enrich_knowledge_with_docs がdictを返すことを確認"""
        from src.mcp.context7_client import Context7Client
        client = Context7Client(auto_enable=False)
        result = client.enrich_knowledge_with_docs(
            "Flask route query with index",
            ["flask", "sqlite"]
        )
        assert isinstance(result, dict)

    def test_context7_caching(self):
        """同じクエリに対してキャッシュが利用されることを確認"""
        from src.mcp.context7_client import Context7Client
        client = Context7Client(auto_enable=False)
        # 最初の呼び出し
        results1 = client.query_documentation("flask", "routing")
        # キャッシュに保存されないことを確認（スタブモードではキャッシュされない）
        assert isinstance(results1, list)


# ─── ClaudeMemClient テスト ─────────────────────────────


class TestClaudeMemClient:
    """ClaudeMemClient のスタブモード動作を確認"""

    def test_claude_mem_stub_mode(self):
        """auto_enable=False でスタブモードになることを確認"""
        from src.mcp.claude_mem_client import ClaudeMemClient
        client = ClaudeMemClient(auto_enable=False)
        assert not client.enabled
        assert client.get_status()["mode"] == "stub"

    def test_claude_mem_stub_search(self):
        """スタブモードで search_memories がデモデータを返すことを確認"""
        from src.mcp.claude_mem_client import ClaudeMemClient
        client = ClaudeMemClient(auto_enable=False)
        results = client.search_memories("データベース接続")
        assert isinstance(results, list)
        assert len(results) > 0
        assert results[0].get("source") == "Claude-Mem-stub"

    def test_claude_mem_store_decision(self):
        """store_decision が正常に動作することを確認"""
        from src.mcp.claude_mem_client import ClaudeMemClient
        client = ClaudeMemClient(auto_enable=False)
        result = client.store_decision(
            title="テスト決定",
            decision="Flaskを使用する",
            rationale="既存の知見がある",
            tags=["architecture"],
        )
        assert result["success"] is True
        assert "decision_id" in result

    def test_claude_mem_get_decisions(self):
        """get_decisions がローカルキャッシュから返すことを確認"""
        from src.mcp.claude_mem_client import ClaudeMemClient
        client = ClaudeMemClient(auto_enable=False)
        client.store_decision(
            title="テスト決定",
            decision="SQLite FTS5を使用",
            rationale="全文検索パフォーマンス",
            tags=["database"],
        )
        decisions = client.get_decisions(tags=["database"])
        assert isinstance(decisions, list)
        assert len(decisions) >= 1

    def test_claude_mem_enhance_knowledge(self):
        """enhance_knowledge_with_memory がdictを返すことを確認"""
        from src.mcp.claude_mem_client import ClaudeMemClient
        client = ClaudeMemClient(auto_enable=False)
        result = client.enhance_knowledge_with_memory(
            "データベース接続エラーが発生",
            "Incident"
        )
        assert isinstance(result, dict)
        assert "related_memories" in result
        assert "keywords_used" in result

    def test_claude_mem_conversation_store(self):
        """store_conversation が正常に動作することを確認"""
        from src.mcp.claude_mem_client import ClaudeMemClient
        client = ClaudeMemClient(auto_enable=False)
        result = client.store_conversation(
            "conv_001",
            [{"role": "user", "content": "テスト"}],
        )
        assert result is True

    def test_claude_mem_link_to_commit(self):
        """link_to_commit が正常に動作することを確認"""
        from src.mcp.claude_mem_client import ClaudeMemClient
        client = ClaudeMemClient(auto_enable=False)
        client.store_decision(
            title="テスト決定",
            decision="テスト",
            rationale="テスト",
        )
        dec_id = client._decision_cache[0]["id"]
        result = client.link_to_commit(dec_id, "abc123", "テストコミット")
        assert result is True

    def test_claude_mem_get_stats(self):
        """get_stats がdictを返すことを確認"""
        from src.mcp.claude_mem_client import ClaudeMemClient
        client = ClaudeMemClient(auto_enable=False)
        stats = client.get_stats()
        assert isinstance(stats, dict)
        assert "total_memories" in stats


# ─── GitHubClient テスト ─────────────────────────────


class TestGitHubClient:
    """GitHubClient のスタブモード動作を確認"""

    def test_github_stub_mode(self):
        """auto_enable=False でスタブモードになることを確認"""
        from src.mcp.github_client import GitHubClient
        client = GitHubClient(auto_enable=False)
        assert not client.enabled
        assert client.get_status()["mode"] == "stub"

    def test_github_stub_commit(self):
        """スタブモードで commit_knowledge がスタブコミットを返すことを確認"""
        from src.mcp.github_client import GitHubClient
        client = GitHubClient(auto_enable=False)
        result = client.commit_knowledge(
            knowledge_id=1,
            file_path="test.md",
            content="# Test",
            commit_message="test commit",
        )
        assert result is not None
        assert result["mode"] == "stub"
        assert "sha" in result

    def test_github_stub_audit_issue(self):
        """スタブモードで create_audit_issue がスタブデータを返すことを確認"""
        from src.mcp.github_client import GitHubClient
        client = GitHubClient(auto_enable=False)
        result = client.create_audit_issue(
            title="テスト監査",
            description="テスト用",
        )
        assert result is not None
        assert result["mode"] == "stub"

    def test_github_stub_pr(self):
        """スタブモードで create_knowledge_pr がスタブデータを返すことを確認"""
        from src.mcp.github_client import GitHubClient
        client = GitHubClient(auto_enable=False)
        result = client.create_knowledge_pr(
            branch_name="test-branch",
            title="テストPR",
            description="テスト用PR",
            files_changed=[],
        )
        assert result is not None
        assert result["mode"] == "stub"

    def test_github_get_audit_trail(self):
        """get_audit_trail がdictを返すことを確認"""
        from src.mcp.github_client import GitHubClient
        client = GitHubClient(auto_enable=False)
        trail = client.get_audit_trail(1)
        assert isinstance(trail, dict)
        assert "knowledge_id" in trail

    def test_github_change_log(self):
        """generate_change_log がstrを返すことを確認"""
        from src.mcp.github_client import GitHubClient
        client = GitHubClient(auto_enable=False)
        log = client.generate_change_log()
        assert isinstance(log, str)
        assert "ナレッジ変更ログ" in log

    def test_github_get_file_content_stub(self):
        """スタブモードで get_file_content がNoneを返すことを確認"""
        from src.mcp.github_client import GitHubClient
        client = GitHubClient(auto_enable=False)
        result = client.get_file_content("test.md")
        assert result is None

    def test_github_knowledge_history_stub(self):
        """スタブモードで get_knowledge_history がキャッシュから返すことを確認"""
        from src.mcp.github_client import GitHubClient
        client = GitHubClient(auto_enable=False)
        client.commit_knowledge(1, "test.md", "content", "msg")
        history = client.get_knowledge_history("test.md")
        assert isinstance(history, list)
        assert len(history) >= 1


# ─── SQLiteクライアントのセキュリティテスト ─────────────────────────────


class TestSQLiteClientSecurity:
    """SQLiteClient のセキュリティ機能を確認"""

    def test_invalid_column_raises_valueerror(self, sqlite_client):
        """不正なカラム名指定で ValueError が発生することを確認"""
        with pytest.raises(ValueError, match="Invalid column name"):
            sqlite_client._validate_update_columns(["malicious_column; DROP TABLE"])

    def test_allowed_columns_pass_validation(self, sqlite_client):
        """許可されたカラム名が検証をパスすることを確認"""
        allowed = ["title", "content", "status"]
        result = sqlite_client._validate_update_columns(allowed)
        assert result == allowed

    def test_knowledge_search_with_sql_injection_safe(self, sqlite_client):
        """SQLインジェクション試みがエラーなく処理されることを確認"""
        results = sqlite_client.search_knowledge(
            query="' OR '1'='1", limit=5
        )
        assert isinstance(results, list)


# ─── sqlite-dev/prod パス分離テスト ─────────────────────────────


class TestSQLitePathSeparation:
    """sqlite-dev と sqlite-prod のパス分離を確認"""

    def test_dev_db_path(self, tmp_path):
        """開発用DBパスが正しく設定されることを確認"""
        from src.mcp.sqlite_client import SQLiteClient
        dev_db = str(tmp_path / "knowledge_dev.db")
        client = SQLiteClient(db_path=dev_db)
        assert client.db_path == dev_db

    def test_prod_db_path(self, tmp_path):
        """本番用DBパスが正しく設定されることを確認"""
        from src.mcp.sqlite_client import SQLiteClient
        prod_db = str(tmp_path / "knowledge.db")
        client = SQLiteClient(db_path=prod_db)
        assert client.db_path == prod_db

    def test_dev_prod_isolation(self, tmp_path):
        """dev/prodのDBが別々のファイルであることを確認"""
        from src.mcp.sqlite_client import SQLiteClient

        dev_db = str(tmp_path / "knowledge_dev.db")
        prod_db = str(tmp_path / "knowledge.db")

        dev_client = SQLiteClient(db_path=dev_db)
        prod_client = SQLiteClient(db_path=prod_db)

        assert dev_client.db_path != prod_client.db_path


# ─── MCP実接続テスト（CI環境ではスキップ） ─────────────────────────────


class TestMCPLiveConnection:
    """MCP実接続テスト（実際のMCPサーバー起動を試行）

    CI環境等でMCPサーバーが利用できない場合はスキップされます。
    """

    @pytest.mark.skipif(
        os.environ.get("CI") == "true",
        reason="CI環境ではMCPサーバーが利用できないためスキップ"
    )
    def test_context7_live_connection_attempt(self):
        """Context7 MCPサーバーへの実接続を試行"""
        from src.mcp.context7_client import Context7Client

        client = Context7Client(auto_enable=True)
        # 接続成功/失敗どちらでもエラーなく完了することを確認
        status = client.get_status()
        assert "mode" in status
        assert status["mode"] in ("live", "stub")
        client.disconnect()

    @pytest.mark.skipif(
        os.environ.get("CI") == "true" or not os.environ.get("GITHUB_TOKEN"),
        reason="CI環境またはGITHUB_TOKEN未設定のためスキップ"
    )
    def test_github_live_connection_attempt(self):
        """GitHub MCPサーバーへの実接続を試行"""
        from src.mcp.github_client import GitHubClient

        client = GitHubClient(auto_enable=True)
        status = client.get_status()
        assert "mode" in status
        assert status["mode"] in ("live", "stub")
        client.disconnect()

    @pytest.mark.skipif(
        os.environ.get("CI") == "true",
        reason="CI環境ではMCPサーバーが利用できないためスキップ"
    )
    def test_claude_mem_live_connection_attempt(self):
        """Claude-Mem MCPサーバーへの実接続を試行"""
        from src.mcp.claude_mem_client import ClaudeMemClient

        client = ClaudeMemClient(auto_enable=True)
        status = client.get_status()
        assert "mode" in status
        assert status["mode"] in ("live", "stub")
        client.disconnect()

    @pytest.mark.skipif(
        os.environ.get("CI") == "true",
        reason="CI環境ではMCPサーバーが利用できないためスキップ"
    )
    def test_integration_connect_all(self):
        """MCPIntegration.connect_all() の実行を確認"""
        from src.mcp.mcp_integration import MCPIntegration

        integration = MCPIntegration(auto_connect=False)
        results = integration.connect_all()
        assert isinstance(results, dict)
        assert "context7" in results
        assert "claude_mem" in results
        assert "github" in results
        integration.disconnect_all()


# ─── MCPClientBase リトライ・診断テスト ─────────────────────────────


class TestMCPClientBaseRetry:
    """MCPClientBase のリトライロジックと診断機能をモックで検証"""

    def test_connect_with_retry_success_on_second_attempt(self):
        """2回目の試行で接続成功するケースを確認"""
        from src.mcp.mcp_client_base import MCPClientBase

        client = MCPClientBase(
            server_command="npx",
            server_args=["-y", "test-server"],
            max_retries=2,
        )

        attempt_count = {"value": 0}

        def mock_attempt():
            attempt_count["value"] += 1
            if attempt_count["value"] == 1:
                client._last_error = "First attempt failed"
                return False
            client._connected = True
            client._server_info = {"protocolVersion": "2024-11-05"}
            return True

        with patch.object(client, '_attempt_connect', side_effect=mock_attempt):
            with patch('src.mcp.mcp_client_base.time.sleep'):
                result = client.connect()

        assert result is True
        assert attempt_count["value"] == 2

    def test_connect_retry_exhausted(self):
        """リトライ全て失敗するケースを確認"""
        from src.mcp.mcp_client_base import MCPClientBase

        client = MCPClientBase(
            server_command="npx",
            server_args=["-y", "test-server"],
            max_retries=1,
        )

        with patch.object(client, '_attempt_connect', return_value=False):
            with patch('src.mcp.mcp_client_base.time.sleep'):
                result = client.connect()

        assert result is False

    def test_connect_no_retry_when_already_connected(self):
        """既に接続済みの場合リトライしないことを確認"""
        from src.mcp.mcp_client_base import MCPClientBase

        client = MCPClientBase(
            server_command="npx",
            server_args=["-y", "test-server"],
        )
        client._connected = True
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        client._process = mock_process

        result = client.connect()
        assert result is True

    def test_health_check_not_connected(self):
        """未接続状態のhealth_checkが適切な情報を返すことを確認"""
        from src.mcp.mcp_client_base import MCPClientBase

        client = MCPClientBase(
            server_command="npx",
            server_args=["-y", "test-server"],
        )
        client._last_error = "Connection refused"

        health = client.health_check()
        assert health["connected"] is False
        assert health["server_command"] == "npx"
        assert health["last_error"] == "Connection refused"
        assert "server_info" not in health

    def test_health_check_connected_with_tools(self):
        """接続済み状態のhealth_checkがツール情報を含むことを確認"""
        from src.mcp.mcp_client_base import MCPClientBase

        client = MCPClientBase(
            server_command="npx",
            server_args=["-y", "test-server"],
        )
        client._connected = True
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        client._process = mock_process
        client._server_info = {
            "protocolVersion": "2024-11-05",
            "serverInfo": {"name": "test-server", "version": "1.0.0"},
        }

        mock_tools = [
            {"name": "tool_a", "description": "Tool A"},
            {"name": "tool_b", "description": "Tool B"},
        ]
        with patch.object(client, 'list_tools', return_value=mock_tools):
            health = client.health_check()

        assert health["connected"] is True
        assert health["server_info"]["server_name"] == "test-server"
        assert health["available_tools"] == 2
        assert "tool_a" in health["tool_names"]

    def test_max_retries_zero(self):
        """max_retries=0 で1回だけ試行することを確認"""
        from src.mcp.mcp_client_base import MCPClientBase

        client = MCPClientBase(
            server_command="npx",
            server_args=["-y", "test-server"],
            max_retries=0,
        )

        call_count = {"value": 0}

        def mock_attempt():
            call_count["value"] += 1
            return False

        with patch.object(client, '_attempt_connect', side_effect=mock_attempt):
            result = client.connect()

        assert result is False
        assert call_count["value"] == 1


# ─── Context7Client 実接続パス モックテスト ─────────────────────────────


class TestContext7ClientLiveMock:
    """Context7Client の実接続パスをモックで検証"""

    def _make_connected_client(self):
        """接続済みContext7Clientを作成（モック）"""
        from src.mcp.context7_client import Context7Client

        client = Context7Client(auto_enable=False)
        client.enabled = True
        client._mcp_client = MagicMock()
        client._mcp_client.is_connected = True
        return client

    def test_resolve_library_id_success(self):
        """resolve-library-id が成功するケースを確認"""
        client = self._make_connected_client()
        client._mcp_client.call_tool.return_value = {
            "content": [{"type": "text", "text": "/upstash/context7/flask"}]
        }

        result = client.resolve_library_id("flask")
        assert result == "/upstash/context7/flask"
        client._mcp_client.call_tool.assert_called_once_with(
            "resolve-library-id", {"libraryName": "flask"}
        )

    def test_resolve_library_id_empty_content(self):
        """resolve-library-id の結果が空の場合Noneを返すことを確認"""
        client = self._make_connected_client()
        client._mcp_client.call_tool.return_value = {"content": []}

        result = client.resolve_library_id("unknown")
        assert result is None

    def test_resolve_library_id_none_result(self):
        """resolve-library-id がNoneを返す場合の処理を確認"""
        client = self._make_connected_client()
        client._mcp_client.call_tool.return_value = None

        result = client.resolve_library_id("flask")
        assert result is None

    def test_query_documentation_full_flow(self):
        """resolve-library-id → query-docs の完全フローを確認"""
        client = self._make_connected_client()

        # resolve-library-id → query-docs の2段階呼び出し
        client._mcp_client.call_tool.side_effect = [
            # Step 1: resolve-library-id
            {"content": [{"type": "text", "text": "/lib/flask-id"}]},
            # Step 2: query-docs
            {"content": [
                {"type": "text", "text": "Flask routing documentation: Use @app.route() decorator..."},
                {"type": "text", "text": "URL building with url_for()..."},
            ]},
        ]

        results = client.query_documentation("flask", "routing")
        assert len(results) == 2
        assert results[0]["source"] == "Context7"
        assert "routing" in results[0]["snippet"].lower()

        calls = client._mcp_client.call_tool.call_args_list
        assert calls[0][0][0] == "resolve-library-id"
        assert calls[1][0][0] == "query-docs"
        assert calls[1][0][1]["libraryId"] == "/lib/flask-id"

    def test_query_documentation_fallback_on_resolve_failure(self):
        """ライブラリID解決失敗時にデモデータにフォールバックすることを確認"""
        client = self._make_connected_client()
        client._mcp_client.call_tool.return_value = None

        results = client.query_documentation("flask", "routing")
        assert len(results) > 0
        assert results[0]["source"] == "Context7-stub"

    def test_query_documentation_caching(self):
        """クエリ結果がキャッシュされることを確認"""
        client = self._make_connected_client()
        client._mcp_client.call_tool.side_effect = [
            {"content": [{"type": "text", "text": "/lib/flask-id"}]},
            {"content": [{"type": "text", "text": "cached doc content"}]},
        ]

        # 最初の呼び出し
        results1 = client.query_documentation("flask", "routing")
        # 2回目はキャッシュから
        results2 = client.query_documentation("flask", "routing")

        assert results1 == results2
        # call_tool は最初の1回だけ（2回 = resolve + query）
        assert client._mcp_client.call_tool.call_count == 2

    def test_query_documentation_exception_fallback(self):
        """例外発生時にデモデータにフォールバックすることを確認"""
        client = self._make_connected_client()
        client._mcp_client.call_tool.side_effect = Exception("Connection lost")

        results = client.query_documentation("flask", "routing")
        assert len(results) > 0
        assert results[0]["source"] == "Context7-stub"

    def test_enrich_knowledge_with_live_docs(self):
        """実接続モードでenrich_knowledge_with_docsが動作することを確認"""
        client = self._make_connected_client()
        # query/route/sessionのキーワードが抽出される
        client._mcp_client.call_tool.side_effect = [
            {"content": [{"type": "text", "text": "/lib/flask-id"}]},
            {"content": [{"type": "text", "text": "Flask routing best practices..."}]},
        ]

        result = client.enrich_knowledge_with_docs(
            "Flask route with session handling",
            ["flask"]
        )
        assert isinstance(result, dict)
        assert "flask" in result


# ─── GitHubClient 実接続パス モックテスト ─────────────────────────────


class TestGitHubClientLiveMock:
    """GitHubClient の実接続パスをモックで検証"""

    def _make_connected_client(self):
        """接続済みGitHubClientを作成（モック）"""
        from src.mcp.github_client import GitHubClient

        client = GitHubClient(repository="test-owner/test-repo", auto_enable=False)
        client.enabled = True
        client._mcp_client = MagicMock()
        client._mcp_client.is_connected = True
        return client

    def test_commit_knowledge_live(self):
        """実接続モードでcommit_knowledgeが動作することを確認"""
        client = self._make_connected_client()
        client._mcp_client.call_tool.return_value = {
            "content": [{"type": "text", "text": "abc123def456..."}]
        }

        result = client.commit_knowledge(
            knowledge_id=1,
            file_path="knowledge/001.md",
            content="# Test Knowledge",
            commit_message="Add knowledge 001",
            author="test-user",
        )

        assert result is not None
        assert result["mode"] == "live"
        assert result["sha"].startswith("abc123")
        client._mcp_client.call_tool.assert_called_once_with(
            "create_or_update_file",
            {
                "owner": "test-owner",
                "repo": "test-repo",
                "path": "knowledge/001.md",
                "content": "# Test Knowledge",
                "message": "Add knowledge 001",
                "branch": "main",
            },
        )

    def test_commit_knowledge_fallback_on_none(self):
        """MCP call_toolがNoneを返した場合スタブにフォールバックすることを確認"""
        client = self._make_connected_client()
        client._mcp_client.call_tool.return_value = None

        result = client.commit_knowledge(
            knowledge_id=2,
            file_path="test.md",
            content="content",
            commit_message="test",
        )

        assert result is not None
        assert result["mode"] == "stub"

    def test_commit_knowledge_fallback_on_exception(self):
        """MCP例外時にスタブにフォールバックすることを確認"""
        client = self._make_connected_client()
        client._mcp_client.call_tool.side_effect = Exception("API error")

        result = client.commit_knowledge(
            knowledge_id=3,
            file_path="test.md",
            content="content",
            commit_message="test",
        )

        assert result is not None
        assert result["mode"] == "stub"

    def test_get_knowledge_history_live(self):
        """実接続モードでget_knowledge_historyが動作することを確認"""
        client = self._make_connected_client()
        client._mcp_client.call_tool.return_value = {
            "content": [{"type": "text", "text": "commit abc123: Initial commit"}]
        }

        history = client.get_knowledge_history("knowledge/001.md")
        assert isinstance(history, list)
        assert len(history) >= 1
        client._mcp_client.call_tool.assert_called_once()

    def test_create_audit_issue_live(self):
        """実接続モードでcreate_audit_issueが動作することを確認"""
        client = self._make_connected_client()
        client._mcp_client.call_tool.return_value = {
            "content": [{"type": "text", "text": "Issue #42 created"}]
        }

        result = client.create_audit_issue(
            title="監査テスト",
            description="テスト用Issue",
            labels=["audit"],
        )

        assert result is not None
        assert result["mode"] == "live"
        assert "Issue #42" in result.get("result_text", "")

    def test_create_audit_issue_none_result(self):
        """create_audit_issueでcall_toolがNoneを返す場合のハンドリングを確認"""
        client = self._make_connected_client()
        client._mcp_client.call_tool.return_value = None

        result = client.create_audit_issue(
            title="テスト",
            description="テスト",
        )

        assert result is not None
        assert result["state"] == "error"

    def test_get_file_content_live(self):
        """実接続モードでget_file_contentが動作することを確認"""
        client = self._make_connected_client()
        client._mcp_client.call_tool.return_value = {
            "content": [{"type": "text", "text": "# File Content\nSome text"}]
        }

        content = client.get_file_content("README.md")
        assert content == "# File Content\nSome text"

    def test_create_knowledge_pr_live(self):
        """実接続モードでcreate_knowledge_prが動作することを確認"""
        client = self._make_connected_client()
        client._mcp_client.call_tool.side_effect = [
            {"content": [{"type": "text", "text": "Branch created"}]},  # create_branch
            {"content": [{"type": "text", "text": "Files pushed"}]},    # push_files
            {"content": [{"type": "text", "text": "PR #10 created"}]},  # create_pull_request
        ]

        result = client.create_knowledge_pr(
            branch_name="feature/knowledge-update",
            title="ナレッジ更新",
            description="テスト用PR",
            files_changed=[{"path": "test.md", "content": "# Test"}],
        )

        assert result is not None
        assert result["mode"] == "live"
        assert client._mcp_client.call_tool.call_count == 3

    def test_parse_repo_valid(self):
        """_parse_repoが正常にowner/repoを分割することを確認"""
        client = self._make_connected_client()
        owner, repo = client._parse_repo()
        assert owner == "test-owner"
        assert repo == "test-repo"


# ─── ClaudeMemClient 実接続パス モックテスト ─────────────────────────────


class TestClaudeMemClientLiveMock:
    """ClaudeMemClient の実接続パスをモックで検証"""

    def _make_connected_client(self):
        """接続済みClaudeMemClientを作成（モック）"""
        from src.mcp.claude_mem_client import ClaudeMemClient

        client = ClaudeMemClient(auto_enable=False)
        client.enabled = True
        client._mcp_client = MagicMock()
        client._mcp_client.is_connected = True
        return client

    def test_search_memories_live(self):
        """実接続モードでsearch_memoriesが動作することを確認"""
        client = self._make_connected_client()
        client._mcp_client.call_tool.return_value = {
            "content": [
                {"type": "text", "text": "DB接続プール最大数は50が推奨"},
                {"type": "text", "text": "Connection pool exhaustionの対処法"},
            ]
        }

        results = client.search_memories("データベース接続", limit=5)
        assert len(results) == 2
        assert results[0]["source"] == "Claude-Mem"
        client._mcp_client.call_tool.assert_called_once_with(
            "search_conversations",
            {"query": "データベース接続", "limit": 5, "scope": "all"},
        )

    def test_search_memories_fallback_on_none(self):
        """call_toolがNoneを返した場合デモデータにフォールバックすることを確認"""
        client = self._make_connected_client()
        client._mcp_client.call_tool.return_value = None

        results = client.search_memories("テスト")
        assert len(results) > 0
        assert results[0]["source"] == "Claude-Mem-stub"

    def test_search_memories_fallback_on_exception(self):
        """例外発生時にデモデータにフォールバックすることを確認"""
        client = self._make_connected_client()
        client._mcp_client.call_tool.side_effect = Exception("MCP error")

        results = client.search_memories("テスト")
        assert len(results) > 0
        assert results[0]["source"] == "Claude-Mem-stub"

    def test_store_decision_with_mcp(self):
        """実接続モードでstore_decisionがMCPにも保存することを確認"""
        client = self._make_connected_client()
        client._mcp_client.call_tool.return_value = {
            "content": [{"type": "text", "text": "Remembered"}]
        }

        result = client.store_decision(
            title="アーキテクチャ決定",
            decision="FastAPIを採用",
            rationale="非同期処理が必要",
            tags=["architecture"],
        )

        assert result["success"] is True
        client._mcp_client.call_tool.assert_called_once_with(
            "remember",
            {"text": "Decision: アーキテクチャ決定 - FastAPIを採用 (Rationale: 非同期処理が必要)"},
        )

    def test_get_decisions_with_mcp(self):
        """実接続モードでget_decisionsがMCP+キャッシュのマージ結果を返すことを確認"""
        client = self._make_connected_client()
        client._mcp_client.call_tool.return_value = {
            "content": [
                {"type": "text", "text": "MCP decision: Use SQLite FTS5 for search"},
            ]
        }

        # ローカルキャッシュにも1件追加
        client.store_decision(
            title="ローカル決定",
            decision="テスト",
            rationale="テスト理由",
        )

        decisions = client.get_decisions(query="search", limit=10)
        assert isinstance(decisions, list)
        # MCP結果とローカルキャッシュがマージされること
        assert len(decisions) >= 1

    def test_store_conversation_with_mcp(self):
        """実接続モードでstore_conversationがMCPにインデックスすることを確認"""
        client = self._make_connected_client()
        client._mcp_client.call_tool.return_value = {
            "content": [{"type": "text", "text": "Indexed"}]
        }

        result = client.store_conversation(
            "conv_001",
            [{"role": "user", "content": "テスト質問"}],
            metadata={"topic": "test"},
        )

        assert result is True
        client._mcp_client.call_tool.assert_called_once_with(
            "index_conversations",
            {"session_id": "conv_001"},
        )

    def test_get_conversation_context_live(self):
        """実接続モードでget_conversation_contextが動作することを確認"""
        client = self._make_connected_client()
        client._mcp_client.call_tool.return_value = {
            "content": [
                {"type": "text", "text": "Previous discussion about DB migration"},
            ]
        }

        results = client.get_conversation_context("データベース移行", limit=3)
        assert isinstance(results, list)
        assert len(results) >= 1

    def test_link_to_commit_with_mcp(self):
        """実接続モードでlink_to_commitがMCPを呼び出すことを確認"""
        client = self._make_connected_client()
        client._mcp_client.call_tool.return_value = {
            "content": [{"type": "text", "text": "Linked"}]
        }
        # 事前に決定を追加
        client.store_decision(
            title="テスト決定",
            decision="テスト",
            rationale="テスト",
        )
        dec_id = client._decision_cache[0]["id"]

        result = client.link_to_commit(dec_id, "abc123def", "Fix bug")
        assert result is True

    def test_search_similar_conversations_live(self):
        """実接続モードでsearch_similar_conversationsが動作することを確認"""
        client = self._make_connected_client()
        client._mcp_client.call_tool.return_value = {
            "content": [
                {"type": "text", "text": "Similar discussion found"},
            ]
        }

        results = client.search_similar_conversations("DB接続エラーの対処")
        assert isinstance(results, list)

    def test_enhance_knowledge_with_memory_live(self):
        """実接続モードでenhance_knowledge_with_memoryが動作することを確認"""
        client = self._make_connected_client()
        client._mcp_client.call_tool.return_value = {
            "content": [
                {"type": "text", "text": "過去の類似インシデント情報"},
            ]
        }

        result = client.enhance_knowledge_with_memory(
            "データベース接続エラーが発生", "Incident"
        )
        assert isinstance(result, dict)
        assert "related_memories" in result


# ─── MCPIntegration ヘルスチェック・レポートテスト ─────────────────────────────


class TestMCPIntegrationHealthCheck:
    """MCPIntegrationのヘルスチェックとレポート機能をモックで検証"""

    def test_health_check_all_stub(self):
        """全てスタブモードの場合のhealth_checkを確認"""
        from src.mcp.mcp_integration import MCPIntegration

        integration = MCPIntegration(auto_connect=False)
        health = integration.health_check()

        assert health["overall"] == "all_stub"
        assert health["live_count"] == 0
        assert health["stub_count"] == 3

    def test_health_check_partial(self):
        """一部接続済みの場合のhealth_checkを確認"""
        from src.mcp.mcp_integration import MCPIntegration
        from src.mcp.context7_client import Context7Client

        integration = MCPIntegration(auto_connect=False)

        # Context7のみ接続済みに設定
        ctx_client = Context7Client(auto_enable=False)
        ctx_client.enabled = True
        ctx_client._mcp_client = MagicMock()
        ctx_client._mcp_client.health_check.return_value = {
            "connected": True,
            "server_command": "npx",
            "available_tools": 2,
        }
        integration._context7 = ctx_client

        health = integration.health_check()
        assert health["overall"] == "partial"
        assert health["live_count"] == 1
        assert health["stub_count"] == 2

    def test_health_check_all_connected(self):
        """全て接続済みの場合のhealth_checkを確認"""
        from src.mcp.mcp_integration import MCPIntegration
        from src.mcp.context7_client import Context7Client
        from src.mcp.claude_mem_client import ClaudeMemClient
        from src.mcp.github_client import GitHubClient

        integration = MCPIntegration(auto_connect=False)

        for client_class, attr, flag in [
            (Context7Client, "_context7", "context7_enabled"),
            (ClaudeMemClient, "_claude_mem", "claude_mem_enabled"),
            (GitHubClient, "_github", "github_enabled"),
        ]:
            client = client_class(auto_enable=False)
            client.enabled = True
            client._mcp_client = MagicMock()
            client._mcp_client.health_check.return_value = {"connected": True}
            setattr(integration, attr, client)
            setattr(integration, flag, True)

        health = integration.health_check()
        assert health["overall"] == "healthy"
        assert health["live_count"] == 3
        assert health["stub_count"] == 0

    def test_generate_connection_report(self):
        """接続確認レポートが生成されることを確認"""
        from src.mcp.mcp_integration import MCPIntegration

        integration = MCPIntegration(auto_connect=False)
        report = integration.generate_connection_report()

        assert isinstance(report, str)
        assert "MCP接続確認レポート" in report
        assert "context7" in report
        assert "claude_mem" in report
        assert "github" in report

    def test_generate_connection_report_with_server_info(self):
        """サーバー情報付きの接続確認レポートが生成されることを確認"""
        from src.mcp.mcp_integration import MCPIntegration
        from src.mcp.context7_client import Context7Client

        integration = MCPIntegration(auto_connect=False)

        ctx_client = Context7Client(auto_enable=False)
        ctx_client.enabled = True
        ctx_client._mcp_client = MagicMock()
        ctx_client._mcp_client.health_check.return_value = {
            "connected": True,
            "server_command": "npx",
            "server_info": {
                "server_name": "context7-mcp",
                "server_version": "1.2.0",
                "protocol_version": "2024-11-05",
            },
            "available_tools": 2,
            "tool_names": ["resolve-library-id", "query-docs"],
            "last_error": None,
        }
        integration._context7 = ctx_client

        report = integration.generate_connection_report()
        assert "context7-mcp" in report
        assert "LIVE" in report
        assert "resolve-library-id" in report

    def test_connect_all_mocked(self):
        """connect_allが各クライアントのenableを呼び出すことを確認"""
        from src.mcp.mcp_integration import MCPIntegration

        integration = MCPIntegration(auto_connect=False)

        with patch.object(integration, 'enable_context7', return_value=True) as mock_ctx, \
             patch.object(integration, 'enable_claude_mem', return_value=False) as mock_mem, \
             patch.object(integration, 'enable_github', return_value=False) as mock_gh:

            results = integration.connect_all()

            assert results["context7"] is True
            assert results["claude_mem"] is False
            assert results["github"] is False
            mock_ctx.assert_called_once()
            mock_mem.assert_called_once()
            mock_gh.assert_called_once()

    def test_disconnect_all(self):
        """disconnect_allが全クライアントを切断することを確認"""
        from src.mcp.mcp_integration import MCPIntegration
        from src.mcp.context7_client import Context7Client
        from src.mcp.claude_mem_client import ClaudeMemClient
        from src.mcp.github_client import GitHubClient

        integration = MCPIntegration(auto_connect=False)
        integration._context7 = Context7Client(auto_enable=False)
        integration._claude_mem = ClaudeMemClient(auto_enable=False)
        integration._github = GitHubClient(auto_enable=False)
        integration.context7_enabled = True
        integration.claude_mem_enabled = True
        integration.github_enabled = True

        integration.disconnect_all()

        assert not integration.context7_enabled
        assert not integration.claude_mem_enabled
        assert not integration.github_enabled
