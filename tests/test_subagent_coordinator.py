"""
CoordinatorSubAgent 単体テスト
カバレッジ目標: 90%以上
"""

import pytest

from src.subagents.base import SubAgentResult
from src.subagents.coordinator import CoordinatorSubAgent


@pytest.fixture
def coordinator():
    """CoordinatorSubAgent インスタンスを生成"""
    return CoordinatorSubAgent()


class TestCoordinatorInit:
    """初期化テスト"""

    def test_init_success(self, coordinator):
        """正常な初期化"""
        assert coordinator.name == "coordinator"
        assert coordinator.role == "coordination_review"
        assert coordinator.priority == "medium"


class TestCoordinatorProcess:
    """process メソッドのテスト"""

    def test_process_all_items_present(self, coordinator):
        """正常系: すべての項目が揃っている"""
        # Given
        input_data = {
            "title": "データベース障害対応記録",
            "content": """
            影響範囲: システム全体に影響
            担当者: 田中太郎
            発生時刻: 2024-01-20 10:00
            復旧時刻: 2024-01-20 12:00
            暫定対策: サーバー再起動
            恒久対策: 設定変更を実施
            """,
            "itsm_type": "Incident",
        }

        # When
        result = coordinator.process(input_data)

        # Then
        assert result.status == "success"
        assert len(result.data["missing_items"]) == 0
        assert result.message == "調整項目の抜け漏れは見つかりませんでした"

    def test_process_with_missing_items(self, coordinator):
        """正常系: 不足項目がある場合"""
        # Given
        input_data = {
            "title": "テスト",
            "content": "簡単な説明のみ",
            "itsm_type": "Incident",
        }

        # When
        result = coordinator.process(input_data)

        # Then
        assert result.status == "warning"
        assert len(result.data["missing_items"]) > 0
        assert len(result.data["coordination_notes"]) > 0

    def test_process_missing_required_fields(self, coordinator):
        """異常系: 必須フィールド不足"""
        # Given
        input_data = {"title": "テスト"}

        # When
        result = coordinator.process(input_data)

        # Then
        assert result.status == "failed"
        assert result.message == "必須フィールドが不足しています"

    def test_process_change_type_without_mitigation(self, coordinator):
        """正常系: Changeタイプで対策なし"""
        # Given
        input_data = {
            "title": "設定変更",
            "content": "設定を変更します",
            "itsm_type": "Change",
        }

        # When
        result = coordinator.process(input_data)

        # Then
        assert result.status == "warning"
        assert any("巻き戻し手順" in flag for flag in result.data["risk_flags"])


class TestRequiredContextChecks:
    """_required_context_checks メソッドのテスト"""

    def test_required_context_structure(self, coordinator):
        """必須コンテキストの構造確認"""
        # When
        result = coordinator._required_context_checks()

        # Then
        assert "impact_scope" in result
        assert "owner" in result
        assert "timeline" in result
        assert "mitigation" in result
        assert all(isinstance(keywords, list) for keywords in result.values())


class TestFindMissingItems:
    """_find_missing_items メソッドのテスト"""

    def test_find_missing_impact_scope(self, coordinator):
        """影響範囲が不足している場合"""
        # Given
        content = "担当者がいます。時刻は10:00。対策を実施。"
        required_context = coordinator._required_context_checks()

        # When
        result = coordinator._find_missing_items(content, required_context)

        # Then
        assert "impact_scope" in result

    def test_find_missing_owner(self, coordinator):
        """担当者が不足している場合"""
        # Given
        content = "影響範囲は全体。時刻は10:00。対策を実施。"
        required_context = coordinator._required_context_checks()

        # When
        result = coordinator._find_missing_items(content, required_context)

        # Then
        assert "owner" in result

    def test_find_missing_timeline(self, coordinator):
        """時刻情報が不足している場合"""
        # Given
        content = "影響範囲は全体。担当者がいます。対策を実施。"
        required_context = coordinator._required_context_checks()

        # When
        result = coordinator._find_missing_items(content, required_context)

        # Then
        assert "timeline" in result

    def test_find_missing_mitigation(self, coordinator):
        """対策が不足している場合"""
        # Given
        content = "影響範囲は全体。担当者がいます。時刻は10:00。"
        required_context = coordinator._required_context_checks()

        # When
        result = coordinator._find_missing_items(content, required_context)

        # Then
        assert "mitigation" in result

    def test_find_no_missing_items(self, coordinator):
        """すべて揃っている場合"""
        # Given
        content = "影響範囲は全体。担当者: 田中。時刻: 10:00。対策を実施。"
        required_context = coordinator._required_context_checks()

        # When
        result = coordinator._find_missing_items(content, required_context)

        # Then
        assert len(result) == 0


class TestBuildCoordinationNotes:
    """_build_coordination_notes メソッドのテスト"""

    def test_build_notes_impact_scope(self, coordinator):
        """影響範囲の注意事項"""
        # Given
        missing_items = ["impact_scope"]

        # When
        result = coordinator._build_coordination_notes(missing_items)

        # Then
        assert len(result) > 0
        assert any("影響範囲" in note for note in result)

    def test_build_notes_owner(self, coordinator):
        """担当者の注意事項"""
        # Given
        missing_items = ["owner"]

        # When
        result = coordinator._build_coordination_notes(missing_items)

        # Then
        assert any("担当者" in note or "責任者" in note for note in result)

    def test_build_notes_timeline(self, coordinator):
        """時刻の注意事項"""
        # Given
        missing_items = ["timeline"]

        # When
        result = coordinator._build_coordination_notes(missing_items)

        # Then
        assert any("時刻" in note or "期限" in note for note in result)

    def test_build_notes_mitigation(self, coordinator):
        """対策の注意事項"""
        # Given
        missing_items = ["mitigation"]

        # When
        result = coordinator._build_coordination_notes(missing_items)

        # Then
        assert any("対策" in note or "回避策" in note for note in result)

    def test_build_notes_multiple(self, coordinator):
        """複数の不足項目"""
        # Given
        missing_items = ["impact_scope", "owner", "timeline"]

        # When
        result = coordinator._build_coordination_notes(missing_items)

        # Then
        assert len(result) == 3

    def test_build_notes_empty(self, coordinator):
        """不足項目なし"""
        # Given
        missing_items = []

        # When
        result = coordinator._build_coordination_notes(missing_items)

        # Then
        assert len(result) == 0


class TestBuildRiskFlags:
    """_build_risk_flags メソッドのテスト"""

    def test_risk_flags_impact_scope(self, coordinator):
        """影響範囲不明確のリスク"""
        # Given
        title = "テストタイトル"
        itsm_type = "Incident"
        missing_items = ["impact_scope"]

        # When
        result = coordinator._build_risk_flags(title, itsm_type, missing_items)

        # Then
        assert any("周知漏れ" in flag for flag in result)

    def test_risk_flags_owner(self, coordinator):
        """担当者未確定のリスク"""
        # Given
        title = "テストタイトル"
        itsm_type = "Incident"
        missing_items = ["owner"]

        # When
        result = coordinator._build_risk_flags(title, itsm_type, missing_items)

        # Then
        assert any("対応遅延" in flag for flag in result)

    def test_risk_flags_change_without_mitigation(self, coordinator):
        """Changeタイプで対策なし"""
        # Given
        title = "テストタイトル"
        itsm_type = "Change"
        missing_items = ["mitigation"]

        # When
        result = coordinator._build_risk_flags(title, itsm_type, missing_items)

        # Then
        assert any("巻き戻し" in flag for flag in result)

    def test_risk_flags_release_without_mitigation(self, coordinator):
        """Releaseタイプで対策なし"""
        # Given
        title = "テストタイトル"
        itsm_type = "Release"
        missing_items = ["mitigation"]

        # When
        result = coordinator._build_risk_flags(title, itsm_type, missing_items)

        # Then
        assert any("巻き戻し" in flag for flag in result)

    def test_risk_flags_short_title(self, coordinator):
        """短いタイトルのリスク"""
        # Given
        title = "テスト"
        itsm_type = "Incident"
        missing_items = ["impact_scope"]

        # When
        result = coordinator._build_risk_flags(title, itsm_type, missing_items)

        # Then
        assert any("タイトルが短く" in flag for flag in result)

    def test_risk_flags_no_missing_items(self, coordinator):
        """不足項目なしの場合"""
        # Given
        title = "テストタイトル"
        itsm_type = "Incident"
        missing_items = []

        # When
        result = coordinator._build_risk_flags(title, itsm_type, missing_items)

        # Then
        assert len(result) == 0


class TestSuggestNextActions:
    """_suggest_next_actions メソッドのテスト"""

    def test_next_actions_impact_scope(self, coordinator):
        """影響範囲の次アクション"""
        # Given
        missing_items = ["impact_scope"]

        # When
        result = coordinator._suggest_next_actions(missing_items)

        # Then
        assert any("影響範囲" in action for action in result)

    def test_next_actions_owner(self, coordinator):
        """担当者の次アクション"""
        # Given
        missing_items = ["owner"]

        # When
        result = coordinator._suggest_next_actions(missing_items)

        # Then
        assert any("担当者" in action for action in result)

    def test_next_actions_timeline(self, coordinator):
        """タイムラインの次アクション"""
        # Given
        missing_items = ["timeline"]

        # When
        result = coordinator._suggest_next_actions(missing_items)

        # Then
        assert any("タイムライン" in action for action in result)

    def test_next_actions_mitigation(self, coordinator):
        """対策の次アクション"""
        # Given
        missing_items = ["mitigation"]

        # When
        result = coordinator._suggest_next_actions(missing_items)

        # Then
        assert any("対策" in action for action in result)

    def test_next_actions_multiple(self, coordinator):
        """複数の次アクション"""
        # Given
        missing_items = ["impact_scope", "owner", "timeline", "mitigation"]

        # When
        result = coordinator._suggest_next_actions(missing_items)

        # Then
        assert len(result) == 4

    def test_next_actions_empty(self, coordinator):
        """次アクションなし"""
        # Given
        missing_items = []

        # When
        result = coordinator._suggest_next_actions(missing_items)

        # Then
        assert len(result) == 0


class TestBuildMessage:
    """_build_message メソッドのテスト"""

    def test_build_message_no_missing(self, coordinator):
        """不足なしのメッセージ"""
        # Given
        missing_items = []

        # When
        result = coordinator._build_message(missing_items)

        # Then
        assert result == "調整項目の抜け漏れは見つかりませんでした"

    def test_build_message_with_missing(self, coordinator):
        """不足ありのメッセージ"""
        # Given
        missing_items = ["impact_scope", "owner"]

        # When
        result = coordinator._build_message(missing_items)

        # Then
        assert "2件" in result


class TestEdgeCases:
    """エッジケースのテスト"""

    def test_process_unicode(self, coordinator):
        """Unicode文字"""
        # Given
        input_data = {
            "title": "テスト 🔥",
            "content": "影響範囲: 全体 😀, 担当者: 田中, 時刻: 10:00, 対策: 実施",
            "itsm_type": "Incident",
        }

        # When
        result = coordinator.process(input_data)

        # Then
        assert result.status in ["success", "warning"]

    def test_process_special_characters(self, coordinator):
        """特殊文字"""
        # Given
        input_data = {
            "title": "<>&\"' テスト",
            "content": "影響範囲: 全体, 担当者: 田中, 時刻: 10:00, 対策: 実施",
            "itsm_type": "Incident",
        }

        # When
        result = coordinator.process(input_data)

        # Then
        assert result.status in ["success", "warning"]

    def test_process_very_long_content(self, coordinator):
        """非常に長いコンテンツ"""
        # Given
        input_data = {
            "title": "テスト",
            "content": "影響範囲: 全体, 担当者: 田中, 時刻: 10:00, 対策: 実施。" * 100,
            "itsm_type": "Incident",
        }

        # When
        result = coordinator.process(input_data)

        # Then
        assert result.status == "success"

    def test_process_all_itsm_types(self, coordinator):
        """すべてのITSMタイプ"""
        # Given
        itsm_types = ["Incident", "Problem", "Change", "Release", "Request", "Other"]

        for itsm_type in itsm_types:
            input_data = {
                "title": f"{itsm_type}テスト",
                "content": "影響範囲: 全体, 担当者: 田中, 時刻: 10:00, 対策: 実施",
                "itsm_type": itsm_type,
            }

            # When
            result = coordinator.process(input_data)

            # Then
            assert result.status in ["success", "warning"]

    def test_process_empty_content(self, coordinator):
        """空のコンテンツ"""
        # Given
        input_data = {"title": "テスト", "content": "", "itsm_type": "Incident"}

        # When
        result = coordinator.process(input_data)

        # Then
        assert result.status == "warning"
        assert len(result.data["missing_items"]) == 4  # すべて不足

    def test_risk_flags_long_title(self, coordinator):
        """長いタイトルではリスクフラグなし"""
        # Given
        title = "これは十分に長いタイトルです"
        itsm_type = "Incident"
        missing_items = []

        # When
        result = coordinator._build_risk_flags(title, itsm_type, missing_items)

        # Then
        assert not any("タイトルが短く" in flag for flag in result)
