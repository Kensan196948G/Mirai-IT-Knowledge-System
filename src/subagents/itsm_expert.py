"""
ITSM Expert SubAgent
ITSM妥当性・逸脱検知を担当
"""

from typing import Dict, Any, List
from .base import BaseSubAgent, SubAgentResult


class ITSMExpertSubAgent(BaseSubAgent):
    """ITSM専門家・サブエージェント"""

    def __init__(self):
        super().__init__(
            name="itsm_expert",
            role="compliance",
            priority="high"
        )
        # ITSM原則定義
        self.itsm_principles = self._load_itsm_principles()

    def process(self, input_data: Dict[str, Any]) -> SubAgentResult:
        """
        ITSM妥当性チェックと逸脱検知

        Args:
            input_data: {
                'title': str,
                'content': str,
                'itsm_type': str
            }

        Returns:
            ITSM準拠性評価結果
        """
        if not self.validate_input(input_data, ['content', 'itsm_type']):
            return SubAgentResult(
                status='failed',
                data={},
                message="必須フィールドが不足しています"
            )

        content = input_data.get('content', '')
        itsm_type = input_data.get('itsm_type', 'Other')

        # 1. ITSM原則チェック
        principle_checks = self._check_itsm_principles(content, itsm_type)

        # 2. 逸脱検知
        deviations = self._detect_deviations(content, itsm_type)

        # 3. ベストプラクティス評価
        best_practices = self._evaluate_best_practices(content, itsm_type)

        # 4. 推奨事項生成
        recommendations = self._generate_recommendations(principle_checks, deviations, best_practices)

        # 総合評価
        compliance_score = self._calculate_compliance_score(principle_checks, deviations)
        status = 'success' if compliance_score >= 0.7 else 'warning'

        return SubAgentResult(
            status=status,
            data={
                'compliance_score': compliance_score,
                'principle_checks': principle_checks,
                'deviations': deviations,
                'best_practices': best_practices,
                'recommendations': recommendations
            },
            message=f"ITSM準拠度: {int(compliance_score*100)}%"
        )

    def _load_itsm_principles(self) -> Dict[str, List[Dict[str, Any]]]:
        """ITSM原則を定義"""
        return {
            'Incident': [
                {
                    'principle': '初動対応の記録',
                    'description': 'インシデント発生時の初動対応が記録されているか',
                    'keywords': ['発生時刻', '検知', '通知', '第一報']
                },
                {
                    'principle': '影響範囲の明確化',
                    'description': '影響を受けるユーザー・システムが明確か',
                    'keywords': ['影響', '範囲', 'ユーザー', 'システム', '対象']
                },
                {
                    'principle': '復旧手順の記録',
                    'description': '復旧に向けた手順が記録されているか',
                    'keywords': ['復旧', '対応', '手順', 'ステップ', '解決']
                },
                {
                    'principle': '根本原因の調査',
                    'description': '一時対応後の根本原因調査が計画されているか',
                    'keywords': ['原因', '調査', '分析', '問題管理']
                }
            ],
            'Problem': [
                {
                    'principle': '根本原因の特定',
                    'description': '根本原因が特定されているか',
                    'keywords': ['根本原因', 'root cause', '原因特定', '真因']
                },
                {
                    'principle': '再発防止策',
                    'description': '再発防止のための恒久対策が定義されているか',
                    'keywords': ['再発防止', '恒久対策', '対策', '改善']
                },
                {
                    'principle': 'インシデントとの紐付け',
                    'description': '関連するインシデントが明確か',
                    'keywords': ['インシデント', '関連', '紐付', 'incident']
                },
                {
                    'principle': '変更管理への移行',
                    'description': '対策実施のための変更管理が計画されているか',
                    'keywords': ['変更', 'change', '実施', '適用']
                }
            ],
            'Change': [
                {
                    'principle': '変更内容の明確化',
                    'description': '何をどう変更するのかが明確か',
                    'keywords': ['変更内容', '対象', '範囲', '変更点']
                },
                {
                    'principle': 'リスク評価',
                    'description': '変更に伴うリスクが評価されているか',
                    'keywords': ['リスク', '影響', '評価', 'リスクアセスメント']
                },
                {
                    'principle': 'ロールバック計画',
                    'description': '失敗時のロールバック手順が用意されているか',
                    'keywords': ['ロールバック', 'rollback', '切り戻し', '復旧手順']
                },
                {
                    'principle': 'テスト計画',
                    'description': '変更後の確認・テスト計画があるか',
                    'keywords': ['テスト', '確認', '検証', 'test', 'verification']
                }
            ],
            'Release': [
                {
                    'principle': 'リリース内容',
                    'description': 'リリース内容が明確に記載されているか',
                    'keywords': ['リリース', '機能', '変更', 'release']
                },
                {
                    'principle': 'リリース手順',
                    'description': 'リリース手順が文書化されているか',
                    'keywords': ['手順', 'ステップ', 'プロセス', 'procedure']
                },
                {
                    'principle': '影響分析',
                    'description': 'リリースによる影響が分析されているか',
                    'keywords': ['影響', '分析', 'impact', '対象']
                }
            ],
            'Request': [
                {
                    'principle': '要求内容の明確化',
                    'description': '何を要求しているのかが明確か',
                    'keywords': ['要求', '依頼', 'リクエスト', '内容']
                },
                {
                    'principle': '承認プロセス',
                    'description': '承認が必要な場合、そのプロセスが明確か',
                    'keywords': ['承認', 'approval', '許可', '申請']
                }
            ]
        }

    def _check_itsm_principles(self, content: str, itsm_type: str) -> List[Dict[str, Any]]:
        """ITSM原則に基づいたチェック"""
        principles = self.itsm_principles.get(itsm_type, [])
        content_lower = content.lower()
        results = []

        for principle_def in principles:
            keywords = principle_def.get('keywords', [])
            matched = any(keyword in content_lower for keyword in keywords)

            results.append({
                'principle': principle_def['principle'],
                'description': principle_def['description'],
                'compliant': matched,
                'severity': 'warning' if not matched else 'info'
            })

        return results

    def _detect_deviations(self, content: str, itsm_type: str) -> List[Dict[str, Any]]:
        """ITSM原則からの逸脱を検知"""
        deviations = []
        content_lower = content.lower()

        # 共通的な逸脱パターン
        common_deviations = [
            {
                'pattern': ['暫定', 'とりあえず', '一旦', 'workaround'],
                'deviation_type': '暫定対応のまま終了',
                'severity': 'warning',
                'description': '暫定対応で終了している可能性があります。恒久対策を検討してください。',
                'itsm_principle': 'Problem Management - 恒久対策の実施'
            },
            {
                'pattern': ['原因不明', '不明', '分からない', 'unknown'],
                'deviation_type': '原因未特定',
                'severity': 'error',
                'description': '原因が特定されていません。問題管理プロセスで根本原因を調査してください。',
                'itsm_principle': 'Problem Management - 根本原因分析'
            },
            {
                'pattern': ['再起動', 'reboot', 'restart'],
                'deviation_type': '再起動による対処',
                'severity': 'warning',
                'description': '再起動で対応していますが、根本原因の調査が必要です。',
                'itsm_principle': 'Incident Management - 根本原因への対応',
                'condition': lambda: itsm_type == 'Incident' and '原因' not in content_lower
            }
        ]

        for deviation_def in common_deviations:
            # 条件チェック
            if 'condition' in deviation_def:
                if not deviation_def['condition']():
                    continue

            # パターンマッチ
            if any(pattern in content_lower for pattern in deviation_def['pattern']):
                deviations.append({
                    'deviation_type': deviation_def['deviation_type'],
                    'severity': deviation_def['severity'],
                    'description': deviation_def['description'],
                    'itsm_principle': deviation_def['itsm_principle']
                })

        return deviations

    def _evaluate_best_practices(self, content: str, itsm_type: str) -> Dict[str, Any]:
        """ベストプラクティスへの準拠評価"""
        content_lower = content.lower()
        best_practices = []

        # 共通ベストプラクティス
        if any(word in content_lower for word in ['日時', '時刻', 'timestamp']):
            best_practices.append('時刻情報が記録されている')

        if any(word in content_lower for word in ['担当', '対応者', '実施者']):
            best_practices.append('担当者が明確')

        if any(word in content_lower for word in ['確認', '検証', 'verify', 'confirm']):
            best_practices.append('確認・検証プロセスがある')

        # ITSMタイプ別
        if itsm_type == 'Change':
            if any(word in content_lower for word in ['承認', 'approval', '許可']):
                best_practices.append('変更承認プロセスがある')
            if any(word in content_lower for word in ['バックアップ', 'backup', '退避']):
                best_practices.append('バックアップが考慮されている')

        if itsm_type == 'Incident':
            if any(word in content_lower for word in ['優先度', 'priority', '緊急度']):
                best_practices.append('優先度が設定されている')

        return {
            'practices_followed': best_practices,
            'count': len(best_practices)
        }

    def _generate_recommendations(
        self,
        principle_checks: List[Dict[str, Any]],
        deviations: List[Dict[str, Any]],
        best_practices: Dict[str, Any]
    ) -> List[str]:
        """推奨事項を生成"""
        recommendations = []

        # 原則チェックから
        non_compliant = [p for p in principle_checks if not p['compliant']]
        for principle in non_compliant:
            recommendations.append(f"{principle['principle']}: {principle['description']}")

        # 逸脱から
        for deviation in deviations:
            if deviation['severity'] == 'error':
                recommendations.append(f"【重要】{deviation['description']}")
            else:
                recommendations.append(deviation['description'])

        # ベストプラクティス
        if best_practices['count'] < 2:
            recommendations.append('時刻、担当者、確認プロセスなどの情報を追加することを推奨します')

        return recommendations

    def _calculate_compliance_score(
        self,
        principle_checks: List[Dict[str, Any]],
        deviations: List[Dict[str, Any]]
    ) -> float:
        """ITSM準拠スコアを計算"""
        if not principle_checks:
            return 0.8  # 原則が定義されていない場合は80%

        # 原則準拠率
        compliant_count = sum(1 for p in principle_checks if p['compliant'])
        principle_score = compliant_count / len(principle_checks)

        # 逸脱ペナルティ
        error_deviations = [d for d in deviations if d['severity'] == 'error']
        warning_deviations = [d for d in deviations if d['severity'] == 'warning']

        deviation_penalty = (len(error_deviations) * 0.2) + (len(warning_deviations) * 0.1)

        final_score = max(0.0, principle_score - deviation_penalty)

        return round(final_score, 2)
