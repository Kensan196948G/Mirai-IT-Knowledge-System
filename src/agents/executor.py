#!/usr/bin/env python3
"""
SubAgent and Hook Executor
SubAgentとHookの実行エンジン
"""

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from .loader import AgentLoader, HookConfig, HookLoader, SubAgentConfig

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """実行結果データクラス"""

    success: bool
    agent_name: str
    output: Any
    execution_time_ms: int
    error_message: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class SubAgentExecutor:
    """SubAgent実行エンジン"""

    def __init__(self, loader: Optional[AgentLoader] = None):
        self.loader = loader or AgentLoader()
        self.loader.load()
        self._executor = ThreadPoolExecutor(max_workers=self._get_max_workers())
        self._results: List[ExecutionResult] = []

    def _get_max_workers(self) -> int:
        """並列実行の最大ワーカー数を取得"""
        config = self.loader.get_execution_config()
        return config.get("max_concurrent", 3)

    def execute(
        self,
        agent_id: str,
        input_data: Dict[str, Any],
        callback: Optional[Callable[[ExecutionResult], None]] = None,
    ) -> ExecutionResult:
        """単一のSubAgentを実行"""
        agent = self.loader.get_agent(agent_id)
        if agent is None:
            return ExecutionResult(
                success=False,
                agent_name=agent_id,
                output=None,
                execution_time_ms=0,
                error_message=f"Agent not found: {agent_id}",
            )

        start_time = time.time()
        try:
            # 実際のAgent実行ロジック（プレースホルダー）
            output = self._execute_agent_logic(agent, input_data)

            execution_time_ms = int((time.time() - start_time) * 1000)
            result = ExecutionResult(
                success=True,
                agent_name=agent.name,
                output=output,
                execution_time_ms=execution_time_ms,
            )

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            result = ExecutionResult(
                success=False,
                agent_name=agent.name,
                output=None,
                execution_time_ms=execution_time_ms,
                error_message=str(e),
            )
            logger.error(f"SubAgent実行エラー [{agent.name}]: {e}")

        self._results.append(result)

        if callback:
            callback(result)

        return result

    def _execute_agent_logic(
        self, agent: SubAgentConfig, input_data: Dict[str, Any]
    ) -> Any:
        """
        実際のAgent処理ロジック
        ここでClaude APIを呼び出す等の処理を行う
        """
        # プレースホルダー実装
        logger.info(f"SubAgent実行: {agent.name} - {agent.description}")

        # 実際の実装では、ここでClaude APIを呼び出す
        return {
            "agent": agent.name,
            "capabilities": agent.capabilities,
            "input": input_data,
            "status": "processed",
        }

    async def execute_parallel(
        self, agent_ids: List[str], input_data: Dict[str, Any]
    ) -> List[ExecutionResult]:
        """複数のSubAgentを並列実行"""
        config = self.loader.get_execution_config()
        if not config.get("parallel_enabled", True):
            # 並列実行が無効の場合は順次実行
            return [self.execute(aid, input_data) for aid in agent_ids]

        loop = asyncio.get_event_loop()
        futures = [
            loop.run_in_executor(self._executor, self.execute, agent_id, input_data)
            for agent_id in agent_ids
        ]

        results = await asyncio.gather(*futures)
        return list(results)

    def execute_by_priority(
        self, input_data: Dict[str, Any], min_priority: str = "low"
    ) -> List[ExecutionResult]:
        """優先度順にSubAgentを実行"""
        priority_order = ["critical", "high", "medium", "low"]
        min_idx = priority_order.index(min_priority)

        results = []
        for priority in priority_order[: min_idx + 1]:
            agents = self.loader.get_agents_by_priority(priority)
            for agent in agents:
                if agent.enabled:
                    result = self.execute(
                        agent.name.lower().replace(" ", "_"), input_data
                    )
                    results.append(result)

        return results

    def get_execution_history(self) -> List[ExecutionResult]:
        """実行履歴を取得"""
        return self._results.copy()

    def clear_history(self):
        """実行履歴をクリア"""
        self._results.clear()


class HookExecutor:
    """Hook実行エンジン"""

    def __init__(self, loader: Optional[HookLoader] = None):
        self.loader = loader or HookLoader()
        self.loader.load()
        self._results: List[ExecutionResult] = []

    def execute_hook(self, hook_id: str, context: Dict[str, Any]) -> ExecutionResult:
        """単一のHookを実行"""
        hook = self.loader.get_hook(hook_id)
        if hook is None:
            return ExecutionResult(
                success=False,
                agent_name=hook_id,
                output=None,
                execution_time_ms=0,
                error_message=f"Hook not found: {hook_id}",
            )

        if not hook.enabled:
            return ExecutionResult(
                success=True,
                agent_name=hook.name,
                output={"skipped": True, "reason": "Hook is disabled"},
                execution_time_ms=0,
            )

        start_time = time.time()
        try:
            output = self._execute_hook_logic(hook, context)
            execution_time_ms = int((time.time() - start_time) * 1000)

            # タイムアウトチェック
            if execution_time_ms > hook.timeout_seconds * 1000:
                logger.warning(
                    f"Hook [{hook.name}] タイムアウト超過: {execution_time_ms}ms"
                )

            result = ExecutionResult(
                success=True,
                agent_name=hook.name,
                output=output,
                execution_time_ms=execution_time_ms,
            )

        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            result = ExecutionResult(
                success=False,
                agent_name=hook.name,
                output=None,
                execution_time_ms=execution_time_ms,
                error_message=str(e),
            )
            logger.error(f"Hook実行エラー [{hook.name}]: {e}")

        self._results.append(result)
        return result

    def _execute_hook_logic(self, hook: HookConfig, context: Dict[str, Any]) -> Any:
        """
        実際のHook処理ロジック
        """
        logger.info(f"Hook実行: {hook.name} - trigger: {hook.trigger}")

        # アクションを順次実行
        action_results = []
        for action in hook.actions:
            action_result = self._execute_action(action, hook, context)
            action_results.append(action_result)

        return {
            "hook": hook.name,
            "trigger": hook.trigger,
            "actions": action_results,
            "context": context,
        }

    def _execute_action(
        self, action: str, hook: HookConfig, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """個別のアクションを実行"""
        # プレースホルダー実装
        return {"action": action, "status": "executed", "hook": hook.name}

    def trigger(
        self, trigger_name: str, context: Dict[str, Any]
    ) -> List[ExecutionResult]:
        """特定のトリガーに関連する全Hookを実行"""
        hooks = self.loader.get_hooks_for_trigger(trigger_name)

        global_settings = self.loader.get_global_settings()
        parallel = global_settings.get("parallel_execution", True)

        if parallel and len(hooks) > 1:
            # 並列実行（簡易版）
            results = []
            for hook in hooks:
                result = self.execute_hook(hook.name.lower().replace(" ", "_"), context)
                results.append(result)
            return results
        else:
            # 順次実行
            return [
                self.execute_hook(h.name.lower().replace(" ", "_"), context)
                for h in hooks
            ]

    def get_execution_history(self) -> List[ExecutionResult]:
        """実行履歴を取得"""
        return self._results.copy()

    def clear_history(self):
        """実行履歴をクリア"""
        self._results.clear()


# ファクトリー関数
def create_subagent_executor() -> SubAgentExecutor:
    """SubAgentExecutorのファクトリー"""
    return SubAgentExecutor()


def create_hook_executor() -> HookExecutor:
    """HookExecutorのファクトリー"""
    return HookExecutor()
