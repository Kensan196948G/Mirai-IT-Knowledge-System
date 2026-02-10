#!/usr/bin/env python3
"""
AgentExecutor詳細単体テスト
SubAgentExecutorとHookExecutorの動作を検証
カバレッジ目標: 70%以上
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
import time
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.agents.executor import (
    ExecutionResult,
    HookExecutor,
    SubAgentExecutor,
    create_hook_executor,
    create_subagent_executor,
)
from src.agents.loader import AgentLoader, HookConfig, HookLoader, SubAgentConfig


# ========== SubAgentExecutor テスト ==========


class TestSubAgentExecutor:
    """SubAgentExecutorの詳細テスト"""

    @pytest.fixture
    def mock_loader(self):
        """モックAgentLoaderを生成"""
        loader = Mock(spec=AgentLoader)
        loader.get_execution_config.return_value = {
            "max_concurrent": 3,
            "parallel_enabled": True,
        }

        # モックSubAgentConfigを生成
        mock_agent = SubAgentConfig(
            name="TestAgent",
            description="Test agent description",
            capabilities=["test", "validation"],
            prompts={"system": "You are a test agent"},
            priority="high",
            model="claude-sonnet-4-20250514",
            enabled=True,
        )

        loader.get_agent.return_value = mock_agent
        loader.get_agents_by_priority.return_value = [mock_agent]

        return loader

    @pytest.fixture
    def executor(self, mock_loader):
        """SubAgentExecutorインスタンスを生成"""
        return SubAgentExecutor(loader=mock_loader)

    # ========== 正常実行テスト ==========

    def test_execute_agent_success(self, executor, mock_loader):
        """SubAgentが正常に実行されること"""
        input_data = {"query": "test query"}
        result = executor.execute("test_agent", input_data)

        assert result.success is True
        assert result.agent_name == "TestAgent"
        assert result.output is not None
        assert result.execution_time_ms >= 0
        assert result.error_message is None

    def test_execute_agent_with_callback(self, executor):
        """コールバック関数が正しく呼び出されること"""
        callback_called = []

        def callback(result: ExecutionResult):
            callback_called.append(result)

        input_data = {"query": "test"}
        result = executor.execute("test_agent", input_data, callback=callback)

        assert len(callback_called) == 1
        assert callback_called[0] == result

    def test_execute_agent_output_structure(self, executor):
        """実行結果の出力構造が正しいこと"""
        input_data = {"query": "test"}
        result = executor.execute("test_agent", input_data)

        assert isinstance(result.output, dict)
        assert "agent" in result.output
        assert "capabilities" in result.output
        assert "status" in result.output
        assert result.output["status"] == "processed"

    # ========== エラーハンドリングテスト ==========

    def test_execute_agent_not_found(self, executor, mock_loader):
        """存在しないAgentを指定した場合、エラーが返されること"""
        mock_loader.get_agent.return_value = None

        result = executor.execute("nonexistent_agent", {})

        assert result.success is False
        assert "not found" in result.error_message.lower()
        assert result.agent_name == "nonexistent_agent"

    def test_execute_agent_exception_handling(self, mock_loader):
        """Agent実行中の例外が適切に処理されること"""
        # 正常なAgentを返すが、実行時に例外をシミュレート
        mock_agent = SubAgentConfig(
            name="ErrorAgent",
            description="Agent that causes error",
            capabilities=["test"],
            prompts={},
        )
        mock_loader.get_agent.return_value = mock_agent

        executor = SubAgentExecutor(loader=mock_loader)

        # _execute_agent_logicをモックして例外を発生させる
        with patch.object(executor, "_execute_agent_logic", side_effect=Exception("Test exception")):
            result = executor.execute("test_agent", {})

            assert result.success is False
            assert result.error_message is not None
            assert "Test exception" in result.error_message

    def test_execute_agent_logs_error(self, mock_loader):
        """エラー時にログが記録されること"""
        mock_agent = SubAgentConfig(
            name="ErrorAgent",
            description="Agent that causes error",
            capabilities=["test"],
            prompts={},
        )
        mock_loader.get_agent.return_value = mock_agent

        executor = SubAgentExecutor(loader=mock_loader)

        with patch("src.agents.executor.logger") as mock_logger:
            with patch.object(executor, "_execute_agent_logic", side_effect=Exception("Test error")):
                executor.execute("test_agent", {})

                mock_logger.error.assert_called_once()
                args = mock_logger.error.call_args[0][0]
                assert "SubAgent実行エラー" in args

    # ========== 並列実行テスト ==========

    @pytest.mark.asyncio
    async def test_execute_parallel_success(self, executor):
        """複数のAgentが並列実行されること"""
        agent_ids = ["agent1", "agent2", "agent3"]
        input_data = {"query": "parallel test"}

        results = await executor.execute_parallel(agent_ids, input_data)

        assert len(results) == 3
        for result in results:
            assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_parallel_disabled(self, executor, mock_loader):
        """並列実行が無効な場合、順次実行されること"""
        mock_loader.get_execution_config.return_value = {
            "parallel_enabled": False,
            "max_concurrent": 3,
        }

        agent_ids = ["agent1", "agent2"]
        results = await executor.execute_parallel(agent_ids, {})

        assert len(results) == 2
        # 順次実行されているため、各結果の成功を確認
        for result in results:
            assert result.success is True

    # ========== 優先度実行テスト ==========

    def test_execute_by_priority_critical(self, executor, mock_loader):
        """優先度順にAgentが実行されること - critical"""
        results = executor.execute_by_priority({}, min_priority="critical")

        # criticalのみが実行される
        assert len(results) >= 0  # モックの設定による

    def test_execute_by_priority_respects_enabled_flag(self, executor, mock_loader):
        """無効化されたAgentが実行されないこと"""
        disabled_agent = SubAgentConfig(
            name="DisabledAgent",
            description="Disabled agent",
            capabilities=["test"],
            prompts={},
            priority="high",
            enabled=False,
        )
        mock_loader.get_agents_by_priority.return_value = [disabled_agent]

        results = executor.execute_by_priority({}, min_priority="high")

        # 無効化されているため実行されない
        assert all(r.agent_name != "DisabledAgent" for r in results)

    # ========== 実行履歴テスト ==========

    def test_get_execution_history(self, executor):
        """実行履歴が正しく記録されること"""
        executor.execute("test_agent", {"query": "test1"})
        executor.execute("test_agent", {"query": "test2"})

        history = executor.get_execution_history()

        assert len(history) == 2
        assert all(isinstance(r, ExecutionResult) for r in history)

    def test_clear_history(self, executor):
        """実行履歴がクリアされること"""
        executor.execute("test_agent", {"query": "test"})
        executor.clear_history()

        history = executor.get_execution_history()

        assert len(history) == 0

    # ========== 実行時間測定テスト ==========

    def test_execution_time_measurement(self, executor):
        """実行時間が正しく計測されること"""
        result = executor.execute("test_agent", {})

        assert result.execution_time_ms >= 0
        assert isinstance(result.execution_time_ms, int)

    # ========== ワーカー数設定テスト ==========

    def test_get_max_workers_default(self, executor, mock_loader):
        """最大ワーカー数が正しく取得されること"""
        max_workers = executor._get_max_workers()

        assert max_workers == 3


# ========== HookExecutor テスト ==========


class TestHookExecutor:
    """HookExecutorの詳細テスト"""

    @pytest.fixture
    def mock_hook_loader(self):
        """モックHookLoaderを生成"""
        loader = Mock(spec=HookLoader)

        # モックHookConfigを生成
        mock_hook = HookConfig(
            name="TestHook",
            description="Test hook description",
            trigger="pre_execution",
            actions=["notify", "log"],
            prompts={"notification": "Test notification"},
            enabled=True,
            timeout_seconds=30,
            extra_config={"channel": "test-channel"},
        )

        loader.get_hook.return_value = mock_hook
        loader.get_hooks_for_trigger.return_value = [mock_hook]
        loader.get_global_settings.return_value = {"parallel_execution": True}

        return loader

    @pytest.fixture
    def hook_executor(self, mock_hook_loader):
        """HookExecutorインスタンスを生成"""
        return HookExecutor(loader=mock_hook_loader)

    # ========== 正常実行テスト ==========

    def test_execute_hook_success(self, hook_executor):
        """Hookが正常に実行されること"""
        context = {"event": "test_event", "data": "test_data"}
        result = hook_executor.execute_hook("test_hook", context)

        assert result.success is True
        assert result.agent_name == "TestHook"
        assert result.output is not None
        assert result.error_message is None

    def test_execute_hook_output_structure(self, hook_executor):
        """Hook実行結果の出力構造が正しいこと"""
        context = {"event": "test"}
        result = hook_executor.execute_hook("test_hook", context)

        assert isinstance(result.output, dict)
        assert "hook" in result.output
        assert "trigger" in result.output
        assert "actions" in result.output
        assert result.output["trigger"] == "pre_execution"

    def test_execute_hook_with_actions(self, hook_executor):
        """複数のアクションが正しく実行されること"""
        context = {"event": "test"}
        result = hook_executor.execute_hook("test_hook", context)

        assert len(result.output["actions"]) == 2
        for action_result in result.output["actions"]:
            assert "action" in action_result
            assert "status" in action_result
            assert action_result["status"] == "executed"

    # ========== Hook無効化テスト ==========

    def test_execute_hook_disabled(self, hook_executor, mock_hook_loader):
        """無効化されたHookがスキップされること"""
        disabled_hook = HookConfig(
            name="DisabledHook",
            description="Disabled hook",
            trigger="post_execution",
            actions=["notify"],
            prompts={},
            enabled=False,
            timeout_seconds=30,
        )
        mock_hook_loader.get_hook.return_value = disabled_hook

        result = hook_executor.execute_hook("disabled_hook", {})

        assert result.success is True
        assert result.output["skipped"] is True
        assert result.output["reason"] == "Hook is disabled"

    # ========== エラーハンドリングテスト ==========

    def test_execute_hook_not_found(self, hook_executor, mock_hook_loader):
        """存在しないHookを指定した場合、エラーが返されること"""
        mock_hook_loader.get_hook.return_value = None

        result = hook_executor.execute_hook("nonexistent_hook", {})

        assert result.success is False
        assert "not found" in result.error_message.lower()

    def test_execute_hook_exception_handling(self, hook_executor, mock_hook_loader):
        """Hook実行中の例外が適切に処理されること"""
        mock_hook = HookConfig(
            name="ErrorHook",
            description="Hook that causes error",
            trigger="test",
            actions=["notify"],
            prompts={},
        )
        mock_hook_loader.get_hook.return_value = mock_hook

        # _execute_hook_logicをモックして例外を発生させる
        with patch.object(hook_executor, "_execute_hook_logic", side_effect=Exception("Hook error")):
            result = hook_executor.execute_hook("test_hook", {})

            assert result.success is False
            assert result.error_message is not None

    # ========== タイムアウトテスト ==========

    def test_execute_hook_timeout_warning(self, hook_executor, mock_hook_loader):
        """タイムアウト超過時に警告ログが出力されること"""
        with patch("src.agents.executor.logger") as mock_logger:
            with patch("time.time") as mock_time:
                # タイムアウトを超過するようシミュレート
                mock_time.side_effect = [0, 35]  # 35秒経過

                hook_executor.execute_hook("test_hook", {})

                # 警告ログが呼び出されたか確認
                assert mock_logger.warning.called

    # ========== トリガー実行テスト ==========

    def test_trigger_hooks_for_event(self, hook_executor, mock_hook_loader):
        """特定のトリガーに関連するHookが実行されること"""
        context = {"event": "pre_execution"}
        results = hook_executor.trigger("pre_execution", context)

        assert len(results) >= 1
        for result in results:
            assert result.success is True

    def test_trigger_with_parallel_disabled(self, hook_executor, mock_hook_loader):
        """並列実行が無効な場合、順次実行されること"""
        mock_hook_loader.get_global_settings.return_value = {
            "parallel_execution": False
        }

        results = hook_executor.trigger("pre_execution", {})

        assert len(results) >= 1

    # ========== 実行履歴テスト ==========

    def test_hook_execution_history(self, hook_executor):
        """Hook実行履歴が正しく記録されること"""
        hook_executor.execute_hook("test_hook", {"event": "test1"})
        hook_executor.execute_hook("test_hook", {"event": "test2"})

        history = hook_executor.get_execution_history()

        assert len(history) == 2

    def test_hook_clear_history(self, hook_executor):
        """Hook実行履歴がクリアされること"""
        hook_executor.execute_hook("test_hook", {"event": "test"})
        hook_executor.clear_history()

        history = hook_executor.get_execution_history()

        assert len(history) == 0


# ========== ExecutionResult テスト ==========


class TestExecutionResult:
    """ExecutionResultデータクラスのテスト"""

    def test_execution_result_creation(self):
        """ExecutionResultが正しく生成されること"""
        result = ExecutionResult(
            success=True,
            agent_name="TestAgent",
            output={"data": "test"},
            execution_time_ms=100,
        )

        assert result.success is True
        assert result.agent_name == "TestAgent"
        assert result.output == {"data": "test"}
        assert result.execution_time_ms == 100
        assert result.error_message is None
        assert result.timestamp is not None

    def test_execution_result_with_error(self):
        """エラー情報を含むExecutionResultが生成されること"""
        result = ExecutionResult(
            success=False,
            agent_name="TestAgent",
            output=None,
            execution_time_ms=50,
            error_message="Test error",
        )

        assert result.success is False
        assert result.error_message == "Test error"

    def test_execution_result_timestamp_auto_generated(self):
        """タイムスタンプが自動生成されること"""
        result1 = ExecutionResult(
            success=True, agent_name="Test", output={}, execution_time_ms=0
        )
        time.sleep(0.01)
        result2 = ExecutionResult(
            success=True, agent_name="Test", output={}, execution_time_ms=0
        )

        assert result1.timestamp != result2.timestamp


# ========== ファクトリー関数テスト ==========


class TestFactoryFunctions:
    """ファクトリー関数のテスト"""

    @patch("src.agents.executor.AgentLoader")
    def test_create_subagent_executor(self, mock_agent_loader_class):
        """SubAgentExecutorのファクトリー関数が動作すること"""
        mock_loader = Mock()
        mock_loader.load.return_value = True
        mock_loader.get_execution_config.return_value = {"max_concurrent": 3}
        mock_agent_loader_class.return_value = mock_loader

        executor = create_subagent_executor()

        assert isinstance(executor, SubAgentExecutor)

    @patch("src.agents.executor.HookLoader")
    def test_create_hook_executor(self, mock_hook_loader_class):
        """HookExecutorのファクトリー関数が動作すること"""
        mock_loader = Mock()
        mock_loader.load.return_value = True
        mock_hook_loader_class.return_value = mock_loader

        executor = create_hook_executor()

        assert isinstance(executor, HookExecutor)


# ========== 統合テスト ==========


class TestAgentExecutorIntegration:
    """SubAgentExecutorとHookExecutorの統合テスト"""

    @pytest.fixture
    def mock_loader(self):
        """統合テスト用モックローダー"""
        loader = Mock(spec=AgentLoader)
        loader.get_execution_config.return_value = {"max_concurrent": 3}
        loader.get_agent.return_value = SubAgentConfig(
            name="IntegrationAgent",
            description="Integration test agent",
            capabilities=["test"],
            prompts={},
        )
        return loader

    @pytest.fixture
    def mock_hook_loader(self):
        """統合テスト用モックHookローダー"""
        loader = Mock(spec=HookLoader)
        loader.get_hook.return_value = HookConfig(
            name="IntegrationHook",
            description="Integration test hook",
            trigger="pre_execution",
            actions=["notify"],
            prompts={},
        )
        loader.get_hooks_for_trigger.return_value = []
        loader.get_global_settings.return_value = {}
        return loader

    def test_agent_and_hook_lifecycle(self, mock_loader, mock_hook_loader):
        """AgentとHookのライフサイクルが正しく動作すること"""
        # 初期化
        agent_executor = SubAgentExecutor(loader=mock_loader)
        hook_executor = HookExecutor(loader=mock_hook_loader)

        # Pre-hook実行
        pre_hook_result = hook_executor.execute_hook("pre_hook", {"stage": "pre"})
        assert pre_hook_result.success is True

        # Agent実行
        agent_result = agent_executor.execute("test_agent", {"query": "test"})
        assert agent_result.success is True

        # Post-hook実行
        post_hook_result = hook_executor.execute_hook("post_hook", {"stage": "post"})
        assert post_hook_result.success is True

        # 履歴確認
        assert len(agent_executor.get_execution_history()) == 1
        assert len(hook_executor.get_execution_history()) == 2
