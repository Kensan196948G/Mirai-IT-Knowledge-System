#!/usr/bin/env python3
"""
Agent and Hook Configuration Loader
設定ファイルからSubAgentとHookの定義を読み込む
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


@dataclass
class SubAgentConfig:
    """SubAgent設定データクラス"""

    name: str
    description: str
    capabilities: List[str]
    prompts: Dict[str, str]
    priority: str = "medium"
    model: str = "claude-sonnet-4-20250514"
    enabled: bool = True


@dataclass
class HookConfig:
    """Hook設定データクラス"""

    name: str
    description: str
    trigger: str
    actions: List[str]
    prompts: Dict[str, str]
    enabled: bool = True
    timeout_seconds: int = 30
    extra_config: Dict[str, Any] = field(default_factory=dict)


class AgentLoader:
    """SubAgent設定ローダー"""

    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            config_path = (
                Path(__file__).parent.parent.parent
                / "config"
                / "agents"
                / "subagents.yaml"
            )
        self.config_path = config_path
        self._agents: Dict[str, SubAgentConfig] = {}
        self._execution_config: Dict[str, Any] = {}
        self._loaded = False

    def load(self) -> bool:
        """設定ファイルを読み込む"""
        try:
            if not self.config_path.exists():
                logger.warning(
                    f"SubAgent設定ファイルが見つかりません: {self.config_path}"
                )
                return False

            with open(self.config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            # SubAgent定義を読み込み
            for agent_id, agent_data in config.get("subagents", {}).items():
                self._agents[agent_id] = SubAgentConfig(
                    name=agent_data.get("name", agent_id),
                    description=agent_data.get("description", ""),
                    capabilities=agent_data.get("capabilities", []),
                    prompts=agent_data.get("prompts", {}),
                    priority=agent_data.get("priority", "medium"),
                    model=agent_data.get("model", "claude-sonnet-4-20250514"),
                    enabled=agent_data.get("enabled", True),
                )

            # 実行設定を読み込み
            self._execution_config = config.get("execution", {})

            self._loaded = True
            logger.info(
                f"SubAgent設定を読み込みました: {len(self._agents)}エージェント"
            )
            return True

        except Exception as e:
            logger.error(f"SubAgent設定の読み込みに失敗: {e}")
            return False

    def get_agent(self, agent_id: str) -> Optional[SubAgentConfig]:
        """指定されたIDのSubAgentを取得"""
        if not self._loaded:
            self.load()
        return self._agents.get(agent_id)

    def get_all_agents(self) -> Dict[str, SubAgentConfig]:
        """全SubAgentを取得"""
        if not self._loaded:
            self.load()
        return self._agents

    def get_agents_by_priority(self, priority: str) -> List[SubAgentConfig]:
        """優先度でSubAgentをフィルタ"""
        if not self._loaded:
            self.load()
        return [a for a in self._agents.values() if a.priority == priority]

    def get_execution_config(self) -> Dict[str, Any]:
        """実行設定を取得"""
        if not self._loaded:
            self.load()
        return self._execution_config


class HookLoader:
    """Hook設定ローダー"""

    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            config_path = (
                Path(__file__).parent.parent.parent / "config" / "agents" / "hooks.yaml"
            )
        self.config_path = config_path
        self._hooks: Dict[str, HookConfig] = {}
        self._triggers: Dict[str, List[str]] = {}
        self._global_settings: Dict[str, Any] = {}
        self._loaded = False

    def load(self) -> bool:
        """設定ファイルを読み込む"""
        try:
            if not self.config_path.exists():
                logger.warning(f"Hook設定ファイルが見つかりません: {self.config_path}")
                return False

            with open(self.config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            # Hook定義を読み込み
            for hook_id, hook_data in config.get("hooks", {}).items():
                extra_config = {
                    k: v
                    for k, v in hook_data.items()
                    if k
                    not in [
                        "name",
                        "description",
                        "trigger",
                        "actions",
                        "prompts",
                        "enabled",
                        "timeout_seconds",
                    ]
                }

                self._hooks[hook_id] = HookConfig(
                    name=hook_data.get("name", hook_id),
                    description=hook_data.get("description", ""),
                    trigger=hook_data.get("trigger", ""),
                    actions=hook_data.get("actions", []),
                    prompts=hook_data.get("prompts", {}),
                    enabled=hook_data.get("enabled", True),
                    timeout_seconds=hook_data.get("timeout_seconds", 30),
                    extra_config=extra_config,
                )

            # イベントトリガーを読み込み
            self._triggers = config.get("event_triggers", {})

            # グローバル設定を読み込み
            self._global_settings = config.get("global_settings", {})

            self._loaded = True
            logger.info(f"Hook設定を読み込みました: {len(self._hooks)}フック")
            return True

        except Exception as e:
            logger.error(f"Hook設定の読み込みに失敗: {e}")
            return False

    def get_hook(self, hook_id: str) -> Optional[HookConfig]:
        """指定されたIDのHookを取得"""
        if not self._loaded:
            self.load()
        return self._hooks.get(hook_id)

    def get_all_hooks(self) -> Dict[str, HookConfig]:
        """全Hookを取得"""
        if not self._loaded:
            self.load()
        return self._hooks

    def get_hooks_for_trigger(self, trigger: str) -> List[HookConfig]:
        """特定のトリガーに関連するHookを取得"""
        if not self._loaded:
            self.load()

        hook_ids = self._triggers.get(trigger, [])
        return [self._hooks[hid] for hid in hook_ids if hid in self._hooks]

    def get_enabled_hooks(self) -> List[HookConfig]:
        """有効なHookのみを取得"""
        if not self._loaded:
            self.load()
        return [h for h in self._hooks.values() if h.enabled]

    def get_global_settings(self) -> Dict[str, Any]:
        """グローバル設定を取得"""
        if not self._loaded:
            self.load()
        return self._global_settings
