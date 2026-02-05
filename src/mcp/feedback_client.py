"""
Feedback Client for User Feedback Collection
ユーザーフィードバック収集クライアント
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from .sqlite_client import SQLiteClient


class FeedbackClient(SQLiteClient):
    """フィードバック管理クライアント"""

    # セキュリティ: 許可されたテーブル名のホワイトリスト
    ALLOWED_TABLES = {
        'knowledge_entries',
        'knowledge_feedback',
        'system_feedback',
        'knowledge_usage_stats',
        'knowledge_ratings'
    }

    # セキュリティ: 許可されたカラム名のホワイトリスト
    ALLOWED_COLUMNS = {
        'status', 'priority', 'assignee', 'notes', 'resolved_at',
        'id', 'title', 'content', 'itsm_type', 'created_at', 'updated_at'
    }

    def __init__(self, db_path: str = "db/knowledge.db"):
        super().__init__(db_path)
        self._ensure_feedback_schema()

    def _validate_table_name(self, table_name: str) -> str:
        """テーブル名を検証（SQL injection対策）"""
        if table_name not in self.ALLOWED_TABLES:
            raise ValueError(f"Invalid table name: {table_name}")
        return table_name

    def _validate_column_names(self, column_names: List[str]) -> List[str]:
        """カラム名を検証（SQL injection対策）"""
        for col in column_names:
            if col not in self.ALLOWED_COLUMNS:
                raise ValueError(f"Invalid column name: {col}")
        return column_names

    def _ensure_feedback_schema(self):
        """フィードバックスキーマの適用"""
        schema_path = Path("db/feedback_schema.sql")
        if schema_path.exists():
            with open(schema_path, "r", encoding="utf-8") as f:
                schema = f.read()
            with self.get_connection() as conn:
                conn.executescript(schema)

    def _table_exists(self, table_name: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,),
            )
            return cursor.fetchone() is not None

    def _get_knowledge_table(self) -> str:
        if self._table_exists("knowledge_entries"):
            return "knowledge_entries"
        return "knowledge"

    # ========== ナレッジフィードバック ==========

    def add_knowledge_feedback(
        self,
        knowledge_id: int,
        user_id: Optional[str] = None,
        rating: Optional[int] = None,
        feedback_type: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> int:
        """
        ナレッジへのフィードバックを追加

        Args:
            knowledge_id: ナレッジID
            user_id: ユーザーID
            rating: 評価（1-5）
            feedback_type: フィードバックタイプ
            comment: コメント

        Returns:
            フィードバックID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO knowledge_feedback (knowledge_id, user_id, rating, feedback_type, comment)
                VALUES (?, ?, ?, ?, ?)
            """,
                (knowledge_id, user_id, rating, feedback_type, comment),
            )
            conn.commit()
            return cursor.lastrowid

    def get_knowledge_feedback(self, knowledge_id: int) -> List[Dict[str, Any]]:
        """特定ナレッジのフィードバックを取得"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM knowledge_feedback
                WHERE knowledge_id = ?
                ORDER BY created_at DESC
            """,
                (knowledge_id,),
            )
            return [self._row_to_dict(row) for row in cursor.fetchall()]

    def get_knowledge_rating(self, knowledge_id: int) -> Optional[Dict[str, Any]]:
        """ナレッジの評価サマリーを取得"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM knowledge_ratings
                WHERE knowledge_id = ?
            """,
                (knowledge_id,),
            )
            row = cursor.fetchone()
            return self._row_to_dict(row) if row else None

    def get_top_rated_knowledge(self, limit: int = 10) -> List[Dict[str, Any]]:
        """評価の高いナレッジを取得"""
        knowledge_table = self._get_knowledge_table()
        # セキュリティ: テーブル名を検証
        knowledge_table = self._validate_table_name(knowledge_table)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            # セキュリティ: 検証済みテーブル名を使用（SQL injection対策）
            query = """
                SELECT k.*, r.avg_rating, r.feedback_count
                FROM {} k
                JOIN knowledge_ratings r ON k.id = r.knowledge_id
                WHERE r.feedback_count >= 3
                ORDER BY r.avg_rating DESC, r.feedback_count DESC
                LIMIT ?
            """.format(knowledge_table)  # 検証済みなので format() 使用は安全

            cursor.execute(query, (limit,))
            return [self._row_to_dict(row) for row in cursor.fetchall()]

    # ========== システムフィードバック ==========

    def add_system_feedback(
        self,
        title: str,
        description: str,
        feedback_category: str,
        user_id: Optional[str] = None,
        priority: str = "medium",
    ) -> int:
        """
        システムフィードバックを追加

        Args:
            title: タイトル
            description: 説明
            feedback_category: カテゴリ
            user_id: ユーザーID
            priority: 優先度

        Returns:
            フィードバックID
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO system_feedback (user_id, feedback_category, title, description, priority)
                VALUES (?, ?, ?, ?, ?)
            """,
                (user_id, feedback_category, title, description, priority),
            )
            conn.commit()
            return cursor.lastrowid

    def get_system_feedback(
        self,
        status: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """システムフィードバックを取得"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            sql = "SELECT * FROM system_feedback WHERE 1=1"
            params = []

            if status:
                sql += " AND status = ?"
                params.append(status)

            if category:
                sql += " AND feedback_category = ?"
                params.append(category)

            sql += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            cursor.execute(sql, params)
            return [self._row_to_dict(row) for row in cursor.fetchall()]

    def update_system_feedback_status(
        self, feedback_id: int, status: str, assigned_to: Optional[str] = None
    ) -> bool:
        """システムフィードバックのステータスを更新"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            updates = ["status = ?"]
            params = [status]

            if assigned_to:
                updates.append("assigned_to = ?")
                params.append(assigned_to)

            if status == "completed":
                updates.append("resolved_at = CURRENT_TIMESTAMP")

            params.append(feedback_id)

            # セキュリティ: カラム名を検証
            update_columns = [u.split(' = ')[0] for u in updates]
            self._validate_column_names(update_columns)

            # セキュリティ: 検証済みカラム名を使用（SQL injection対策）
            query = "UPDATE system_feedback SET {} WHERE id = ?".format(', '.join(updates))
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount > 0

    # ========== 使用統計 ==========

    def log_knowledge_usage(
        self,
        knowledge_id: int,
        action_type: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> int:
        """ナレッジ使用を記録"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO knowledge_usage_stats (knowledge_id, user_id, action_type, session_id)
                VALUES (?, ?, ?, ?)
            """,
                (knowledge_id, user_id, action_type, session_id),
            )
            conn.commit()
            return cursor.lastrowid

    def get_knowledge_usage_stats(self, knowledge_id: int) -> Dict[str, Any]:
        """ナレッジの使用統計を取得"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 総閲覧数
            cursor.execute(
                """
                SELECT COUNT(*) as view_count
                FROM knowledge_usage_stats
                WHERE knowledge_id = ? AND action_type = 'view'
            """,
                (knowledge_id,),
            )
            view_count = cursor.fetchone()["view_count"]

            # アクション別統計
            cursor.execute(
                """
                SELECT action_type, COUNT(*) as count
                FROM knowledge_usage_stats
                WHERE knowledge_id = ?
                GROUP BY action_type
            """,
                (knowledge_id,),
            )
            action_stats = {
                row["action_type"]: row["count"] for row in cursor.fetchall()
            }

            # 最近30日の閲覧トレンド
            cursor.execute(
                """
                SELECT DATE(created_at) as date, COUNT(*) as count
                FROM knowledge_usage_stats
                WHERE knowledge_id = ?
                  AND action_type = 'view'
                  AND created_at > datetime('now', '-30 days')
                GROUP BY DATE(created_at)
                ORDER BY date DESC
            """,
                (knowledge_id,),
            )
            trend = [dict(row) for row in cursor.fetchall()]

            return {
                "view_count": view_count,
                "action_stats": action_stats,
                "trend_30days": trend,
            }

    def get_popular_knowledge(
        self, limit: int = 10, days: int = 30
    ) -> List[Dict[str, Any]]:
        """人気のナレッジを取得"""
        knowledge_table = self._get_knowledge_table()
        # セキュリティ: テーブル名を検証
        knowledge_table = self._validate_table_name(knowledge_table)

        with self.get_connection() as conn:
            cursor = conn.cursor()
            # セキュリティ: 検証済みテーブル名を使用（SQL injection対策）
            query = """
                SELECT k.*, COUNT(u.id) as view_count
                FROM {} k
                JOIN knowledge_usage_stats u ON k.id = u.knowledge_id
                WHERE u.action_type = 'view'
                  AND u.created_at > datetime('now', '-' || ? || ' days')
                GROUP BY k.id
                ORDER BY view_count DESC
                LIMIT ?
            """.format(knowledge_table)  # 検証済みなので format() 使用は安全

            cursor.execute(query, (days, limit))
            return [self._row_to_dict(row) for row in cursor.fetchall()]

    # ========== 分析・レポート ==========

    def get_feedback_summary(self) -> Dict[str, Any]:
        """フィードバックサマリーを取得"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # ナレッジフィードバック統計
            cursor.execute("""
                SELECT
                    COUNT(*) as total_feedback,
                    AVG(rating) as avg_rating,
                    COUNT(DISTINCT knowledge_id) as knowledge_with_feedback
                FROM knowledge_feedback
                WHERE rating IS NOT NULL
            """)
            knowledge_feedback = dict(cursor.fetchone())

            # システムフィードバック統計
            cursor.execute("""
                SELECT
                    COUNT(*) as total_feedback,
                    SUM(CASE WHEN status = 'new' THEN 1 ELSE 0 END) as new_count,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_count
                FROM system_feedback
            """)
            system_feedback = dict(cursor.fetchone())

            # カテゴリ別システムフィードバック
            cursor.execute("""
                SELECT feedback_category, COUNT(*) as count
                FROM system_feedback
                GROUP BY feedback_category
                ORDER BY count DESC
            """)
            feedback_by_category = {
                row["feedback_category"]: row["count"] for row in cursor.fetchall()
            }

            return {
                "knowledge_feedback": knowledge_feedback,
                "system_feedback": system_feedback,
                "feedback_by_category": feedback_by_category,
            }
