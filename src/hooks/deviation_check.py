"""
Deviation Check Hook
ITSM原則からの逸脱検知フック
"""

from typing import Dict, Any, List
from .base import BaseHook, HookResponse, HookResult


class DeviationCheckHook(BaseHook):
    """逸脱検知フック"""

    def __init__(self):
        super().__init__(
            name="deviation-check",
            hook_type="quality",
            enabled=True
        )

    def execute(self, context: Dict[str, Any]) -> HookResponse:
        """
        ITSM原則からの逸脱を検知

        Args:
            context: {
                'itsm_type': str,
                'itsm_expert_result': dict (ITSMExpertサブエージェントの結果)
            }

        Returns:
            フック実行結果
        """
        # ITSMExpertサブエージェントの結果を利用
        itsm_expert_result = context.get('itsm_expert_result', {})
        deviations = itsm_expert_result.get('deviations', [])
        compliance_score = itsm_expert_result.get('compliance_score', 1.0)

        # エラーレベルの逸脱がある場合
        error_deviations = [d for d in deviations if d.get('severity') == 'error']
        if error_deviations:
            return HookResponse(
                result=HookResult.ERROR,
                message=f"{len(error_deviations)}件の重大な逸脱が検出されました",
                details={
                    'deviations': error_deviations,
                    'compliance_score': compliance_score,
                    'recommendation': 'ITSM原則に準拠するよう内容を修正してください'
                },
                block_execution=False  # 警告のみ、強制ブロックはしない
            )

        # 警告レベルの逸脱がある場合
        warning_deviations = [d for d in deviations if d.get('severity') == 'warning']
        if warning_deviations:
            return HookResponse(
                result=HookResult.WARNING,
                message=f"{len(warning_deviations)}件の逸脱が検出されました",
                details={
                    'deviations': warning_deviations,
                    'compliance_score': compliance_score,
                    'recommendation': '可能であればITSM原則に準拠するよう改善してください'
                },
                block_execution=False
            )

        # ITSM準拠スコアが低い場合
        elif compliance_score < 0.7:
            return HookResponse(
                result=HookResult.WARNING,
                message=f"ITSM準拠度が低いです: {int(compliance_score*100)}%",
                details={
                    'compliance_score': compliance_score,
                    'principle_checks': itsm_expert_result.get('principle_checks', []),
                    'recommendation': 'ITSM原則に基づいた情報を追加することを推奨します'
                },
                block_execution=False
            )

        # 問題なし
        else:
            return HookResponse(
                result=HookResult.PASS,
                message=f"ITSM原則に準拠しています（準拠度: {int(compliance_score*100)}%）",
                details={
                    'compliance_score': compliance_score,
                    'deviations': []
                }
            )
