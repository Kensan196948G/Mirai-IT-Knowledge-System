"""
Pre-Task Hook
サブエージェント割り当て前に実行されるフック
"""

from typing import Dict, Any, List
from .base import BaseHook, HookResponse, HookResult


class PreTaskHook(BaseHook):
    """タスク前処理フック"""

    def __init__(self):
        super().__init__(
            name="pre-task",
            hook_type="pre-task",
            enabled=True
        )

    def execute(self, context: Dict[str, Any]) -> HookResponse:
        """
        タスク実行前の検証とサブエージェント割り当て

        Args:
            context: {
                'title': str,
                'content': str,
                'itsm_type': str,
                'available_subagents': list
            }

        Returns:
            フック実行結果
        """
        # 入力データの検証
        validation_result = self._validate_input(context)
        if not validation_result['valid']:
            return HookResponse(
                result=HookResult.ERROR,
                message=f"入力データが不正です: {validation_result['error']}",
                block_execution=True
            )

        # サブエージェントの割り当て推奨
        recommended_subagents = self._recommend_subagents(context)

        return HookResponse(
            result=HookResult.PASS,
            message="タスク前チェック完了",
            details={
                'recommended_subagents': recommended_subagents,
                'validation': validation_result
            }
        )

    def _validate_input(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """入力データを検証"""
        title = context.get('title', '')
        content = context.get('content', '')
        itsm_type = context.get('itsm_type', '')

        # 必須フィールドチェック
        if not title:
            return {'valid': False, 'error': 'タイトルが空です'}

        if not content:
            return {'valid': False, 'error': '内容が空です'}

        if len(title) < 5:
            return {'valid': False, 'error': 'タイトルが短すぎます（最低5文字）'}

        if len(content) < 20:
            return {'valid': False, 'error': '内容が短すぎます（最低20文字）'}

        # ITSMタイプの検証
        valid_itsm_types = ['Incident', 'Problem', 'Change', 'Release', 'Request', 'Other']
        if itsm_type and itsm_type not in valid_itsm_types:
            return {'valid': False, 'error': f'無効なITSMタイプ: {itsm_type}'}

        return {
            'valid': True,
            'title_length': len(title),
            'content_length': len(content),
            'itsm_type': itsm_type
        }

    def _recommend_subagents(self, context: Dict[str, Any]) -> List[Dict[str, str]]:
        """実行すべきサブエージェントを推奨"""
        recommendations = []

        # 常に実行すべきコアサブエージェント
        core_subagents = [
            {'name': 'architect', 'reason': '設計整合性チェック', 'priority': 'high'},
            {'name': 'knowledge_curator', 'reason': 'ナレッジ整理・分類', 'priority': 'high'},
            {'name': 'itsm_expert', 'reason': 'ITSM妥当性チェック', 'priority': 'high'},
            {'name': 'qa', 'reason': '品質保証・重複検知', 'priority': 'high'},
            {'name': 'documenter', 'reason': 'ドキュメント整形', 'priority': 'medium'}
        ]
        recommendations.extend(core_subagents)

        # 内容に応じた追加サブエージェント
        content_lower = context.get('content', '').lower()

        # DevOpsサブエージェントの推奨判定
        devops_keywords = [
            'コマンド', 'command', 'スクリプト', 'script', '自動化', 'automation',
            'デプロイ', 'deploy', 'リリース', 'release'
        ]
        if any(keyword in content_lower for keyword in devops_keywords):
            recommendations.append({
                'name': 'devops',
                'reason': '技術分析・自動化提案が必要',
                'priority': 'medium'
            })

        return recommendations
