"""
チケット管理クライアント
Ticket Management Client for Mirai IT Knowledge Systems
"""

from .sqlite_client import SQLiteClient
from datetime import datetime
from typing import Dict, List, Optional
import json


class TicketClient(SQLiteClient):
    """チケット管理クライアント"""

    def __init__(self, db_path: str = "db/knowledge_dev.db"):
        super().__init__(db_path)

    def create_ticket(
        self,
        session_id: str,
        title: str,
        description: str,
        category: str,
        priority: str = 'medium',
        created_by: str = 'ai'
    ) -> Dict:
        """
        チケット作成

        Args:
            session_id: 会話セッションID
            title: チケットタイトル
            description: 詳細説明
            category: カテゴリ（incident, problem, request, question, consultation）
            priority: 優先度（low, medium, high, critical）
            created_by: 作成者

        Returns:
            {"success": True, "ticket_id": id, "ticket_number": number}
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # チケット番号生成
                ticket_number = self._generate_ticket_number()

                # チケット作成
                cursor.execute(
                    """
                    INSERT INTO tickets (
                        ticket_number, session_id, title, description,
                        category, priority, created_by, assigned_to, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 'ai', 'new')
                    """,
                    (ticket_number, session_id, title, description,
                     category, priority, created_by)
                )
                ticket_id = cursor.lastrowid

                # 履歴記録
                cursor.execute(
                    """
                    INSERT INTO ticket_history (
                        ticket_id, action, to_value, comment, created_by
                    ) VALUES (?, 'created', ?, ?, ?)
                    """,
                    (ticket_id, 'new', f'チケット作成: {title}', created_by)
                )

                conn.commit()

                return {
                    "success": True,
                    "ticket_id": ticket_id,
                    "ticket_number": ticket_number
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_ticket(self, ticket_id: int) -> Optional[Dict]:
        """
        チケット取得

        Args:
            ticket_id: チケットID

        Returns:
            チケット情報（コメント数を含む）
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT t.*,
                           COUNT(tc.id) as comment_count
                    FROM tickets t
                    LEFT JOIN ticket_comments tc ON t.id = tc.ticket_id
                    WHERE t.id = ?
                    GROUP BY t.id
                    """,
                    (ticket_id,)
                )
                row = cursor.fetchone()
                if row:
                    return self._row_to_dict_ticket(row)
                return None

        except Exception as e:
            print(f"Error getting ticket: {e}")
            return None

    def get_ticket_by_number(self, ticket_number: str) -> Optional[Dict]:
        """
        チケット番号で取得

        Args:
            ticket_number: チケット番号（例: TKT-20260205-001）

        Returns:
            チケット情報
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT t.*,
                           COUNT(tc.id) as comment_count
                    FROM tickets t
                    LEFT JOIN ticket_comments tc ON t.id = tc.ticket_id
                    WHERE t.ticket_number = ?
                    GROUP BY t.id
                    """,
                    (ticket_number,)
                )
                row = cursor.fetchone()
                if row:
                    return self._row_to_dict_ticket(row)
                return None

        except Exception as e:
            print(f"Error getting ticket by number: {e}")
            return None

    def get_ticket_by_session(self, session_id: str) -> Optional[Dict]:
        """
        セッションIDからチケット取得

        Args:
            session_id: セッションID

        Returns:
            チケット情報（最新のもの）
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT t.*,
                           COUNT(tc.id) as comment_count
                    FROM tickets t
                    LEFT JOIN ticket_comments tc ON t.id = tc.ticket_id
                    WHERE t.session_id = ?
                    GROUP BY t.id
                    ORDER BY t.created_at DESC
                    LIMIT 1
                    """,
                    (session_id,)
                )
                row = cursor.fetchone()
                if row:
                    return self._row_to_dict_ticket(row)
                return None

        except Exception as e:
            print(f"Error getting ticket by session: {e}")
            return None

    def update_ticket_status(
        self,
        ticket_id: int,
        status: str,
        comment: str = None,
        updated_by: str = 'ai'
    ) -> bool:
        """
        ステータス更新

        Args:
            ticket_id: チケットID
            status: 新しいステータス
            comment: 更新コメント
            updated_by: 更新者

        Returns:
            成功したかどうか
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # 現在のステータス取得
                cursor.execute("SELECT status FROM tickets WHERE id = ?", (ticket_id,))
                row = cursor.fetchone()
                if not row:
                    return False

                old_status = row['status']

                # ステータス更新
                cursor.execute(
                    """
                    UPDATE tickets
                    SET status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (status, ticket_id)
                )

                # 履歴記録
                cursor.execute(
                    """
                    INSERT INTO ticket_history (
                        ticket_id, action, from_value, to_value, comment, created_by
                    ) VALUES (?, 'status_change', ?, ?, ?, ?)
                    """,
                    (ticket_id, old_status, status, comment, updated_by)
                )

                # コメントがあればコメントテーブルにも追加（同じトランザクション内）
                if comment:
                    cursor.execute(
                        """
                        INSERT INTO ticket_comments (
                            ticket_id, author, content, author_type,
                            is_internal, is_solution, ai_generated
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (ticket_id, updated_by,
                         f"ステータスを {old_status} から {status} に変更: {comment}",
                         'ai' if updated_by == 'ai' else 'user',
                         False, False, updated_by == 'ai')
                    )

                conn.commit()
                return True

        except Exception as e:
            print(f"Error updating ticket status: {e}")
            return False

    def add_ticket_comment(
        self,
        ticket_id: int,
        author: str,
        content: str,
        author_type: str = 'user',
        is_internal: bool = False,
        is_solution: bool = False
    ) -> bool:
        """
        コメント追加

        Args:
            ticket_id: チケットID
            author: 著者名
            content: コメント内容
            author_type: 著者タイプ（user, ai, system）
            is_internal: 内部コメント（ユーザーに非表示）
            is_solution: 解決策コメント

        Returns:
            成功したかどうか
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO ticket_comments (
                        ticket_id, author, content, author_type,
                        is_internal, is_solution, ai_generated
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (ticket_id, author, content, author_type,
                     is_internal, is_solution, author_type == 'ai')
                )
                conn.commit()
                return True

        except Exception as e:
            print(f"Error adding ticket comment: {e}")
            return False

    def get_ticket_comments(
        self,
        ticket_id: int,
        include_internal: bool = False
    ) -> List[Dict]:
        """
        コメント一覧取得

        Args:
            ticket_id: チケットID
            include_internal: 内部コメントを含めるか

        Returns:
            コメントリスト
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                sql = """
                    SELECT * FROM ticket_comments
                    WHERE ticket_id = ?
                """

                if not include_internal:
                    sql += " AND is_internal = 0"

                sql += " ORDER BY created_at ASC"

                cursor.execute(sql, (ticket_id,))
                return [dict(row) for row in cursor.fetchall()]

        except Exception as e:
            print(f"Error getting ticket comments: {e}")
            return []

    def get_active_tickets(
        self,
        limit: int = 20,
        category: str = None
    ) -> List[Dict]:
        """
        アクティブチケット一覧

        Args:
            limit: 取得件数
            category: カテゴリフィルタ

        Returns:
            アクティブチケットリスト
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                sql = """
                    SELECT t.*,
                           COUNT(tc.id) as comment_count
                    FROM tickets t
                    LEFT JOIN ticket_comments tc ON t.id = tc.ticket_id
                    WHERE t.status NOT IN ('closed', 'cancelled')
                """

                params = []
                if category:
                    sql += " AND t.category = ?"
                    params.append(category)

                sql += """
                    GROUP BY t.id
                    ORDER BY
                        CASE t.priority
                            WHEN 'critical' THEN 1
                            WHEN 'high' THEN 2
                            WHEN 'medium' THEN 3
                            WHEN 'low' THEN 4
                        END,
                        t.created_at DESC
                    LIMIT ?
                """
                params.append(limit)

                cursor.execute(sql, params)
                return [self._row_to_dict_ticket(row) for row in cursor.fetchall()]

        except Exception as e:
            print(f"Error getting active tickets: {e}")
            return []

    def resolve_ticket(
        self,
        ticket_id: int,
        resolution: str,
        knowledge_id: int = None,
        resolved_by: str = 'ai'
    ) -> bool:
        """
        チケット解決

        Args:
            ticket_id: チケットID
            resolution: 解決策・対応内容
            knowledge_id: 関連ナレッジID
            resolved_by: 解決者

        Returns:
            成功したかどうか
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # チケット更新
                cursor.execute(
                    """
                    UPDATE tickets
                    SET status = 'resolved',
                        resolution = ?,
                        knowledge_id = ?,
                        resolved_at = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (resolution, knowledge_id, ticket_id)
                )

                # 履歴記録
                cursor.execute(
                    """
                    INSERT INTO ticket_history (
                        ticket_id, action, to_value, comment, created_by
                    ) VALUES (?, 'resolved', 'resolved', ?, ?)
                    """,
                    (ticket_id, resolution, resolved_by)
                )

                # 解決コメント追加（同じトランザクション内）
                cursor.execute(
                    """
                    INSERT INTO ticket_comments (
                        ticket_id, author, content, author_type,
                        is_internal, is_solution, ai_generated
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (ticket_id, resolved_by, f"解決: {resolution}",
                     'ai' if resolved_by == 'ai' else 'user',
                     False, True, resolved_by == 'ai')
                )

                conn.commit()
                return True

        except Exception as e:
            print(f"Error resolving ticket: {e}")
            return False

    def close_ticket(self, ticket_id: int, closed_by: str = 'system') -> bool:
        """
        チケットクローズ

        Args:
            ticket_id: チケットID
            closed_by: クローズ実行者

        Returns:
            成功したかどうか
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # チケット更新
                cursor.execute(
                    """
                    UPDATE tickets
                    SET status = 'closed',
                        closed_at = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (ticket_id,)
                )

                # 履歴記録
                cursor.execute(
                    """
                    INSERT INTO ticket_history (
                        ticket_id, action, to_value, created_by
                    ) VALUES (?, 'closed', 'closed', ?)
                    """,
                    (ticket_id, closed_by)
                )

                conn.commit()
                return True

        except Exception as e:
            print(f"Error closing ticket: {e}")
            return False

    def get_ticket_history(self, ticket_id: int) -> List[Dict]:
        """
        チケット履歴取得

        Args:
            ticket_id: チケットID

        Returns:
            履歴リスト
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT * FROM ticket_history
                    WHERE ticket_id = ?
                    ORDER BY created_at DESC
                    """,
                    (ticket_id,)
                )
                return [dict(row) for row in cursor.fetchall()]

        except Exception as e:
            print(f"Error getting ticket history: {e}")
            return []

    def get_ticket_stats(self) -> Dict:
        """
        チケット統計取得

        Returns:
            統計情報
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM ticket_stats")
                rows = cursor.fetchall()

                stats = {
                    "by_category": {},
                    "by_status": {},
                    "by_priority": {},
                    "total_tickets": 0
                }

                for row in rows:
                    row_dict = dict(row)
                    category = row_dict['category']
                    status = row_dict['status']
                    priority = row_dict['priority']
                    count = row_dict['count']

                    if category not in stats['by_category']:
                        stats['by_category'][category] = 0
                    stats['by_category'][category] += count

                    if status not in stats['by_status']:
                        stats['by_status'][status] = 0
                    stats['by_status'][status] += count

                    if priority not in stats['by_priority']:
                        stats['by_priority'][priority] = 0
                    stats['by_priority'][priority] += count

                    stats['total_tickets'] += count

                return stats

        except Exception as e:
            print(f"Error getting ticket stats: {e}")
            return {
                "by_category": {},
                "by_status": {},
                "by_priority": {},
                "total_tickets": 0
            }

    def _generate_ticket_number(self) -> str:
        """
        チケット番号生成（TKT-YYYYMMDD-NNN形式）

        Returns:
            チケット番号
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # 今日の日付
                today = datetime.now().strftime('%Y%m%d')
                prefix = f"TKT-{today}-"

                # 同日の最大番号を取得
                cursor.execute(
                    """
                    SELECT ticket_number FROM tickets
                    WHERE ticket_number LIKE ?
                    ORDER BY ticket_number DESC
                    LIMIT 1
                    """,
                    (f"{prefix}%",)
                )
                row = cursor.fetchone()

                if row:
                    # 最後の番号を取得して+1
                    last_number = row['ticket_number']
                    last_seq = int(last_number.split('-')[-1])
                    new_seq = last_seq + 1
                else:
                    # 今日最初のチケット
                    new_seq = 1

                return f"{prefix}{new_seq:03d}"

        except Exception as e:
            print(f"Error generating ticket number: {e}")
            # フォールバック: タイムスタンプベース
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            return f"TKT-{timestamp}"

    def _row_to_dict_ticket(self, row) -> Dict:
        """
        チケット用のRow→Dict変換（JSON文字列をパース）

        Args:
            row: sqlite3.Row

        Returns:
            辞書形式のチケット情報
        """
        data = dict(row)

        # JSON フィールドのパース
        json_fields = [
            'current_symptoms', 'related_ticket_ids', 'tags', 'metadata'
        ]

        for field in json_fields:
            if field in data and data[field]:
                try:
                    data[field] = json.loads(data[field])
                except (json.JSONDecodeError, TypeError):
                    pass

        return data
