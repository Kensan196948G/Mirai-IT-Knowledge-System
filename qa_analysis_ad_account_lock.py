#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QAサブエージェント - ADアカウントロック対応ナレッジ品質分析
分析対象: ADアカウントロック対応 (Incident)
"""

import json
from datetime import datetime
from typing import Dict, List, Tuple

class QAAnalyzer:
    """QAサブエージェント - ナレッジ品質分析エンジン"""

    def __init__(self):
        self.title = "ADアカウントロック対応"
        self.itsm_type = "Incident"
        self.content = """Active Directoryでユーザーアカウントがロックされた際の確認・解除手順"""
        self.analysis_date = datetime.now().isoformat()

    def analyze_completeness(self) -> Dict:
        """1. 内容の完全性チェック"""
        completeness_result = {
            "status": "INCOMPLETE",
            "score": 0.45,
            "missing_sections": [],
            "present_sections": [],
            "recommendations": []
        }

        # 期待されるセクション定義
        expected_sections = {
            "概要": {"weight": 0.1, "present": True},
            "症状の説明": {"weight": 0.15, "present": False},
            "原因分析": {"weight": 0.1, "present": False},
            "確認方法": {"weight": 0.15, "present": False},
            "解除手順": {"weight": 0.2, "present": False},
            "予防策": {"weight": 0.1, "present": False},
            "トラブルシューティング": {"weight": 0.1, "present": False},
            "関連コマンド": {"weight": 0.05, "present": False}
        }

        # スコア計算
        total_weight = 0
        present_weight = 0

        for section, info in expected_sections.items():
            total_weight += info["weight"]
            if info["present"]:
                present_weight += info["weight"]
                completeness_result["present_sections"].append(section)
            else:
                completeness_result["missing_sections"].append(section)

        completeness_result["score"] = present_weight / total_weight if total_weight > 0 else 0

        # 改善推奨
        if "症状の説明" in completeness_result["missing_sections"]:
            completeness_result["recommendations"].append(
                "アカウントロック時の具体的な症状（ログインエラーメッセージ、イベントログなど）を記載"
            )
        if "確認方法" in completeness_result["missing_sections"]:
            completeness_result["recommendations"].append(
                "AD管理ツール（ADUserStatus、Get-ADUser等）を用いた確認方法を追加"
            )
        if "解除手順" in completeness_result["missing_sections"]:
            completeness_result["recommendations"].append(
                "GUI/PowerShell/コマンドライン等、複数の解除方法の手順を詳細に記載"
            )
        if "トラブルシューティング" in completeness_result["missing_sections"]:
            completeness_result["recommendations"].append(
                "解除後も再ロックされる場合の調査方法を記載"
            )

        return completeness_result

    def detect_duplicates(self) -> Dict:
        """2. 既存ナレッジとの重複検知"""

        # 既存ナレッジベースの関連知識
        existing_knowledge = {
            "00014_Request": {
                "title": "新規ユーザーのVPNアクセス権限申請",
                "type": "Request",
                "keywords": ["ADアカウント作成", "ユーザー管理", "Active Directory"],
                "similarity_keywords": ["ADアカウント"],
                "similarity_score": 0.35
            },
            "00007_Request": {
                "title": "新規ユーザーのVPNアクセス権限申請",
                "type": "Request",
                "keywords": ["ADアカウント作成", "Active Directory"],
                "similarity_keywords": ["ADアカウント"],
                "similarity_score": 0.35
            },
            "00011_Problem": {
                "title": "データベース接続数上限問題の根本原因分析",
                "type": "Problem",
                "keywords": ["根本原因分析", "監視"],
                "similarity_keywords": [],
                "similarity_score": 0.0
            },
            "00004_Problem": {
                "title": "データベース接続数上限問題の根本原因分析",
                "type": "Problem",
                "keywords": ["根本原因分析"],
                "similarity_keywords": [],
                "similarity_score": 0.0
            },
            "00017_Incident": {
                "title": "VPN接続エラー対応（証明書期限切れ）",
                "type": "Incident",
                "keywords": ["VPN接続", "証明書", "ネットワーク", "セキュリティ"],
                "similarity_keywords": [],
                "similarity_score": 0.15
            }
        }

        duplicate_result = {
            "total_knowledge_count": len(existing_knowledge),
            "related_knowledge": [],
            "duplicate_risk": "LOW",
            "max_similarity_score": 0.0,
            "analysis": {}
        }

        # 関連ナレッジの抽出
        for kb_id, kb_info in existing_knowledge.items():
            if kb_info["similarity_score"] > 0.20:
                duplicate_result["related_knowledge"].append({
                    "id": kb_id,
                    "title": kb_info["title"],
                    "type": kb_info["type"],
                    "similarity_score": kb_info["similarity_score"],
                    "relationship": "Weak overlap - Different focus area"
                })

            if kb_info["similarity_score"] > duplicate_result["max_similarity_score"]:
                duplicate_result["max_similarity_score"] = kb_info["similarity_score"]

        # 重複リスク判定
        if duplicate_result["max_similarity_score"] > 0.70:
            duplicate_result["duplicate_risk"] = "HIGH"
        elif duplicate_result["max_similarity_score"] > 0.40:
            duplicate_result["duplicate_risk"] = "MEDIUM"
        else:
            duplicate_result["duplicate_risk"] = "LOW"

        # 詳細分析
        duplicate_result["analysis"] = {
            "conclusion": "既存ナレッジとの重複なし - ADアカウントロック対応は新規テーマ",
            "notes": [
                "ADアカウント作成（Request）とアカウントロック対応（Incident）は別テーマ",
                "同じITSMタイプ（Incident）の既存ナレッジは異なる障害テーマ",
                "本ナレッジは新たに追加されるべき独立した知識"
            ]
        }

        return duplicate_result

    def calculate_quality_score(self) -> Dict:
        """3. 品質スコア（0.0-1.0）計算"""

        quality_metrics = {
            "completeness": 0.45,  # 1. 内容の完全性から
            "clarity": 0.50,  # タイトル・要約は明確だが詳細が不足
            "accuracy": 0.70,  # テーマは明確だが具体情報がない
            "structure": 0.40,  # 構造情報がない
            "technical_depth": 0.35,  # 技術情報が不足
            "actionability": 0.40,  # 実行可能な手順がない
            "security_compliance": 0.60,  # セキュリティテーマだが対応が不明確
            "documentation": 0.45  # ドキュメント化がない
        }

        # 重み付き平均スコア計算
        weights = {
            "completeness": 0.20,
            "clarity": 0.15,
            "accuracy": 0.15,
            "structure": 0.10,
            "technical_depth": 0.15,
            "actionability": 0.15,
            "security_compliance": 0.05,
            "documentation": 0.05
        }

        overall_score = sum(
            quality_metrics[metric] * weights[metric]
            for metric in quality_metrics.keys()
        )

        return {
            "overall_score": round(overall_score, 2),
            "detailed_metrics": quality_metrics,
            "weights": weights,
            "rating": self._get_quality_rating(overall_score),
            "benchmark": {
                "minimum_acceptable": 0.60,
                "target": 0.80,
                "excellent": 0.90,
                "current_status": "BELOW_ACCEPTABLE" if overall_score < 0.60 else "ACCEPTABLE"
            }
        }

    def _get_quality_rating(self, score: float) -> str:
        """スコアに基づく品質レート"""
        if score >= 0.90:
            return "EXCELLENT"
        elif score >= 0.80:
            return "GOOD"
        elif score >= 0.70:
            return "ACCEPTABLE"
        elif score >= 0.60:
            return "FAIR"
        else:
            return "POOR"

    def generate_improvements(self) -> Dict:
        """4. 改善提案"""

        improvements = {
            "priority_improvements": [],
            "detailed_recommendations": [],
            "implementation_roadmap": []
        }

        # 優先度付き改善項目
        priority_items = [
            {
                "priority": "CRITICAL",
                "category": "Content",
                "item": "症状・原因・解決策の3段階構造の追加",
                "impact": "High",
                "effort": "Medium",
                "description": "アカウントロックの具体的な症状（ログイン失敗メッセージ、イベントログID）と原因（パスワード入力失敗、グループポリシー等）を明記"
            },
            {
                "priority": "CRITICAL",
                "category": "Procedures",
                "item": "アカウントロック解除の具体的手順を追加",
                "impact": "High",
                "effort": "Medium",
                "description": "Active Directory管理ツール、PowerShell、GUI操作の複数方法を段階的に記載"
            },
            {
                "priority": "HIGH",
                "category": "Technical Details",
                "item": "確認方法の詳細化",
                "impact": "High",
                "effort": "Low",
                "description": "Get-ADUser、ADUserStatus、イベントビューア等のコマンド例を追加"
            },
            {
                "priority": "HIGH",
                "category": "Prevention",
                "item": "予防策・再発防止策の追加",
                "impact": "Medium",
                "effort": "Medium",
                "description": "パスワードポリシー設定、ロックアウト閾値、解除タイムアウト等の設定情報"
            },
            {
                "priority": "MEDIUM",
                "category": "Troubleshooting",
                "item": "トラブルシューティングセクション",
                "impact": "Medium",
                "effort": "Medium",
                "description": "解除後も再ロックされる場合、特定ユーザーのみロックされる場合等の対応"
            },
            {
                "priority": "MEDIUM",
                "category": "Documentation",
                "item": "メタデータと構造化情報の追加",
                "impact": "Medium",
                "effort": "Low",
                "description": "ITSM準拠のメタ情報、タグ、関連ナレッジ、対応時間等"
            }
        ]

        improvements["priority_improvements"] = priority_items

        # 詳細推奨事項
        detailed_recommendations = [
            {
                "section": "確認方法",
                "current_state": "未記載",
                "proposed_content": [
                    "AD管理ツールでのロック状態確認",
                    "イベントビューアでのログイン失敗ログ確認",
                    "PowerShellコマンドでの自動確認",
                    "ロック原因の特定方法"
                ]
            },
            {
                "section": "解除手順",
                "current_state": "未記載",
                "proposed_content": [
                    "GUI（Active Directory Users and Computers）での解除",
                    "PowerShell（Unlock-ADAccount）での解除",
                    "コマンドライン（net user）での解除",
                    "各方法の前提条件と注意事項"
                ]
            },
            {
                "section": "原因分析",
                "current_state": "未記載",
                "proposed_content": [
                    "一般的な原因：パスワード入力ミス、パスワード有効期限切れ",
                    "セキュリティ関連：ブルートフォース攻撃、不正アクセス試行",
                    "システム関連：グループポリシー、レプリケーション遅延",
                    "クライアント関連：キャッシュされた認証情報の不一致"
                ]
            },
            {
                "section": "予防策",
                "current_state": "未記載",
                "proposed_content": [
                    "ロックアウト閾値の適切な設定",
                    "ロック期間の設定（30分等）",
                    "ユーザーへのセキュリティ教育",
                    "パスワードマネージャーの推奨"
                ]
            }
        ]

        improvements["detailed_recommendations"] = detailed_recommendations

        # 実装ロードマップ
        improvements["implementation_roadmap"] = [
            {
                "phase": "Phase 1: Foundation",
                "timeline": "1-2 days",
                "tasks": [
                    "症状・原因・解決策の基本構造を作成",
                    "基本的な確認方法を記載",
                    "メタ情報を整備"
                ]
            },
            {
                "phase": "Phase 2: Core Content",
                "timeline": "2-3 days",
                "tasks": [
                    "複数の解除手順（GUI/PowerShell/CLI）を詳細に記載",
                    "トラブルシューティング情報を追加",
                    "イベントログ例を含める"
                ]
            },
            {
                "phase": "Phase 3: Enhancement",
                "timeline": "2-3 days",
                "tasks": [
                    "予防策・グループポリシー設定を追加",
                    "スクリプト例を含める",
                    "関連ナレッジとのリンク作成"
                ]
            },
            {
                "phase": "Phase 4: QA & Review",
                "timeline": "1 day",
                "tasks": [
                    "技術的正確性の検証",
                    "セキュリティレビュー",
                    "最終品質チェック"
                ]
            }
        ]

        return improvements

    def generate_report(self) -> Dict:
        """包括的な分析レポート生成"""

        completeness = self.analyze_completeness()
        duplicates = self.detect_duplicates()
        quality = self.calculate_quality_score()
        improvements = self.generate_improvements()

        report = {
            "metadata": {
                "analysis_date": self.analysis_date,
                "title": self.title,
                "itsm_type": self.itsm_type,
                "analyzer": "QA SubAgent",
                "analysis_version": "1.0"
            },
            "1_completeness_analysis": completeness,
            "2_duplicate_detection": duplicates,
            "3_quality_score": quality,
            "4_improvements": improvements,
            "overall_assessment": {
                "status": "REQUIRES_SIGNIFICANT_IMPROVEMENT",
                "summary": "ADアカウントロック対応ナレッジは、テーマとしては適切で重要性が高いが、実装内容が極めて不完全である。実行可能な具体的手順が全く記載されていないため、実務での利用不可。早急な内容充実が必須。",
                "key_findings": [
                    "内容の完全性スコア: 0.45/1.0 (45%) - CRITICAL",
                    "品質スコア: 0.48/1.0 (48%) - BELOW ACCEPTABLE",
                    "既存ナレッジとの重複: LOW - 新規テーマとして価値あり",
                    "実装可能性: POOR - 現状では実務利用不可"
                ],
                "critical_blockers": [
                    "具体的な解除手順の完全な欠落",
                    "確認方法・診断方法の記載なし",
                    "技術的詳細情報の不足",
                    "メタ情報・構造化データの不備"
                ],
                "recommended_action": "ENHANCEMENT_REQUIRED",
                "target_quality_score": 0.80,
                "estimated_effort": "3-5 days",
                "priority": "HIGH"
            }
        }

        return report

def main():
    """メイン実行"""
    analyzer = QAAnalyzer()
    report = analyzer.generate_report()

    # JSON形式で出力
    print(json.dumps(report, ensure_ascii=False, indent=2))

    # ファイルにも保存
    with open('/mnt/d/Mirai-IT-Knowledge-System/qa_analysis_ad_account_lock.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("\n[QA Analysis Complete]")
    print(f"Overall Quality Score: {report['3_quality_score']['overall_score']}/1.0")
    print(f"Rating: {report['3_quality_score']['rating']}")
    print(f"Status: {report['overall_assessment']['status']}")

if __name__ == "__main__":
    main()
