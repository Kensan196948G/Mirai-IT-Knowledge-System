"""
Duplicate Check Hook
重複検知フック
"""

from typing import Any, Dict, List

from .base import BaseHook, HookResponse, HookResult


class DuplicateCheckHook(BaseHook):
    """重複検知フック"""

    def __init__(self, similarity_threshold: float = 0.85):
        super().__init__(name="duplicate-check", hook_type="quality", enabled=True)
        self.similarity_threshold = similarity_threshold

    def execute(self, context: Dict[str, Any]) -> HookResponse:
        """
        重複ナレッジの検知

        Args:
            context: {
                'title': str,
                'content': str,
                'existing_knowledge': list,
                'qa_result': dict (QAサブエージェントの結果)
            }

        Returns:
            フック実行結果
        """
        # QAサブエージェントの重複検知結果を利用
        qa_result = context.get("qa_result", {})
        duplicates = qa_result.get("duplicates", {})

        similar_knowledge = duplicates.get("similar_knowledge", [])
        high_similarity_count = duplicates.get("high_similarity_count", 0)

        # 高い類似度のナレッジがある場合は警告
        if high_similarity_count > 0:
            high_sim_items = [
                item
                for item in similar_knowledge
                if item.get("overall_similarity", 0) >= self.similarity_threshold
            ]

            return HookResponse(
                result=HookResult.WARNING,
                message=f"{high_similarity_count}件の高い類似度のナレッジが検出されました",
                details={
                    "threshold": self.similarity_threshold,
                    "similar_knowledge": high_sim_items,
                    "recommendation": "既存ナレッジとの統合または差別化を検討してください",
                },
                block_execution=False,  # 警告のみ、実行はブロックしない
            )

        # 中程度の類似度
        elif len(similar_knowledge) > 0:
            return HookResponse(
                result=HookResult.WARNING,
                message=f"{len(similar_knowledge)}件の類似ナレッジが見つかりました",
                details={
                    "similar_knowledge": similar_knowledge[:3],  # 上位3件
                    "recommendation": "関連ナレッジとして参照することを検討してください",
                },
                block_execution=False,
            )

        # 重複なし
        else:
            return HookResponse(
                result=HookResult.PASS,
                message="重複するナレッジは検出されませんでした",
                details={"threshold": self.similarity_threshold},
            )

    def set_threshold(self, threshold: float):
        """類似度閾値を設定"""
        if 0.0 <= threshold <= 1.0:
            self.similarity_threshold = threshold
        else:
            raise ValueError("閾値は0.0〜1.0の範囲で指定してください")
