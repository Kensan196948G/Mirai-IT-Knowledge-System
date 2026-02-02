"""
KnowledgeCuratorSubAgent 単体テスト
カバレッジ目標: 90%以上
"""

import pytest

from src.subagents.base import SubAgentResult
from src.subagents.knowledge_curator import KnowledgeCuratorSubAgent


@pytest.fixture
def curator():
    """KnowledgeCuratorSubAgent インスタンスを生成"""
    return KnowledgeCuratorSubAgent()


class TestKnowledgeCuratorInit:
    """初期化テスト"""

    def test_init_success(self, curator):
        """正常な初期化"""
        assert curator.name == "knowledge_curator"
        assert curator.role == "organization"
        assert curator.priority == "high"


class TestCuratorProcess:
    """process メソッドのテスト"""

    def test_process_success(self, curator):
        """正常系: 処理成功"""
        # Given
        input_data = {
            "title": "データベース接続エラーの対処法",
            "content": """
            データベースサーバーへの接続エラーが発生しました。
            ネットワーク設定を確認し、DBサーバーを再起動しました。
            セキュリティ設定も見直しました。
            """,
            "itsm_type": "Incident",
        }

        # When
        result = curator.process(input_data)

        # Then
        assert result.status == "success"
        assert "tags" in result.data
        assert "categories" in result.data
        assert "keywords" in result.data
        assert "importance" in result.data
        assert "metadata" in result.data

    def test_process_missing_required_fields(self, curator):
        """異常系: 必須フィールド不足"""
        # Given
        input_data = {
            "title": "テスト"
            # contentが不足
        }

        # When
        result = curator.process(input_data)

        # Then
        assert result.status == "failed"
        assert result.message == "必須フィールドが不足しています"

    def test_process_with_default_itsm_type(self, curator):
        """正常系: ITSMタイプがデフォルト値"""
        # Given
        input_data = {"title": "テスト", "content": "テスト内容"}

        # When
        result = curator.process(input_data)

        # Then
        assert result.status == "success"


class TestExtractTags:
    """_extract_tags メソッドのテスト"""

    def test_extract_tech_tags_database(self, curator):
        """データベース関連タグの抽出"""
        # Given
        title = "データベーステスト"
        content = "MySQLデータベースのエラー対応"
        itsm_type = "Incident"

        # When
        result = curator._extract_tags(title, content, itsm_type)

        # Then
        assert "データベース" in result

    def test_extract_tech_tags_network(self, curator):
        """ネットワーク関連タグの抽出"""
        # Given
        title = "ネットワーク障害"
        content = "VPN接続エラーが発生、DNSの設定を確認"
        itsm_type = "Incident"

        # When
        result = curator._extract_tags(title, content, itsm_type)

        # Then
        assert "ネットワーク" in result

    def test_extract_tech_tags_security(self, curator):
        """セキュリティ関連タグの抽出"""
        # Given
        title = "セキュリティ対応"
        content = "ファイアウォール設定の脆弱性を修正"
        itsm_type = "Change"

        # When
        result = curator._extract_tags(title, content, itsm_type)

        # Then
        assert "セキュリティ" in result

    def test_extract_tags_incident_critical(self, curator):
        """Incidentタイプで緊急対応タグ"""
        # Given
        title = "緊急障害対応"
        content = "クリティカルな障害が発生しました"
        itsm_type = "Incident"

        # When
        result = curator._extract_tags(title, content, itsm_type)

        # Then
        assert "緊急対応" in result
        assert "障害対応" in result

    def test_extract_tags_problem_root_cause(self, curator):
        """Problemタイプで根本原因分析タグ"""
        # Given
        title = "根本原因分析"
        content = "root causeを特定し、再発防止対策を実施"
        itsm_type = "Problem"

        # When
        result = curator._extract_tags(title, content, itsm_type)

        # Then
        assert "根本原因分析" in result
        assert "再発防止" in result

    def test_extract_tags_change_maintenance(self, curator):
        """Changeタイプで定期メンテナンスタグ"""
        # Given
        title = "定期メンテナンス"
        content = "計画停止によるメンテナンスを実施"
        itsm_type = "Change"

        # When
        result = curator._extract_tags(title, content, itsm_type)

        # Then
        assert "計画停止" in result
        assert "定期メンテナンス" in result

    def test_extract_tags_release_deployment(self, curator):
        """Releaseタイプでリリースタグ"""
        # Given
        title = "アプリケーションリリース"
        content = "デプロイを実施し、ロールバック計画も準備"
        itsm_type = "Release"

        # When
        result = curator._extract_tags(title, content, itsm_type)

        # Then
        assert "リリース" in result or "ロールバック" in result

    def test_extract_tags_no_duplicates(self, curator):
        """重複タグが除去される"""
        # Given
        title = "データベースデータベース"
        content = "データベース database db mysql"
        itsm_type = "Incident"

        # When
        result = curator._extract_tags(title, content, itsm_type)

        # Then
        # データベースタグは1つだけ
        assert result.count("データベース") == 1


class TestClassifyCategories:
    """_classify_categories メソッドのテスト"""

    def test_classify_infrastructure(self, curator):
        """インフラカテゴリの分類"""
        # Given
        content = "インフラストラクチャーの設定を変更し、サーバーを再起動しました。"

        # When
        result = curator._classify_categories(content)

        # Then
        assert "インフラ" in result

    def test_classify_middleware(self, curator):
        """ミドルウェアカテゴリの分類"""
        # Given
        content = "Apacheミドルウェアの設定を変更しました。"

        # When
        result = curator._classify_categories(content)

        # Then
        assert "ミドルウェア" in result

    def test_classify_application(self, curator):
        """アプリケーションカテゴリの分類"""
        # Given
        content = "アプリケーションシステムのバグを修正しました。"

        # When
        result = curator._classify_categories(content)

        # Then
        assert "アプリケーション" in result

    def test_classify_security(self, curator):
        """セキュリティカテゴリの分類"""
        # Given
        content = "セキュリティの脆弱性を修正し、認証機能を強化しました。"

        # When
        result = curator._classify_categories(content)

        # Then
        assert "セキュリティ" in result

    def test_classify_no_category_default(self, curator):
        """カテゴリが見つからない場合"""
        # Given
        content = "一般的な内容です。"

        # When
        result = curator._classify_categories(content)

        # Then
        assert result == ["その他"]

    def test_classify_multiple_categories(self, curator):
        """複数カテゴリに該当する場合"""
        # Given
        content = """
        インフラの設定変更とアプリケーションのデプロイ、
        セキュリティパッチの適用を実施しました。
        """

        # When
        result = curator._classify_categories(content)

        # Then
        assert len(result) >= 2


class TestExtractKeywords:
    """_extract_keywords メソッドのテスト"""

    def test_extract_keywords_from_content(self, curator):
        """コンテンツからキーワードを抽出"""
        # Given
        content = "データベース データベース サーバー サーバー エラー エラー エラー"

        # When
        result = curator._extract_keywords(content)

        # Then
        assert len(result) > 0
        assert "エラー" in result  # 最頻出

    def test_extract_keywords_stopwords_excluded(self, curator):
        """ストップワードが除外される"""
        # Given
        content = "これはテストです。これはテストです。テストテストテスト。"

        # When
        result = curator._extract_keywords(content)

        # Then
        # ストップワード「これは」「です」は除外される
        assert "これ" not in result
        assert "です" not in result

    def test_extract_keywords_min_length(self, curator):
        """3文字未満の単語が除外される"""
        # Given
        content = "aa bb cc データベース データベース"

        # When
        result = curator._extract_keywords(content)

        # Then
        # 3文字以上のみ
        assert "aa" not in result
        assert "bb" not in result

    def test_extract_keywords_top_10(self, curator):
        """上位10件のみ返される"""
        # Given
        content = " ".join([f"word{i}" * (20 - i) for i in range(20)])

        # When
        result = curator._extract_keywords(content)

        # Then
        assert len(result) <= 10


class TestEvaluateImportance:
    """_evaluate_importance メソッドのテスト"""

    def test_importance_critical_keywords(self, curator):
        """緊急キーワードで重要度が上がる"""
        # Given
        title = "緊急障害対応"
        content = "クリティカルな障害が発生しました。"
        itsm_type = "Incident"

        # When
        result = curator._evaluate_importance(title, content, itsm_type)

        # Then
        assert result["score"] > 0.7
        assert result["level"] in ["high", "critical"]

    def test_importance_incident_type(self, curator):
        """Incidentタイプで重要度加点"""
        # Given
        title = "テスト"
        content = "テスト内容"
        itsm_type = "Incident"

        # When
        result = curator._evaluate_importance(title, content, itsm_type)

        # Then
        assert result["score"] >= 0.6

    def test_importance_problem_type(self, curator):
        """Problemタイプで重要度加点（より高い）"""
        # Given
        title = "テスト"
        content = "テスト内容"
        itsm_type = "Problem"

        # When
        result = curator._evaluate_importance(title, content, itsm_type)

        # Then
        assert result["score"] >= 0.7

    def test_importance_wide_impact(self, curator):
        """影響範囲が広い場合"""
        # Given
        title = "システム全体障害"
        content = "全ユーザーに影響する本番環境での障害"
        itsm_type = "Incident"

        # When
        result = curator._evaluate_importance(title, content, itsm_type)

        # Then
        assert result["score"] >= 0.8
        assert result["level"] == "critical"

    def test_importance_long_content(self, curator):
        """長いコンテンツで重要度加点"""
        # Given
        title = "テスト"
        content = "テスト内容。" * 100
        itsm_type = "Other"

        # When
        result = curator._evaluate_importance(title, content, itsm_type)

        # Then
        assert result["score"] >= 0.6

    def test_importance_low(self, curator):
        """低い重要度"""
        # Given
        title = "テスト"
        content = "短い内容"
        itsm_type = "Other"

        # When
        result = curator._evaluate_importance(title, content, itsm_type)

        # Then
        assert result["level"] in ["low", "medium"]


class TestGenerateMetadata:
    """_generate_metadata メソッドのテスト"""

    def test_metadata_basic_info(self, curator):
        """基本的なメタデータ生成"""
        # Given
        title = "テストタイトル"
        content = "テストコンテンツ"
        tags = ["タグ1", "タグ2"]
        categories = ["カテゴリ1"]

        # When
        result = curator._generate_metadata(title, content, tags, categories)

        # Then
        assert result["title_length"] == len(title)
        assert result["content_length"] == len(content)
        assert result["tag_count"] == 2
        assert result["category_count"] == 1

    def test_metadata_with_code_block(self, curator):
        """コードブロックを含む場合"""
        # Given
        title = "テスト"
        content = """
        実行コマンド:
        ```bash
        systemctl restart apache2
        ```
        """
        tags = []
        categories = []

        # When
        result = curator._generate_metadata(title, content, tags, categories)

        # Then
        assert result["has_code_block"] is True

    def test_metadata_with_url(self, curator):
        """URLを含む場合"""
        # Given
        title = "テスト"
        content = "詳細はhttps://example.comを参照してください。"
        tags = []
        categories = []

        # When
        result = curator._generate_metadata(title, content, tags, categories)

        # Then
        assert result["has_url"] is True

    def test_metadata_with_list(self, curator):
        """リストを含む場合"""
        # Given
        title = "テスト"
        content = """
        - 項目1
        - 項目2
        1. 番号付き項目
        """
        tags = []
        categories = []

        # When
        result = curator._generate_metadata(title, content, tags, categories)

        # Then
        assert result["has_list"] is True

    def test_metadata_word_count(self, curator):
        """単語数のカウント"""
        # Given
        title = "テスト"
        content = "これは テスト の コンテンツ です"
        tags = []
        categories = []

        # When
        result = curator._generate_metadata(title, content, tags, categories)

        # Then
        assert result["word_count"] == 5


class TestEdgeCases:
    """エッジケースのテスト"""

    def test_process_unicode_content(self, curator):
        """Unicode文字を含む入力"""
        # Given
        input_data = {
            "title": "テスト 🔥",
            "content": "絵文字テスト 😀 ✅",
            "itsm_type": "Incident",
        }

        # When
        result = curator.process(input_data)

        # Then
        assert result.status == "success"

    def test_process_special_characters(self, curator):
        """特殊文字を含む入力"""
        # Given
        input_data = {
            "title": "<>&\"' テスト",
            "content": "特殊文字: !@#$%^&*()_+-=",
            "itsm_type": "Incident",
        }

        # When
        result = curator.process(input_data)

        # Then
        assert result.status == "success"

    def test_process_very_long_content(self, curator):
        """非常に長いコンテンツ"""
        # Given
        input_data = {
            "title": "長文テスト",
            "content": "テスト " * 5000,
            "itsm_type": "Incident",
        }

        # When
        result = curator.process(input_data)

        # Then
        assert result.status == "success"

    def test_extract_tags_all_tech_categories(self, curator):
        """すべての技術カテゴリをカバー"""
        # Given
        title = "テスト"
        content = """
        Linux Windows データベース MySQL Apache Docker Kubernetes
        AWS Python ネットワーク VPN ストレージ NFS メモリ CPU
        バックアップ アプリケーション セキュリティ クラウド
        """
        itsm_type = "Incident"

        # When
        result = curator._extract_tags(title, content, itsm_type)

        # Then
        assert len(result) > 10

    def test_extract_keywords_empty_content(self, curator):
        """空のコンテンツ"""
        # Given
        content = ""

        # When
        result = curator._extract_keywords(content)

        # Then
        assert result == []

    def test_classify_categories_empty_content(self, curator):
        """空のコンテンツ"""
        # Given
        content = ""

        # When
        result = curator._classify_categories(content)

        # Then
        assert result == ["その他"]

    def test_importance_maximum_score(self, curator):
        """最大スコアが1.0を超えない"""
        # Given
        title = "緊急クリティカル重大障害"
        content = """
        緊急対応が必要なクリティカルな障害が本番環境の全体に発生しました。
        """ * 100
        itsm_type = "Problem"

        # When
        result = curator._evaluate_importance(title, content, itsm_type)

        # Then
        assert result["score"] <= 1.0
