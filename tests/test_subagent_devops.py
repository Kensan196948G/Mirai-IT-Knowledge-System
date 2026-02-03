"""
DevOpsSubAgent 単体テスト
カバレッジ目標: 90%以上
"""

import pytest

from src.subagents.base import SubAgentResult
from src.subagents.devops import DevOpsSubAgent


@pytest.fixture
def devops():
    """DevOpsSubAgent インスタンスを生成"""
    return DevOpsSubAgent()


class TestDevOpsInit:
    """初期化テスト"""

    def test_init_success(self, devops):
        """正常な初期化"""
        assert devops.name == "devops"
        assert devops.role == "technical_analysis"
        assert devops.priority == "medium"


class TestDevOpsProcess:
    """process メソッドのテスト"""

    def test_process_success(self, devops):
        """正常系: 処理成功"""
        # Given
        input_data = {
            "title": "Apacheサーバーの再起動手順",
            "content": """
            定期的なメンテナンスとして、以下のコマンドを実行:
            ```bash
            systemctl restart apache2
            ```
            本番環境で実施。バックアップ取得済み。
            """,
            "itsm_type": "Change",
        }

        # When
        result = devops.process(input_data)

        # Then
        assert result.status == "success"
        assert "technical_elements" in result.data
        assert "automation_potential" in result.data
        assert "technical_risks" in result.data
        assert "commands" in result.data
        assert "improvements" in result.data

    def test_process_missing_required_fields(self, devops):
        """異常系: 必須フィールド不足"""
        # Given
        input_data = {"title": "テスト"}

        # When
        result = devops.process(input_data)

        # Then
        assert result.status == "failed"


class TestExtractTechnicalElements:
    """_extract_technical_elements メソッドのテスト"""

    def test_extract_os_elements(self, devops):
        """OS要素の抽出"""
        # Given
        content = "Linux サーバーで Ubuntu を使用"

        # When
        result = devops._extract_technical_elements(content)

        # Then
        assert any(elem["category"] == "OS" for elem in result)

    def test_extract_database_elements(self, devops):
        """データベース要素の抽出"""
        # Given
        content = "MySQL データベースと Redis を使用"

        # When
        result = devops._extract_technical_elements(content)

        # Then
        assert any(elem["category"] == "データベース" for elem in result)

    def test_extract_cloud_elements(self, devops):
        """クラウド要素の抽出"""
        # Given
        content = "AWS の EC2 と S3 を使用"

        # When
        result = devops._extract_technical_elements(content)

        # Then
        assert any(elem["category"] == "クラウド" for elem in result)


class TestEvaluateAutomationPotential:
    """_evaluate_automation_potential メソッドのテスト"""

    def test_automation_high_repetitive_task(self, devops):
        """繰り返しタスクで高い自動化可能性"""
        # Given
        content = """
        毎日定期的に実行する手順:
        1. ログをチェック
        2. バックアップを実行
        ```bash
        ./backup.sh
        ```
        """
        itsm_type = "Change"

        # When
        result = devops._evaluate_automation_potential(content, itsm_type)

        # Then
        assert result["score"] >= 0.7
        assert result["level"] == "high"

    def test_automation_medium_with_steps(self, devops):
        """手順明確で中程度の自動化可能性"""
        # Given
        content = """
        手順:
        1. サーバーにログイン
        2. 設定ファイルを編集
        3. サービス再起動
        """
        itsm_type = "Change"

        # When
        result = devops._evaluate_automation_potential(content, itsm_type)

        # Then
        assert result["score"] >= 0.2

    def test_automation_low_manual_task(self, devops):
        """手動作業で低い自動化可能性"""
        # Given
        content = "手動で確認してください。"
        itsm_type = "Incident"

        # When
        result = devops._evaluate_automation_potential(content, itsm_type)

        # Then
        assert result["level"] == "low"


class TestAnalyzeTechnicalRisks:
    """_analyze_technical_risks メソッドのテスト"""

    def test_analyze_deletion_risk(self, devops):
        """データ削除リスクの検出"""
        # Given
        content = "rm -rf /data を実行してファイルを削除"

        # When
        result = devops._analyze_technical_risks(content)

        # Then
        assert any(risk["risk"] == "データ削除リスク" for risk in result)
        assert any(risk["severity"] == "high" for risk in result)

    def test_analyze_production_risk(self, devops):
        """本番環境リスクの検出"""
        # Given
        content = "本番環境で変更を実施します。"

        # When
        result = devops._analyze_technical_risks(content)

        # Then
        assert any(risk["risk"] == "本番環境への影響" for risk in result)

    def test_analyze_service_stop_risk(self, devops):
        """サービス停止リスクの検出"""
        # Given
        content = "サービスを停止してメンテナンスを実施"

        # When
        result = devops._analyze_technical_risks(content)

        # Then
        assert any(risk["risk"] == "サービス停止リスク" for risk in result)

    def test_analyze_security_risk(self, devops):
        """セキュリティリスクの検出"""
        # Given
        content = "chmod 777 を実行して権限を変更"

        # When
        result = devops._analyze_technical_risks(content)

        # Then
        assert any(risk["risk"] == "セキュリティリスク" for risk in result)

    def test_analyze_credential_risk(self, devops):
        """認証情報リスクの検出"""
        # Given
        content = "パスワードと認証情報を設定"

        # When
        result = devops._analyze_technical_risks(content)

        # Then
        assert any(risk["risk"] == "認証情報の取り扱い" for risk in result)


class TestExtractCommands:
    """_extract_commands メソッドのテスト"""

    def test_extract_code_blocks(self, devops):
        """コードブロックの抽出"""
        # Given
        content = """
        実行コマンド:
        ```bash
        systemctl restart apache2
        systemctl status apache2
        ```
        """

        # When
        result = devops._extract_commands(content)

        # Then
        assert any(cmd["type"] == "code_block" for cmd in result)

    def test_extract_inline_commands(self, devops):
        """インラインコマンドの抽出"""
        # Given
        content = "`systemctl restart apache2` を実行してください。"

        # When
        result = devops._extract_commands(content)

        # Then
        assert any(cmd["type"] == "inline_command" for cmd in result)

    def test_extract_shell_commands(self, devops):
        """シェルコマンドの抽出"""
        # Given
        content = """
        $ ls -la
        # systemctl status
        """

        # When
        result = devops._extract_commands(content)

        # Then
        assert any(cmd["type"] == "shell_command" for cmd in result)

    def test_extract_commands_filter_short(self, devops):
        """短すぎるインラインコマンドは除外"""
        # Given
        content = "`ls` と `pwd` を実行"

        # When
        result = devops._extract_commands(content)

        # Then
        # 5文字以下は除外される
        inline_cmds = [cmd for cmd in result if cmd["type"] == "inline_command"]
        assert len(inline_cmds) == 0


class TestSuggestImprovements:
    """_suggest_improvements メソッドのテスト"""

    def test_improvements_automation_suggestion(self, devops):
        """自動化提案"""
        # Given
        content = """
        毎日実行する手順:
        ```bash
        backup.sh
        ```
        """
        automation_potential = {"score": 0.8, "recommendation": "自動化を推奨"}

        # When
        result = devops._suggest_improvements(content, automation_potential)

        # Then
        assert any("自動化" in imp for imp in result)

    def test_improvements_log_suggestion(self, devops):
        """ログ記録の提案"""
        # Given
        content = "エラーが発生しました。"
        automation_potential = {"score": 0.2}

        # When
        result = devops._suggest_improvements(content, automation_potential)

        # Then
        assert any("ログ" in imp for imp in result)

    def test_improvements_monitoring_suggestion(self, devops):
        """監視設定の提案"""
        # Given
        content = "障害が発生しました。"
        automation_potential = {"score": 0.2}

        # When
        result = devops._suggest_improvements(content, automation_potential)

        # Then
        assert any("監視" in imp for imp in result)

    def test_improvements_test_suggestion(self, devops):
        """テストの提案"""
        # Given
        content = "変更をリリースします。"
        automation_potential = {"score": 0.2}

        # When
        result = devops._suggest_improvements(content, automation_potential)

        # Then
        assert any("テスト" in imp for imp in result)

    def test_improvements_backup_suggestion(self, devops):
        """バックアップの提案"""
        # Given
        content = "データを削除します。"
        automation_potential = {"score": 0.2}

        # When
        result = devops._suggest_improvements(content, automation_potential)

        # Then
        assert any("バックアップ" in imp for imp in result)


class TestEdgeCases:
    """エッジケースのテスト"""

    def test_process_unicode(self, devops):
        """Unicode文字"""
        # Given
        input_data = {
            "title": "テスト 🔥",
            "content": "絵文字 😀",
            "itsm_type": "Incident",
        }

        # When
        result = devops.process(input_data)

        # Then
        assert result.status == "success"

    def test_process_very_long_content(self, devops):
        """非常に長いコンテンツ"""
        # Given
        input_data = {
            "title": "テスト",
            "content": "テスト " * 1000,
            "itsm_type": "Incident",
        }

        # When
        result = devops.process(input_data)

        # Then
        assert result.status == "success"

    def test_extract_technical_elements_multiple(self, devops):
        """複数の技術要素"""
        # Given
        content = "Linux MySQL Apache Docker Kubernetes AWS Python"

        # When
        result = devops._extract_technical_elements(content)

        # Then
        assert len(result) >= 5

    def test_analyze_technical_risks_multiple(self, devops):
        """複数のリスク"""
        # Given
        content = """
        本番環境でrm -rf を実行。
        サービスを停止してパスワードを変更。
        chmod 777 で権限を設定。
        """

        # When
        result = devops._analyze_technical_risks(content)

        # Then
        assert len(result) >= 4

    def test_automation_potential_maximum(self, devops):
        """最大自動化可能性"""
        # Given
        content = """
        毎日定期的に実行する手順:
        1. ステップ1
        2. ステップ2
        ```bash
        curl -X POST http://api.example.com
        ssh server.example.com "systemctl restart app"
        ```
        スクリプト化して自動実行。
        """
        itsm_type = "Change"

        # When
        result = devops._evaluate_automation_potential(content, itsm_type)

        # Then
        assert result["score"] >= 0.8
        assert result["level"] == "high"
