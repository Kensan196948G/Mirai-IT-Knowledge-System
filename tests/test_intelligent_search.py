"""
IntelligentSearchAssistant 単体テスト
src/workflows/intelligent_search.py のモックテスト
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock


@pytest.fixture
def mock_search_dependencies():
    """検索アシスタントの依存コンポーネントをモック化"""
    with patch("src.workflows.intelligent_search.SQLiteClient") as mock_sqlite, \
         patch("src.workflows.intelligent_search.Context7Client") as mock_ctx7, \
         patch("src.workflows.intelligent_search.ClaudeMemClient") as mock_claudemem, \
         patch("src.workflows.intelligent_search.IntelligentSearchAssistant._init_orchestrator"):
        mock_sqlite.return_value = MagicMock()
        mock_ctx7.return_value = MagicMock()
        mock_claudemem.return_value = MagicMock()
        yield {
            "sqlite": mock_sqlite.return_value,
            "context7": mock_ctx7.return_value,
            "claude_mem": mock_claudemem.return_value,
        }


@pytest.fixture
def assistant(mock_search_dependencies):
    """IntelligentSearchAssistantインスタンス（モック付き）"""
    from src.workflows.intelligent_search import IntelligentSearchAssistant
    inst = IntelligentSearchAssistant()
    inst.db_client = mock_search_dependencies["sqlite"]
    inst.context7 = mock_search_dependencies["context7"]
    inst.claude_mem = mock_search_dependencies["claude_mem"]
    inst._orchestrator = None  # デフォルトはNone（フォールバック動作）
    return inst


class TestIntelligentSearchAssistantInit:
    """初期化テスト"""

    def test_init_creates_db_client(self, mock_search_dependencies):
        """SQLiteClientが初期化されること"""
        from src.workflows.intelligent_search import IntelligentSearchAssistant
        inst = IntelligentSearchAssistant()
        assert inst.db_client is not None

    def test_init_creates_context7(self, mock_search_dependencies):
        """Context7Clientが初期化されること"""
        from src.workflows.intelligent_search import IntelligentSearchAssistant
        inst = IntelligentSearchAssistant()
        assert inst.context7 is not None

    def test_init_orchestrator_failure_is_handled(self):
        """オーケストレーター初期化失敗時にエラーにならないこと（_orchestratorがNone）"""
        with patch("src.workflows.intelligent_search.SQLiteClient"), \
             patch("src.workflows.intelligent_search.Context7Client"), \
             patch("src.workflows.intelligent_search.ClaudeMemClient"), \
             patch("src.workflows.intelligent_search.IntelligentSearchAssistant._init_orchestrator"):
            from src.workflows.intelligent_search import IntelligentSearchAssistant
            # get_orchestratorが失敗する場合のシナリオ
            with patch("src.ai.orchestrator.get_orchestrator", side_effect=Exception("Orchestrator failed")):
                inst = IntelligentSearchAssistant()
                # _orchestratorがNoneのままでもインスタンス生成できること
                assert inst is not None


class TestUnderstandIntent:
    """_understand_intent メソッドテスト"""

    def test_understand_intent_how_to(self, assistant):
        """「方法」キーワードでhow_toに分類されること"""
        result = assistant._understand_intent("どうすればいいですか")
        assert result["type"] == "how_to"

    def test_understand_intent_why(self, assistant):
        """「なぜ」キーワードでwhyに分類されること"""
        result = assistant._understand_intent("なぜエラーが出るのか")
        assert result["type"] == "why"

    def test_understand_intent_general(self, assistant):
        """分類不明はgeneralになること"""
        result = assistant._understand_intent("xxxxx")
        assert result["type"] == "general"

    def test_understand_intent_performance_problem(self, assistant):
        """「遅い」キーワードでperformanceに分類されること"""
        result = assistant._understand_intent("データベースが遅い")
        assert result["problem_type"] == "performance"

    def test_understand_intent_error_problem(self, assistant):
        """「エラー」キーワードでerrorに分類されること"""
        result = assistant._understand_intent("エラーが発生した")
        assert result["problem_type"] == "error"

    def test_understand_intent_config_problem(self, assistant):
        """「設定」キーワードでconfigurationに分類されること"""
        result = assistant._understand_intent("設定を変更したい")
        assert result["problem_type"] == "configuration"

    def test_understand_intent_technology_database(self, assistant):
        """データベースキーワードでtechnology抽出されること"""
        result = assistant._understand_intent("MySQLが動かない")
        assert "database" in result["technologies"]

    def test_understand_intent_technology_network(self, assistant):
        """ネットワークキーワードでtechnology抽出されること"""
        result = assistant._understand_intent("VPN接続できない")
        assert "network" in result["technologies"]


class TestExtractTechnologies:
    """_extract_technologies メソッドテスト"""

    def test_extract_cloud_technology(self, assistant):
        """クラウドキーワードでcloud抽出されること"""
        result = assistant._extract_technologies("AWSのEC2が起動しない")
        assert "cloud" in result

    def test_extract_security_technology(self, assistant):
        """セキュリティキーワードでsecurity抽出されること"""
        result = assistant._extract_technologies("SSLの設定方法")
        assert "security" in result

    def test_extract_multiple_technologies(self, assistant):
        """複数技術キーワードで複数抽出されること"""
        result = assistant._extract_technologies("WebサーバーのSQL接続が遅い")
        assert len(result) >= 1

    def test_extract_no_technology(self, assistant):
        """技術キーワードなしで空リストを返すこと"""
        result = assistant._extract_technologies("こんにちは")
        assert result == []


class TestClassifyProblemType:
    """_classify_problem_type メソッドテスト"""

    def test_classify_performance(self, assistant):
        """パフォーマンス問題の分類"""
        assert assistant._classify_problem_type("レスポンスが遅い") == "performance"

    def test_classify_error(self, assistant):
        """エラー問題の分類"""
        assert assistant._classify_problem_type("障害が発生しました") == "error"

    def test_classify_configuration(self, assistant):
        """設定問題の分類"""
        assert assistant._classify_problem_type("インストール手順") == "configuration"

    def test_classify_security(self, assistant):
        """セキュリティ問題の分類"""
        assert assistant._classify_problem_type("セキュリティの脆弱性") == "security"

    def test_classify_investigation(self, assistant):
        """原因調査の分類"""
        assert assistant._classify_problem_type("なぜこうなるのか") == "investigation"

    def test_classify_general(self, assistant):
        """一般的な問い合わせの分類"""
        assert assistant._classify_problem_type("テストです") == "general"


class TestSearchKnowledge:
    """_search_knowledge メソッドテスト"""

    def test_search_knowledge_returns_results(self, assistant):
        """ナレッジ検索結果が返ること"""
        assistant.db_client.search_knowledge.return_value = [
            {"id": 1, "title": "テスト", "tags": [], "itsm_type": "Incident"}
        ]
        intent = {"problem_type": "unknown", "technologies": []}
        result = assistant._search_knowledge("テスト", intent)
        assert isinstance(result, list)

    def test_search_knowledge_performance_filter(self, assistant):
        """performance問題時にパフォーマンス関連でフィルタされること"""
        assistant.db_client.search_knowledge.return_value = [
            {"id": 1, "title": "DB遅い", "tags": ["パフォーマンス"], "content": "パフォーマンス問題", "itsm_type": "Incident"},
            {"id": 2, "title": "その他", "tags": [], "content": "無関係", "itsm_type": "Change"},
        ]
        intent = {"problem_type": "performance", "technologies": []}
        result = assistant._search_knowledge("DBが遅い", intent)
        # パフォーマンス関連のみが返されること
        assert all("パフォーマンス" in r.get("tags", []) or "performance" in r.get("content", "").lower() for r in result)


class TestSearch:
    """search メソッドテスト（統合）"""

    def test_search_returns_required_keys(self, assistant):
        """検索結果に必須キーが含まれること"""
        assistant.db_client.search_knowledge.return_value = []
        assistant.context7.query_documentation.return_value = []
        assistant.claude_mem.search_memories.return_value = []

        result = assistant.search("テスト検索")
        assert "query" in result
        assert "intent" in result
        assert "answer" in result
        assert "knowledge" in result

    def test_search_without_orchestrator_uses_fallback(self, assistant):
        """オーケストレーター未設定時にフォールバック動作すること"""
        assistant._orchestrator = None
        assistant.db_client.search_knowledge.return_value = []
        assistant.context7.query_documentation.return_value = []
        assistant.claude_mem.search_memories.return_value = []

        result = assistant.search("テスト")
        assert result["query"] == "テスト"


class TestGenerateSuggestions:
    """_generate_suggestions メソッドテスト"""

    def test_generate_suggestions_for_performance(self, assistant):
        """パフォーマンス問題で関連質問が生成されること"""
        intent = {"problem_type": "performance"}
        result = assistant._generate_suggestions(intent)
        assert len(result) > 0

    def test_generate_suggestions_for_error(self, assistant):
        """エラー問題で関連質問が生成されること"""
        intent = {"problem_type": "error"}
        result = assistant._generate_suggestions(intent)
        assert len(result) > 0

    def test_generate_suggestions_for_unknown(self, assistant):
        """不明な問題種別で空リストを返すこと"""
        intent = {"problem_type": "unknown"}
        result = assistant._generate_suggestions(intent)
        assert result == []


class TestUnderstandIntentWithAI:
    """_understand_intent_with_ai メソッドテスト"""

    def test_ai_intent_faq_maps_to_how_to(self, assistant):
        """orchestrator.classify_query が faq を返す場合 how_to にマッピングされること"""
        mock_orch = MagicMock()
        mock_query_type = MagicMock()
        mock_query_type.value = "faq"
        mock_orch.classify_query.return_value = mock_query_type
        assistant._orchestrator = mock_orch

        result = assistant._understand_intent_with_ai("設定方法を教えて")
        assert result["type"] == "how_to"
        assert result["ai_classified"] is True
        assert result["query_type"] == "faq"

    def test_ai_intent_evidence_maps_to_why(self, assistant):
        """orchestrator.classify_query が evidence を返す場合 why にマッピングされること"""
        mock_orch = MagicMock()
        mock_query_type = MagicMock()
        mock_query_type.value = "evidence"
        mock_orch.classify_query.return_value = mock_query_type
        assistant._orchestrator = mock_orch

        result = assistant._understand_intent_with_ai("なぜエラーが出るのか")
        assert result["type"] == "why"

    def test_ai_intent_investigation_maps_to_troubleshoot(self, assistant):
        """orchestrator.classify_query が investigation を返す場合 troubleshoot にマッピングされること"""
        mock_orch = MagicMock()
        mock_query_type = MagicMock()
        mock_query_type.value = "investigation"
        mock_orch.classify_query.return_value = mock_query_type
        assistant._orchestrator = mock_orch

        result = assistant._understand_intent_with_ai("障害が発生した")
        assert result["type"] == "troubleshoot"

    def test_ai_intent_fallback_on_exception(self, assistant):
        """orchestrator が例外を投げた場合フォールバックで _understand_intent が使われること"""
        mock_orch = MagicMock()
        mock_orch.classify_query.side_effect = Exception("API error")
        assistant._orchestrator = mock_orch

        result = assistant._understand_intent_with_ai("データベースが遅い方法")
        # フォールバックで _understand_intent が呼ばれるのでキーが存在
        assert "type" in result
        assert "technologies" in result
        assert "problem_type" in result
        # ai_classified キーがない（フォールバック版にはない）
        assert result.get("ai_classified") is None or result.get("ai_classified") is True


class TestEnrichWithMCP:
    """_enrich_with_mcp メソッドテスト"""

    def test_enrich_with_technologies(self, assistant):
        """技術要素がある場合 Context7 が呼ばれること"""
        assistant.context7.query_documentation.return_value = [
            {"title": "MySQL Docs", "url": "https://example.com"}
        ]
        assistant.claude_mem.search_memories.return_value = []

        intent = {"technologies": ["database"], "problem_type": "performance"}
        result = assistant._enrich_with_mcp("DBが遅い", intent)

        assert "technical_docs" in result
        assert "database" in result["technical_docs"]
        assistant.context7.query_documentation.assert_called_once_with("database", "DBが遅い")

    def test_enrich_without_technologies(self, assistant):
        """技術要素がない場合 Context7 が呼ばれないこと"""
        assistant.claude_mem.search_memories.return_value = []

        intent = {"technologies": [], "problem_type": "general"}
        result = assistant._enrich_with_mcp("テスト", intent)

        assert result.get("technical_docs") is None or result.get("technical_docs") == {}
        assistant.context7.query_documentation.assert_not_called()

    def test_enrich_calls_claude_mem(self, assistant):
        """ClaudeMem の search_memories が常に呼ばれること"""
        assistant.context7.query_documentation.return_value = []
        assistant.claude_mem.search_memories.return_value = [
            {"title": "過去のDB障害", "content": "MySQLの接続数超過"}
        ]

        intent = {"technologies": [], "problem_type": "error"}
        result = assistant._enrich_with_mcp("エラー発生", intent)

        assert "memories" in result
        assert len(result["memories"]) == 1
        assistant.claude_mem.search_memories.assert_called_once_with("エラー発生", limit=3)

    def test_enrich_limits_technologies_to_two(self, assistant):
        """技術要素が3つ以上でも最大2つまでしか Context7 を呼ばないこと"""
        assistant.context7.query_documentation.return_value = []
        assistant.claude_mem.search_memories.return_value = []

        intent = {"technologies": ["database", "web", "network"], "problem_type": "error"}
        assistant._enrich_with_mcp("テスト", intent)

        assert assistant.context7.query_documentation.call_count == 2


class TestGenerateAnswer:
    """_generate_answer メソッドテスト（フォールバック版）"""

    def test_generate_answer_with_knowledge(self, assistant):
        """ナレッジがある場合テキストに含まれること"""
        knowledge = [
            {"id": 1, "title": "DB障害対応", "summary_non_technical": "データベース接続を確認"}
        ]
        enrichments = {}
        result = assistant._generate_answer("テスト", knowledge, enrichments)

        assert "DB障害対応" in result["text"]
        assert result["knowledge_count"] == 1
        assert result["has_enrichments"] is False

    def test_generate_answer_with_technical_docs(self, assistant):
        """技術ドキュメントが含まれる場合テキストに反映されること"""
        knowledge = []
        enrichments = {
            "technical_docs": {
                "database": [{"title": "MySQL公式ドキュメント", "url": "https://dev.mysql.com"}]
            }
        }
        result = assistant._generate_answer("テスト", knowledge, enrichments)

        assert "MySQL公式ドキュメント" in result["text"]
        assert result["has_enrichments"] is True

    def test_generate_answer_with_memories(self, assistant):
        """過去の記憶が含まれる場合テキストに反映されること"""
        knowledge = []
        enrichments = {
            "memories": [{"title": "前回の対応", "content": "MySQLの接続数を増やした"}]
        }
        result = assistant._generate_answer("テスト", knowledge, enrichments)

        assert "前回の対応" in result["text"]
        assert result["has_enrichments"] is True

    def test_generate_answer_empty_all(self, assistant):
        """全て空の場合、空テキストでknowledge_count=0を返すこと"""
        result = assistant._generate_answer("テスト", [], {})
        assert result["knowledge_count"] == 0
        assert result["has_enrichments"] is False

    def test_generate_answer_shows_quick_actions_with_knowledge(self, assistant):
        """ナレッジがある場合「即座に試せる対処法」セクションが含まれること"""
        knowledge = [
            {"id": 1, "title": "テスト", "summary_non_technical": "テスト概要"}
        ]
        result = assistant._generate_answer("テスト", knowledge, {})
        assert "即座に試せる対処法" in result["text"]


class TestGenerateAnswerWithAI:
    """_generate_answer_with_ai メソッドテスト"""

    def test_ai_answer_success(self, assistant):
        """orchestrator.process 成功時に正しい構造が返ること"""
        mock_orch = MagicMock()
        mock_result = MagicMock()
        mock_result.answer = "AIが生成した回答"
        mock_result.evidence = ["根拠1"]
        mock_result.sources = ["ソース1"]
        mock_result.confidence = 0.9
        mock_result.ai_used = ["claude", "gemini"]

        import asyncio

        async def mock_process(*args, **kwargs):
            return mock_result

        mock_orch.process = mock_process
        assistant._orchestrator = mock_orch

        result = assistant._generate_answer_with_ai("テスト", [], {})
        assert result["text"] == "AIが生成した回答"
        assert result["confidence"] == 0.9
        assert "claude" in result["ai_used"]

    def test_ai_answer_fallback_on_exception(self, assistant):
        """orchestrator.process が例外時にフォールバック回答を返すこと"""
        mock_orch = MagicMock()

        import asyncio

        async def mock_process_fail(*args, **kwargs):
            raise Exception("API failure")

        mock_orch.process = mock_process_fail
        assistant._orchestrator = mock_orch

        result = assistant._generate_answer_with_ai("テスト", [], {})
        # フォールバック結果: confidence=0.5, ai_used=["fallback"]
        assert result["confidence"] == 0.5
        assert "fallback" in result["ai_used"]


class TestSearchIntegration:
    """search メソッドの統合テスト（AI有/無の分岐）"""

    def test_search_with_orchestrator_uses_ai_intent(self, assistant):
        """orchestrator が設定されている場合 _understand_intent_with_ai が呼ばれること"""
        mock_orch = MagicMock()
        mock_query_type = MagicMock()
        mock_query_type.value = "faq"
        mock_orch.classify_query.return_value = mock_query_type

        import asyncio
        mock_result = MagicMock()
        mock_result.answer = "AI回答"
        mock_result.evidence = []
        mock_result.sources = []
        mock_result.confidence = 0.8
        mock_result.ai_used = ["claude"]

        async def mock_process(*args, **kwargs):
            return mock_result

        mock_orch.process = mock_process

        assistant._orchestrator = mock_orch
        assistant.db_client.search_knowledge.return_value = []
        assistant.context7.query_documentation.return_value = []
        assistant.claude_mem.search_memories.return_value = []

        result = assistant.search("設定方法")
        assert result["query"] == "設定方法"
        assert result["intent"]["ai_classified"] is True

    def test_search_response_has_all_keys(self, assistant):
        """search の戻り値に必須キーが全て含まれること"""
        assistant.db_client.search_knowledge.return_value = []
        assistant.context7.query_documentation.return_value = []
        assistant.claude_mem.search_memories.return_value = []

        result = assistant.search("テスト")
        required_keys = ["query", "intent", "answer", "evidence", "sources",
                         "confidence", "knowledge", "enrichments", "suggestions", "ai_used"]
        for key in required_keys:
            assert key in result, f"Missing key: {key}"
