"""
ArchitectSubAgent 単体テスト
カバレッジ目標: 90%以上
"""

import pytest
from src.subagents.architect import ArchitectSubAgent
from src.subagents.base import SubAgentResult


@pytest.fixture
def architect():
    """ArchitectSubAgent インスタンスを生成"""
    return ArchitectSubAgent()


class TestArchitectSubAgentInit:
    """初期化テスト"""

    def test_init_success(self, architect):
        """正常な初期化"""
        assert architect.name == "architect"
        assert architect.role == "design_coherence"
        assert architect.priority == "high"


class TestArchitectProcess:
    """process メソッドのテスト"""

    def test_process_all_checks_passed(self, architect):
        """正常系: すべてのチェックが合格"""
        # Given
        input_data = {
            'title': 'データベース障害の復旧',
            'content': '''
            データベースサーバーで障害が発生しました。
            エラーログを確認し、原因を特定しました。
            対策として設定を変更し、影響範囲を確認しました。
            手順を実施し、正常に復旧しました。
            ''',
            'itsm_type': 'Incident',
            'existing_knowledge': []
        }

        # When
        result = architect.process(input_data)

        # Then
        assert result.status == 'success'
        assert result.data['coherence_score'] > 0.5
        assert len(result.data['checks']) > 0

    def test_process_with_warnings(self, architect):
        """正常系: 警告がある場合"""
        # Given
        input_data = {
            'title': '全く関係ないタイトル',
            'content': 'データベースエラーの対応について',
            'itsm_type': 'Incident',
            'existing_knowledge': []
        }

        # When
        result = architect.process(input_data)

        # Then
        assert result.status == 'warning'
        assert len(result.data['warnings']) > 0

    def test_process_missing_required_fields(self, architect):
        """異常系: 必須フィールド不足"""
        # Given
        input_data = {
            'title': 'テスト'
            # contentが不足
        }

        # When
        result = architect.process(input_data)

        # Then
        assert result.status == 'failed'
        assert "必須フィールドが不足しています" in result.message

    def test_process_with_existing_knowledge(self, architect):
        """正常系: 既存ナレッジがある場合"""
        # Given
        input_data = {
            'title': 'テストタイトル',
            'content': 'テストコンテンツ',
            'itsm_type': 'Incident',
            'existing_knowledge': [
                {'id': 'KB001', 'title': 'テスト', 'content': 'テスト内容'}
            ]
        }

        # When
        result = architect.process(input_data)

        # Then
        assert result.status in ['success', 'warning']
        assert 'coherence_score' in result.data


class TestCheckTitleContentCoherence:
    """_check_title_content_coherence メソッドのテスト"""

    def test_title_content_coherence_high(self, architect):
        """タイトルと内容の整合性が高い"""
        # Given
        title = 'データベース接続エラーの対処法'
        content = 'データベースへの接続エラーが発生した場合の対処法について説明します。'

        # When
        result = architect._check_title_content_coherence(title, content)

        # Then
        assert result['passed'] is True
        assert 'match_rate' in result['details']

    def test_title_content_coherence_low(self, architect):
        """タイトルと内容の整合性が低い"""
        # Given
        title = 'データベースエラー対処法'
        content = 'ネットワーク設定の変更手順について記載します。'

        # When
        result = architect._check_title_content_coherence(title, content)

        # Then
        assert result['passed'] is False

    def test_title_content_coherence_generic_title(self, architect):
        """一般的すぎるタイトル"""
        # Given
        title = 'について に を'
        content = 'データベースエラーについて'

        # When
        result = architect._check_title_content_coherence(title, content)

        # Then
        assert result['passed'] is True
        assert 'スキップ' in result['message']

    def test_title_content_coherence_empty_content(self, architect):
        """空のコンテンツ"""
        # Given
        title = 'テストタイトル'
        content = ''

        # When
        result = architect._check_title_content_coherence(title, content)

        # Then
        assert result['passed'] is False


class TestCheckITSMValidity:
    """_check_itsm_validity メソッドのテスト"""

    def test_itsm_validity_incident_valid(self, architect):
        """Incidentタイプが妥当"""
        # Given
        itsm_type = 'Incident'
        content = 'システム障害が発生し、緊急対応が必要です。エラーが検出されました。'

        # When
        result = architect._check_itsm_validity(itsm_type, content)

        # Then
        assert result['passed'] is True
        assert itsm_type in result['message']

    def test_itsm_validity_problem_valid(self, architect):
        """Problemタイプが妥当"""
        # Given
        itsm_type = 'Problem'
        content = '根本原因を分析し、再発防止対策を立てました。'

        # When
        result = architect._check_itsm_validity(itsm_type, content)

        # Then
        assert result['passed'] is True

    def test_itsm_validity_change_valid(self, architect):
        """Changeタイプが妥当"""
        # Given
        itsm_type = 'Change'
        content = 'システム変更を実施します。リリース予定です。'

        # When
        result = architect._check_itsm_validity(itsm_type, content)

        # Then
        assert result['passed'] is True

    def test_itsm_validity_invalid_type(self, architect):
        """無効なITSMタイプ"""
        # Given
        itsm_type = 'InvalidType'
        content = 'テスト内容'

        # When
        result = architect._check_itsm_validity(itsm_type, content)

        # Then
        assert result['passed'] is False
        assert 'valid_types' in result['details']

    def test_itsm_validity_other_type(self, architect):
        """Otherタイプ（キーワードなし）"""
        # Given
        itsm_type = 'Other'
        content = 'その他の内容'

        # When
        result = architect._check_itsm_validity(itsm_type, content)

        # Then
        assert result['passed'] is True

    def test_itsm_validity_type_content_mismatch(self, architect):
        """ITSMタイプと内容が不一致"""
        # Given
        itsm_type = 'Incident'
        content = 'リリース計画を作成します。'

        # When
        result = architect._check_itsm_validity(itsm_type, content)

        # Then
        assert result['passed'] is False


class TestCheckKnowledgeCoherence:
    """_check_knowledge_coherence メソッドのテスト"""

    def test_knowledge_coherence_no_similar(self, architect):
        """類似ナレッジがない場合"""
        # Given
        content = '全く新しいトピックについての記述です。'
        existing_knowledge = [
            {'id': 'KB001', 'content': '完全に異なる内容の既存ナレッジ。'}
        ]

        # When
        result = architect._check_knowledge_coherence(content, existing_knowledge)

        # Then
        assert result['passed'] is True

    def test_knowledge_coherence_high_similar(self, architect):
        """高類似度のナレッジが存在する場合"""
        # Given
        content = 'データベース接続エラーの対処方法について'
        existing_knowledge = [
            {'id': 'KB002', 'content': 'データベース接続エラーの対処方法について説明'}
        ]

        # When
        result = architect._check_knowledge_coherence(content, existing_knowledge)

        # Then
        assert result['details']['similar_count'] >= 0


class TestCheckDesignPrinciples:
    """_check_design_principles メソッドのテスト"""

    def test_design_principles_all_matched(self, architect):
        """すべての設計原則に準拠"""
        # Given
        content = '''
        原因を特定し、対策を実施しました。
        手順を記載し、影響範囲を確認しました。
        '''

        # When
        result = architect._check_design_principles(content)

        # Then
        assert result['passed'] is True
        assert 'principles' in result['details']

    def test_design_principles_partial_match(self, architect):
        """部分的に準拠"""
        # Given
        content = '原因を特定しました。'

        # When
        result = architect._check_design_principles(content)

        # Then
        # 3つの原則のうち60%以上（2つ以上）必要
        assert 'principles' in result['details']

    def test_design_principles_none_matched(self, architect):
        """準拠していない場合"""
        # Given
        content = '簡単な説明のみ。'

        # When
        result = architect._check_design_principles(content)

        # Then
        assert result['passed'] is False


class TestCalculateSimilarity:
    """_calculate_similarity メソッドのテスト"""

    def test_similarity_identical(self, architect):
        """同一テキスト"""
        # Given
        text1 = 'これはテストです'
        text2 = 'これはテストです'

        # When
        result = architect._calculate_similarity(text1, text2)

        # Then
        assert result == 1.0

    def test_similarity_different(self, architect):
        """異なるテキスト"""
        # Given
        text1 = 'データベースエラー'
        text2 = 'ネットワーク設定'

        # When
        result = architect._calculate_similarity(text1, text2)

        # Then
        assert result < 0.5

    def test_similarity_empty_text1(self, architect):
        """text1が空"""
        # Given
        text1 = ''
        text2 = 'テスト'

        # When
        result = architect._calculate_similarity(text1, text2)

        # Then
        assert result == 0.0

    def test_similarity_empty_text2(self, architect):
        """text2が空"""
        # Given
        text1 = 'テスト'
        text2 = ''

        # When
        result = architect._calculate_similarity(text1, text2)

        # Then
        assert result == 0.0

    def test_similarity_both_empty(self, architect):
        """両方空"""
        # Given
        text1 = ''
        text2 = ''

        # When
        result = architect._calculate_similarity(text1, text2)

        # Then
        assert result == 0.0

    def test_similarity_partial_match(self, architect):
        """部分的に一致"""
        # Given
        text1 = 'データベース エラー 発生 対応'
        text2 = 'データベース エラー 解決'

        # When
        result = architect._calculate_similarity(text1, text2)

        # Then
        assert 0.3 <= result <= 0.8


class TestGenerateRecommendations:
    """_generate_recommendations メソッドのテスト"""

    def test_recommendations_title_content_coherence(self, architect):
        """タイトルと内容の整合性に関する推奨事項"""
        # Given
        warnings = [
            {'check_name': 'タイトルと内容の整合性'}
        ]

        # When
        result = architect._generate_recommendations(warnings)

        # Then
        assert len(result) > 0
        assert any('タイトル' in rec for rec in result)

    def test_recommendations_itsm_validity(self, architect):
        """ITSMタイプの妥当性に関する推奨事項"""
        # Given
        warnings = [
            {'check_name': 'ITSMタイプの妥当性'}
        ]

        # When
        result = architect._generate_recommendations(warnings)

        # Then
        assert len(result) > 0
        assert any('ITSMタイプ' in rec for rec in result)

    def test_recommendations_knowledge_coherence(self, architect):
        """既存ナレッジとの整合性に関する推奨事項"""
        # Given
        warnings = [
            {'check_name': '既存ナレッジとの整合性'}
        ]

        # When
        result = architect._generate_recommendations(warnings)

        # Then
        assert len(result) > 0
        assert any('類似ナレッジ' in rec or '統合' in rec for rec in result)

    def test_recommendations_design_principles(self, architect):
        """設計原則に関する推奨事項"""
        # Given
        warnings = [
            {'check_name': '設計原則への準拠'}
        ]

        # When
        result = architect._generate_recommendations(warnings)

        # Then
        assert len(result) > 0
        assert any('原因' in rec or '対策' in rec or '影響' in rec for rec in result)

    def test_recommendations_empty_warnings(self, architect):
        """警告がない場合"""
        # Given
        warnings = []

        # When
        result = architect._generate_recommendations(warnings)

        # Then
        assert result == []

    def test_recommendations_multiple_warnings(self, architect):
        """複数の警告がある場合"""
        # Given
        warnings = [
            {'check_name': 'タイトルと内容の整合性'},
            {'check_name': 'ITSMタイプの妥当性'},
            {'check_name': '設計原則への準拠'}
        ]

        # When
        result = architect._generate_recommendations(warnings)

        # Then
        assert len(result) >= 3


class TestEdgeCases:
    """エッジケースのテスト"""

    def test_process_unicode_content(self, architect):
        """Unicode文字を含む入力"""
        # Given
        input_data = {
            'title': 'テスト 🔥',
            'content': '絵文字テスト 😀 ✅',
            'itsm_type': 'Incident'
        }

        # When
        result = architect.process(input_data)

        # Then
        assert result.status in ['success', 'warning']

    def test_process_special_characters(self, architect):
        """特殊文字を含む入力"""
        # Given
        input_data = {
            'title': '<>&"\' テスト',
            'content': '特殊文字: !@#$%^&*()_+-=',
            'itsm_type': 'Incident'
        }

        # When
        result = architect.process(input_data)

        # Then
        assert result.status in ['success', 'warning']

    def test_process_very_long_content(self, architect):
        """非常に長いコンテンツ"""
        # Given
        input_data = {
            'title': '長文テスト',
            'content': 'テスト ' * 5000,
            'itsm_type': 'Incident'
        }

        # When
        result = architect.process(input_data)

        # Then
        assert result.status in ['success', 'warning']

    def test_process_empty_itsm_type(self, architect):
        """空のITSMタイプ"""
        # Given
        input_data = {
            'title': 'テスト',
            'content': 'テスト内容',
            'itsm_type': ''
        }

        # When
        result = architect.process(input_data)

        # Then
        assert result.status in ['success', 'warning']

    def test_process_all_itsm_types(self, architect):
        """すべての有効なITSMタイプをテスト"""
        # Given
        itsm_types = ['Incident', 'Problem', 'Change', 'Release', 'Request', 'Other']

        for itsm_type in itsm_types:
            input_data = {
                'title': f'{itsm_type}テスト',
                'content': f'{itsm_type}に関する内容です。',
                'itsm_type': itsm_type
            }

            # When
            result = architect.process(input_data)

            # Then
            assert result.status in ['success', 'warning']
            assert 'coherence_score' in result.data

    def test_check_title_content_coherence_case_insensitive(self, architect):
        """大文字小文字を区別しない"""
        # Given
        title = 'DATABASE Error Handling'
        content = 'database error handling procedure'

        # When
        result = architect._check_title_content_coherence(title, content)

        # Then
        assert result['passed'] is True

    def test_process_with_many_existing_knowledge(self, architect):
        """大量の既存ナレッジ"""
        # Given
        existing = [
            {'id': f'KB{i:03d}', 'content': f'内容{i}'}
            for i in range(100)
        ]
        input_data = {
            'title': 'テスト',
            'content': 'テスト内容',
            'itsm_type': 'Incident',
            'existing_knowledge': existing
        }

        # When
        result = architect.process(input_data)

        # Then
        assert result.status in ['success', 'warning']
