"""
Hooks詳細単体テスト
5種類のHooksの動作を検証
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest

from src.hooks.auto_summary import AutoSummaryHook
from src.hooks.base import BaseHook, HookResponse, HookResult
from src.hooks.deviation_check import DeviationCheckHook
from src.hooks.duplicate_check import DuplicateCheckHook
from src.hooks.post_task import PostTaskHook
from src.hooks.pre_task import PreTaskHook

# ========== BaseHook テスト ==========


class TestBaseHook:
    """BaseHookの基本機能テスト"""

    def test_hook_result_enum_values(self):
        """HookResultの列挙値が正しいこと"""
        assert HookResult.PASS.value == "pass"
        assert HookResult.WARNING.value == "warning"
        assert HookResult.ERROR.value == "error"

    def test_hook_response_initialization(self):
        """HookResponseの初期化が正しいこと"""
        response = HookResponse(
            result=HookResult.PASS,
            message="Test message",
            details={"key": "value"},
            block_execution=False,
        )
        assert response.result == HookResult.PASS
        assert response.message == "Test message"
        assert response.details == {"key": "value"}
        assert response.block_execution is False

    def test_hook_response_to_dict(self):
        """HookResponseの辞書変換が正しいこと"""
        response = HookResponse(
            result=HookResult.WARNING, message="Warning message", details={"count": 3}
        )
        result_dict = response.to_dict()
        assert result_dict["result"] == "warning"
        assert result_dict["message"] == "Warning message"
        assert result_dict["details"]["count"] == 3
        assert result_dict["block_execution"] is False

    def test_hook_response_default_details(self):
        """HookResponseのdetailsがNoneの場合デフォルトで空辞書になること"""
        response = HookResponse(result=HookResult.PASS, message="Test")
        assert response.details == {}


# ========== PreTaskHook テスト ==========


class TestPreTaskHook:
    """PreTaskHookの詳細テスト"""

    @pytest.fixture
    def hook(self):
        """PreTaskHookインスタンスを生成"""
        return PreTaskHook()

    def test_valid_input_returns_pass(self, hook):
        """正常な入力データでPASSが返ること"""
        context = {
            "title": "テストタイトル",
            "content": "これは20文字以上のテスト内容です。正常なデータです。",
            "itsm_type": "Incident",
        }
        result = hook.execute(context)
        assert result.result == HookResult.PASS
        assert result.block_execution is False
        assert "recommended_subagents" in result.details

    def test_empty_title_returns_error(self, hook):
        """タイトルが空の場合ERRORが返り、実行がブロックされること"""
        context = {
            "title": "",
            "content": "これは20文字以上のテスト内容です。",
            "itsm_type": "Incident",
        }
        result = hook.execute(context)
        assert result.result == HookResult.ERROR
        assert result.block_execution is True
        assert "タイトルが空です" in result.message

    def test_empty_content_returns_error(self, hook):
        """内容が空の場合ERRORが返り、実行がブロックされること"""
        context = {"title": "テストタイトル", "content": "", "itsm_type": "Incident"}
        result = hook.execute(context)
        assert result.result == HookResult.ERROR
        assert result.block_execution is True
        assert "内容が空です" in result.message

    def test_short_title_returns_error(self, hook):
        """タイトルが短すぎる場合ERRORが返ること"""
        context = {
            "title": "短い",
            "content": "これは20文字以上のテスト内容です。",
            "itsm_type": "Incident",
        }
        result = hook.execute(context)
        assert result.result == HookResult.ERROR
        assert result.block_execution is True
        assert "タイトルが短すぎます" in result.message

    def test_short_content_returns_error(self, hook):
        """内容が短すぎる場合ERRORが返ること"""
        context = {
            "title": "テストタイトル",
            "content": "短い",
            "itsm_type": "Incident",
        }
        result = hook.execute(context)
        assert result.result == HookResult.ERROR
        assert result.block_execution is True
        assert "内容が短すぎます" in result.message

    def test_invalid_itsm_type_returns_error(self, hook):
        """無効なITSMタイプの場合ERRORが返ること"""
        context = {
            "title": "テストタイトル",
            "content": "これは20文字以上のテスト内容です。正常なデータです。",
            "itsm_type": "InvalidType",
        }
        result = hook.execute(context)
        assert result.result == HookResult.ERROR
        assert result.block_execution is True
        assert "無効なITSMタイプ" in result.message

    def test_recommend_core_subagents(self, hook):
        """コアサブエージェントが推奨されること"""
        context = {
            "title": "テストタイトル",
            "content": "これは20文字以上のテスト内容です。正常なデータです。",
            "itsm_type": "Incident",
        }
        result = hook.execute(context)
        subagents = result.details["recommended_subagents"]

        # コアサブエージェントが含まれているか確認
        subagent_names = [s["name"] for s in subagents]
        assert "architect" in subagent_names
        assert "knowledge_curator" in subagent_names
        assert "itsm_expert" in subagent_names
        assert "qa" in subagent_names
        assert "documenter" in subagent_names

    def test_recommend_devops_for_technical_content(self, hook):
        """技術的なキーワードがある場合DevOpsサブエージェントが推奨されること"""
        context = {
            "title": "デプロイスクリプトの自動化",
            "content": "本番環境へのデプロイコマンドを自動化するスクリプトを作成しました。",
            "itsm_type": "Change",
        }
        result = hook.execute(context)
        subagents = result.details["recommended_subagents"]

        # DevOpsサブエージェントが含まれているか確認
        subagent_names = [s["name"] for s in subagents]
        assert "devops" in subagent_names


# ========== PostTaskHook テスト ==========


class TestPostTaskHook:
    """PostTaskHookの詳細テスト"""

    @pytest.fixture
    def hook(self):
        """PostTaskHookインスタンスを生成"""
        return PostTaskHook()

    def test_all_success_returns_pass(self, hook):
        """全サブエージェントが成功した場合PASSが返ること"""
        context = {
            "subagent_results": {
                "architect": {"status": "success", "message": "OK"},
                "qa": {"status": "success", "message": "OK"},
            },
            "hook_results": [],
        }
        result = hook.execute(context)
        assert result.result == HookResult.PASS
        assert result.block_execution is False
        assert result.details["overall_assessment"]["quality_level"] in [
            "excellent",
            "good",
        ]

    def test_warnings_present_returns_warning(self, hook):
        """警告がある場合WARNINGが返ること"""
        context = {
            "subagent_results": {
                "architect": {"status": "success", "message": "OK"},
                "qa": {"status": "warning", "message": "類似ナレッジあり"},
            },
            "hook_results": [],
        }
        result = hook.execute(context)
        assert result.result == HookResult.WARNING
        assert "警告" in result.message

    def test_errors_present_returns_error(self, hook):
        """エラーがある場合ERRORが返ること"""
        context = {
            "subagent_results": {
                "architect": {"status": "success", "message": "OK"},
                "qa": {"status": "failed", "message": "重大なエラー"},
            },
            "hook_results": [],
        }
        result = hook.execute(context)
        assert result.result == HookResult.ERROR
        assert "重大な問題" in result.message

    def test_quality_score_calculation(self, hook):
        """品質スコアが正しく計算されること"""
        context = {
            "subagent_results": {
                "agent1": {"status": "success", "message": "OK"},
                "agent2": {"status": "success", "message": "OK"},
                "agent3": {"status": "failed", "message": "エラー"},
            },
            "hook_results": [],
        }
        result = hook.execute(context)
        assessment = result.details["overall_assessment"]

        # 成功率は2/3 = 0.67、失敗があるので quality_score は 0.67 * 0.5 = 0.335
        assert assessment["success_rate"] > 0.6
        assert assessment["quality_score"] < 0.5
        assert assessment["critical_issues"] == 1

    def test_collect_issues_from_hooks(self, hook):
        """フックからの問題も集約されること"""
        context = {
            "subagent_results": {"architect": {"status": "success", "message": "OK"}},
            "hook_results": [
                {
                    "hook_name": "duplicate_check",
                    "result": "warning",
                    "message": "重複検出",
                }
            ],
        }
        result = hook.execute(context)
        issues = result.details["issues"]

        # フックからの問題が含まれているか
        hook_issues = [i for i in issues if "Hook" in i["source"]]
        assert len(hook_issues) > 0


# ========== DuplicateCheckHook テスト ==========


class TestDuplicateCheckHook:
    """DuplicateCheckHookの詳細テスト"""

    @pytest.fixture
    def hook(self):
        """DuplicateCheckHookインスタンスを生成"""
        return DuplicateCheckHook(similarity_threshold=0.85)

    def test_no_duplicates_returns_pass(self, hook):
        """重複がない場合PASSが返ること"""
        context = {
            "qa_result": {
                "duplicates": {"similar_knowledge": [], "high_similarity_count": 0}
            }
        }
        result = hook.execute(context)
        assert result.result == HookResult.PASS
        assert result.block_execution is False

    def test_high_similarity_returns_warning(self, hook):
        """高い類似度の重複がある場合WARNINGが返ること"""
        context = {
            "qa_result": {
                "duplicates": {
                    "similar_knowledge": [
                        {
                            "knowledge_id": 1,
                            "overall_similarity": 0.9,
                            "title": "類似ナレッジ",
                        }
                    ],
                    "high_similarity_count": 1,
                }
            }
        }
        result = hook.execute(context)
        assert result.result == HookResult.WARNING
        assert "高い類似度" in result.message
        assert result.block_execution is False  # 警告のみ、ブロックしない

    def test_medium_similarity_returns_warning(self, hook):
        """中程度の類似度がある場合WARNINGが返ること"""
        context = {
            "qa_result": {
                "duplicates": {
                    "similar_knowledge": [
                        {
                            "knowledge_id": 2,
                            "overall_similarity": 0.7,
                            "title": "類似ナレッジ",
                        }
                    ],
                    "high_similarity_count": 0,
                }
            }
        }
        result = hook.execute(context)
        assert result.result == HookResult.WARNING
        assert "類似ナレッジが見つかりました" in result.message

    def test_threshold_setting(self, hook):
        """類似度閾値が正しく設定できること"""
        hook.set_threshold(0.75)
        assert hook.similarity_threshold == 0.75

    def test_invalid_threshold_raises_error(self, hook):
        """無効な閾値でエラーが発生すること"""
        with pytest.raises(ValueError):
            hook.set_threshold(1.5)


# ========== DeviationCheckHook テスト ==========


class TestDeviationCheckHook:
    """DeviationCheckHookの詳細テスト"""

    @pytest.fixture
    def hook(self):
        """DeviationCheckHookインスタンスを生成"""
        return DeviationCheckHook()

    def test_no_deviations_returns_pass(self, hook):
        """逸脱がない場合PASSが返ること"""
        context = {"itsm_expert_result": {"deviations": [], "compliance_score": 0.95}}
        result = hook.execute(context)
        assert result.result == HookResult.PASS
        assert "準拠しています" in result.message

    def test_error_deviations_returns_error(self, hook):
        """エラーレベルの逸脱がある場合ERRORが返ること"""
        context = {
            "itsm_expert_result": {
                "deviations": [
                    {
                        "deviation_type": "missing_info",
                        "severity": "error",
                        "description": "必須情報が不足",
                    }
                ],
                "compliance_score": 0.5,
            }
        }
        result = hook.execute(context)
        assert result.result == HookResult.ERROR
        assert "重大な逸脱" in result.message
        assert result.block_execution is False  # 警告のみ、強制ブロックしない

    def test_warning_deviations_returns_warning(self, hook):
        """警告レベルの逸脱がある場合WARNINGが返ること"""
        context = {
            "itsm_expert_result": {
                "deviations": [
                    {
                        "deviation_type": "recommendation",
                        "severity": "warning",
                        "description": "推奨事項が不足",
                    }
                ],
                "compliance_score": 0.8,
            }
        }
        result = hook.execute(context)
        assert result.result == HookResult.WARNING
        assert "逸脱が検出されました" in result.message

    def test_low_compliance_score_returns_warning(self, hook):
        """準拠度が低い場合WARNINGが返ること"""
        context = {
            "itsm_expert_result": {
                "deviations": [],
                "compliance_score": 0.6,
                "principle_checks": [],
            }
        }
        result = hook.execute(context)
        assert result.result == HookResult.WARNING
        assert "準拠度が低いです" in result.message


# ========== AutoSummaryHook テスト ==========


class TestAutoSummaryHook:
    """AutoSummaryHookの詳細テスト"""

    @pytest.fixture
    def hook(self):
        """AutoSummaryHookインスタンスを生成"""
        return AutoSummaryHook(max_lines=3)

    def test_valid_summary_returns_pass(self, hook):
        """正常な3行要約でPASSが返ること"""
        context = {
            "documenter_result": {
                "summary_3lines": [
                    "要約の1行目です。",
                    "要約の2行目です。",
                    "要約の3行目です。",
                ]
            }
        }
        result = hook.execute(context)
        assert result.result == HookResult.PASS
        assert "正常に生成されました" in result.message
        assert result.details["line_count"] == 3

    def test_missing_summary_returns_warning(self, hook):
        """要約が生成されていない場合WARNINGが返ること"""
        context = {"documenter_result": {"summary_3lines": []}}
        result = hook.execute(context)
        assert result.result == HookResult.WARNING
        assert "生成に失敗しました" in result.message

    def test_incomplete_summary_returns_warning(self, hook):
        """要約が不完全な場合WARNINGが返ること"""
        context = {
            "documenter_result": {
                "summary_3lines": ["要約の1行目です。", "要約の2行目です。"]
            }
        }
        result = hook.execute(context)
        assert result.result == HookResult.WARNING
        assert "不完全です" in result.message
        assert result.details["valid_line_count"] == 2

    def test_empty_lines_are_filtered(self, hook):
        """空行がフィルタされること"""
        context = {
            "documenter_result": {"summary_3lines": ["要約の1行目です。", "", "   "]}
        }
        result = hook.execute(context)
        assert result.result == HookResult.WARNING
        assert result.details["valid_line_count"] == 1


# ========== 全Hooksの共通動作テスト ==========


class TestHooksCommonBehavior:
    """全Hooksの共通動作テスト"""

    def test_all_hooks_have_is_enabled(self):
        """全てのHooksがis_enabled()メソッドを持つこと"""
        hooks = [
            PreTaskHook(),
            PostTaskHook(),
            DuplicateCheckHook(),
            DeviationCheckHook(),
            AutoSummaryHook(),
        ]
        for hook in hooks:
            assert hook.is_enabled() is True

    def test_all_hooks_can_be_disabled(self):
        """全てのHooksが無効化できること"""
        hooks = [
            PreTaskHook(),
            PostTaskHook(),
            DuplicateCheckHook(),
            DeviationCheckHook(),
            AutoSummaryHook(),
        ]
        for hook in hooks:
            hook.set_enabled(False)
            assert hook.is_enabled() is False

    def test_all_hooks_return_hook_response(self):
        """全てのHooksがHookResponseを返すこと"""
        test_contexts = {
            "pre_task": {
                "title": "テストタイトル",
                "content": "これは20文字以上のテスト内容です。",
                "itsm_type": "Incident",
            },
            "post_task": {
                "subagent_results": {"agent1": {"status": "success", "message": "OK"}},
                "hook_results": [],
            },
            "duplicate_check": {
                "qa_result": {
                    "duplicates": {"similar_knowledge": [], "high_similarity_count": 0}
                }
            },
            "deviation_check": {
                "itsm_expert_result": {"deviations": [], "compliance_score": 0.9}
            },
            "auto_summary": {
                "documenter_result": {"summary_3lines": ["Line1", "Line2", "Line3"]}
            },
        }

        hooks = {
            "pre_task": PreTaskHook(),
            "post_task": PostTaskHook(),
            "duplicate_check": DuplicateCheckHook(),
            "deviation_check": DeviationCheckHook(),
            "auto_summary": AutoSummaryHook(),
        }

        for hook_name, hook in hooks.items():
            result = hook.execute(test_contexts[hook_name])
            assert isinstance(result, HookResponse)
            assert hasattr(result, "result")
            assert hasattr(result, "message")
            assert hasattr(result, "details")
            assert hasattr(result, "block_execution")
