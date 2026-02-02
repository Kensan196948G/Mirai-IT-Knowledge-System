"""
ITSM Classifier
ITSMタイプ自動分類器
"""

import re
from typing import Any, Dict, List


class ITSMClassifier:
    """ITSMタイプ自動分類器"""

    def __init__(self):
        """分類ルールを初期化"""
        self.classification_rules = self._load_classification_rules()

    def classify(self, title: str, content: str) -> Dict[str, Any]:
        """
        タイトルと内容からITSMタイプを分類

        Args:
            title: タイトル
            content: 内容

        Returns:
            分類結果
        """
        text = (title + " " + content).lower()

        scores = {}
        for itsm_type, rules in self.classification_rules.items():
            score = self._calculate_score(text, rules)
            scores[itsm_type] = score

        # 最高スコアのITSMタイプを選択
        if not scores:
            return {
                "itsm_type": "Other",
                "confidence": 0.0,
                "scores": {},
                "reason": "分類ルールが適用されませんでした",
            }

        max_type = max(scores.items(), key=lambda x: x[1])
        itsm_type = max_type[0]
        confidence = max_type[1]

        # 信頼度が低い場合はOther
        if confidence < 0.3:
            itsm_type = "Other"
            reason = "明確なITSMタイプが判定できませんでした"
        else:
            reason = f"{itsm_type}の特徴的なキーワードが検出されました"

        return {
            "itsm_type": itsm_type,
            "confidence": round(confidence, 2),
            "scores": {k: round(v, 2) for k, v in scores.items()},
            "reason": reason,
        }

    def _load_classification_rules(self) -> Dict[str, Dict[str, Any]]:
        """分類ルールを定義"""
        return {
            "Incident": {
                "primary_keywords": [
                    "障害",
                    "インシデント",
                    "incident",
                    "エラー",
                    "error",
                    "異常",
                    "停止",
                    "ダウン",
                    "down",
                    "緊急",
                    "アラート",
                ],
                "secondary_keywords": ["復旧", "対応", "影響", "発生", "検知", "通知"],
                "weight_primary": 0.6,
                "weight_secondary": 0.4,
            },
            "Problem": {
                "primary_keywords": [
                    "問題",
                    "problem",
                    "根本原因",
                    "root cause",
                    "再発",
                    "傾向",
                    "分析",
                    "真因",
                    "恒久対策",
                ],
                "secondary_keywords": ["調査", "特定", "対策", "改善", "防止"],
                "weight_primary": 0.7,
                "weight_secondary": 0.3,
            },
            "Change": {
                "primary_keywords": [
                    "変更",
                    "change",
                    "改修",
                    "適用",
                    "パッチ",
                    "patch",
                    "更新",
                    "update",
                    "修正",
                ],
                "secondary_keywords": [
                    "計画",
                    "スケジュール",
                    "承認",
                    "ロールバック",
                    "テスト",
                    "リスク",
                    "影響評価",
                ],
                "weight_primary": 0.6,
                "weight_secondary": 0.4,
            },
            "Release": {
                "primary_keywords": [
                    "リリース",
                    "release",
                    "デプロイ",
                    "deploy",
                    "展開",
                    "本番",
                    "production",
                    "リリースノート",
                ],
                "secondary_keywords": [
                    "機能",
                    "バージョン",
                    "version",
                    "ビルド",
                    "build",
                    "ロールアウト",
                ],
                "weight_primary": 0.7,
                "weight_secondary": 0.3,
            },
            "Request": {
                "primary_keywords": [
                    "依頼",
                    "要求",
                    "request",
                    "リクエスト",
                    "申請",
                    "サービスリクエスト",
                    "サービス要求",
                ],
                "secondary_keywords": [
                    "承認",
                    "approval",
                    "許可",
                    "権限",
                    "アクセス",
                    "追加",
                    "削除",
                ],
                "weight_primary": 0.6,
                "weight_secondary": 0.4,
            },
        }

    def _calculate_score(self, text: str, rules: Dict[str, Any]) -> float:
        """テキストに対するスコアを計算"""
        primary_keywords = rules.get("primary_keywords", [])
        secondary_keywords = rules.get("secondary_keywords", [])
        weight_primary = rules.get("weight_primary", 0.5)
        weight_secondary = rules.get("weight_secondary", 0.5)

        # プライマリキーワードのマッチ数
        primary_matches = sum(1 for keyword in primary_keywords if keyword in text)
        primary_score = min(1.0, primary_matches / max(1, len(primary_keywords)))

        # セカンダリキーワードのマッチ数
        secondary_matches = sum(1 for keyword in secondary_keywords if keyword in text)
        secondary_score = min(1.0, secondary_matches / max(1, len(secondary_keywords)))

        # 重み付けスコア
        total_score = (primary_score * weight_primary) + (
            secondary_score * weight_secondary
        )

        return total_score

    def suggest_itsm_type(
        self, title: str, content: str, threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        複数のITSMタイプ候補を提案

        Args:
            title: タイトル
            content: 内容
            threshold: スコア閾値（これ以上のスコアのみ返す）

        Returns:
            候補リスト
        """
        result = self.classify(title, content)
        scores = result["scores"]

        # 閾値以上のものを抽出してソート
        candidates = [
            {
                "itsm_type": itsm_type,
                "score": score,
                "is_primary": itsm_type == result["itsm_type"],
            }
            for itsm_type, score in scores.items()
            if score >= threshold
        ]

        # スコア順にソート
        candidates.sort(key=lambda x: x["score"], reverse=True)

        return candidates
