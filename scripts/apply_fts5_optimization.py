#!/usr/bin/env python3
"""
FTS5全文検索最適化スクリプト
Phase 8.2実装
"""

import sys
import sqlite3
import time
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def apply_fts5_optimization(db_path: str = "db/knowledge.db"):
    """FTS5最適化を適用"""
    print("=" * 80)
    print("FTS5全文検索最適化")
    print("=" * 80)

    # SQLファイル読み込み
    sql_file = project_root / "db" / "fts5_optimizations.sql"
    if not sql_file.exists():
        print(f"❌ SQLファイルが見つかりません: {sql_file}")
        return False

    with open(sql_file, "r", encoding="utf-8") as f:
        optimization_sql = f.read()

    # データベース接続
    conn = sqlite3.connect(db_path)

    try:
        print(f"\n📂 データベース: {db_path}")

        # FTS5テーブル存在確認
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='knowledge_fts'"
        )
        if not cursor.fetchone():
            print("\n⚠️  FTS5テーブルが存在しません。スキーマを適用します...")
            schema_file = project_root / "db" / "schema.sql"
            if schema_file.exists():
                with open(schema_file, 'r', encoding='utf-8') as f:
                    schema = f.read()
                conn.executescript(schema)
                print("   ✅ スキーマ適用完了")
            else:
                print("   ❌ schema.sqlが見つかりません")
                return False

        # WALモード有効化
        print("\n🔧 WALモード有効化...")
        conn.execute("PRAGMA journal_mode = WAL")
        result = conn.execute("PRAGMA journal_mode").fetchone()
        print(f"   ✅ Journal mode: {result[0]}")

        # FTS5最適化実行
        print("\n🔍 FTS5インデックス最適化中...")
        start_time = time.time()

        # optimize実行
        conn.execute("INSERT INTO knowledge_fts(knowledge_fts) VALUES('optimize')")
        optimize_time = int((time.time() - start_time) * 1000)
        print(f"   ✅ FTS5 optimize完了: {optimize_time}ms")

        # rebuild実行
        start_time = time.time()
        conn.execute("INSERT INTO knowledge_fts(knowledge_fts) VALUES('rebuild')")
        rebuild_time = int((time.time() - start_time) * 1000)
        print(f"   ✅ FTS5 rebuild完了: {rebuild_time}ms")

        # 追加インデックス作成
        print("\n📊 追加インデックス作成中...")

        indexes = [
            ("idx_knowledge_itsm_created", "knowledge_entries(itsm_type, created_at DESC)"),
            ("idx_knowledge_status_itsm", "knowledge_entries(status, itsm_type)"),
            ("idx_knowledge_created_by", "knowledge_entries(created_by)"),
            ("idx_knowledge_updated_at", "knowledge_entries(updated_at DESC)"),
        ]

        for idx_name, idx_def in indexes:
            try:
                conn.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {idx_def}")
                print(f"   ✅ {idx_name}")
            except sqlite3.Error as e:
                print(f"   ⚠️  {idx_name}: {e}")

        conn.commit()

        # 統計情報表示
        print("\n📈 データベース統計:")
        cursor = conn.execute("""
            SELECT COUNT(*) FROM knowledge_entries
        """)
        knowledge_count = cursor.fetchone()[0]
        print(f"   - ナレッジエントリ数: {knowledge_count}")

        cursor = conn.execute("""
            SELECT COUNT(*) FROM knowledge_fts
        """)
        fts_count = cursor.fetchone()[0]
        print(f"   - FTS5インデックス数: {fts_count}")

        # インデックス一覧
        cursor = conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND name LIKE 'idx_knowledge%'
            ORDER BY name
        """)
        indexes_list = cursor.fetchall()
        print(f"\n📋 作成済みインデックス ({len(indexes_list)}個):")
        for idx in indexes_list:
            print(f"   - {idx[0]}")

        print("\n" + "=" * 80)
        print("✅ FTS5最適化完了")
        print("=" * 80)

        return True

    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        conn.close()


def test_search_performance(db_path: str = "db/knowledge.db"):
    """検索パフォーマンステスト"""
    print("\n" + "=" * 80)
    print("検索パフォーマンステスト")
    print("=" * 80)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    test_queries = [
        "データベース",
        "サーバー エラー",
        "証明書 更新",
        "Active Directory ロック"
    ]

    print("\n検索クエリ実行:")
    for query in test_queries:
        start_time = time.time()

        cursor = conn.execute("""
            SELECT ke.id, ke.title, ke.itsm_type, rank
            FROM knowledge_fts
            JOIN knowledge_entries ke ON knowledge_fts.rowid = ke.id
            WHERE knowledge_fts MATCH ?
            ORDER BY rank
            LIMIT 5
        """, (query,))

        results = cursor.fetchall()
        elapsed_ms = int((time.time() - start_time) * 1000)

        print(f"\n   Query: '{query}'")
        print(f"   Time: {elapsed_ms}ms")
        print(f"   Results: {len(results)}件")

        if elapsed_ms < 100:
            print(f"   ✅ 優秀 (< 100ms)")
        elif elapsed_ms < 200:
            print(f"   ✅ 良好 (< 200ms)")
        else:
            print(f"   ⚠️  要改善 (> 200ms)")

    conn.close()

    print("\n" + "=" * 80)
    print("✅ 検索パフォーマンステスト完了")
    print("=" * 80)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="FTS5最適化実行")
    parser.add_argument(
        "--db",
        default="db/knowledge.db",
        help="データベースパス（デフォルト: db/knowledge.db）"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="検索パフォーマンステストも実行"
    )

    args = parser.parse_args()

    # 最適化実行
    success = apply_fts5_optimization(args.db)

    # パフォーマンステスト
    if success and args.test:
        test_search_performance(args.db)

    sys.exit(0 if success else 1)
