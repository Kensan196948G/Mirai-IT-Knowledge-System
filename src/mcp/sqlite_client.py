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
            with open(schema_path, 'r', encoding='utf-8') as f:
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
        created_by: Optional[str] = None
    ) -> int:
        """
        新規ナレッジエントリを作成

        Returns:
            作成されたナレッジのID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO knowledge_entries (
                    title, itsm_type, content, summary_technical, summary_non_technical,
                    insights, tags, markdown_path, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                title,
                itsm_type,
                content,
                summary_technical,
                summary_non_technical,
                json.dumps(insights or [], ensure_ascii=False),
                json.dumps(tags or [], ensure_ascii=False),
                markdown_path,
                created_by
            ))
            conn.commit()
            return cursor.lastrowid

    def get_knowledge(self, knowledge_id: int) -> Optional[Dict[str, Any]]:
        """ナレッジエントリを取得"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM knowledge_entries WHERE id = ?", (knowledge_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_dict(row)
            return None

    def update_knowledge(
        self,
        knowledge_id: int,
        **kwargs
    ) -> bool:
        """
        ナレッジエントリを更新

        Args:
            knowledge_id: 更新対象のID
            **kwargs: 更新するフィールド

        Returns:
            更新成功したかどうか
        """
        # JSON変換が必要なフィールド
        json_fields = {'insights', 'tags', 'related_ids'}
        for field in json_fields:
            if field in kwargs and isinstance(kwargs[field], (list, dict)):
                kwargs[field] = json.dumps(kwargs[field], ensure_ascii=False)

        set_clause = ", ".join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [knowledge_id]

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE knowledge_entries
                SET {set_clause}
                WHERE id = ?
            """, values)
            conn.commit()
            return cursor.rowcount > 0

    def search_knowledge(
        self,
        query: Optional[str] = None,
        itsm_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        status: str = 'active',
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        ナレッジを検索

        Args:
            query: 全文検索クエリ
            itsm_type: ITSMタイプでフィルタ
            tags: タグでフィルタ
            status: ステータスでフィルタ
            limit: 最大取得件数
            offset: オフセット

        Returns:
            検索結果のリスト
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()

            if query:
                # ハイブリッド検索（FTS5 + LIKE）
                # 日本語対応のため、LIKE検索も併用
                like_pattern = f'%{query}%'
                sql = """
                    SELECT DISTINCT k.* FROM knowledge_entries k
                    WHERE k.status = ?
                    AND (
                        k.title LIKE ?
                        OR k.content LIKE ?
                        OR k.summary_technical LIKE ?
                        OR k.summary_non_technical LIKE ?
                    )
                """
                params = [status, like_pattern, like_pattern, like_pattern, like_pattern]
            else:
                sql = "SELECT * FROM knowledge_entries WHERE status = ?"
                params = [status]

            if itsm_type:
                sql += " AND itsm_type = ?"
                params.append(itsm_type)

            if tags:
                # タグでフィルタ（JSON配列内検索）
                for tag in tags:
                    sql += " AND tags LIKE ?"
                    params.append(f'%"{tag}"%')

            sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(sql, params)
            return [self._row_to_dict(row) for row in cursor.fetchall()]

    def delete_knowledge(self, knowledge_id: int) -> bool:
        """ナレッジを削除（論理削除）"""
        return self.update_knowledge(knowledge_id, status='archived')

    # ========== 関係性管理 ==========

    def create_relationship(
        self,
        source_id: int,
        target_id: int,
        relationship_type: str,
        description: Optional[str] = None
    ) -> int:
        """ナレッジ間の関係を作成"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO relationships (source_id, target_id, relationship_type, description)
                VALUES (?, ?, ?, ?)
            """, (source_id, target_id, relationship_type, description))
            conn.commit()
            return cursor.lastrowid

    def get_related_knowledge(
        self,
        knowledge_id: int,
        relationship_type: Optional[str] = None
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
        self,
        workflow_type: str,
        knowledge_id: Optional[int] = None
    ) -> int:
        """ワークフロー実行を記録"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO workflow_executions (knowledge_id, workflow_type, status)
                VALUES (?, ?, 'running')
            """, (knowledge_id, workflow_type))
            conn.commit()
            return cursor.lastrowid

    def update_workflow_execution(
        self,
        execution_id: int,
        status: str,
        subagents_used: Optional[List[str]] = None,
        hooks_triggered: Optional[List[str]] = None,
        execution_time_ms: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """ワークフロー実行を更新"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE workflow_executions
                SET status = ?,
                    subagents_used = ?,
                    hooks_triggered = ?,
                    execution_time_ms = ?,
                    error_message = ?,
                    completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                status,
                json.dumps(subagents_used or [], ensure_ascii=False),
                json.dumps(hooks_triggered or [], ensure_ascii=False),
                execution_time_ms,
                error_message,
                execution_id
            ))
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
        status: str = 'success',
        message: Optional[str] = None
    ) -> int:
        """サブエージェント実行をログ"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO subagent_logs (
                    workflow_execution_id, subagent_name, role,
                    input_data, output_data, execution_time_ms, status, message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                workflow_execution_id,
                subagent_name,
                role,
                json.dumps(input_data or {}, ensure_ascii=False),
                json.dumps(output_data or {}, ensure_ascii=False),
                execution_time_ms,
                status,
                message
            ))
            conn.commit()
            return cursor.lastrowid

    def log_hook_execution(
        self,
        workflow_execution_id: int,
        hook_name: str,
        hook_type: str,
        result: str,
        message: Optional[str] = None,
        details: Optional[Dict] = None
    ) -> int:
        """フック実行をログ"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO hook_logs (
                    workflow_execution_id, hook_name, hook_type, result, message, details
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                workflow_execution_id,
                hook_name,
                hook_type,
                result,
                message,
                json.dumps(details or {}, ensure_ascii=False)
            ))
            conn.commit()
            return cursor.lastrowid

    # ========== 重複・逸脱検知 ==========

    def record_duplicate_check(
        self,
        knowledge_id: int,
        potential_duplicate_id: int,
        similarity_score: float,
        check_type: str = 'semantic'
    ) -> int:
        """重複検知結果を記録"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO duplicate_checks (
                    knowledge_id, potential_duplicate_id, similarity_score, check_type, status
                ) VALUES (?, ?, ?, ?, 'pending')
            """, (knowledge_id, potential_duplicate_id, similarity_score, check_type))
            conn.commit()
            return cursor.lastrowid

    def record_deviation_check(
        self,
        knowledge_id: int,
        deviation_type: str,
        severity: str,
        description: str,
        itsm_principle: Optional[str] = None,
        recommendation: Optional[str] = None
    ) -> int:
        """逸脱検知結果を記録"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO deviation_checks (
                    knowledge_id, deviation_type, severity, itsm_principle, description, recommendation, status
                ) VALUES (?, ?, ?, ?, ?, ?, 'pending')
            """, (knowledge_id, deviation_type, severity, itsm_principle, description, recommendation))
            conn.commit()
            return cursor.lastrowid

    # ========== ユーティリティ ==========

    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """sqlite3.RowをDictに変換（JSON文字列をパース）"""
        data = dict(row)
        json_fields = {'insights', 'tags', 'related_ids', 'subagents_used', 'hooks_triggered', 'input_data', 'output_data', 'details', 'filters'}

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
            cursor.execute("SELECT COUNT(*) as total FROM knowledge_entries WHERE status = 'active'")
            total_knowledge = cursor.fetchone()['total']

            # ITSMタイプ別
            cursor.execute("""
                SELECT itsm_type, COUNT(*) as count
                FROM knowledge_entries
                WHERE status = 'active'
                GROUP BY itsm_type
            """)
            by_itsm_type = {row['itsm_type']: row['count'] for row in cursor.fetchall()}

            # 最近のワークフロー実行
            cursor.execute("""
                SELECT status, COUNT(*) as count
                FROM workflow_executions
                WHERE created_at > datetime('now', '-7 days')
                GROUP BY status
            """)
            recent_workflows = {row['status']: row['count'] for row in cursor.fetchall()}

            return {
                'total_knowledge': total_knowledge,
                'by_itsm_type': by_itsm_type,
                'recent_workflows': recent_workflows
            }
