"""
SubAgent Base Class
サブエージェント基底クラス
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
import time


class SubAgentResult:
    """サブエージェント実行結果"""

    def __init__(
        self,
        status: str,  # 'success', 'failed', 'warning'
        data: Dict[str, Any],
        message: Optional[str] = None,
        execution_time_ms: Optional[int] = None
    ):
        self.status = status
        self.data = data
        self.message = message
        self.execution_time_ms = execution_time_ms

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'status': self.status,
            'data': self.data,
            'message': self.message,
            'execution_time_ms': self.execution_time_ms
        }


class BaseSubAgent(ABC):
    """サブエージェント基底クラス"""

    def __init__(self, name: str, role: str, priority: str = 'medium'):
        """
        Args:
            name: サブエージェント名
            role: 役割
            priority: 優先度 ('high', 'medium', 'low')
        """
        self.name = name
        self.role = role
        self.priority = priority

    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> SubAgentResult:
        """
        メイン処理

        Args:
            input_data: 入力データ

        Returns:
            処理結果
        """
        pass

    def execute(self, input_data: Dict[str, Any]) -> SubAgentResult:
        """
        実行ラッパー（実行時間計測付き）

        Args:
            input_data: 入力データ

        Returns:
            処理結果
        """
        start_time = time.time()

        try:
            result = self.process(input_data)
            execution_time_ms = int((time.time() - start_time) * 1000)
            result.execution_time_ms = execution_time_ms
            return result
        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            return SubAgentResult(
                status='failed',
                data={},
                message=f"エラーが発生しました: {str(e)}",
                execution_time_ms=execution_time_ms
            )

    def validate_input(self, input_data: Dict[str, Any], required_keys: list) -> bool:
        """
        入力データの検証

        Args:
            input_data: 検証する入力データ
            required_keys: 必須キーのリスト

        Returns:
            検証結果
        """
        return all(key in input_data for key in required_keys)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name='{self.name}' role='{self.role}' priority='{self.priority}'>"
