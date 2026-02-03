#!/usr/bin/env python3
"""
対話履歴スキーマ適用スクリプト
Apply Conversation Schema to Database
"""

import sys
import sqlite3
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def main():
    """対話履歴スキーマを適用"""
    print("🔧 対話履歴スキーマを適用します...")

    db_path = project_root / "db" / "knowledge.db"

    schema_sql = """
    CREATE TABLE IF NOT EXISTS conversation_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT UNIQUE NOT NULL,
        user_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP,
        knowledge_id INTEGER,
        FOREIGN KEY (knowledge_id) REFERENCES knowledge_entries(id) ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS conversation_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        role TEXT CHECK(role IN ('user', 'assistant')),
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES conversation_sessions(session_id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_conversation_session ON conversation_sessions(created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_conversation_message ON conversation_messages(session_id, created_at DESC);
    """

    with sqlite3.connect(db_path) as conn:
        conn.executescript(schema_sql)
        conn.commit()

    print("✅ 対話履歴スキーマの適用が完了しました！")


if __name__ == "__main__":
    main()
