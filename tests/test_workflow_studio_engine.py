"""
WorkflowStudioEngine 単体テスト
src/workflows/workflow_studio_engine.py のテスト
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_db_client():
    """SQLiteClientのモック"""
    mock = MagicMock()
    mock.create_workflow_execution.return_value = 1
    mock.update_workflow_execution.return_value = None
    return mock


@pytest.fixture
def engine(mock_db_client, tmp_path):
    """WorkflowStudioEngineインスタンス（モック付き）"""
    with patch("src.workflows.workflow_studio_engine.SQLiteClient", return_value=mock_db_client):
        from src.workflows.workflow_studio_engine import WorkflowStudioEngine
        return WorkflowStudioEngine(
            workflows_dir=tmp_path / "workflows",
            db_client=mock_db_client,
        )


class TestWorkflowStudioEngineInit:
    """初期化テスト"""

    def test_init_with_default_db_client(self, tmp_path):
        """デフォルトSQLiteClientで初期化できること"""
        with patch("src.workflows.workflow_studio_engine.SQLiteClient") as mock_cls:
            from src.workflows.workflow_studio_engine import WorkflowStudioEngine
            eng = WorkflowStudioEngine(workflows_dir=tmp_path / "workflows")
            assert eng is not None

    def test_init_sets_workflows_dir(self, engine, tmp_path):
        """workflows_dirが正しく設定されること"""
        assert isinstance(engine.workflows_dir, Path)

    def test_init_registry_has_default_handlers(self, engine):
        """デフォルトハンドラーが登録されていること"""
        assert "knowledge_register" in engine._registry
        assert "search_assist" in engine._registry
        assert "incident_to_problem" in engine._registry

    def test_init_empty_definitions_when_no_workflows(self, engine):
        """ワークフローファイルがない場合空の定義になること"""
        assert isinstance(engine._definitions, dict)


class TestListWorkflows:
    """list_workflows メソッドテスト"""

    def test_list_workflows_returns_list(self, engine):
        """リスト形式で返ること"""
        result = engine.list_workflows()
        assert isinstance(result, list)

    def test_list_workflows_empty_when_no_definitions(self, engine):
        """定義なしの場合空リストを返すこと"""
        engine._definitions = {}
        result = engine.list_workflows()
        assert result == []


class TestGetDefinition:
    """get_definition メソッドテスト"""

    def test_get_definition_returns_none_for_unknown(self, engine):
        """存在しないワークフロー名でNoneを返すこと"""
        result = engine.get_definition("nonexistent")
        assert result is None

    def test_get_definition_returns_definition(self, engine):
        """定義が存在する場合返すこと"""
        from src.workflows.workflow_studio_engine import WorkflowDefinition
        fake_def = WorkflowDefinition(
            name="test_workflow",
            display_name="テスト",
            description="テスト用",
            handler="knowledge_register",
            inputs=["title", "content"],
            outputs=["id"],
            steps=[],
            source_path="/fake/path.workflow",
        )
        engine._definitions["test_workflow"] = fake_def
        result = engine.get_definition("test_workflow")
        assert result is not None
        assert result.name == "test_workflow"


class TestRunWorkflow:
    """run_workflow メソッドテスト"""

    def test_run_workflow_not_found_returns_error(self, engine):
        """存在しないワークフロー名でエラーを返すこと"""
        result = engine.run_workflow("nonexistent", {})
        assert result["success"] is False
        assert "not found" in result["error"]

    def test_run_workflow_handler_not_found_returns_error(self, engine, mock_db_client):
        """ハンドラー未登録でエラーを返すこと"""
        from src.workflows.workflow_studio_engine import WorkflowDefinition
        fake_def = WorkflowDefinition(
            name="test_wf",
            display_name="Test",
            description="",
            handler="unknown_handler",
            inputs=[],
            outputs=[],
            steps=[],
            source_path="/fake/path.workflow",
        )
        engine._definitions["test_wf"] = fake_def
        result = engine.run_workflow("test_wf", {})
        assert result["success"] is False

    def test_run_workflow_knowledge_register_missing_inputs(self, engine, mock_db_client):
        """knowledge_registerでtitle/content欠如時にエラーを返すこと"""
        from src.workflows.workflow_studio_engine import WorkflowDefinition
        fake_def = WorkflowDefinition(
            name="knowledge_register",
            display_name="知識登録",
            description="",
            handler="knowledge_register",
            inputs=["title", "content"],
            outputs=["id"],
            steps=[],
            source_path="/fake/path.workflow",
        )
        engine._definitions["knowledge_register"] = fake_def
        result = engine.run_workflow("knowledge_register", {})
        assert result["success"] is False

    def test_run_workflow_search_assist_missing_query(self, engine, mock_db_client):
        """search_assistでquery欠如時にエラーを返すこと"""
        from src.workflows.workflow_studio_engine import WorkflowDefinition
        fake_def = WorkflowDefinition(
            name="search_assist",
            display_name="検索支援",
            description="",
            handler="search_assist",
            inputs=["query"],
            outputs=["result"],
            steps=[],
            source_path="/fake/path.workflow",
        )
        engine._definitions["search_assist"] = fake_def
        result = engine.run_workflow("search_assist", {})
        assert result["success"] is False


class TestEmitEvent:
    """_emit_event メソッドテスト"""

    def test_emit_event_calls_sink(self, engine):
        """event_sinkが設定されている場合呼び出されること"""
        mock_sink = MagicMock()
        engine.event_sink = mock_sink
        engine._emit_event("test_event", {"key": "value"})
        mock_sink.assert_called_once_with("test_event", {"key": "value"})

    def test_emit_event_no_sink_does_not_raise(self, engine):
        """event_sinkが未設定でもエラーにならないこと"""
        engine.event_sink = None
        engine._emit_event("test_event", {})  # エラーなし


class TestLoadDefinitions:
    """_load_definitions メソッドテスト"""

    def test_load_definitions_from_yaml(self, mock_db_client, tmp_path):
        """YAMLファイルからワークフロー定義を読み込めること"""
        workflows_dir = tmp_path / "workflows"
        workflows_dir.mkdir()
        workflow_file = workflows_dir / "test_wf.workflow"
        workflow_file.write_text(
            "workflow_id: test_wf\n"
            "name: テストワークフロー\n"
            "description: テスト用\n"
            "handler: knowledge_register\n"
            "inputs:\n  - title\n  - content\n"
            "outputs:\n  - id\n"
            "steps:\n  - name: step1\n",
            encoding="utf-8",
        )

        with patch("src.workflows.workflow_studio_engine.SQLiteClient", return_value=mock_db_client):
            from src.workflows.workflow_studio_engine import WorkflowStudioEngine
            eng = WorkflowStudioEngine(workflows_dir=workflows_dir, db_client=mock_db_client)

        assert "test_wf" in eng._definitions
        defn = eng._definitions["test_wf"]
        assert defn.display_name == "テストワークフロー"
        assert defn.handler == "knowledge_register"

    def test_load_definitions_empty_dir(self, mock_db_client, tmp_path):
        """空のディレクトリでは空辞書を返すこと"""
        workflows_dir = tmp_path / "workflows"
        workflows_dir.mkdir()

        with patch("src.workflows.workflow_studio_engine.SQLiteClient", return_value=mock_db_client):
            from src.workflows.workflow_studio_engine import WorkflowStudioEngine
            eng = WorkflowStudioEngine(workflows_dir=workflows_dir, db_client=mock_db_client)

        assert eng._definitions == {}

    def test_load_definitions_nonexistent_dir(self, mock_db_client, tmp_path):
        """存在しないディレクトリでは空辞書を返すこと"""
        with patch("src.workflows.workflow_studio_engine.SQLiteClient", return_value=mock_db_client):
            from src.workflows.workflow_studio_engine import WorkflowStudioEngine
            eng = WorkflowStudioEngine(
                workflows_dir=tmp_path / "nonexistent",
                db_client=mock_db_client,
            )

        assert eng._definitions == {}

    def test_load_definitions_uses_stem_as_fallback_name(self, mock_db_client, tmp_path):
        """workflow_id がない場合ファイル名のstemがnameになること"""
        workflows_dir = tmp_path / "workflows"
        workflows_dir.mkdir()
        workflow_file = workflows_dir / "my_flow.workflow"
        workflow_file.write_text("description: fallback test\n", encoding="utf-8")

        with patch("src.workflows.workflow_studio_engine.SQLiteClient", return_value=mock_db_client):
            from src.workflows.workflow_studio_engine import WorkflowStudioEngine
            eng = WorkflowStudioEngine(workflows_dir=workflows_dir, db_client=mock_db_client)

        assert "my_flow" in eng._definitions


class TestRunWorkflowSuccess:
    """run_workflow 成功パステスト"""

    def test_run_knowledge_register_success(self, engine, mock_db_client):
        """knowledge_register ハンドラーが正常実行されること"""
        from src.workflows.workflow_studio_engine import WorkflowDefinition
        fake_def = WorkflowDefinition(
            name="knowledge_register",
            display_name="知識登録",
            description="",
            handler="knowledge_register",
            inputs=["title", "content"],
            outputs=["id"],
            steps=[],
            source_path="/fake/path.workflow",
        )
        engine._definitions["knowledge_register"] = fake_def

        with patch("src.workflows.workflow_studio_engine.ITSMClassifier") as mock_cls, \
             patch("src.workflows.workflow_studio_engine.WorkflowEngine") as mock_wf:
            mock_cls.return_value.classify.return_value = {"itsm_type": "Incident"}
            mock_wf.return_value.process_knowledge.return_value = {
                "success": True, "id": 1, "subagents_used": ["agent1"], "hooks_triggered": []
            }
            result = engine.run_workflow("knowledge_register", {
                "title": "テスト障害", "content": "内容", "itsm_type": "auto"
            })

        assert result["success"] is True
        assert result["execution_id"] == 1
        mock_db_client.update_workflow_execution.assert_called_once()

    def test_run_search_assist_success(self, engine, mock_db_client):
        """search_assist ハンドラーが正常実行されること"""
        from src.workflows.workflow_studio_engine import WorkflowDefinition
        fake_def = WorkflowDefinition(
            name="search_assist",
            display_name="検索支援",
            description="",
            handler="search_assist",
            inputs=["query"],
            outputs=["result"],
            steps=[],
            source_path="/fake/path.workflow",
        )
        engine._definitions["search_assist"] = fake_def

        with patch("src.workflows.workflow_studio_engine.IntelligentSearchAssistant") as mock_isa:
            mock_isa.return_value.search.return_value = {
                "query": "テスト", "intent": {}, "knowledge": [{"id": 1}]
            }
            result = engine.run_workflow("search_assist", {"query": "テスト"})

        assert result["success"] is True
        assert result["result"]["payload"]["query"] == "テスト"

    def test_run_incident_to_problem_success(self, engine, mock_db_client):
        """incident_to_problem ハンドラーが正常実行されること"""
        from src.workflows.workflow_studio_engine import WorkflowDefinition
        fake_def = WorkflowDefinition(
            name="incident_to_problem",
            display_name="インシデント→問題",
            description="",
            handler="incident_to_problem",
            inputs=["title", "content"],
            outputs=["id"],
            steps=[],
            source_path="/fake/path.workflow",
        )
        engine._definitions["incident_to_problem"] = fake_def

        with patch("src.workflows.workflow_studio_engine.WorkflowEngine") as mock_wf:
            mock_wf.return_value.process_knowledge.return_value = {
                "success": True, "id": 2
            }
            result = engine.run_workflow("incident_to_problem", {
                "title": "障害報告", "content": "サーバーダウン"
            })

        assert result["success"] is True
        # itsm_type が "Problem" で呼ばれること
        mock_wf.return_value.process_knowledge.assert_called_once()
        call_kwargs = mock_wf.return_value.process_knowledge.call_args
        assert call_kwargs[1]["itsm_type"] == "Problem" or call_kwargs.kwargs.get("itsm_type") == "Problem"

    def test_run_workflow_emits_events(self, engine, mock_db_client):
        """ワークフロー実行時に workflow_started と workflow_completed イベントが発行されること"""
        from src.workflows.workflow_studio_engine import WorkflowDefinition
        fake_def = WorkflowDefinition(
            name="knowledge_register",
            display_name="知識登録",
            description="",
            handler="knowledge_register",
            inputs=["title", "content"],
            outputs=["id"],
            steps=[],
            source_path="/fake/path.workflow",
        )
        engine._definitions["knowledge_register"] = fake_def

        mock_sink = MagicMock()
        engine.event_sink = mock_sink

        with patch("src.workflows.workflow_studio_engine.ITSMClassifier") as mock_cls, \
             patch("src.workflows.workflow_studio_engine.WorkflowEngine") as mock_wf:
            mock_cls.return_value.classify.return_value = {"itsm_type": "Incident"}
            mock_wf.return_value.process_knowledge.return_value = {"success": True, "id": 1}
            engine.run_workflow("knowledge_register", {"title": "テスト", "content": "内容"})

        event_types = [call[0][0] for call in mock_sink.call_args_list]
        assert "workflow_started" in event_types
        assert "workflow_completed" in event_types


class TestListWorkflowsWithDefinitions:
    """list_workflows にデータがある場合のテスト"""

    def test_list_workflows_includes_definition_fields(self, engine):
        """定義がある場合、必須フィールドが全て含まれること"""
        from src.workflows.workflow_studio_engine import WorkflowDefinition
        fake_def = WorkflowDefinition(
            name="test_wf",
            display_name="テスト",
            description="テスト用",
            handler="knowledge_register",
            inputs=["title"],
            outputs=["id"],
            steps=[],
            source_path="/fake/path.workflow",
        )
        engine._definitions["test_wf"] = fake_def

        result = engine.list_workflows()
        assert len(result) == 1
        wf = result[0]
        assert wf["name"] == "test_wf"
        assert wf["display_name"] == "テスト"
        assert wf["handler"] == "knowledge_register"
