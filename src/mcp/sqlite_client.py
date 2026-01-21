"""
SQLite MCP Client for Knowledge Management
ナレッジ管理用SQLiteクライアント
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path


class SQLiteClient:
    """SQLiteデータベース操作クライアント"""

    def __init__(self, db_path: str = "db/knowledge.db"):
        """
        Args:
            db_path: データベースファイルパス
        """
        self.db_path = db_path
        self._ensure_db_exists()

    def _ensure_db_exists(self):
        """データベースの存在確認と初期化"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

        # スキーマファイルが存在する場合は適用
        schema_path = Path("db/schema.sql")
        if schema_path.exists() and not Path(self.db_path).exists():
            with open(schema_path, "r", encoding="utf-8") as f:
                schema = f.read()
            with self.get_connection() as conn:
                conn.executescript(schema)

    def get_connection(self) -> sqlite3.Connection:
        """データベース接続を取得"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ========== ナレッジエントリ操作 ==========

    def create_knowledge(
        self,
        title: str,
        itsm_type: str,
        content: str,
        summary_technical: Optional[str] = None,
        summary_non_technical: Optional[str] = None,
        insights: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        markdown_path: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> int:
        """
        新規ナレッジエントリを作成

        Returns:
            作成されたナレッジのID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO knowledge_entries (
                    title, itsm_type, content, summary_technical, summary_non_technical,
                    insights, tags, markdown_path, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    title,
                    itsm_type,
                    content,
                    summary_technical,
                    summary_non_technical,
                    json.dumps(insights or [], ensure_ascii=False),
                    json.dumps(tags or [], ensure_ascii=False),
                    markdown_path,
                    created_by,
                ),
            )
            conn.commit()
            return int(cursor.lastrowid or 0)

    def get_related_knowledge(
        self, knowledge_id: int, relationship_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """関連するナレッジを取得"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            sql = """
                SELECT k.*, r.relationship_type, r.description as relation_description
                FROM knowledge_entries k
                JOIN relationships r ON (k.id = r.target_id OR k.id = r.source_id)
                WHERE (r.source_id = ? OR r.target_id = ?)
                AND k.id != ?
            """
            params = [knowledge_id, knowledge_id, knowledge_id]

            if relationship_type:
                sql += " AND r.relationship_type = ?"
                params.append(relationship_type)

            cursor.execute(sql, params)
            return [self._row_to_dict(row) for row in cursor.fetchall()]

    # ========== ワークフロー管理 ==========

    def create_workflow_execution(
        self, workflow_type: str, knowledge_id: Optional[int] = None
    ) -> int:
        """ワークフロー実行を記録"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO workflow_executions (knowledge_id, workflow_type, status)
                VALUES (?, ?, 'running')
            """,
                (knowledge_id, workflow_type),
            )
            conn.commit()
            return cursor.lastrowid

    def update_workflow_execution(
        self,
        execution_id: int,
        status: str,
        subagents_used: Optional[List[str]] = None,
        hooks_triggered: Optional[List[str]] = None,
        execution_time_ms: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> bool:
        """ワークフロー実行を更新"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE workflow_executions
                SET status = ?,
                    subagents_used = ?,
                    hooks_triggered = ?,
                    execution_time_ms = ?,
                    error_message = ?,
                    completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """,
                (
                    status,
                    json.dumps(subagents_used or [], ensure_ascii=False),
                    json.dumps(hooks_triggered or [], ensure_ascii=False),
                    execution_time_ms,
                    error_message,
                    execution_id,
                ),
            )
            conn.commit()
            return cursor.rowcount > 0

    def log_subagent_execution(
        self,
        workflow_execution_id: int,
        subagent_name: str,
        role: str,
        input_data: Optional[Dict] = None,
        output_data: Optional[Dict] = None,
        execution_time_ms: Optional[int] = None,
        status: str = "success",
        message: Optional[str] = None,
    ) -> int:
        """サブエージェント実行をログ"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO subagent_logs (
                    workflow_execution_id, subagent_name, role,
                    input_data, output_data, execution_time_ms, status, message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    workflow_execution_id,
                    subagent_name,
                    role,
                    json.dumps(input_data or {}, ensure_ascii=False),
                    json.dumps(output_data or {}, ensure_ascii=False),
                    execution_time_ms,
                    status,
                    message,
                ),
            )
            conn.commit()
            return cursor.lastrowid

    def log_hook_execution(
        self,
        workflow_execution_id: int,
        hook_name: str,
        hook_type: str,
        result: str,
        message: Optional[str] = None,
        details: Optional[Dict] = None,
    ) -> int:
        """フック実行をログ"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO hook_logs (
                    workflow_execution_id, hook_name, hook_type, result, message, details
                ) VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    workflow_execution_id,
                    hook_name,
                    hook_type,
                    result,
                    message,
                    json.dumps(details or {}, ensure_ascii=False),
                ),
            )
            conn.commit()
            return cursor.lastrowid

    # ========== 検索履歴・対話履歴 ==========

    def log_search_history(
        self,
        search_query: str,
        search_type: str = "natural_language",
        filters: Optional[Dict[str, Any]] = None,
        results_count: Optional[int] = None,
        selected_result_id: Optional[int] = None,
        user_id: Optional[str] = None,
    ) -> int:
        """検索履歴を記録"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO search_history (
                    search_query, search_type, filters, results_count, selected_result_id, user_id
                ) VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    search_query,
                    search_type,
                    json.dumps(filters or {}, ensure_ascii=False),
                    results_count,
                    selected_result_id,
                    user_id,
                ),
            )
            conn.commit()
            return cursor.lastrowid

    def create_conversation_session(
        self, session_id: str, user_id: Optional[str] = None
    ) -> int:
        """対話セッションを作成"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR IGNORE INTO conversation_sessions (session_id, user_id)
                VALUES (?, ?)
            """,
                (session_id, user_id),
            )
            conn.commit()

            cursor.execute(
                "SELECT id FROM conversation_sessions WHERE session_id = ?",
                (session_id,),
            )
            row = cursor.fetchone()
            return row["id"] if row else 0

    def add_conversation_message(
        self, session_id: str, role: str, content: str, created_at: Optional[str] = None
    ) -> int:
        """対話メッセージを保存"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO conversation_messages (session_id, role, content, created_at)
                VALUES (?, ?, ?, COALESCE(?, CURRENT_TIMESTAMP))
            """,
                (session_id, role, content, created_at),
            )
            conn.commit()
            return cursor.lastrowid

    def complete_conversation_session(
        self, session_id: str, knowledge_id: Optional[int] = None
    ) -> bool:
        """対話セッションを完了状態に更新"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE conversation_sessions
                SET completed_at = CURRENT_TIMESTAMP,
                    knowledge_id = ?
                WHERE session_id = ?
            """,
                (knowledge_id, session_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_recent_conversation_sessions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """最近の対話セッションを取得"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM conversation_sessions
                ORDER BY created_at DESC
                LIMIT ?
            """,
                (limit,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_conversation_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """対話メッセージ一覧を取得"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM conversation_messages
                WHERE session_id = ?
                ORDER BY created_at ASC
            """,
                (session_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_recent_workflow_executions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """最近のワークフロー実行を取得"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM workflow_executions
                ORDER BY created_at DESC
                LIMIT ?
            """,
                (limit,),
            )
            return [self._row_to_dict(row) for row in cursor.fetchall()]

    def get_workflow_execution(self, execution_id: int) -> Optional[Dict[str, Any]]:
        """ワークフロー実行の詳細を取得"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM workflow_executions WHERE id = ?", (execution_id,)
            )
            row = cursor.fetchone()
            return self._row_to_dict(row) if row else None

    def get_subagent_logs(self, execution_id: int) -> List[Dict[str, Any]]:
        """サブエージェントログを取得"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM subagent_logs
                WHERE workflow_execution_id = ?
                ORDER BY created_at ASC
            """,
                (execution_id,),
            )
            return [self._row_to_dict(row) for row in cursor.fetchall()]

    def get_hook_logs(self, execution_id: int) -> List[Dict[str, Any]]:
        """フックログを取得"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM hook_logs
                WHERE workflow_execution_id = ?
                ORDER BY triggered_at ASC
            """,
                (execution_id,),
            )
            return [self._row_to_dict(row) for row in cursor.fetchall()]

    # ========== 重複・逸脱検知 ==========

    def record_duplicate_check(
        self,
        knowledge_id: int,
        potential_duplicate_id: int,
        similarity_score: float,
        check_type: str = "semantic",
    ) -> int:
        """重複検知結果を記録"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO duplicate_checks (
                    knowledge_id, potential_duplicate_id, similarity_score, check_type, status
                ) VALUES (?, ?, ?, ?, 'pending')
            """,
                (knowledge_id, potential_duplicate_id, similarity_score, check_type),
            )
            conn.commit()
            return cursor.lastrowid

    def record_deviation_check(
        self,
        knowledge_id: int,
        deviation_type: str,
        severity: str,
        description: str,
        itsm_principle: Optional[str] = None,
        recommendation: Optional[str] = None,
    ) -> int:
        """逸脱検知結果を記録"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO deviation_checks (
                    knowledge_id, deviation_type, severity, itsm_principle, description, recommendation, status
                ) VALUES (?, ?, ?, ?, ?, ?, 'pending')
            """,
                (
                    knowledge_id,
                    deviation_type,
                    severity,
                    itsm_principle,
                    description,
                    recommendation,
                ),
            )
            conn.commit()
            return cursor.lastrowid

    # ========== ユーティリティ ==========

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """sqlite3.RowをDictに変換（JSON文字列をパース）"""
        data = dict(row)
        json_fields = {
            "insights",
            "tags",
            "related_ids",
            "subagents_used",
            "hooks_triggered",
            "input_data",
            "output_data",
            "details",
            "filters",
        }

        for field in json_fields:
            if field in data and data[field]:
                try:
                    data[field] = json.loads(data[field])
                except (json.JSONDecodeError, TypeError):
                    pass

        return data

    def get_statistics(self) -> Dict[str, Any]:
        """統計情報を取得"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # ナレッジ数
            cursor.execute(
                "SELECT COUNT(*) as total FROM knowledge_entries WHERE status = 'active'"
            )
            total_knowledge = cursor.fetchone()["total"]

            # ITSMタイプ別
            cursor.execute("""
                SELECT itsm_type, COUNT(*) as count
                FROM knowledge_entries
                WHERE status = 'active'
                GROUP BY itsm_type
            """)
            by_itsm_type = {row["itsm_type"]: row["count"] for row in cursor.fetchall()}

            # 最近のワークフロー実行
            cursor.execute("""
                SELECT status, COUNT(*) as count
                FROM workflow_executions
                WHERE created_at > datetime('now', '-7 days')
                GROUP BY status
            """)
            recent_workflows = {
                row["status"]: row["count"] for row in cursor.fetchall()
            }

            return {
                "total_knowledge": total_knowledge,
                "by_itsm_type": by_itsm_type,
                "recent_workflows": recent_workflows,
            }
