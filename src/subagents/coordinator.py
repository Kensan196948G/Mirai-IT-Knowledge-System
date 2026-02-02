"""
Coordinator SubAgent
全体調整と抜け漏れ確認を担当
"""

from typing import Any, Dict, List

from .base import BaseSubAgent, SubAgentResult


class CoordinatorSubAgent(BaseSubAgent):
    """コーディネーター・サブエージェント"""

    def __init__(self):
        super().__init__(
            name="coordinator", role="coordination_review", priority="medium"
        )

    def process(self, input_data: Dict[str, Any]) -> SubAgentResult:
        """
        調整観点での抜け漏れ確認

        Args:
            input_data: {
                'title': str,
                'content': str,
                'itsm_type': str (オプション)
            }

        Returns:
            調整チェック結果
        """
        if not self.validate_input(input_data, ["title", "content"]):
            return SubAgentResult(
                status="failed", data={}, message="必須フィールドが不足しています"
            )

        title = input_data.get("title", "")
        content = input_data.get("content", "")
        itsm_type = input_data.get("itsm_type", "Other")

        required_context = self._required_context_checks()
        missing_items = self._find_missing_items(content, required_context)
        coordination_notes = self._build_coordination_notes(missing_items)
        risk_flags = self._build_risk_flags(title, itsm_type, missing_items)
        next_actions = self._suggest_next_actions(missing_items)

        status = "warning" if missing_items else "success"
        message = self._build_message(missing_items)

        return SubAgentResult(
            status=status,
            data={
                "coordination_notes": coordination_notes,
                "missing_items": missing_items,
                "risk_flags": risk_flags,
                "next_actions": next_actions,
            },
            message=message,
        )

    def _required_context_checks(self) -> Dict[str, List[str]]:
        return {
            "impact_scope": ["影響範囲", "影響", "影響度", "影響先"],
            "owner": ["担当", "責任者", "オーナー", "担当者"],
            "timeline": ["時刻", "日時", "期限", "復旧", "完了"],
            "mitigation": ["対策", "回避", "復旧", "暫定", "ロールバック"],
        }

    def _find_missing_items(
        self, content: str, required_context: Dict[str, List[str]]
    ) -> List[str]:
        missing_items = []
        for key, keywords in required_context.items():
            if not any(keyword in content for keyword in keywords):
                missing_items.append(key)
        return missing_items

    def _build_coordination_notes(self, missing_items: List[str]) -> List[str]:
        notes = []

        if "impact_scope" in missing_items:
            notes.append("影響範囲（対象システム・ユーザー）を明記してください")
        if "owner" in missing_items:
            notes.append("担当者/責任者の明記を推奨します")
        if "timeline" in missing_items:
            notes.append("発生/復旧の時刻や期限を追記してください")
        if "mitigation" in missing_items:
            notes.append("暫定対策や回避策の有無を記載してください")

        return notes

    def _build_risk_flags(
        self, title: str, itsm_type: str, missing_items: List[str]
    ) -> List[str]:
        risk_flags = []
        if not missing_items:
            return risk_flags

        if "impact_scope" in missing_items:
            risk_flags.append("影響範囲が不明確なため周知漏れのリスクがあります")
        if "owner" in missing_items:
            risk_flags.append("担当者が未確定のため対応遅延のリスクがあります")
        if itsm_type in ["Change", "Release"] and "mitigation" in missing_items:
            risk_flags.append("変更/リリースの巻き戻し手順が未記載です")

        if len(title) < 10:
            risk_flags.append("タイトルが短く、共有時の誤解につながる可能性があります")

        return risk_flags

    def _suggest_next_actions(self, missing_items: List[str]) -> List[str]:
        actions = []

        if "impact_scope" in missing_items:
            actions.append("影響範囲と関係者リストを追記する")
        if "owner" in missing_items:
            actions.append("担当者/レビューアの割り当てを行う")
        if "timeline" in missing_items:
            actions.append("タイムライン（発生〜復旧）を整理する")
        if "mitigation" in missing_items:
            actions.append("暫定対策・恒久対策の整理を行う")

        return actions

    def _build_message(self, missing_items: List[str]) -> str:
        if not missing_items:
            return "調整項目の抜け漏れは見つかりませんでした"

        return f"調整項目の不足を確認しました: {len(missing_items)}件"
