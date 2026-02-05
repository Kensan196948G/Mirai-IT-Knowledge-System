"""
Core Workflow Engine
中核ワークフローエンジン
"""

import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

# モジュールパスを追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.hooks import (
    AutoSummaryHook,
    DeviationCheckHook,
    DuplicateCheckHook,
    HookResult,
    PostTaskHook,
    PreTaskHook,
)
from src.mcp.mcp_integration import mcp_integration
from src.mcp.sqlite_client import SQLiteClient
from src.subagents import (
    ArchitectSubAgent,
    CoordinatorSubAgent,
    DevOpsSubAgent,
    DocumenterSubAgent,
    ITSMExpertSubAgent,
    KnowledgeCuratorSubAgent,
    QASubAgent,
)


class WorkflowEngine:
    """ワークフローエンジン"""

    def __init__(self, db_path: str = "db/knowledge.db"):
        """
        Args:
            db_path: データベースファイルパス
        """
        self.db_client = SQLiteClient(db_path)

        # サブエージェント初期化
        self.subagents = {
            "architect": ArchitectSubAgent(),
            "knowledge_curator": KnowledgeCuratorSubAgent(),
            "itsm_expert": ITSMExpertSubAgent(),
            "devops": DevOpsSubAgent(),
            "qa": QASubAgent(),
            "coordinator": CoordinatorSubAgent(),
            "documenter": DocumenterSubAgent(),
        }

        # フック初期化
        self.hooks = {
            "pre_task": PreTaskHook(),
            "duplicate_check": DuplicateCheckHook(),
            "deviation_check": DeviationCheckHook(),
            "auto_summary": AutoSummaryHook(),
            "post_task": PostTaskHook(),
        }

    def process_knowledge(
        self,
        title: str,
        content: str,
        itsm_type: str = "Other",
        created_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        ナレッジ生成ワークフローを実行

        Args:
            title: タイトル
            content: 内容
            itsm_type: ITSMタイプ
            created_by: 作成者

        Returns:
            処理結果
        """
        start_time = time.time()

        # ワークフロー実行を記録
        execution_id = self.db_client.create_workflow_execution(
            workflow_type="knowledge_generation"
        )

        try:
            # 1. Pre-Task Hook: 入力検証
            print("🔍 Pre-Task Hook: 入力検証中...")
            pre_task_result = self._execute_hook(
                "pre_task",
                {"title": title, "content": content, "itsm_type": itsm_type},
                execution_id,
            )

            if pre_task_result.block_execution:
                raise ValueError(
                    f"Pre-Task Hook でブロックされました: {pre_task_result.message}"
                )

            # 2. 既存ナレッジを検索（重複チェック用）
            existing_knowledge = self.db_client.search_knowledge(query=title, limit=10)

            # 3. サブエージェント並列実行
            print(f"\n⚙️  {len(self.subagents)}個のサブエージェントを実行中...")
            subagent_results = self._execute_subagents_parallel(
                {
                    "title": title,
                    "content": content,
                    "itsm_type": itsm_type,
                    "existing_knowledge": existing_knowledge,
                },
                execution_id,
            )

            # 4. 品質チェックフック実行
            print("\n✅ 品質チェック実行中...")
            hook_results = self._execute_quality_hooks(
                {
                    "title": title,
                    "content": content,
                    "itsm_type": itsm_type,
                    "existing_knowledge": existing_knowledge,
                    "qa_result": subagent_results.get("qa", {}).get("data", {}),
                    "itsm_expert_result": subagent_results.get("itsm_expert", {}).get(
                        "data", {}
                    ),
                    "documenter_result": subagent_results.get("documenter", {}).get(
                        "data", {}
                    ),
                },
                execution_id,
            )

            # 5. Post-Task Hook: 統合レビュー
            print("\n📊 Post-Task Hook: 統合レビュー中...")
            post_task_result = self._execute_hook(
                "post_task",
                {"subagent_results": subagent_results, "hook_results": hook_results},
                execution_id,
            )

            # 6. ナレッジを集約
            aggregated_knowledge = self._aggregate_knowledge(
                title, content, itsm_type, subagent_results
            )

            # 7. データベースに保存
            print("\n💾 データベースに保存中...")
            knowledge_id = self._save_knowledge(
                aggregated_knowledge, created_by, subagent_results
            )

            # 8. Markdownファイルとして保存
            markdown_path = self._save_markdown(knowledge_id, aggregated_knowledge)

            # 実行時間
            execution_time_ms = int((time.time() - start_time) * 1000)

            # ワークフロー実行結果を更新
            used_subagents = list(subagent_results.keys())
            triggered_hooks = [h["hook_name"] for h in hook_results]

            self.db_client.update_workflow_execution(
                execution_id,
                status="completed",
                subagents_used=used_subagents,
                hooks_triggered=triggered_hooks,
                execution_time_ms=execution_time_ms,
            )

            print(
                f"\n✨ ナレッジ生成完了！ (ID: {knowledge_id}, 実行時間: {execution_time_ms}ms)"
            )

            return {
                "success": True,
                "knowledge_id": knowledge_id,
                "execution_id": execution_id,
                "execution_time_ms": execution_time_ms,
                "markdown_path": markdown_path,
                "subagent_results": subagent_results,
                "hook_results": hook_results,
                "post_task_assessment": post_task_result.details.get(
                    "overall_assessment", {}
                ),
                "aggregated_knowledge": aggregated_knowledge,
            }

        except Exception as e:
            # エラー処理
            execution_time_ms = int((time.time() - start_time) * 1000)
            self.db_client.update_workflow_execution(
                execution_id,
                status="failed",
                execution_time_ms=execution_time_ms,
                error_message=str(e),
            )

            print(f"\n❌ エラーが発生しました: {str(e)}")

            return {"success": False, "error": str(e), "execution_id": execution_id}

    def _execute_hook(self, hook_name: str, context: Dict[str, Any], execution_id: int):
        """フックを実行"""
        hook = self.hooks.get(hook_name)
        if not hook or not hook.is_enabled():
            return None

        result = hook.execute(context)

        # ログ記録
        self.db_client.log_hook_execution(
            workflow_execution_id=execution_id,
            hook_name=hook_name,
            hook_type=hook.hook_type,
            result=result.result.value,
            message=result.message,
            details=result.details,
        )

        return result

    def _execute_subagents_parallel(
        self, input_data: Dict[str, Any], execution_id: int
    ) -> Dict[str, Any]:
        """サブエージェントを並列実行（真の並列実装）

        SubAgentを依存関係に基づいて3つのフェーズで並列実行:
        - Phase 1 (並列): Architect, KnowledgeCurator, ITSMExpert, DevOps
        - Phase 2 (並列): QA, Coordinator (Phase 1の結果を利用)
        - Phase 3 (順次): Documenter (全結果を統合)
        """
        results = {}
        start_time = time.time()

        try:
            # Python 3.7+のイベントループ取得
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    raise RuntimeError()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # 非同期実行
            results = loop.run_until_complete(
                self._execute_subagents_async(input_data, execution_id)
            )

            parallel_time = int((time.time() - start_time) * 1000)
            print(f"  ⚡ Parallel execution completed in {parallel_time}ms")

        except Exception as e:
            print(f"Warning: Parallel execution failed: {e}. Falling back to sequential.")
            # フォールバック: 順次実行
            results = self._execute_subagents_sequential(input_data, execution_id)

        return results

    async def _execute_subagents_async(
        self, input_data: Dict[str, Any], execution_id: int
    ) -> Dict[str, Any]:
        """非同期SubAgent実行"""
        results = {}

        # Phase 1: 独立して実行可能なSubAgent（並列実行）
        phase1_agents = ["architect", "knowledge_curator", "itsm_expert", "devops"]
        print(f"  → Phase 1: Executing {len(phase1_agents)} agents in parallel...")

        phase1_tasks = [
            self._execute_subagent_async(name, input_data, execution_id)
            for name in phase1_agents
        ]
        phase1_results = await asyncio.gather(*phase1_tasks, return_exceptions=True)

        # Phase 1結果を統合
        for name, result in zip(phase1_agents, phase1_results):
            if isinstance(result, Exception):
                print(f"  ⚠️  {name} failed: {result}")
                results[name] = {"status": "error", "data": {}}
            else:
                results[name] = result

        # Phase 2: Phase 1の結果を利用するSubAgent（並列実行）
        phase2_agents = ["qa", "coordinator"]
        print(f"  → Phase 2: Executing {len(phase2_agents)} agents in parallel...")

        # Phase 1の結果をinput_dataに追加
        enhanced_input = {**input_data, "phase1_results": results}

        phase2_tasks = [
            self._execute_subagent_async(name, enhanced_input, execution_id)
            for name in phase2_agents
        ]
        phase2_results = await asyncio.gather(*phase2_tasks, return_exceptions=True)

        # Phase 2結果を統合
        for name, result in zip(phase2_agents, phase2_results):
            if isinstance(result, Exception):
                print(f"  ⚠️  {name} failed: {result}")
                results[name] = {"status": "error", "data": {}}
            else:
                results[name] = result

        # Phase 3: 最終処理（順次実行 - 全結果を統合）
        print(f"  → Phase 3: Executing documenter (final integration)...")

        documenter_input = {**input_data, "all_results": results}
        documenter_result = await self._execute_subagent_async(
            "documenter", documenter_input, execution_id
        )

        if isinstance(documenter_result, Exception):
            print(f"  ⚠️  documenter failed: {documenter_result}")
            results["documenter"] = {"status": "error", "data": {}}
        else:
            results["documenter"] = documenter_result

        return results

    async def _execute_subagent_async(
        self, name: str, input_data: Dict[str, Any], execution_id: int
    ) -> Dict[str, Any]:
        """単一SubAgentを非同期実行"""
        loop = asyncio.get_event_loop()

        # SubAgent実行を別スレッドで実行（CPUバウンド処理の並列化）
        with ThreadPoolExecutor(max_workers=1) as executor:
            result = await loop.run_in_executor(
                executor,
                self._execute_single_subagent,
                name,
                input_data,
                execution_id
            )

        return result

    def _execute_single_subagent(
        self, name: str, input_data: Dict[str, Any], execution_id: int
    ) -> Dict[str, Any]:
        """単一SubAgent実行（スレッド内で実行）"""
        if name not in self.subagents:
            return {"status": "error", "data": {}, "message": f"SubAgent {name} not found"}

        subagent = self.subagents[name]
        print(f"    ├─ {name} ({subagent.role})...")

        result = subagent.execute(input_data)

        # ログ記録
        self.db_client.log_subagent_execution(
            workflow_execution_id=execution_id,
            subagent_name=name,
            role=subagent.role,
            input_data={"title": input_data.get("title", "")},
            output_data=result.to_dict()["data"],
            execution_time_ms=result.execution_time_ms,
            status=result.status,
            message=result.message,
        )

        return result.to_dict()

    def _execute_subagents_sequential(
        self, input_data: Dict[str, Any], execution_id: int
    ) -> Dict[str, Any]:
        """SubAgentを順次実行（フォールバック用）"""
        results = {}

        for name, subagent in self.subagents.items():
            print(f"  → {name} ({subagent.role})...")

            result = subagent.execute(input_data)

            # ログ記録
            self.db_client.log_subagent_execution(
                workflow_execution_id=execution_id,
                subagent_name=name,
                role=subagent.role,
                input_data={"title": input_data.get("title", "")},
                output_data=result.to_dict()["data"],
                execution_time_ms=result.execution_time_ms,
                status=result.status,
                message=result.message,
            )

            results[name] = result.to_dict()

        return results

    def _execute_quality_hooks(
        self, context: Dict[str, Any], execution_id: int
    ) -> List[Dict[str, Any]]:
        """品質チェックフックを実行"""
        hook_results = []

        quality_hooks = ["duplicate_check", "deviation_check", "auto_summary"]

        for hook_name in quality_hooks:
            result = self._execute_hook(hook_name, context, execution_id)
            if result:
                hook_results.append(
                    {
                        "hook_name": hook_name,
                        "result": result.result.value,
                        "message": result.message,
                        "details": result.details,
                    }
                )

        return hook_results

    def _aggregate_knowledge(
        self, title: str, content: str, itsm_type: str, subagent_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """サブエージェント結果を集約"""
        # Documenterの結果から要約を取得
        documenter_data = subagent_results.get("documenter", {}).get("data", {})
        summary_technical = documenter_data.get("summary_technical", "")
        summary_non_technical = documenter_data.get("summary_non_technical", "")

        # Knowledge Curatorの結果からタグとメタデータを取得
        curator_data = subagent_results.get("knowledge_curator", {}).get("data", {})
        tags = curator_data.get("tags", [])
        keywords = curator_data.get("keywords", [])
        importance = curator_data.get("importance", {})

        # ITSMExpertの結果から推奨事項を取得
        itsm_data = subagent_results.get("itsm_expert", {}).get("data", {})
        recommendations = itsm_data.get("recommendations", [])

        # DevOpsの結果から改善提案を取得
        devops_data = subagent_results.get("devops", {}).get("data", {})
        improvements = devops_data.get("improvements", [])

        # 知見を統合
        insights = []
        insights.extend(recommendations)
        insights.extend(improvements)

        # MCP連携でナレッジを補強
        mcp_enrichments = {}
        try:
            # 検出された技術を抽出
            detected_techs = [
                tag
                for tag in tags
                if tag.lower() in ["flask", "sqlite", "python", "apache", "nginx"]
            ]

            # MCP統合でナレッジ補強
            mcp_enrichments = mcp_integration.enrich_knowledge_with_mcps(
                knowledge_content=content,
                detected_technologies=detected_techs,
                itsm_type=itsm_type,
            )

            # MCP補強情報をinsightsに追加
            if mcp_enrichments.get("related_memories"):
                insights.append(
                    f"📚 過去の関連記憶: {len(mcp_enrichments['related_memories'])}件見つかりました"
                )
            if mcp_enrichments.get("technical_documentation"):
                insights.append(
                    f"📖 技術ドキュメント: {len(mcp_enrichments['technical_documentation'])}個の技術について参照可能"
                )

        except Exception as e:
            print(f"⚠️  MCP補強でエラー: {e}")

        return {
            "title": title,
            "content": content,
            "itsm_type": itsm_type,
            "summary_technical": summary_technical,
            "summary_non_technical": summary_non_technical,
            "tags": tags,
            "keywords": keywords,
            "importance": importance,
            "insights": insights,
            "markdown": documenter_data.get("markdown", ""),
            "html": documenter_data.get("html", ""),
            "mcp_enrichments": mcp_enrichments,
        }

    def _save_knowledge(
        self,
        knowledge: Dict[str, Any],
        created_by: Optional[str],
        subagent_results: Dict[str, Any],
    ) -> int:
        """ナレッジをデータベースに保存"""
        # ナレッジエントリ作成
        knowledge_id = self.db_client.create_knowledge(
            title=knowledge["title"],
            itsm_type=knowledge["itsm_type"],
            content=knowledge["content"],
            summary_technical=knowledge["summary_technical"],
            summary_non_technical=knowledge["summary_non_technical"],
            insights=knowledge["insights"],
            tags=knowledge["tags"],
            created_by=created_by,
        )

        # 重複検知結果を記録
        qa_data = subagent_results.get("qa", {}).get("data", {})
        duplicates = qa_data.get("duplicates", {})
        for similar in duplicates.get("similar_knowledge", []):
            self.db_client.record_duplicate_check(
                knowledge_id=knowledge_id,
                potential_duplicate_id=similar["knowledge_id"],
                similarity_score=similar["overall_similarity"],
                check_type="semantic",
            )

        # 逸脱検知結果を記録
        itsm_data = subagent_results.get("itsm_expert", {}).get("data", {})
        for deviation in itsm_data.get("deviations", []):
            self.db_client.record_deviation_check(
                knowledge_id=knowledge_id,
                deviation_type=deviation["deviation_type"],
                severity=deviation["severity"],
                description=deviation["description"],
                itsm_principle=deviation.get("itsm_principle"),
                recommendation=None,
            )

        return knowledge_id

    def _save_markdown(self, knowledge_id: int, knowledge: Dict[str, Any]) -> str:
        """Markdownファイルとして保存"""
        markdown_dir = Path("data/knowledge")
        markdown_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{knowledge_id:05d}_{knowledge['itsm_type']}.md"
        filepath = markdown_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(knowledge["markdown"])

        # データベースにパスを保存
        self.db_client.update_knowledge(knowledge_id, markdown_path=str(filepath))

        return str(filepath)
