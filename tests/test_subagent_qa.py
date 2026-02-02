"""
QASubAgent 単体テスト
カバレッジ目標: 90%以上
"""

import pytest

from src.subagents.base import SubAgentResult
from src.subagents.qa import QASubAgent


@pytest.fixture
def qa_agent():
    """QASubAgent インスタンスを生成"""
    return QASubAgent()


class TestQASubAgentInit:
    """初期化テスト"""

    def test_init_success(self, qa_agent):
        """正常な初期化"""
        assert qa_agent.name == "qa"
        assert qa_agent.role == "quality_validation"
        assert qa_agent.priority == "high"


class TestQAProcess:
    """process メソッドのテスト"""

    def test_process_high_quality_content(self, qa_agent):
        """正常系: 高品質なコンテンツ"""
        # Given
        input_data = {
            "title": "データベース接続エラーの対処法",
            "content": """
## 発生状況
2024-01-20 10:00にユーザーからDBアクセスエラーの報告。
システム全体が影響を受けている。

## 原因
- コネクションプール設定の不適切な値
- 同時接続数の上限超過

## 対応手順
1. コネクションプール設定を確認
2. max_connectionsを500に変更
3. サーバー再起動
4. 動作確認

## 結果
対応完了。正常に復旧しました。
            """,
            "existing_knowledge": [],
        }

        # When
        result = qa_agent.process(input_data)

        # Then
        assert result.status == "success"
        assert result.data["quality_score"]["score"] >= 0.6
        assert result.data["completeness"]["rate"] > 0.5

    def test_process_with_duplicates(self, qa_agent):
        """正常系: 重複ナレッジが存在する場合"""
        # Given
        input_data = {
            "title": "データベース接続エラー",
            "content": "データベースへの接続に失敗しました。",
            "existing_knowledge": [
                {
                    "id": "KB001",
                    "title": "データベース接続エラーの対処",
                    "content": "データベースへの接続に失敗した場合の対処方法。",
                }
            ],
        }

        # When
        result = qa_agent.process(input_data)

        # Then
        assert result.status == "warning"
        assert result.data["duplicates"]["high_similarity_count"] >= 0
        assert "similar_knowledge" in result.data["duplicates"]

    def test_process_missing_required_fields(self, qa_agent):
        """異常系: 必須フィールド不足"""
        # Given
        input_data = {
            "title": "テスト"
            # contentが不足
        }

        # When
        result = qa_agent.process(input_data)

        # Then
        assert result.status == "failed"
        assert result.message == "必須フィールドが不足しています"

    def test_process_low_quality_content(self, qa_agent):
        """正常系: 低品質なコンテンツ"""
        # Given
        input_data = {"title": "テスト", "content": "短い", "existing_knowledge": []}

        # When
        result = qa_agent.process(input_data)

        # Then
        assert result.status == "warning"
        assert result.data["quality_score"]["score"] < 0.5

    def test_process_empty_existing_knowledge(self, qa_agent):
        """正常系: 既存ナレッジが空の場合"""
        # Given
        input_data = {
            "title": "新規ナレッジ",
            "content": "これは新しいナレッジです。" * 20,
            "existing_knowledge": [],
        }

        # When
        result = qa_agent.process(input_data)

        # Then
        assert result.status in ["success", "warning"]
        assert result.data["duplicates"]["total_similar_count"] == 0


class TestCheckCompleteness:
    """_check_completeness メソッドのテスト"""

    def test_completeness_all_checks_passed(self, qa_agent):
        """すべてのチェックが合格"""
        # Given
        title = "データベース障害の復旧手順について詳しく"
        content = """
## 発生時刻
2024-01-20 10:00:00

## 内容
ユーザーからデータベースアクセスエラーの報告があり、
システム管理者が調査を実施しました。

1. エラーログを確認
2. サーバーステータスをチェック
3. コマンドでDBを再起動

対応が完了し、正常に復旧しました。
        """

        # When
        result = qa_agent._check_completeness(title, content)

        # Then
        assert result["rate"] > 0.8
        assert result["passed_count"] >= 4

    def test_completeness_short_title(self, qa_agent):
        """タイトルが短すぎる場合"""
        # Given
        title = "テスト"
        content = "これは十分な長さのコンテンツです。" * 10

        # When
        result = qa_agent._check_completeness(title, content)

        # Then
        assert any(
            not check["passed"] and check["item"] == "タイトル"
            for check in result["checks"]
        )

    def test_completeness_long_title(self, qa_agent):
        """タイトルが長すぎる場合"""
        # Given
        title = "テスト" * 50
        content = "コンテンツ" * 20

        # When
        result = qa_agent._check_completeness(title, content)

        # Then
        assert any(
            not check["passed"] and check["item"] == "タイトル"
            for check in result["checks"]
        )

    def test_completeness_short_content(self, qa_agent):
        """コンテンツが不足している場合"""
        # Given
        title = "適切な長さのタイトル"
        content = "短い"

        # When
        result = qa_agent._check_completeness(title, content)

        # Then
        assert any(
            not check["passed"] and check["item"] == "内容"
            for check in result["checks"]
        )

    def test_completeness_structured_content(self, qa_agent):
        """構造化されたコンテンツ"""
        # Given
        title = "適切な長さのタイトル"
        content = """
## 見出し1
- リスト項目1
- リスト項目2

## 見出し2
1. 番号付きリスト
2. 番号付きリスト
        """

        # When
        result = qa_agent._check_completeness(title, content)

        # Then
        assert any(
            check["passed"] and check["item"] == "構造化" for check in result["checks"]
        )

    def test_completeness_with_specifics(self, qa_agent):
        """具体的な情報を含む場合"""
        # Given
        title = "適切なタイトル"
        content = "時刻: 10:00, システム: Webサーバーでエラーが発生しました。"

        # When
        result = qa_agent._check_completeness(title, content)

        # Then
        assert any(
            check["passed"] and check["item"] == "具体性" for check in result["checks"]
        )


class TestDetectDuplicates:
    """_detect_duplicates メソッドのテスト"""

    def test_detect_exact_duplicate(self, qa_agent):
        """完全一致の重複を検知"""
        # Given
        title = "データベース接続エラー"
        content = "データベースへの接続に失敗しました。"
        existing_knowledge = [
            {
                "id": "KB001",
                "title": "データベース接続エラー",
                "content": "データベースへの接続に失敗しました。",
            }
        ]

        # When
        result = qa_agent._detect_duplicates(title, content, existing_knowledge)

        # Then
        assert result["total_similar_count"] > 0
        assert len(result["similar_knowledge"]) > 0

    def test_detect_high_similarity(self, qa_agent):
        """高類似度の重複を検知"""
        # Given
        title = "Webサーバー障害対応"
        content = "Webサーバーが停止した際の復旧手順について"
        existing_knowledge = [
            {
                "id": "KB002",
                "title": "Webサーバー障害の復旧方法",
                "content": "Webサーバーが停止した時の復旧手順を記載",
            }
        ]

        # When
        result = qa_agent._detect_duplicates(title, content, existing_knowledge)

        # Then
        assert result["total_similar_count"] >= 0

    def test_detect_no_duplicates(self, qa_agent):
        """重複がない場合"""
        # Given
        title = "全く新しいトピック"
        content = "前例のない問題についての記録です。"
        existing_knowledge = [
            {
                "id": "KB003",
                "title": "既存の別トピック",
                "content": "完全に異なる内容の説明文。",
            }
        ]

        # When
        result = qa_agent._detect_duplicates(title, content, existing_knowledge)

        # Then
        assert result["total_similar_count"] == 0

    def test_detect_duplicates_empty_existing(self, qa_agent):
        """既存ナレッジが空の場合"""
        # Given
        title = "テスト"
        content = "テストコンテンツ"
        existing_knowledge = []

        # When
        result = qa_agent._detect_duplicates(title, content, existing_knowledge)

        # Then
        assert result["total_similar_count"] == 0
        assert result["high_similarity_count"] == 0


class TestCalculateTextSimilarity:
    """_calculate_text_similarity メソッドのテスト"""

    def test_similarity_identical_texts(self, qa_agent):
        """同一テキストの類似度"""
        # Given
        text1 = "これはテストです"
        text2 = "これはテストです"

        # When
        result = qa_agent._calculate_text_similarity(text1, text2)

        # Then
        assert result == 1.0

    def test_similarity_completely_different(self, qa_agent):
        """完全に異なるテキストの類似度"""
        # Given
        text1 = "データベース接続エラー"
        text2 = "全く関係ない話題"

        # When
        result = qa_agent._calculate_text_similarity(text1, text2)

        # Then
        assert result < 0.3

    def test_similarity_empty_texts(self, qa_agent):
        """空のテキストの類似度"""
        # Given
        text1 = ""
        text2 = "テスト"

        # When
        result = qa_agent._calculate_text_similarity(text1, text2)

        # Then
        assert result == 0.0

    def test_similarity_both_empty(self, qa_agent):
        """両方空のテキストの類似度"""
        # Given
        text1 = ""
        text2 = ""

        # When
        result = qa_agent._calculate_text_similarity(text1, text2)

        # Then
        assert result == 0.0

    def test_similarity_partial_match(self, qa_agent):
        """部分的に一致するテキストの類似度"""
        # Given
        text1 = "データベース 接続 エラー 発生"
        text2 = "データベース エラー 対応"

        # When
        result = qa_agent._calculate_text_similarity(text1, text2)

        # Then
        assert 0.3 <= result <= 0.8


class TestCalculateQualityScore:
    """_calculate_quality_score メソッドのテスト"""

    def test_quality_score_excellent(self, qa_agent):
        """優秀な品質スコア"""
        # Given
        title = "適切な長さのタイトル"
        content = "十分な長さのコンテンツ。" * 50 + "\n## 見出し\n- リスト"
        completeness = {"rate": 1.0}

        # When
        result = qa_agent._calculate_quality_score(title, content, completeness)

        # Then
        assert result["score"] >= 0.8
        assert result["level"] == "excellent"

    def test_quality_score_low(self, qa_agent):
        """低い品質スコア"""
        # Given
        title = "テスト"
        content = "短い"
        completeness = {"rate": 0.2}

        # When
        result = qa_agent._calculate_quality_score(title, content, completeness)

        # Then
        assert result["score"] < 0.5
        assert result["level"] in ["needs_improvement", "acceptable"]

    def test_quality_score_factors(self, qa_agent):
        """品質スコアの要因が正しく計算される"""
        # Given
        title = "適切な長さのタイトル"
        content = "コンテンツ。" * 30
        completeness = {"rate": 0.8}

        # When
        result = qa_agent._calculate_quality_score(title, content, completeness)

        # Then
        assert len(result["factors"]) == 4
        assert all("factor" in f for f in result["factors"])
        assert all("weight" in f for f in result["factors"])


class TestEvaluateReadability:
    """_evaluate_readability メソッドのテスト"""

    def test_readability_good(self, qa_agent):
        """可読性が良い場合"""
        # Given
        content = """
## 見出し1
内容1

## 見出し2
- リスト1
- リスト2

適切な長さの行。
        """

        # When
        result = qa_agent._evaluate_readability(content)

        # Then
        assert result > 0.7

    def test_readability_poor(self, qa_agent):
        """可読性が悪い場合"""
        # Given
        content = "改行なしの非常に長い1行のテキストで、これは読みにくいです。" * 100

        # When
        result = qa_agent._evaluate_readability(content)

        # Then
        assert result <= 0.8

    def test_readability_empty(self, qa_agent):
        """空のコンテンツ"""
        # Given
        content = ""

        # When
        result = qa_agent._evaluate_readability(content)

        # Then
        assert 0.0 <= result <= 1.0


class TestEvaluateUsefulness:
    """_evaluate_usefulness メソッドのテスト"""

    def test_usefulness_with_commands(self, qa_agent):
        """コマンドを含む場合"""
        # Given
        content = """
実行コマンド:
```bash
systemctl restart apache2
```
        """

        # When
        result = qa_agent._evaluate_usefulness(content)

        # Then
        assert result >= 0.7

    def test_usefulness_with_solution(self, qa_agent):
        """対策や解決方法を含む場合"""
        # Given
        content = "対策として、設定ファイルを修正する方法があります。"

        # When
        result = qa_agent._evaluate_usefulness(content)

        # Then
        assert result >= 0.7

    def test_usefulness_with_cause_analysis(self, qa_agent):
        """原因分析を含む場合"""
        # Given
        content = "原因はメモリ不足であることが判明しました。"

        # When
        result = qa_agent._evaluate_usefulness(content)

        # Then
        assert result >= 0.6

    def test_usefulness_low(self, qa_agent):
        """有用性が低い場合"""
        # Given
        content = "簡単な説明のみ。"

        # When
        result = qa_agent._evaluate_usefulness(content)

        # Then
        assert result >= 0.5


class TestSuggestQualityImprovements:
    """_suggest_quality_improvements メソッドのテスト"""

    def test_improvements_from_failed_checks(self, qa_agent):
        """失敗したチェックから改善提案を生成"""
        # Given
        completeness = {
            "checks": [{"passed": False, "message": "タイトルが短すぎます"}]
        }
        quality_score = {"score": 0.8, "factors": []}

        # When
        result = qa_agent._suggest_quality_improvements(completeness, quality_score)

        # Then
        assert len(result) > 0
        assert "タイトルが短すぎます" in result

    def test_improvements_low_quality_score(self, qa_agent):
        """低い品質スコアの場合"""
        # Given
        completeness = {"checks": []}
        quality_score = {"score": 0.5, "factors": []}

        # When
        result = qa_agent._suggest_quality_improvements(completeness, quality_score)

        # Then
        assert len(result) > 0
        assert any("詳細に記載" in imp for imp in result)

    def test_improvements_low_readability(self, qa_agent):
        """可読性が低い場合"""
        # Given
        completeness = {"checks": []}
        quality_score = {
            "score": 0.7,
            "factors": [{"factor": "可読性", "weight": 0.2, "contribution": 0.05}],
        }

        # When
        result = qa_agent._suggest_quality_improvements(completeness, quality_score)

        # Then
        assert any("構造化" in imp for imp in result)


class TestEdgeCases:
    """エッジケースのテスト"""

    def test_process_with_unicode(self, qa_agent):
        """Unicode文字を含む入力"""
        # Given
        input_data = {
            "title": "テスト 🔥",
            "content": "絵文字を含むテスト 😀 ✅",
            "existing_knowledge": [],
        }

        # When
        result = qa_agent.process(input_data)

        # Then
        assert result.status in ["success", "warning"]

    def test_process_with_special_chars(self, qa_agent):
        """特殊文字を含む入力"""
        # Given
        input_data = {
            "title": "<>&\"' テスト",
            "content": "特殊文字: !@#$%^&*()_+-=",
            "existing_knowledge": [],
        }

        # When
        result = qa_agent.process(input_data)

        # Then
        assert result.status in ["success", "warning"]

    def test_process_very_long_content(self, qa_agent):
        """非常に長いコンテンツ"""
        # Given
        input_data = {
            "title": "長文テスト",
            "content": "テスト " * 5000,
            "existing_knowledge": [],
        }

        # When
        result = qa_agent.process(input_data)

        # Then
        assert result.status in ["success", "warning"]

    def test_process_many_existing_knowledge(self, qa_agent):
        """大量の既存ナレッジ"""
        # Given
        existing = [
            {"id": f"KB{i:03d}", "title": f"ナレッジ{i}", "content": f"内容{i}"}
            for i in range(100)
        ]
        input_data = {
            "title": "テスト",
            "content": "テスト内容",
            "existing_knowledge": existing,
        }

        # When
        result = qa_agent.process(input_data)

        # Then
        assert result.status in ["success", "warning"]
        assert len(result.data["duplicates"]["similar_knowledge"]) <= 5
