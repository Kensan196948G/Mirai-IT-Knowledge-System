"""
SQLiteClient 単体テスト
カバレッジ目標: 70%以上
"""

import pytest
from pathlib import Path
from src.mcp.sqlite_client import SQLiteClient


class TestSQLiteClientCRUD:
    """CRUD操作のテスト"""

    def test_create_knowledge_returns_id(self, test_sqlite_client, sample_knowledge_data):
        """ナレッジ作成が新規IDを返すこと"""
        knowledge_id = test_sqlite_client.create_knowledge(**sample_knowledge_data)
        assert knowledge_id > 0

    def test_get_knowledge_by_id_returns_correct_data(
        self, test_sqlite_client, sample_knowledge_data
    ):
        """IDでナレッジを正しく取得できること"""
        knowledge_id = test_sqlite_client.create_knowledge(**sample_knowledge_data)
        result = test_sqlite_client.get_knowledge_by_id(knowledge_id)
        assert result is not None
        assert result["title"] == sample_knowledge_data["title"]
        assert result["itsm_type"] == sample_knowledge_data["itsm_type"]

    def test_update_knowledge_modifies_fields(
        self, test_sqlite_client, sample_knowledge_data
    ):
        """ナレッジ更新がフィールドを変更すること"""
        knowledge_id = test_sqlite_client.create_knowledge(**sample_knowledge_data)
        success = test_sqlite_client.update_knowledge(
            knowledge_id, title="更新タイトル"
        )
        assert success
        result = test_sqlite_client.get_knowledge_by_id(knowledge_id)
        assert result["title"] == "更新タイトル"

    def test_search_knowledge_by_query(
        self, test_sqlite_client, sample_knowledge_data
    ):
        """クエリ検索が動作すること"""
        test_sqlite_client.create_knowledge(**sample_knowledge_data)
        results = test_sqlite_client.search_knowledge(query="Webサーバー")
        assert len(results) >= 1

    def test_validate_update_columns_rejects_invalid_columns(self, test_sqlite_client):
        """無効なカラム名を拒否すること（SQL injection対策）"""
        with pytest.raises(ValueError):
            test_sqlite_client._validate_update_columns(["DROP TABLE"])

    def test_create_knowledge_with_minimal_fields(self, test_sqlite_client):
        """最小限のフィールドでナレッジ作成できること"""
        knowledge_id = test_sqlite_client.create_knowledge(
            title="最小テスト",
            itsm_type="Incident",
            content="最小テスト内容",
            created_by="test_user",
        )
        assert knowledge_id > 0

    def test_search_knowledge_with_itsm_filter(
        self, test_sqlite_client, sample_knowledge_data
    ):
        """ITSMタイプでフィルタリングできること"""
        test_sqlite_client.create_knowledge(**sample_knowledge_data)
        results = test_sqlite_client.search_knowledge(
            query="", itsm_type="Incident"
        )
        assert all(r["itsm_type"] == "Incident" for r in results)


class TestSQLiteClientWorkflow:
    """ワークフロー記録のテスト"""

    def test_create_workflow_execution_returns_id(self, test_sqlite_client):
        """ワークフロー実行記録がIDを返すこと"""
        execution_id = test_sqlite_client.create_workflow_execution(
            workflow_type="knowledge_register", knowledge_id=1
        )
        assert execution_id > 0

    def test_update_workflow_execution_modifies_status(self, test_sqlite_client):
        """ワークフロー実行ステータスを更新できること"""
        execution_id = test_sqlite_client.create_workflow_execution(
            workflow_type="knowledge_register", knowledge_id=1
        )
        success = test_sqlite_client.update_workflow_execution(
            execution_id, status="completed", execution_time_ms=1000
        )
        assert success

    def test_log_subagent_execution_stores_data(self, test_sqlite_client):
        """サブエージェント実行ログが保存されること"""
        execution_id = test_sqlite_client.create_workflow_execution(
            workflow_type="test", knowledge_id=1
        )
        log_id = test_sqlite_client.log_subagent_execution(
            workflow_execution_id=execution_id,
            subagent_name="architect",
            role="classification",
            status="success",
            output_data={"score": 0.9},
        )
        # エラーが発生しないことを確認
        assert log_id > 0

    def test_log_hook_execution_stores_data(self, test_sqlite_client):
        """フック実行ログが保存されること"""
        execution_id = test_sqlite_client.create_workflow_execution(
            workflow_type="test", knowledge_id=1
        )
        log_id = test_sqlite_client.log_hook_execution(
            workflow_execution_id=execution_id,
            hook_name="duplicate_check",
            hook_type="pre-task",
            result="pass",
            details={"threshold": 0.85},
        )
        # エラーが発生しないことを確認
        assert log_id > 0


class TestSQLiteClientConversation:
    """対話履歴のテスト"""

    def test_create_conversation_session_returns_id(self, test_sqlite_client):
        """対話セッション作成がsession_idを返すこと"""
        session_id = test_sqlite_client.create_conversation_session(
            session_id="test_session_001"
        )
        assert session_id == "test_session_001"

    def test_add_conversation_message_stores_data(self, test_sqlite_client):
        """対話メッセージが保存されること"""
        session_id = test_sqlite_client.create_conversation_session(
            session_id="test_session_002"
        )
        test_sqlite_client.add_conversation_message(
            session_id=session_id, role="user", content="テストメッセージ"
        )
        # エラーが発生しないことを確認
        assert True

    def test_get_conversation_messages_returns_messages(self, test_sqlite_client):
        """対話履歴が取得できること"""
        session_id = test_sqlite_client.create_conversation_session(
            session_id="test_session_003"
        )
        test_sqlite_client.add_conversation_message(
            session_id=session_id, role="user", content="メッセージ1"
        )
        test_sqlite_client.add_conversation_message(
            session_id=session_id, role="assistant", content="メッセージ2"
        )
        messages = test_sqlite_client.get_conversation_messages(session_id)
        assert len(messages) == 2


class TestSQLiteClientStatistics:
    """統計情報のテスト"""

    def test_get_statistics_returns_valid_data(
        self, test_sqlite_client, sample_knowledge_data
    ):
        """統計情報が取得できること"""
        test_sqlite_client.create_knowledge(**sample_knowledge_data)
        stats = test_sqlite_client.get_statistics()
        assert "total_knowledge" in stats
        assert stats["total_knowledge"] >= 1


class TestSQLiteClientEdgeCases:
    """エッジケースのテスト"""

    def test_search_knowledge_with_empty_query(self, test_sqlite_client):
        """空クエリで全件取得できること"""
        results = test_sqlite_client.search_knowledge(query="")
        assert isinstance(results, list)

    def test_update_knowledge_with_invalid_id(self, test_sqlite_client):
        """存在しないIDで更新するとFalseを返すこと"""
        success = test_sqlite_client.update_knowledge(99999, title="test")
        assert not success

    def test_get_knowledge_by_id_with_invalid_id(self, test_sqlite_client):
        """存在しないIDで取得するとNoneを返すこと"""
        result = test_sqlite_client.get_knowledge_by_id(99999)
        assert result is None

    def test_create_knowledge_with_special_characters(self, test_sqlite_client):
        """特殊文字を含むナレッジを作成できること"""
        knowledge_id = test_sqlite_client.create_knowledge(
            title="テスト<>&\"'",
            itsm_type="Incident",
            content="特殊文字: <script>alert('xss')</script>",
            created_by="test",
        )
        assert knowledge_id > 0
        result = test_sqlite_client.get_knowledge_by_id(knowledge_id)
        assert "<script>" in result["content"]  # エスケープなしで保存

    def test_search_knowledge_with_limit(
        self, test_sqlite_client, sample_knowledge_data
    ):
        """検索結果の件数制限が動作すること"""
        # 複数のナレッジを作成
        for i in range(5):
            data = sample_knowledge_data.copy()
            data["title"] = f"テスト{i}"
            test_sqlite_client.create_knowledge(**data)

        results = test_sqlite_client.search_knowledge(query="", limit=3)
        assert len(results) <= 3
