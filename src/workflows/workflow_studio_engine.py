"""
Workflow Studio Execution Engine
ワークフロースタジオ実行エンジン
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import yaml

from src.core.workflow import WorkflowEngine
from src.core.itsm_classifier import ITSMClassifier
from src.mcp.sqlite_client import SQLiteClient
from src.workflows.intelligent_search import IntelligentSearchAssistant


@dataclass
class WorkflowDefinition:
    name: str
    display_name: str
    description: str
    handler: str
    inputs: List[str]
    outputs: List[str]
    steps: List[Dict[str, Any]]
    source_path: str


class WorkflowStudioEngine:
    """Workflow Studio用の簡易実行エンジン"""

    def __init__(
        self,
        workflows_dir: str | Path = ".vscode/workflows",
        db_client: Optional[SQLiteClient] = None,
        event_sink: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    ):
        self.workflows_dir = Path(workflows_dir)
        self.db_client = db_client or SQLiteClient()
        self.event_sink = event_sink
        self._definitions = self._load_definitions()
        self._registry = {
            "knowledge_register": self._run_knowledge_register,
            "search_assist": self._run_search_assist,
            "incident_to_problem": self._run_incident_to_problem,
        }

    def list_workflows(self) -> List[Dict[str, Any]]:
        """利用可能なワークフロー一覧を取得"""
        return [
            {
                "name": definition.name,
                "display_name": definition.display_name,
                "description": definition.description,
                "handler": definition.handler,
                "inputs": definition.inputs,
                "outputs": definition.outputs,
                "source_path": definition.source_path,
            }
            for definition in self._definitions.values()
        ]

    def get_definition(self, name: str) -> Optional[WorkflowDefinition]:
        """ワークフロー定義を取得"""
        return self._definitions.get(name)

    def run_workflow(
        self,
        name: str,
        inputs: Dict[str, Any],
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """ワークフローを実行"""
        definition = self.get_definition(name)
        if not definition:
            return {"success": False, "error": f"workflow not found: {name}"}

        execution_id = self.db_client.create_workflow_execution(
            workflow_type=definition.name
        )
        self._emit_event(
            "workflow_started", {"execution_id": execution_id, "name": name}
        )

        start_time = datetime.now()
        try:
            handler = self._registry.get(definition.handler)
            if not handler:
                raise ValueError(f"handler not found: {definition.handler}")

            result = handler(inputs, user_id=user_id)

            execution_time_ms = int(
                (datetime.now() - start_time).total_seconds() * 1000
            )
            status = "completed" if result.get("success", True) else "failed"
            subagents_used = result.get("subagents_used")
            hooks_triggered = result.get("hooks_triggered")

            self.db_client.update_workflow_execution(
                execution_id,
                status=status,
                subagents_used=subagents_used,
                hooks_triggered=hooks_triggered,
                execution_time_ms=execution_time_ms,
                error_message=result.get("error"),
            )

            self._emit_event(
                "workflow_completed",
                {
                    "execution_id": execution_id,
                    "name": name,
                    "status": status,
                    "execution_time_ms": execution_time_ms,
                },
            )

            return {
                "success": status == "completed",
                "execution_id": execution_id,
                "workflow": definition.name,
                "result": result,
            }

        except Exception as exc:
            execution_time_ms = int(
                (datetime.now() - start_time).total_seconds() * 1000
            )
            self.db_client.update_workflow_execution(
                execution_id,
                status="failed",
                execution_time_ms=execution_time_ms,
                error_message=str(exc),
            )

            self._emit_event(
                "workflow_failed",
                {
                    "execution_id": execution_id,
                    "name": name,
                    "error": str(exc),
                },
            )

            return {
                "success": False,
                "execution_id": execution_id,
                "workflow": definition.name,
                "error": str(exc),
            }

    def _load_definitions(self) -> Dict[str, WorkflowDefinition]:
        definitions: Dict[str, WorkflowDefinition] = {}
        if not self.workflows_dir.exists():
            return definitions

        for workflow_path in self.workflows_dir.glob("*.workflow"):
            with open(workflow_path, "r", encoding="utf-8") as file:
                data = yaml.safe_load(file) or {}

            name = data.get("workflow_id") or data.get("id") or workflow_path.stem
            display_name = data.get("name", name)
            description = data.get("description", "")
            handler = data.get("handler", name)
            inputs = data.get("inputs", [])
            outputs = data.get("outputs", [])
            steps = data.get("steps", [])

            definitions[name] = WorkflowDefinition(
                name=name,
                display_name=display_name,
                description=description,
                handler=handler,
                inputs=inputs,
                outputs=outputs,
                steps=steps,
                source_path=str(workflow_path),
            )

        return definitions

    def _run_knowledge_register(
        self, inputs: Dict[str, Any], user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        title = inputs.get("title")
        content = inputs.get("content")
        itsm_type = inputs.get("itsm_type")
        created_by = inputs.get("created_by") or user_id or "workflow_studio"

        if not title or not content:
            return {"success": False, "error": "title/contentが必要です"}

        if not itsm_type or itsm_type == "auto":
            classifier = ITSMClassifier()
            itsm_type = classifier.classify(title, content).get("itsm_type", "Other")

        engine = WorkflowEngine()
        return engine.process_knowledge(
            title=title,
            content=content,
            itsm_type=itsm_type,
            created_by=created_by,
        )

    def _run_search_assist(
        self, inputs: Dict[str, Any], user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        query = inputs.get("query")
        if not query:
            return {"success": False, "error": "queryが必要です"}

        assistant = IntelligentSearchAssistant()
        result = assistant.search(query)

        try:
            self.db_client.log_search_history(
                search_query=query,
                search_type="natural_language",
                filters={"intent": result.get("intent")},
                results_count=len(result.get("knowledge", [])),
                user_id=user_id,
            )
        except Exception:
            pass

        return {"success": True, "payload": result}

    def _run_incident_to_problem(
        self, inputs: Dict[str, Any], user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        title = inputs.get("title")
        content = inputs.get("content")
        created_by = inputs.get("created_by") or user_id or "workflow_studio"

        if not title or not content:
            return {"success": False, "error": "title/contentが必要です"}

        engine = WorkflowEngine()
        return engine.process_knowledge(
            title=title,
            content=content,
            itsm_type="Problem",
            created_by=created_by,
        )

    def _emit_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        if not self.event_sink:
            return
        self.event_sink(event_type, payload)
