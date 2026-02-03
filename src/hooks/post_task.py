"""
Post-Task Hook
タスク完了後の統合レビューフック
"""

from typing import Any, Dict, List

from .base import BaseHook, HookResponse, HookResult


class PostTaskHook(BaseHook):
    """タスク後処理フック"""

    def __init__(self):
        super().__init__(name="post-task", hook_type="post-task", enabled=True)

    def execute(self, context: Dict[str, Any]) -> HookResponse:
        """
        全サブエージェント実行後の統合レビュー

        Args:
            context: {
                'subagent_results': dict,  # 全サブエージェントの結果
                'hook_results': list  # これまでのフック実行結果
            }

        Returns:
            フック実行結果
        """
        subagent_results = context.get("subagent_results", {})
        hook_results = context.get("hook_results", [])

        # 1. サブエージェント実行結果の統合
        integration_report = self._integrate_subagent_results(subagent_results)

        # 2. 警告・エラーの集約
        issues = self._collect_issues(subagent_results, hook_results)

        # 3. 総合評価
        overall_assessment = self._assess_overall_quality(integration_report, issues)

        # 結果判定
        if overall_assessment["critical_issues"] > 0:
            result = HookResult.ERROR
            message = f"{overall_assessment['critical_issues']}件の重大な問題があります"
        elif overall_assessment["warnings"] > 0:
            result = HookResult.WARNING
            message = f"{overall_assessment['warnings']}件の警告があります"
        else:
            result = HookResult.PASS
            message = "全チェックが正常に完了しました"

        return HookResponse(
            result=result,
            message=message,
            details={
                "integration_report": integration_report,
                "issues": issues,
                "overall_assessment": overall_assessment,
            },
            block_execution=False,
        )

    def _integrate_subagent_results(
        self, subagent_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """サブエージェント結果を統合"""
        report = {"executed_subagents": [], "successful": 0, "failed": 0, "warnings": 0}

        for subagent_name, result in subagent_results.items():
            report["executed_subagents"].append(subagent_name)

            status = result.get("status", "unknown")
            if status == "success":
                report["successful"] += 1
            elif status == "failed":
                report["failed"] += 1
            elif status == "warning":
                report["warnings"] += 1

        return report

    def _collect_issues(
        self, subagent_results: Dict[str, Any], hook_results: List[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """警告・エラーを集約"""
        issues = []

        # サブエージェントからの問題
        for subagent_name, result in subagent_results.items():
            if result.get("status") in ["failed", "warning"]:
                issues.append(
                    {
                        "source": f"SubAgent: {subagent_name}",
                        "severity": (
                            "error" if result.get("status") == "failed" else "warning"
                        ),
                        "message": result.get("message", "不明なエラー"),
                    }
                )

        # フックからの問題
        for hook_result in hook_results:
            if hook_result.get("result") in ["error", "warning"]:
                issues.append(
                    {
                        "source": f"Hook: {hook_result.get('hook_name', 'unknown')}",
                        "severity": hook_result.get("result"),
                        "message": hook_result.get("message", ""),
                    }
                )

        return issues

    def _assess_overall_quality(
        self, integration_report: Dict[str, Any], issues: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """総合品質評価"""
        critical_issues = sum(1 for issue in issues if issue["severity"] == "error")
        warnings = sum(1 for issue in issues if issue["severity"] == "warning")

        # 成功率
        total_subagents = len(integration_report["executed_subagents"])
        successful = integration_report["successful"]
        success_rate = (successful / total_subagents) if total_subagents > 0 else 0

        # 総合品質スコア
        quality_score = success_rate
        if critical_issues > 0:
            quality_score *= 0.5
        if warnings > 0:
            quality_score *= 0.8

        # 品質レベル
        if quality_score >= 0.9:
            quality_level = "excellent"
        elif quality_score >= 0.7:
            quality_level = "good"
        elif quality_score >= 0.5:
            quality_level = "acceptable"
        else:
            quality_level = "poor"

        return {
            "critical_issues": critical_issues,
            "warnings": warnings,
            "success_rate": round(success_rate, 2),
            "quality_score": round(quality_score, 2),
            "quality_level": quality_level,
            "total_issues": len(issues),
        }
