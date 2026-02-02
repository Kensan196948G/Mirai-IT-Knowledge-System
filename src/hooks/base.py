"""
Hook Base Class
フック基底クラス
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Optional


class HookResult(Enum):
    """フック実行結果"""

    PASS = "pass"
    WARNING = "warning"
    ERROR = "error"


class HookResponse:
    """フック実行レスポンス"""

    def __init__(
        self,
        result: HookResult,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        block_execution: bool = False,
    ):
        """
        Args:
            result: 実行結果（pass/warning/error）
            message: メッセージ
            details: 詳細情報
            block_execution: 実行をブロックするか（Trueの場合、ワークフローを中断）
        """
        self.result = result
        self.message = message
        self.details = details or {}
        self.block_execution = block_execution

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "result": self.result.value,
            "message": self.message,
            "details": self.details,
            "block_execution": self.block_execution,
        }

    def __repr__(self) -> str:
        return f"<HookResponse result={self.result.value} block={self.block_execution}>"


class BaseHook(ABC):
    """フック基底クラス"""

    def __init__(self, name: str, hook_type: str, enabled: bool = True):
        """
        Args:
            name: フック名
            hook_type: フックタイプ（pre-task/on-change/post-task/quality）
            enabled: 有効/無効
        """
        self.name = name
        self.hook_type = hook_type
        self.enabled = enabled

    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> HookResponse:
        """
        フックを実行

        Args:
            context: 実行コンテキスト

        Returns:
            フック実行結果
        """
        pass

    def is_enabled(self) -> bool:
        """フックが有効かどうか"""
        return self.enabled

    def set_enabled(self, enabled: bool):
        """フックの有効/無効を設定"""
        self.enabled = enabled

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name='{self.name}' type='{self.hook_type}' enabled={self.enabled}>"
