"""
DocumenterSubAgent 単体テスト
カバレッジ目標: 90%以上
"""

import pytest

from src.subagents.base import SubAgentResult
from src.subagents.documenter import DocumenterSubAgent


@pytest.fixture
def documenter():
    """DocumenterSubAgent インスタンスを生成"""
    return DocumenterSubAgent()


class TestDocumenterInit:
    """初期化テスト"""

    def test_init_success(self, documenter):
        """正常な初期化"""
        assert documenter.name == "documenter"
        assert documenter.role == "formatting"
        assert documenter.priority == "medium"


class TestDocumenterProcess:
    """process メソッドのテスト"""

    def test_process_success(self, documenter):
        """正常系: 処理成功"""
        # Given
        input_data = {
            "title": "データベース障害対応",
            "content": "発生時刻: 10:00, 原因を特定し対応完了しました。",
            "itsm_type": "Incident",
            "tags": ["データベース", "障害対応"],
            "metadata": {"word_count": 20},
        }

        # When
        result = documenter.process(input_data)

        # Then
        assert result.status == "success"
        assert "summary_technical" in result.data
        assert "summary_non_technical" in result.data
        assert "summary_3lines" in result.data
        assert "markdown" in result.data
        assert "html" in result.data

    def test_process_missing_required_fields(self, documenter):
        """異常系: 必須フィールド不足"""
        # Given
        input_data = {"title": "テスト"}

        # When
        result = documenter.process(input_data)

        # Then
        assert result.status == "failed"

    def test_process_minimal_input(self, documenter):
        """正常系: 最小限の入力"""
        # Given
        input_data = {"title": "テスト", "content": "テスト内容"}

        # When
        result = documenter.process(input_data)

        # Then
        assert result.status == "success"


class TestGenerateTechnicalSummary:
    """_generate_technical_summary メソッドのテスト"""

    def test_technical_summary_incident(self, documenter):
        """Incidentタイプの技術要約"""
        # Given
        title = "DB障害"
        content = "発生時刻: 10:00, 影響範囲: 全体, 復旧完了"
        itsm_type = "Incident"

        # When
        result = documenter._generate_technical_summary(title, content, itsm_type)

        # Then
        assert "Incident" in result
        assert "DB障害" in result

    def test_technical_summary_problem(self, documenter):
        """Problemタイプの技術要約"""
        # Given
        title = "根本原因分析"
        content = "根本原因を特定し、再発防止策を実施"
        itsm_type = "Problem"

        # When
        result = documenter._generate_technical_summary(title, content, itsm_type)

        # Then
        assert "Problem" in result


class TestGenerateNonTechnicalSummary:
    """_generate_non_technical_summary メソッドのテスト"""

    def test_non_technical_summary_incident(self, documenter):
        """Incidentタイプの非技術者向け要約"""
        # Given
        title = "システム障害"
        content = "緊急対応が必要。全ユーザーに影響。解決しました。"
        itsm_type = "Incident"

        # When
        result = documenter._generate_non_technical_summary(title, content, itsm_type)

        # Then
        assert "インシデント" in result
        assert "緊急" in result

    def test_non_technical_summary_status_detection(self, documenter):
        """ステータス検出"""
        # Given
        title = "テスト"
        content = "対応中です。調査を進めています。"
        itsm_type = "Incident"

        # When
        result = documenter._generate_non_technical_summary(title, content, itsm_type)

        # Then
        assert "対応中" in result


class TestGenerate3LineSummary:
    """_generate_3line_summary メソッドのテスト"""

    def test_3line_summary_basic(self, documenter):
        """基本的な3行要約"""
        # Given
        title = "テスト"
        content = "発生しました。原因を特定しました。解決しました。"

        # When
        result = documenter._generate_3line_summary(title, content)

        # Then
        assert len(result) == 3
        assert all(isinstance(line, str) for line in result)

    def test_3line_summary_with_cause(self, documenter):
        """原因を含む要約"""
        # Given
        title = "テスト"
        content = "障害が発生。原因はメモリ不足。対策を実施。"

        # When
        result = documenter._generate_3line_summary(title, content)

        # Then
        assert len(result) == 3
        assert any("原因" in line for line in result if line)


class TestExtractIncidentSummary:
    """_extract_incident_summary メソッドのテスト"""

    def test_incident_summary_complete(self, documenter):
        """完全なインシデント情報"""
        # Given
        content = "発生時刻: 10:00, 影響範囲: 全体, 復旧完了"

        # When
        result = documenter._extract_incident_summary(content)

        # Then
        assert len(result) > 0
        assert "発生時刻記録あり" in result


class TestFormatAsMarkdown:
    """_format_as_markdown メソッドのテスト"""

    def test_markdown_format_basic(self, documenter):
        """基本的なMarkdownフォーマット"""
        # Given
        title = "テスト"
        content = "コンテンツ"
        itsm_type = "Incident"
        tags = ["タグ1"]
        summary_technical = "技術要約"
        summary_non_technical = "非技術要約"
        metadata = {}

        # When
        result = documenter._format_as_markdown(
            title,
            content,
            itsm_type,
            tags,
            summary_technical,
            summary_non_technical,
            metadata,
        )

        # Then
        assert "# テスト" in result
        assert "Incident" in result
        assert "タグ1" in result


class TestFormatAsHTML:
    """_format_as_html メソッドのテスト"""

    def test_html_format_basic(self, documenter):
        """基本的なHTMLフォーマット"""
        # Given
        title = "テスト"
        content = "コンテンツ"
        itsm_type = "Incident"
        tags = ["タグ1"]
        summary_technical = "技術要約"
        summary_non_technical = "非技術要約"

        # When
        result = documenter._format_as_html(
            title, content, itsm_type, tags, summary_technical, summary_non_technical
        )

        # Then
        assert "<html" in result
        assert "<title>テスト</title>" in result
        assert "Incident" in result


class TestEdgeCases:
    """エッジケースのテスト"""

    def test_process_unicode(self, documenter):
        """Unicode文字"""
        # Given
        input_data = {
            "title": "テスト 🔥",
            "content": "絵文字 😀",
            "itsm_type": "Incident",
        }

        # When
        result = documenter.process(input_data)

        # Then
        assert result.status == "success"

    def test_process_very_long_content(self, documenter):
        """非常に長いコンテンツ"""
        # Given
        input_data = {
            "title": "テスト",
            "content": "テスト " * 1000,
            "itsm_type": "Incident",
        }

        # When
        result = documenter.process(input_data)

        # Then
        assert result.status == "success"
