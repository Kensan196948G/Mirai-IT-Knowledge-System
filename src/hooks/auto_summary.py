"""
Auto Summary Hook
3行要約自動生成フック
"""

from typing import Any, Dict

from .base import BaseHook, HookResponse, HookResult


class AutoSummaryHook(BaseHook):
    """自動要約フック"""

    def __init__(self, max_lines: int = 3):
        super().__init__(name="auto-summary", hook_type="quality", enabled=True)
        self.max_lines = max_lines

    def execute(self, context: Dict[str, Any]) -> HookResponse:
        """
        3行要約の自動生成

        Args:
            context: {
                'documenter_result': dict (Documenterサブエージェントの結果)
            }

        Returns:
            フック実行結果
        """
        # Documenterサブエージェントの結果を利用
        documenter_result = context.get("documenter_result", {})
        summary_3lines = documenter_result.get("summary_3lines", [])

        # 要約が正常に生成されているか確認
        if not summary_3lines:
            return HookResponse(
                result=HookResult.WARNING,
                message="3行要約の生成に失敗しました",
                details={"summary_3lines": []},
                block_execution=False,
            )

        # 要約の各行が空でないか確認
        valid_lines = [line for line in summary_3lines if line and line.strip()]
        if len(valid_lines) < self.max_lines:
            return HookResponse(
                result=HookResult.WARNING,
                message=f"3行要約が不完全です（{len(valid_lines)}/{self.max_lines}行）",
                details={
                    "summary_3lines": summary_3lines,
                    "valid_line_count": len(valid_lines),
                },
                block_execution=False,
            )

        # 正常に生成されている
        return HookResponse(
            result=HookResult.PASS,
            message="3行要約が正常に生成されました",
            details={"summary_3lines": summary_3lines, "line_count": len(valid_lines)},
        )
