"""
Advanced Analytics Engine
高度な分析エンジン
"""

import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Tuple

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.mcp.feedback_client import FeedbackClient
from src.mcp.sqlite_client import SQLiteClient


class AnalyticsEngine:
    """高度な分析エンジン"""

    def __init__(self, db_path: str = "db/knowledge.db"):
        self.db_client = SQLiteClient(db_path)
        self.feedback_client = FeedbackClient(db_path)

    # ========== トレンド分析 ==========

    def analyze_incident_trends(self, days: int = 90) -> Dict[str, Any]:
        """
        インシデントトレンド分析

        Args:
            days: 分析期間（日数）

        Returns:
            トレンド分析結果
        """
        with self.db_client.get_connection() as conn:
            cursor = conn.cursor()

            # 期間内のインシデント数推移
            cursor.execute(
                """
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM knowledge_entries
                WHERE itsm_type = 'Incident'
                  AND created_at > datetime('now', '-' || ? || ' days')
                GROUP BY DATE(created_at)
                ORDER BY date
            """,
                (days,),
            )
            daily_counts = [dict(row) for row in cursor.fetchall()]

            # タグ別インシデント数
            cursor.execute(
                """
                SELECT tags, COUNT(*) as count
                FROM knowledge_entries
                WHERE itsm_type = 'Incident'
                  AND created_at > datetime('now', '-' || ? || ' days')
                GROUP BY tags
            """,
                (days,),
            )
            tag_distribution = [dict(row) for row in cursor.fetchall()]

            # 再発インシデント検知（類似タイトル）
            cursor.execute(
                """
                SELECT k1.id, k1.title, COUNT(*) as recurrence_count
                FROM knowledge_entries k1
                JOIN knowledge_entries k2 ON k1.title = k2.title AND k1.id != k2.id
                WHERE k1.itsm_type = 'Incident'
                  AND k1.created_at > datetime('now', '-' || ? || ' days')
                GROUP BY k1.id, k1.title
                HAVING COUNT(*) > 0
                ORDER BY recurrence_count DESC
                LIMIT 10
            """,
                (days,),
            )
            recurring_incidents = [dict(row) for row in cursor.fetchall()]

            return {
                "period_days": days,
                "daily_counts": daily_counts,
                "tag_distribution": tag_distribution,
                "recurring_incidents": recurring_incidents,
                "total_incidents": sum(d["count"] for d in daily_counts),
            }

    def analyze_problem_resolution_rate(self) -> Dict[str, Any]:
        """問題管理の解決率分析"""
        with self.db_client.get_connection() as conn:
            cursor = conn.cursor()

            # 全Problem数
            cursor.execute("""
                SELECT COUNT(*) as total FROM knowledge_entries WHERE itsm_type = 'Problem'
            """)
            total = cursor.fetchone()["total"]

            # 解決済み（変更管理に移行したもの）
            cursor.execute("""
                SELECT COUNT(DISTINCT r.source_id) as resolved
                FROM relationships r
                JOIN knowledge_entries k ON r.source_id = k.id
                WHERE k.itsm_type = 'Problem'
                  AND r.relationship_type = 'Problem→Change'
            """)
            resolved = cursor.fetchone()["resolved"]

            # 平均解決時間（Problem作成から最初のChange作成まで）
            cursor.execute("""
                SELECT AVG(julianday(c.created_at) - julianday(p.created_at)) as avg_days
                FROM knowledge_entries p
                JOIN relationships r ON p.id = r.source_id
                JOIN knowledge_entries c ON r.target_id = c.id
                WHERE p.itsm_type = 'Problem'
                  AND c.itsm_type = 'Change'
                  AND r.relationship_type = 'Problem→Change'
            """)
            avg_resolution_days = cursor.fetchone()["avg_days"] or 0

            return {
                "total_problems": total,
                "resolved_problems": resolved,
                "resolution_rate": round(resolved / total * 100, 1) if total > 0 else 0,
                "avg_resolution_days": round(avg_resolution_days, 1),
            }

    # ========== 品質分析 ==========

    def analyze_knowledge_quality(self) -> Dict[str, Any]:
        """ナレッジ品質分析"""
        with self.db_client.get_connection() as conn:
            cursor = conn.cursor()

            # 品質スコア分布
            cursor.execute("""
                SELECT
                    CASE
                        WHEN LENGTH(content) < 100 THEN 'very_short'
                        WHEN LENGTH(content) < 300 THEN 'short'
                        WHEN LENGTH(content) < 1000 THEN 'medium'
                        WHEN LENGTH(content) < 3000 THEN 'long'
                        ELSE 'very_long'
                    END as length_category,
                    COUNT(*) as count
                FROM knowledge_entries
                GROUP BY length_category
            """)
            length_distribution = {
                row["length_category"]: row["count"] for row in cursor.fetchall()
            }

            # 要約が生成されているナレッジの割合
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN summary_technical IS NOT NULL AND summary_technical != '' THEN 1 ELSE 0 END) as with_summary
                FROM knowledge_entries
            """)
            summary_stats = dict(cursor.fetchone())

            # タグ数分布
            cursor.execute("""
                SELECT
                    json_array_length(tags) as tag_count,
                    COUNT(*) as knowledge_count
                FROM knowledge_entries
                WHERE tags IS NOT NULL
                GROUP BY tag_count
                ORDER BY tag_count
            """)
            tag_distribution = [dict(row) for row in cursor.fetchall()]

            return {
                "length_distribution": length_distribution,
                "summary_coverage": (
                    round(
                        summary_stats["with_summary"] / summary_stats["total"] * 100, 1
                    )
                    if summary_stats["total"] > 0
                    else 0
                ),
                "tag_distribution": tag_distribution,
            }

    # ========== 相関分析 ==========

    def analyze_itsm_flow(self) -> Dict[str, Any]:
        """ITSMフロー分析（Incident→Problem→Change）"""
        with self.db_client.get_connection() as conn:
            cursor = conn.cursor()

            # Incident→Problem移行率
            cursor.execute("""
                SELECT
                    (SELECT COUNT(*) FROM knowledge_entries WHERE itsm_type = 'Incident') as total_incidents,
                    (SELECT COUNT(DISTINCT r.source_id)
                     FROM relationships r
                     JOIN knowledge_entries k ON r.source_id = k.id
                     WHERE k.itsm_type = 'Incident' AND r.relationship_type = 'Incident→Problem') as escalated_to_problem
            """)
            incident_to_problem = dict(cursor.fetchone())

            # Problem→Change移行率
            cursor.execute("""
                SELECT
                    (SELECT COUNT(*) FROM knowledge_entries WHERE itsm_type = 'Problem') as total_problems,
                    (SELECT COUNT(DISTINCT r.source_id)
                     FROM relationships r
                     JOIN knowledge_entries k ON r.source_id = k.id
                     WHERE k.itsm_type = 'Problem' AND r.relationship_type = 'Problem→Change') as escalated_to_change
            """)
            problem_to_change = dict(cursor.fetchone())

            # 完全なフロー（Incident→Problem→Change）の数
            cursor.execute("""
                SELECT COUNT(DISTINCT i.id) as complete_flow_count
                FROM knowledge_entries i
                JOIN relationships r1 ON i.id = r1.source_id AND r1.relationship_type = 'Incident→Problem'
                JOIN knowledge_entries p ON r1.target_id = p.id
                JOIN relationships r2 ON p.id = r2.source_id AND r2.relationship_type = 'Problem→Change'
                WHERE i.itsm_type = 'Incident'
            """)
            complete_flow = cursor.fetchone()["complete_flow_count"]

            return {
                "incident_to_problem": {
                    "total": incident_to_problem["total_incidents"],
                    "escalated": incident_to_problem["escalated_to_problem"],
                    "rate": (
                        round(
                            incident_to_problem["escalated_to_problem"]
                            / incident_to_problem["total_incidents"]
                            * 100,
                            1,
                        )
                        if incident_to_problem["total_incidents"] > 0
                        else 0
                    ),
                },
                "problem_to_change": {
                    "total": problem_to_change["total_problems"],
                    "escalated": problem_to_change["escalated_to_change"],
                    "rate": (
                        round(
                            problem_to_change["escalated_to_change"]
                            / problem_to_change["total_problems"]
                            * 100,
                            1,
                        )
                        if problem_to_change["total_problems"] > 0
                        else 0
                    ),
                },
                "complete_flow_count": complete_flow,
            }

    # ========== 利用状況分析 ==========

    def analyze_usage_patterns(self, days: int = 30) -> Dict[str, Any]:
        """利用パターン分析"""
        # 人気のナレッジ
        popular = self.feedback_client.get_popular_knowledge(limit=10, days=days)

        # 評価の高いナレッジ
        top_rated = self.feedback_client.get_top_rated_knowledge(limit=10)

        # 検索キーワードトレンド
        with self.db_client.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT search_query, COUNT(*) as count
                FROM search_history
                WHERE created_at > datetime('now', '-' || ? || ' days')
                  AND search_query IS NOT NULL AND search_query != ''
                GROUP BY search_query
                ORDER BY count DESC
                LIMIT 20
            """,
                (days,),
            )
            search_trends = [dict(row) for row in cursor.fetchall()]

        return {
            "popular_knowledge": popular,
            "top_rated_knowledge": top_rated,
            "search_trends": search_trends,
            "period_days": days,
        }

    # ========== 総合レポート ==========

    def generate_comprehensive_report(self, days: int = 30) -> Dict[str, Any]:
        """総合分析レポート生成"""
        return {
            "report_date": datetime.now().isoformat(),
            "period_days": days,
            "incident_trends": self.analyze_incident_trends(days),
            "problem_resolution": self.analyze_problem_resolution_rate(),
            "knowledge_quality": self.analyze_knowledge_quality(),
            "itsm_flow": self.analyze_itsm_flow(),
            "usage_patterns": self.analyze_usage_patterns(days),
            "feedback_summary": self.feedback_client.get_feedback_summary(),
        }

    # ========== 推奨事項生成 ==========

    def generate_recommendations(self) -> List[Dict[str, str]]:
        """改善推奨事項を生成"""
        recommendations = []

        # インシデントトレンド分析から
        trends = self.analyze_incident_trends(30)
        if trends["total_incidents"] > 50:
            recommendations.append(
                {
                    "category": "incident_management",
                    "priority": "high",
                    "recommendation": "インシデント数が多いため、根本原因分析の強化を推奨します",
                }
            )

        # 問題解決率から
        problem_stats = self.analyze_problem_resolution_rate()
        if problem_stats["resolution_rate"] < 70:
            recommendations.append(
                {
                    "category": "problem_management",
                    "priority": "high",
                    "recommendation": "問題管理の解決率が低いため、恒久対策の実施を強化してください",
                }
            )

        # 品質分析から
        quality = self.analyze_knowledge_quality()
        if quality["summary_coverage"] < 80:
            recommendations.append(
                {
                    "category": "quality",
                    "priority": "medium",
                    "recommendation": "要約が不足しているナレッジがあります。自動要約機能の改善を検討してください",
                }
            )

        return recommendations
