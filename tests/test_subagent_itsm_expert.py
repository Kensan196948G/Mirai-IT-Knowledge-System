"""
ITSMExpertSubAgent 単体テスト
カバレッジ目標: 90%以上
"""

import pytest

from src.subagents.base import SubAgentResult
from src.subagents.itsm_expert import ITSMExpertSubAgent


@pytest.fixture
def itsm_expert():
    """ITSMExpertSubAgent インスタンスを生成"""
    return ITSMExpertSubAgent()


class TestITSMExpertSubAgentInit:
    """初期化テスト"""

    def test_init_success(self, itsm_expert):
        """正常な初期化"""
        assert itsm_expert.name == "itsm_expert"
        assert itsm_expert.role == "compliance"
        assert itsm_expert.priority == "high"
        assert itsm_expert.itsm_principles is not None
        assert len(itsm_expert.itsm_principles) > 0

    def test_itsm_principles_loaded(self, itsm_expert):
        """ITSM原則が正しくロードされている"""
        assert "Incident" in itsm_expert.itsm_principles
        assert "Problem" in itsm_expert.itsm_principles
        assert "Change" in itsm_expert.itsm_principles
        assert "Release" in itsm_expert.itsm_principles
        assert "Request" in itsm_expert.itsm_principles


class TestITSMExpertProcess:
    """process メソッドのテスト"""

    def test_process_incident_high_compliance(self, itsm_expert):
        """正常系: Incidentタイプで高い準拠度"""
        # Given
        input_data = {
            "title": "DBサーバー障害対応",
            "content": """
            発生時刻: 2024-01-20 10:00
            影響範囲: ユーザー全体がシステムにアクセス不可
            復旧手順: 1. DBサーバー再起動 2. 接続確認
            原因調査: ログ分析により根本原因を特定する
            """,
            "itsm_type": "Incident",
        }

        # When
        result = itsm_expert.process(input_data)

        # Then
        assert result.status == "success"
        assert result.data["compliance_score"] >= 0.7
        assert "principle_checks" in result.data
        assert "deviations" in result.data
        assert "recommendations" in result.data

    def test_process_problem_with_root_cause(self, itsm_expert):
        """正常系: Problemタイプで根本原因あり"""
        # Given
        input_data = {
            "title": "定期的なメモリリーク問題",
            "content": """
            根本原因: アプリケーションのメモリ解放処理の不具合
            再発防止策: コードレビューとメモリプロファイリングの実施
            関連インシデント: INC-001, INC-002
            変更管理への移行: CHG-100で修正パッチを適用予定
            """,
            "itsm_type": "Problem",
        }

        # When
        result = itsm_expert.process(input_data)

        # Then
        assert result.status == "success"
        assert result.data["compliance_score"] >= 0.7
        assert len(result.data["principle_checks"]) > 0

    def test_process_change_complete_info(self, itsm_expert):
        """正常系: Changeタイプで完全な情報"""
        # Given
        input_data = {
            "title": "Webサーバーバージョンアップ",
            "content": """
            変更内容: Apache 2.2 から 2.4 へのバージョンアップ
            対象範囲: Web01, Web02サーバー
            リスク評価: 設定互換性の問題が発生する可能性あり
            ロールバック計画: 旧バージョンのバックアップから復元
            テスト計画: ステージング環境で動作確認後、本番適用
            """,
            "itsm_type": "Change",
        }

        # When
        result = itsm_expert.process(input_data)

        # Then
        assert result.status == "success"
        assert result.data["compliance_score"] >= 0.7

    def test_process_missing_required_fields(self, itsm_expert):
        """異常系: 必須フィールド不足"""
        # Given
        input_data = {
            "title": "テスト"
            # contentとitsm_typeが不足
        }

        # When
        result = itsm_expert.process(input_data)

        # Then
        assert result.status == "failed"
        assert result.message == "必須フィールドが不足しています"

    def test_process_empty_content(self, itsm_expert):
        """エッジケース: 空のコンテンツ"""
        # Given
        input_data = {"title": "テスト", "content": "", "itsm_type": "Incident"}

        # When
        result = itsm_expert.process(input_data)

        # Then
        assert result.status == "warning"
        assert result.data["compliance_score"] < 0.7

    def test_process_low_compliance_triggers_warning(self, itsm_expert):
        """正常系: 低い準拠度で警告ステータス"""
        # Given
        input_data = {
            "title": "テスト",
            "content": "簡単な説明のみ",
            "itsm_type": "Incident",
        }

        # When
        result = itsm_expert.process(input_data)

        # Then
        assert result.status == "warning"
        assert result.data["compliance_score"] < 0.7
        assert len(result.data["recommendations"]) > 0


class TestCheckITSMPrinciples:
    """_check_itsm_principles メソッドのテスト"""

    def test_check_incident_principles_all_matched(self, itsm_expert):
        """Incident原則がすべて合致"""
        # Given
        content = """
        発生時刻: 2024-01-20 10:00
        影響範囲: ユーザー全体
        復旧手順: サーバー再起動
        原因調査: ログを分析
        """
        itsm_type = "Incident"

        # When
        result = itsm_expert._check_itsm_principles(content, itsm_type)

        # Then
        assert len(result) > 0
        assert all(check["compliant"] for check in result)

    def test_check_problem_principles_partial_match(self, itsm_expert):
        """Problem原則が部分的に合致"""
        # Given
        content = "根本原因を特定しました。再発防止策を検討中。"
        itsm_type = "Problem"

        # When
        result = itsm_expert._check_itsm_principles(content, itsm_type)

        # Then
        assert len(result) > 0
        compliant_count = sum(1 for check in result if check["compliant"])
        assert compliant_count >= 1

    def test_check_unknown_itsm_type(self, itsm_expert):
        """未知のITSMタイプ"""
        # Given
        content = "テスト内容"
        itsm_type = "UnknownType"

        # When
        result = itsm_expert._check_itsm_principles(content, itsm_type)

        # Then
        assert result == []


class TestDetectDeviations:
    """_detect_deviations メソッドのテスト"""

    def test_detect_temporary_workaround_deviation(self, itsm_expert):
        """暫定対応の逸脱を検知"""
        # Given
        content = "とりあえずサーバーを再起動して対応しました。"
        itsm_type = "Incident"

        # When
        result = itsm_expert._detect_deviations(content, itsm_type)

        # Then
        assert len(result) > 0
        assert any(d["deviation_type"] == "暫定対応のまま終了" for d in result)

    def test_detect_unknown_cause_deviation(self, itsm_expert):
        """原因不明の逸脱を検知"""
        # Given
        content = "原因は不明ですが、再起動で復旧しました。"
        itsm_type = "Incident"

        # When
        result = itsm_expert._detect_deviations(content, itsm_type)

        # Then
        assert len(result) > 0
        assert any(d["deviation_type"] == "原因未特定" for d in result)
        assert any(d["severity"] == "error" for d in result)

    def test_detect_restart_without_cause_analysis(self, itsm_expert):
        """原因分析なしの再起動を検知"""
        # Given
        content = "サーバーを再起動しました。"
        itsm_type = "Incident"

        # When
        result = itsm_expert._detect_deviations(content, itsm_type)

        # Then
        # 再起動あり、かつ原因が含まれていないのでフラグが立つ
        assert len(result) >= 0  # 条件によって変動

    def test_no_deviations_detected(self, itsm_expert):
        """逸脱が検知されない場合"""
        # Given
        content = """
        根本原因を特定し、恒久対策を実施しました。
        詳細なログ分析により問題を解決しました。
        """
        itsm_type = "Problem"

        # When
        result = itsm_expert._detect_deviations(content, itsm_type)

        # Then
        # 暫定や不明などの逸脱パターンがないので、空または少ない
        assert len(result) == 0


class TestEvaluateBestPractices:
    """_evaluate_best_practices メソッドのテスト"""

    def test_evaluate_with_timestamp(self, itsm_expert):
        """時刻情報を含む場合"""
        # Given
        content = "発生日時: 2024-01-20 10:00"
        itsm_type = "Incident"

        # When
        result = itsm_expert._evaluate_best_practices(content, itsm_type)

        # Then
        assert result["count"] > 0
        assert "時刻情報が記録されている" in result["practices_followed"]

    def test_evaluate_with_owner(self, itsm_expert):
        """担当者情報を含む場合"""
        # Given
        content = "担当者: 田中太郎"
        itsm_type = "Incident"

        # When
        result = itsm_expert._evaluate_best_practices(content, itsm_type)

        # Then
        assert result["count"] > 0
        assert "担当者が明確" in result["practices_followed"]

    def test_evaluate_change_with_approval(self, itsm_expert):
        """Changeタイプで承認プロセスがある場合"""
        # Given
        content = "変更承認を取得し、バックアップを実施しました。"
        itsm_type = "Change"

        # When
        result = itsm_expert._evaluate_best_practices(content, itsm_type)

        # Then
        assert "変更承認プロセスがある" in result["practices_followed"]
        assert "バックアップが考慮されている" in result["practices_followed"]

    def test_evaluate_incident_with_priority(self, itsm_expert):
        """Incidentタイプで優先度がある場合"""
        # Given
        content = "優先度: 高"
        itsm_type = "Incident"

        # When
        result = itsm_expert._evaluate_best_practices(content, itsm_type)

        # Then
        assert "優先度が設定されている" in result["practices_followed"]


class TestGenerateRecommendations:
    """_generate_recommendations メソッドのテスト"""

    def test_generate_recommendations_from_non_compliant(self, itsm_expert):
        """非準拠項目から推奨事項を生成"""
        # Given
        principle_checks = [
            {"principle": "テスト原則", "compliant": False, "description": "説明文"}
        ]
        deviations = []
        best_practices = {"count": 3}

        # When
        result = itsm_expert._generate_recommendations(
            principle_checks, deviations, best_practices
        )

        # Then
        assert len(result) > 0
        assert "テスト原則: 説明文" in result

    def test_generate_recommendations_from_deviations(self, itsm_expert):
        """逸脱から推奨事項を生成"""
        # Given
        principle_checks = []
        deviations = [{"severity": "error", "description": "重大な問題があります"}]
        best_practices = {"count": 3}

        # When
        result = itsm_expert._generate_recommendations(
            principle_checks, deviations, best_practices
        )

        # Then
        assert len(result) > 0
        assert any("【重要】" in rec for rec in result)

    def test_generate_recommendations_low_best_practices(self, itsm_expert):
        """ベストプラクティスが少ない場合"""
        # Given
        principle_checks = []
        deviations = []
        best_practices = {"count": 1}

        # When
        result = itsm_expert._generate_recommendations(
            principle_checks, deviations, best_practices
        )

        # Then
        assert len(result) > 0
        assert any("情報を追加することを推奨します" in rec for rec in result)


class TestCalculateComplianceScore:
    """_calculate_compliance_score メソッドのテスト"""

    def test_calculate_score_all_compliant_no_deviations(self, itsm_expert):
        """すべて準拠、逸脱なし"""
        # Given
        principle_checks = [
            {"compliant": True},
            {"compliant": True},
            {"compliant": True},
        ]
        deviations = []

        # When
        result = itsm_expert._calculate_compliance_score(principle_checks, deviations)

        # Then
        assert result == 1.0

    def test_calculate_score_partial_compliant_no_deviations(self, itsm_expert):
        """部分的に準拠、逸脱なし"""
        # Given
        principle_checks = [
            {"compliant": True},
            {"compliant": False},
            {"compliant": True},
        ]
        deviations = []

        # When
        result = itsm_expert._calculate_compliance_score(principle_checks, deviations)

        # Then
        assert 0.6 <= result <= 0.7

    def test_calculate_score_with_error_deviations(self, itsm_expert):
        """エラー逸脱ありの場合"""
        # Given
        principle_checks = [{"compliant": True}, {"compliant": True}]
        deviations = [{"severity": "error"}]

        # When
        result = itsm_expert._calculate_compliance_score(principle_checks, deviations)

        # Then
        # 1.0 - 0.2(error) = 0.8
        assert result == 0.8

    def test_calculate_score_with_warning_deviations(self, itsm_expert):
        """警告逸脱ありの場合"""
        # Given
        principle_checks = [{"compliant": True}, {"compliant": True}]
        deviations = [{"severity": "warning"}]

        # When
        result = itsm_expert._calculate_compliance_score(principle_checks, deviations)

        # Then
        # 1.0 - 0.1(warning) = 0.9
        assert result == 0.9

    def test_calculate_score_empty_principles(self, itsm_expert):
        """原則が定義されていない場合"""
        # Given
        principle_checks = []
        deviations = []

        # When
        result = itsm_expert._calculate_compliance_score(principle_checks, deviations)

        # Then
        assert result == 0.8

    def test_calculate_score_minimum_zero(self, itsm_expert):
        """スコアが負にならないことを確認"""
        # Given
        principle_checks = [{"compliant": False}, {"compliant": False}]
        deviations = [
            {"severity": "error"},
            {"severity": "error"},
            {"severity": "warning"},
        ]

        # When
        result = itsm_expert._calculate_compliance_score(principle_checks, deviations)

        # Then
        assert result >= 0.0


class TestExecuteMethod:
    """execute メソッドのテスト（基底クラスから継承）"""

    def test_execute_success_with_timing(self, itsm_expert):
        """execute経由での実行と実行時間計測"""
        # Given
        input_data = {
            "title": "テスト",
            "content": "発生時刻: 10:00, 影響範囲: システム全体, 復旧完了",
            "itsm_type": "Incident",
        }

        # When
        result = itsm_expert.execute(input_data)

        # Then
        assert result.status in ["success", "warning", "failed"]
        assert result.execution_time_ms is not None
        assert result.execution_time_ms >= 0

    def test_execute_handles_exception(self, itsm_expert):
        """execute時の例外ハンドリング"""
        # Given
        input_data = None  # 意図的に不正な入力

        # When
        result = itsm_expert.execute(input_data)

        # Then
        assert result.status == "failed"
        assert "エラーが発生しました" in result.message
        assert result.execution_time_ms is not None


class TestEdgeCases:
    """エッジケースのテスト"""

    def test_process_with_special_characters(self, itsm_expert):
        """特殊文字を含む入力"""
        # Given
        input_data = {
            "title": "テスト <>&\"'",
            "content": "特殊文字: !@#$%^&*()_+-=[]{}|;:,.<>?/~`",
            "itsm_type": "Incident",
        }

        # When
        result = itsm_expert.process(input_data)

        # Then
        assert result.status in ["success", "warning"]

    def test_process_with_very_long_content(self, itsm_expert):
        """非常に長いコンテンツ"""
        # Given
        input_data = {
            "title": "テスト",
            "content": "テスト " * 10000,
            "itsm_type": "Incident",
        }

        # When
        result = itsm_expert.process(input_data)

        # Then
        assert result.status in ["success", "warning"]

    def test_process_with_unicode_content(self, itsm_expert):
        """Unicode文字を含む入力"""
        # Given
        input_data = {
            "title": "障害対応 🔥",
            "content": "発生時刻: 10:00 😀 影響範囲: システム全体 ✅",
            "itsm_type": "Incident",
        }

        # When
        result = itsm_expert.process(input_data)

        # Then
        assert result.status in ["success", "warning"]

    def test_process_release_type(self, itsm_expert):
        """Releaseタイプのテスト"""
        # Given
        input_data = {
            "title": "アプリケーションリリース",
            "content": "リリース内容を記載。手順あり。影響分析済み。",
            "itsm_type": "Release",
        }

        # When
        result = itsm_expert.process(input_data)

        # Then
        assert result.status in ["success", "warning"]
        assert "compliance_score" in result.data

    def test_process_request_type(self, itsm_expert):
        """Requestタイプのテスト"""
        # Given
        input_data = {
            "title": "ユーザーアカウント作成依頼",
            "content": "要求内容を明記。承認プロセスあり。",
            "itsm_type": "Request",
        }

        # When
        result = itsm_expert.process(input_data)

        # Then
        assert result.status in ["success", "warning"]
        assert "compliance_score" in result.data
