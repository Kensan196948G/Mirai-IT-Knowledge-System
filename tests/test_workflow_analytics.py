"""
WorkflowとAnalyticsの追加カバレッジテスト
モックを使用してDB依存部分をテスト
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, PropertyMock, patch

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest

# ========== Workflow カバレッジ追加テスト ==========


class TestWorkflowEngineCoverage:
    """WorkflowEngineのカバレッジ向上テスト"""

    @patch("src.core.workflow.SQLiteClient")
    @patch("src.core.workflow.ArchitectSubAgent")
    @patch("src.core.workflow.KnowledgeCuratorSubAgent")
    @patch("src.core.workflow.ITSMExpertSubAgent")
    @patch("src.core.workflow.DevOpsSubAgent")
    @patch("src.core.workflow.QASubAgent")
    @patch("src.core.workflow.DocumenterSubAgent")
    @patch("src.core.workflow.CoordinatorSubAgent")
    def test_workflow_engine_initialization(
        self,
        mock_coordinator,
        mock_documenter,
        mock_qa,
        mock_devops,
        mock_itsm,
        mock_curator,
        mock_architect,
        mock_db,
    ):
        """WorkflowEngineが正しく初期化されること"""
        from src.core.workflow import WorkflowEngine

        engine = WorkflowEngine(db_path="test.db")

        # サブエージェントが初期化されていること
        assert "architect" in engine.subagents
        assert "knowledge_curator" in engine.subagents
        assert "itsm_expert" in engine.subagents
        assert "devops" in engine.subagents
        assert "qa" in engine.subagents
        assert "coordinator" in engine.subagents
        assert "documenter" in engine.subagents

        # フックが初期化されていること
        assert "pre_task" in engine.hooks
        assert "duplicate_check" in engine.hooks
        assert "deviation_check" in engine.hooks
        assert "auto_summary" in engine.hooks
        assert "post_task" in engine.hooks

    @patch("src.core.workflow.SQLiteClient")
    def test_workflow_aggregate_knowledge(self, mock_db):
        """ナレッジ集約ロジックが正しく動作すること"""
        from src.core.workflow import WorkflowEngine

        # モックサブエージェントを作成
        mock_subagents = {}
        for name in [
            "architect",
            "knowledge_curator",
            "itsm_expert",
            "devops",
            "qa",
            "coordinator",
            "documenter",
        ]:
            mock_subagents[name] = MagicMock()

        with patch.multiple(
            "src.core.workflow",
            ArchitectSubAgent=MagicMock(return_value=mock_subagents["architect"]),
            KnowledgeCuratorSubAgent=MagicMock(
                return_value=mock_subagents["knowledge_curator"]
            ),
            ITSMExpertSubAgent=MagicMock(return_value=mock_subagents["itsm_expert"]),
            DevOpsSubAgent=MagicMock(return_value=mock_subagents["devops"]),
            QASubAgent=MagicMock(return_value=mock_subagents["qa"]),
            DocumenterSubAgent=MagicMock(return_value=mock_subagents["documenter"]),
            CoordinatorSubAgent=MagicMock(return_value=mock_subagents["coordinator"]),
        ):
            engine = WorkflowEngine(db_path="test.db")

            # サブエージェント結果をモック
            subagent_results = {
                "documenter": {
                    "data": {
                        "summary_technical": "技術要約",
                        "summary_non_technical": "非技術要約",
                        "markdown": "# Test",
                        "html": "<h1>Test</h1>",
                    }
                },
                "knowledge_curator": {
                    "data": {
                        "tags": ["tag1", "tag2"],
                        "keywords": ["keyword1"],
                        "importance": {"score": 0.8},
                    }
                },
                "itsm_expert": {"data": {"recommendations": ["推奨事項1"]}},
                "devops": {"data": {"improvements": ["改善案1"]}},
            }

            # _aggregate_knowledge メソッドを直接テスト
            result = engine._aggregate_knowledge(
                title="テストタイトル",
                content="テスト内容",
                itsm_type="Incident",
                subagent_results=subagent_results,
            )

            # 結果検証
            assert result["title"] == "テストタイトル"
            assert result["content"] == "テスト内容"
            assert result["itsm_type"] == "Incident"
            assert result["summary_technical"] == "技術要約"
            assert result["summary_non_technical"] == "非技術要約"
            assert result["tags"] == ["tag1", "tag2"]
            assert result["keywords"] == ["keyword1"]
            assert "推奨事項1" in result["insights"]
            assert "改善案1" in result["insights"]


# ========== Analytics カバレッジ追加テスト ==========


class TestAnalyticsEngineCoverage:
    """AnalyticsEngineのカバレッジ向上テスト"""

    @patch("src.core.analytics.SQLiteClient")
    @patch("src.core.analytics.FeedbackClient")
    def test_analytics_engine_initialization(self, mock_feedback, mock_db):
        """AnalyticsEngineが正しく初期化されること"""
        from src.core.analytics import AnalyticsEngine

        engine = AnalyticsEngine(db_path="test.db")

        # クライアントが初期化されていること
        assert engine.db_client is not None
        assert engine.feedback_client is not None

    @patch("src.core.analytics.SQLiteClient")
    @patch("src.core.analytics.FeedbackClient")
    def test_analytics_incident_trends_mock(self, mock_feedback, mock_db):
        """インシデントトレンド分析のロジックをテスト"""
        from src.core.analytics import AnalyticsEngine

        # モックコネクション設定
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_db.return_value.get_connection.return_value.__enter__.return_value = (
            mock_conn
        )

        # モッククエリ結果
        mock_cursor.fetchall.side_effect = [
            # daily_counts
            [{"date": "2024-01-01", "count": 5}],
            # tag_distribution
            [{"tags": '["Server", "Network"]', "count": 3}],
            # recurring_incidents
            [{"id": 1, "title": "Test Incident", "recurrence_count": 2}],
        ]

        engine = AnalyticsEngine(db_path="test.db")
        result = engine.analyze_incident_trends(days=30)

        # 結果検証
        assert result["period_days"] == 30
        assert "daily_counts" in result
        assert "tag_distribution" in result
        assert "recurring_incidents" in result

    @patch("src.core.analytics.SQLiteClient")
    @patch("src.core.analytics.FeedbackClient")
    def test_analytics_problem_resolution_mock(self, mock_feedback, mock_db):
        """問題解決率分析のロジックをテスト"""
        from src.core.analytics import AnalyticsEngine

        # モックコネクション設定
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_db.return_value.get_connection.return_value.__enter__.return_value = (
            mock_conn
        )

        # モッククエリ結果
        mock_cursor.fetchone.side_effect = [
            {"total": 100},
            {"resolved": 75},
            {"avg_days": 5.5},
        ]

        engine = AnalyticsEngine(db_path="test.db")
        result = engine.analyze_problem_resolution_rate()

        # 結果検証
        assert result["total_problems"] == 100
        assert result["resolved_problems"] == 75
        assert result["resolution_rate"] == 75.0
        assert result["avg_resolution_days"] == 5.5

    @patch("src.core.analytics.SQLiteClient")
    @patch("src.core.analytics.FeedbackClient")
    def test_analytics_knowledge_quality_mock(self, mock_feedback, mock_db):
        """ナレッジ品質分析のロジックをテスト"""
        from src.core.analytics import AnalyticsEngine

        # モックコネクション設定
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_db.return_value.get_connection.return_value.__enter__.return_value = (
            mock_conn
        )

        # モッククエリ結果
        mock_cursor.fetchall.side_effect = [
            # length_distribution
            [
                {"length_category": "short", "count": 10},
                {"length_category": "medium", "count": 20},
            ],
            # tag_distribution
            [
                {"tag_count": 1, "knowledge_count": 5},
                {"tag_count": 2, "knowledge_count": 10},
            ],
        ]
        mock_cursor.fetchone.return_value = {"total": 100, "with_summary": 80}

        engine = AnalyticsEngine(db_path="test.db")
        result = engine.analyze_knowledge_quality()

        # 結果検証
        assert "length_distribution" in result
        assert result["summary_coverage"] == 80.0
        assert "tag_distribution" in result

    @patch("src.core.analytics.SQLiteClient")
    @patch("src.core.analytics.FeedbackClient")
    def test_analytics_itsm_flow_mock(self, mock_feedback, mock_db):
        """ITSMフロー分析のロジックをテスト"""
        from src.core.analytics import AnalyticsEngine

        # モックコネクション設定
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_db.return_value.get_connection.return_value.__enter__.return_value = (
            mock_conn
        )

        # モッククエリ結果
        mock_cursor.fetchone.side_effect = [
            {"total_incidents": 100, "escalated_to_problem": 30},
            {"total_problems": 50, "escalated_to_change": 40},
            {"complete_flow_count": 25},
        ]

        engine = AnalyticsEngine(db_path="test.db")
        result = engine.analyze_itsm_flow()

        # 結果検証
        assert result["incident_to_problem"]["total"] == 100
        assert result["incident_to_problem"]["escalated"] == 30
        assert result["incident_to_problem"]["rate"] == 30.0
        assert result["problem_to_change"]["total"] == 50
        assert result["problem_to_change"]["escalated"] == 40
        assert result["complete_flow_count"] == 25

    @patch("src.core.analytics.SQLiteClient")
    @patch("src.core.analytics.FeedbackClient")
    def test_analytics_usage_patterns_mock(self, mock_feedback, mock_db):
        """利用パターン分析のロジックをテスト"""
        from src.core.analytics import AnalyticsEngine

        # FeedbackClientのモックメソッド
        mock_feedback.return_value.get_popular_knowledge.return_value = [
            {"knowledge_id": 1, "title": "人気ナレッジ1", "view_count": 100}
        ]
        mock_feedback.return_value.get_top_rated_knowledge.return_value = [
            {"knowledge_id": 2, "title": "高評価ナレッジ1", "avg_rating": 4.5}
        ]

        # モックコネクション設定
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_db.return_value.get_connection.return_value.__enter__.return_value = (
            mock_conn
        )

        # 検索トレンドのモッククエリ結果
        mock_cursor.fetchall.return_value = [
            {"search_query": "障害", "count": 50},
            {"search_query": "設定", "count": 30},
        ]

        engine = AnalyticsEngine(db_path="test.db")
        result = engine.analyze_usage_patterns(days=30)

        # 結果検証
        assert "popular_knowledge" in result
        assert "top_rated_knowledge" in result
        assert "search_trends" in result
        assert result["period_days"] == 30

    @patch("src.core.analytics.SQLiteClient")
    @patch("src.core.analytics.FeedbackClient")
    def test_analytics_generate_recommendations(self, mock_feedback, mock_db):
        """推奨事項生成のロジックをテスト"""
        from src.core.analytics import AnalyticsEngine

        # モックコネクション設定
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_db.return_value.get_connection.return_value.__enter__.return_value = (
            mock_conn
        )

        engine = AnalyticsEngine(db_path="test.db")

        # インシデント多数シナリオをモック
        with patch.object(
            engine, "analyze_incident_trends", return_value={"total_incidents": 60}
        ):
            with patch.object(
                engine,
                "analyze_problem_resolution_rate",
                return_value={"resolution_rate": 65},
            ):
                with patch.object(
                    engine,
                    "analyze_knowledge_quality",
                    return_value={"summary_coverage": 75},
                ):
                    recommendations = engine.generate_recommendations()

                    # 推奨事項が生成されること
                    assert len(recommendations) > 0

                    # カテゴリーチェック
                    categories = [r["category"] for r in recommendations]
                    assert "incident_management" in categories
                    assert "problem_management" in categories
                    assert "quality" in categories

    @patch("src.core.analytics.SQLiteClient")
    @patch("src.core.analytics.FeedbackClient")
    def test_analytics_comprehensive_report(self, mock_feedback, mock_db):
        """総合レポート生成のロジックをテスト"""
        from src.core.analytics import AnalyticsEngine

        # モックコネクション設定
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_db.return_value.get_connection.return_value.__enter__.return_value = (
            mock_conn
        )

        # 各分析メソッドの戻り値を詳細にモック
        mock_cursor.fetchall.side_effect = [
            # analyze_incident_trends
            [{"date": "2024-01-01", "count": 5}],
            [{"tags": '["test"]', "count": 1}],
            [],
            # analyze_knowledge_quality
            [{"length_category": "medium", "count": 10}],
            [{"tag_count": 1, "knowledge_count": 5}],
            # analyze_usage_patterns
            [{"search_query": "test", "count": 10}],
        ]
        mock_cursor.fetchone.side_effect = [
            # analyze_problem_resolution_rate
            {"total": 10},
            {"resolved": 8},
            {"avg_days": 3.5},
            # analyze_knowledge_quality
            {"total": 100, "with_summary": 80},
            # analyze_itsm_flow
            {"total_incidents": 100, "escalated_to_problem": 30},
            {"total_problems": 50, "escalated_to_change": 40},
            {"complete_flow_count": 25},
        ]

        mock_feedback.return_value.get_popular_knowledge.return_value = []
        mock_feedback.return_value.get_top_rated_knowledge.return_value = []
        mock_feedback.return_value.get_feedback_summary.return_value = {}

        engine = AnalyticsEngine(db_path="test.db")
        report = engine.generate_comprehensive_report(days=30)

        # レポートに必要な項目が含まれていること
        assert "report_date" in report
        assert "period_days" in report
        assert "incident_trends" in report
        assert "problem_resolution" in report
        assert "knowledge_quality" in report
        assert "itsm_flow" in report
        assert "usage_patterns" in report
        assert "feedback_summary" in report
        assert report["period_days"] == 30
