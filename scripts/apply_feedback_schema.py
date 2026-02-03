#!/usr/bin/env python3
"""
フィードバックスキーマ適用スクリプト
Apply Feedback Schema to Database
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.mcp.feedback_client import FeedbackClient


def main():
    """フィードバックスキーマを適用"""
    print("🔧 フィードバックスキーマを適用します...")

    db_path = project_root / "db" / "knowledge.db"

    # FeedbackClientの初期化でスキーマが自動適用される
    client = FeedbackClient(str(db_path))

    print("✅ フィードバックスキーマの適用が完了しました！")

    # 確認
    with client.get_connection() as conn:
        cursor = conn.cursor()

        # テーブル確認
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name LIKE '%feedback%'
        """)
        tables = [row['name'] for row in cursor.fetchall()]

        print(f"\n📊 追加されたテーブル:")
        for table in tables:
            print(f"  - {table}")

    print("\n✨ フィードバック機能が利用可能になりました！")


if __name__ == "__main__":
    main()
