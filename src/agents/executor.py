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
        start_time = time.time()
        try:
            agent = self.loader.get_agent(agent_id)
            if agent is None:
                return ExecutionResult(
                    success=False,
                    agent_name=agent_id,
                    output=None,
                    execution_time_ms=0,
                    error_message=f"Agent not found: {agent_id}",
                )
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
        BaseSubAgentパターンに従ってエージェントを実行
        """
        logger.info(f"SubAgent実行: {agent.name} - {agent.description}")

        # 1. エージェントインスタンスの取得
        #    実際の実装では、agentのclass_nameから動的にインスタンス化する
        #    例: agent_instance = self._load_agent_instance(agent)

        # 2. エージェント実行
        #    BaseSubAgent.execute()パターンを想定
        #    execute()は内部でprocess()を呼び出し、実行時間を自動計測する

        # 3. 入力データの検証
        if not isinstance(input_data, dict):
            raise ValueError(f"input_data must be dict, got {type(input_data)}")

        # 4. Capabilitiesチェック
        required_capabilities = input_data.get("required_capabilities", [])
        if required_capabilities:
            missing = set(required_capabilities) - set(agent.capabilities)
            if missing:
                logger.warning(
                    f"Agent [{agent.name}] missing capabilities: {missing}"
                )

        # 5. 実際の処理実行（プレースホルダー）
        #    実際の実装では、BaseSubAgent.execute(input_data)を呼び出す
        result = {
            "agent": agent.name,
            "capabilities": agent.capabilities,
            "input": input_data,
            "status": "processed",
            "output": f"Processed by {agent.name}",
            "metadata": {
                "description": agent.description,
                "priority": agent.priority,
            },
        }

        logger.info(f"SubAgent完了: {agent.name} - status: {result['status']}")
        return result

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
        start_time = time.time()
        try:
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
        """
        個別のアクションを実行
        BaseHookパターンに従ってアクションを処理
        """
        logger.debug(f"Hook [{hook.name}] アクション実行: {action}")

        # 1. アクション文字列のパース
        #    例: "notify:message" -> type="notify", params="message"
        parts = action.split(":", 1)
        action_type = parts[0].strip()
        action_params = parts[1].strip() if len(parts) > 1 else ""

        # 2. アクションタイプ別処理
        try:
            if action_type == "notify":
                # 通知アクション
                message = action_params or f"Hook [{hook.name}] triggered"
                logger.info(f"🔔 {message}")
                return {
                    "action": action,
                    "type": "notify",
                    "status": "executed",
                    "message": message,
                    "hook": hook.name,
                }

            elif action_type == "log":
                # ログ出力アクション
                log_level = action_params or "INFO"
                logger.log(
                    getattr(logging, log_level.upper(), logging.INFO),
                    f"Hook [{hook.name}] action: {action}",
                )
                return {
                    "action": action,
                    "type": "log",
                    "status": "executed",
                    "level": log_level,
                    "hook": hook.name,
                }

            elif action_type == "retry":
                # リトライアクション（プレースホルダー）
                retry_count = int(action_params) if action_params.isdigit() else 3
                logger.info(f"Retry action: max_retries={retry_count}")
                return {
                    "action": action,
                    "type": "retry",
                    "status": "configured",
                    "max_retries": retry_count,
                    "hook": hook.name,
                }

            elif action_type == "abort":
                # 中断アクション
                error_message = action_params or f"Aborted by hook: {hook.name}"
                logger.error(f"❌ {error_message}")
                return {
                    "action": action,
                    "type": "abort",
                    "status": "aborted",
                    "error": error_message,
                    "hook": hook.name,
                }

            elif action_type == "webhook":
                # Webhook呼び出し（プレースホルダー）
                webhook_url = action_params
                logger.info(f"Webhook call: {webhook_url}")
                return {
                    "action": action,
                    "type": "webhook",
                    "status": "called",
                    "url": webhook_url,
                    "hook": hook.name,
                }

            else:
                # 未知のアクションタイプ
                logger.warning(f"Unknown action type: {action_type}")
                return {
                    "action": action,
                    "type": "unknown",
                    "status": "skipped",
                    "reason": f"Unsupported action type: {action_type}",
                    "hook": hook.name,
                }

        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            return {
                "action": action,
                "type": action_type,
                "status": "failed",
                "error": str(e),
                "hook": hook.name,
            }

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
