"""
Architect SubAgent
全体設計整合・判断統制を担当
"""

from typing import Any, Dict

from .base import BaseSubAgent, SubAgentResult


class ArchitectSubAgent(BaseSubAgent):
    """アーキテクト・サブエージェント"""

    def __init__(self):
        super().__init__(name="architect", role="design_coherence", priority="high")

    def process(self, input_data: Dict[str, Any]) -> SubAgentResult:
        """
        全体設計の整合性チェックと判断統制

        Args:
            input_data: {
                'title': str,
                'content': str,
                'itsm_type': str,
                'existing_knowledge': list (オプション)
            }

        Returns:
            設計整合性の評価結果
        """
        if not self.validate_input(input_data, ["title", "content"]):
            return SubAgentResult(
                status="failed",
                data={},
                message="必須フィールドが不足しています: title, content",
            )

        title = input_data.get("title", "")
        content = input_data.get("content", "")
        itsm_type = input_data.get("itsm_type", "")
        existing_knowledge = input_data.get("existing_knowledge", [])

        # 設計整合性評価
        coherence_checks = []

        # 1. タイトルと内容の整合性
        title_content_coherence = self._check_title_content_coherence(title, content)
        coherence_checks.append(title_content_coherence)

        # 2. ITSMタイプの妥当性
        itsm_validity = self._check_itsm_validity(itsm_type, content)
        coherence_checks.append(itsm_validity)

        # 3. 既存ナレッジとの整合性
        if existing_knowledge:
            knowledge_coherence = self._check_knowledge_coherence(
                content, existing_knowledge
            )
            coherence_checks.append(knowledge_coherence)

        # 4. 設計原則への準拠
        design_principles = self._check_design_principles(content)
        coherence_checks.append(design_principles)

        # 総合判断
        all_passed = all(check["passed"] for check in coherence_checks)
        warnings = [check for check in coherence_checks if not check["passed"]]

        status = "success" if all_passed else "warning"
        message = (
            "設計整合性チェック完了"
            if all_passed
            else f"{len(warnings)}件の懸念事項があります"
        )

        return SubAgentResult(
            status=status,
            data={
                "coherence_score": sum(1 for c in coherence_checks if c["passed"])
                / len(coherence_checks),
                "checks": coherence_checks,
                "warnings": warnings,
                "recommendations": self._generate_recommendations(warnings),
            },
            message=message,
        )

    def _check_title_content_coherence(
        self, title: str, content: str
    ) -> Dict[str, Any]:
        """タイトルと内容の整合性をチェック"""
        # 簡易的な実装: タイトルの主要キーワードが内容に含まれているか
        title_words = set(title.lower().split())
        content_lower = content.lower()

        # 一般的なストップワードを除外
        stop_words = {
            "の",
            "に",
            "を",
            "は",
            "が",
            "で",
            "と",
            "から",
            "まで",
            "について",
            "に関する",
        }
        title_keywords = title_words - stop_words

        if not title_keywords:
            return {
                "check_name": "タイトルと内容の整合性",
                "passed": True,
                "message": "タイトルが一般的すぎるため、スキップしました",
            }

        # キーワードの含有率をチェック
        matched_keywords = sum(
            1 for keyword in title_keywords if keyword in content_lower
        )
        match_rate = matched_keywords / len(title_keywords) if title_keywords else 0

        passed = match_rate >= 0.5  # 50%以上のキーワードが含まれていればOK

        return {
            "check_name": "タイトルと内容の整合性",
            "passed": passed,
            "message": (
                f"タイトルキーワードの{int(match_rate*100)}%が内容に含まれています"
                if passed
                else f"タイトルと内容の関連性が低い可能性があります（{int(match_rate*100)}%）"
            ),
            "details": {
                "title_keywords": list(title_keywords),
                "match_rate": match_rate,
            },
        }

    def _check_itsm_validity(self, itsm_type: str, content: str) -> Dict[str, Any]:
        """ITSMタイプの妥当性をチェック"""
        valid_types = ["Incident", "Problem", "Change", "Release", "Request", "Other"]

        if not itsm_type or itsm_type not in valid_types:
            return {
                "check_name": "ITSMタイプの妥当性",
                "passed": False,
                "message": f"無効なITSMタイプです: {itsm_type}",
                "details": {"valid_types": valid_types},
            }

        # ITSMタイプと内容の関連性をチェック
        type_keywords = {
            "Incident": ["障害", "エラー", "停止", "異常", "アラート", "緊急"],
            "Problem": ["根本原因", "再発", "傾向", "分析", "対策"],
            "Change": ["変更", "改修", "適用", "リリース", "デプロイ"],
            "Release": ["リリース", "デプロイ", "本番", "展開"],
            "Request": ["依頼", "要求", "リクエスト", "申請"],
        }

        keywords = type_keywords.get(itsm_type, [])
        if not keywords:
            return {
                "check_name": "ITSMタイプの妥当性",
                "passed": True,
                "message": f'ITSMタイプ "{itsm_type}" は有効です',
            }

        content_lower = content.lower()
        matched = any(keyword in content_lower for keyword in keywords)

        return {
            "check_name": "ITSMタイプの妥当性",
            "passed": matched,
            "message": (
                f'ITSMタイプ "{itsm_type}" と内容が整合しています'
                if matched
                else f'ITSMタイプ "{itsm_type}" と内容の整合性を確認してください'
            ),
            "details": {
                "itsm_type": itsm_type,
                "expected_keywords": keywords,
                "matched": matched,
            },
        }

    def _check_knowledge_coherence(
        self, content: str, existing_knowledge: list
    ) -> Dict[str, Any]:
        """既存ナレッジとの整合性をチェック"""
        # 既存ナレッジとの矛盾や重複をチェック
        # 簡易実装: 類似度が高すぎる場合は警告
        similar_count = len(
            [
                k
                for k in existing_knowledge
                if self._calculate_similarity(content, k.get("content", "")) > 0.8
            ]
        )

        passed = similar_count == 0

        return {
            "check_name": "既存ナレッジとの整合性",
            "passed": passed,
            "message": (
                "既存ナレッジとの整合性OK"
                if passed
                else f"{similar_count}件の類似ナレッジが存在します"
            ),
            "details": {"similar_count": similar_count},
        }

    def _check_design_principles(self, content: str) -> Dict[str, Any]:
        """設計原則への準拠をチェック"""
        # ITSMベストプラクティスへの準拠をチェック
        principles = {
            "原因と対策が明確": ["原因", "対策", "対応", "解決"],
            "再現手順が記載": ["手順", "ステップ", "方法", "操作"],
            "影響範囲が明確": ["影響", "範囲", "スコープ", "対象"],
        }

        content_lower = content.lower()
        checks = []

        for principle, keywords in principles.items():
            matched = any(keyword in content_lower for keyword in keywords)
            checks.append({"principle": principle, "matched": matched})

        passed_count = sum(1 for check in checks if check["matched"])
        passed = (
            passed_count >= len(principles) * 0.6
        )  # 60%以上の原則に準拠していればOK

        return {
            "check_name": "設計原則への準拠",
            "passed": passed,
            "message": f"{passed_count}/{len(principles)}の設計原則に準拠しています",
            "details": {"principles": checks},
        }

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """2つのテキストの類似度を計算（簡易版）"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union) if union else 0.0

    def _generate_recommendations(self, warnings: list) -> list:
        """警告に基づいた推奨事項を生成"""
        recommendations = []

        for warning in warnings:
            check_name = warning.get("check_name", "")

            if check_name == "タイトルと内容の整合性":
                recommendations.append(
                    "タイトルを内容に即したものに修正することを推奨します"
                )
            elif check_name == "ITSMタイプの妥当性":
                recommendations.append(
                    "ITSMタイプの見直し、または内容の明確化を推奨します"
                )
            elif check_name == "既存ナレッジとの整合性":
                recommendations.append(
                    "既存の類似ナレッジとの統合または差別化を検討してください"
                )
            elif check_name == "設計原則への準拠":
                recommendations.append(
                    "原因・対策・影響範囲などの情報を追加することを推奨します"
                )

        return recommendations
