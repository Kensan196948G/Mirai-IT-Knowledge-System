#!/usr/bin/env python3
"""
FTS5全文検索インデックス同期修正スクリプト
Fix FTS5 Search Index Synchronization
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.mcp.sqlite_client import SQLiteClient


def main():
    """FTS5インデックスを再構築"""
    print("🔧 FTS5全文検索インデックスの修正を開始します...")
    print()

    client = SQLiteClient()

    with client.get_connection() as conn:
        cursor = conn.cursor()

        # 現在のFTS5の状態を確認
        cursor.execute("SELECT COUNT(*) as count FROM knowledge_fts")
        fts_count = cursor.fetchone()['count']
        print(f"現在のFTS5インデックス件数: {fts_count}件")

        cursor.execute("SELECT COUNT(*) as count FROM knowledge_entries WHERE status = 'active'")
        entries_count = cursor.fetchone()['count']
        print(f"アクティブなナレッジ件数: {entries_count}件")
        print()

        if fts_count != entries_count:
            print("⚠️  FTS5インデックスとナレッジエントリが同期していません！")
            print("   インデックスを再構築します...")
            print()

            # FTS5を完全に再構築
            cursor.execute("DELETE FROM knowledge_fts")

            # 全ナレッジをFTS5に再挿入
            cursor.execute("""
                SELECT id, title, summary_technical, summary_non_technical, content
                FROM knowledge_entries
                WHERE status = 'active'
            """)

            count = 0
            for row in cursor.fetchall():
                cursor.execute("""
                    INSERT INTO knowledge_fts(rowid, title, summary_technical, summary_non_technical, content)
                    VALUES (?, ?, ?, ?, ?)
                """, (row['id'], row['title'], row['summary_technical'], row['summary_non_technical'], row['content']))
                count += 1

            conn.commit()
            print(f"✅ {count}件のナレッジをFTS5に再登録しました")
        else:
            print("✅ FTS5インデックスは正常に同期されています")

        print()

        # 検証テスト
        print("🔍 検索テストを実行中...")
        test_queries = ['メール', 'データベース', 'Web', 'エラー', 'バックアップ']

        for query in test_queries:
            cursor.execute("""
                SELECT k.id, k.title
                FROM knowledge_entries k
                JOIN knowledge_fts f ON k.id = f.rowid
                WHERE knowledge_fts MATCH ?
                LIMIT 5
            """, (query,))
            results = cursor.fetchall()
            print(f"  「{query}」: {len(results)}件")
            for r in results:
                print(f"    - {r['title']}")

    print()
    print("✨ FTS5インデックスの修正が完了しました！")


if __name__ == "__main__":
    main()
