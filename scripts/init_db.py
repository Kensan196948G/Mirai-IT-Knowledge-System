#!/usr/bin/env python3
"""
データベース初期化スクリプト
Database Initialization Script
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.mcp.sqlite_client import SQLiteClient


def main():
    """データベースを初期化"""
    print("🔧 データベース初期化を開始します...")

    db_path = project_root / "db" / "knowledge.db"
    schema_path = project_root / "db" / "schema.sql"

    # 既存のDBがある場合は確認
    if db_path.exists():
        response = input(f"⚠️  既存のデータベースが存在します: {db_path}\n削除して再作成しますか? (y/N): ")
        if response.lower() != 'y':
            print("❌ 初期化をキャンセルしました。")
            return
        db_path.unlink()
        print("🗑️  既存のデータベースを削除しました。")

    # SQLiteClientで初期化（スキーマ自動適用）
    client = SQLiteClient(str(db_path))
    print(f"✅ データベースを作成しました: {db_path}")

    # 統計情報を表示
    stats = client.get_statistics()
    print("\n📊 データベース統計:")
    print(f"  - アクティブなナレッジ: {stats['total_knowledge']}件")
    print(f"  - ITSMタイプ別:")
    for itsm_type, count in stats['by_itsm_type'].items():
        print(f"    - {itsm_type}: {count}件")

    # ITSMタグ数を確認
    with client.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM itsm_tags")
        tag_count = cursor.fetchone()['count']
        print(f"  - 登録済みITSMタグ: {tag_count}件")

    print("\n✨ データベース初期化が完了しました！")


if __name__ == "__main__":
    main()
