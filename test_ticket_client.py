#!/usr/bin/env python3
"""
チケット管理クライアント テストスクリプト
Test script for TicketClient
"""

import sys
from pathlib import Path

# プロジェクトのsrcをパスに追加
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcp.ticket_client import TicketClient


def test_ticket_client():
    """チケットクライアントの基本機能をテスト"""

    print("=" * 70)
    print("チケット管理クライアント テスト開始")
    print("=" * 70)
    print()

    # クライアント初期化
    client = TicketClient()
    print("✓ TicketClient 初期化完了")
    print()

    # 1. チケット作成
    print("【1. チケット作成】")
    ticket_result = client.create_ticket(
        session_id="test_session_001",
        title="VPN接続エラーのテスト",
        description="Cisco AnyConnect で認証に失敗します。エラーコード: 0x80004005",
        category="incident",
        priority="high",
        created_by="test_user"
    )

    if ticket_result['success']:
        print(f"✓ チケット作成成功")
        print(f"  - チケットID: {ticket_result['ticket_id']}")
        print(f"  - チケット番号: {ticket_result['ticket_number']}")
        ticket_id = ticket_result['ticket_id']
        ticket_number = ticket_result['ticket_number']
    else:
        print(f"✗ チケット作成失敗: {ticket_result.get('error')}")
        return False
    print()

    # 2. チケット取得（ID）
    print("【2. チケット取得（ID）】")
    ticket = client.get_ticket(ticket_id)
    if ticket:
        print(f"✓ チケット取得成功")
        print(f"  - タイトル: {ticket['title']}")
        print(f"  - ステータス: {ticket['status']}")
        print(f"  - 優先度: {ticket['priority']}")
        print(f"  - カテゴリ: {ticket['category']}")
        print(f"  - コメント数: {ticket['comment_count']}")
    else:
        print("✗ チケット取得失敗")
        return False
    print()

    # 3. チケット取得（番号）
    print("【3. チケット取得（番号）】")
    ticket_by_number = client.get_ticket_by_number(ticket_number)
    if ticket_by_number:
        print(f"✓ チケット番号で取得成功: {ticket_by_number['ticket_number']}")
    else:
        print("✗ チケット番号で取得失敗")
        return False
    print()

    # 4. セッションIDでチケット取得
    print("【4. セッションIDでチケット取得】")
    ticket_by_session = client.get_ticket_by_session("test_session_001")
    if ticket_by_session:
        print(f"✓ セッションIDで取得成功")
        print(f"  - チケット番号: {ticket_by_session['ticket_number']}")
    else:
        print("✗ セッションIDで取得失敗")
        return False
    print()

    # 5. ステータス更新
    print("【5. ステータス更新】")
    if client.update_ticket_status(
        ticket_id,
        'in_progress',
        'VPN証明書の確認を開始',
        'ai'
    ):
        print("✓ ステータス更新成功: new → in_progress")

        # 更新確認
        ticket = client.get_ticket(ticket_id)
        print(f"  - 現在のステータス: {ticket['status']}")
        print(f"  - コメント数: {ticket['comment_count']}")
    else:
        print("✗ ステータス更新失敗")
        return False
    print()

    # 6. コメント追加
    print("【6. コメント追加】")
    if client.add_ticket_comment(
        ticket_id,
        'ai',
        '診断中: VPN証明書の有効期限を確認しています...',
        'ai'
    ):
        print("✓ コメント追加成功（1件目）")
    else:
        print("✗ コメント追加失敗")
        return False

    if client.add_ticket_comment(
        ticket_id,
        'ai',
        '証明書の有効期限が切れていることを確認しました',
        'ai',
        is_internal=False,
        is_solution=False
    ):
        print("✓ コメント追加成功（2件目）")
    else:
        print("✗ コメント追加失敗")
        return False
    print()

    # 7. コメント一覧取得
    print("【7. コメント一覧取得】")
    comments = client.get_ticket_comments(ticket_id, include_internal=False)
    print(f"✓ コメント取得成功: {len(comments)}件")
    for i, comment in enumerate(comments, 1):
        print(f"  [{i}] {comment['author']} ({comment['author_type']}): "
              f"{comment['content'][:50]}...")
    print()

    # 8. チケット履歴取得
    print("【8. チケット履歴取得】")
    history = client.get_ticket_history(ticket_id)
    print(f"✓ 履歴取得成功: {len(history)}件")
    for i, entry in enumerate(history, 1):
        print(f"  [{i}] {entry['action']}: {entry.get('from_value', 'N/A')} → "
              f"{entry.get('to_value', 'N/A')} ({entry['created_by']})")
    print()

    # 9. アクティブチケット一覧
    print("【9. アクティブチケット一覧】")
    active_tickets = client.get_active_tickets(limit=10)
    print(f"✓ アクティブチケット取得成功: {len(active_tickets)}件")
    for ticket in active_tickets[:3]:  # 最初の3件を表示
        print(f"  - {ticket['ticket_number']}: {ticket['title']} "
              f"[{ticket['status']}/{ticket['priority']}]")
    print()

    # 10. チケット解決
    print("【10. チケット解決】")
    if client.resolve_ticket(
        ticket_id,
        'VPN証明書を更新することで解決しました。\n'
        '手順: 設定 > 証明書管理 > 新しい証明書をインポート',
        knowledge_id=None,
        resolved_by='ai'
    ):
        print("✓ チケット解決成功")

        # 解決確認
        ticket = client.get_ticket(ticket_id)
        print(f"  - 現在のステータス: {ticket['status']}")
        print(f"  - 解決策: {ticket['resolution'][:60]}...")
        print(f"  - 解決日時: {ticket['resolved_at']}")
    else:
        print("✗ チケット解決失敗")
        return False
    print()

    # 11. チケット統計取得
    print("【11. チケット統計取得】")
    stats = client.get_ticket_stats()
    print(f"✓ 統計取得成功")
    print(f"  - 総チケット数: {stats['total_tickets']}")
    print(f"  - カテゴリ別: {stats['by_category']}")
    print(f"  - ステータス別: {stats['by_status']}")
    print(f"  - 優先度別: {stats['by_priority']}")
    print()

    # 12. 追加のチケット作成（番号生成確認）
    print("【12. 複数チケット作成（番号生成確認）】")
    for i in range(3):
        result = client.create_ticket(
            session_id=f"test_session_{i:03d}",
            title=f"テストチケット {i+1}",
            description=f"これはテストチケット #{i+1} です",
            category="request",
            priority="medium"
        )
        if result['success']:
            print(f"  ✓ チケット作成: {result['ticket_number']}")
        else:
            print(f"  ✗ チケット作成失敗: {result.get('error')}")
    print()

    # 13. チケットクローズ
    print("【13. チケットクローズ】")
    if client.close_ticket(ticket_id, closed_by='system'):
        print("✓ チケットクローズ成功")

        # クローズ確認
        ticket = client.get_ticket(ticket_id)
        print(f"  - 最終ステータス: {ticket['status']}")
        print(f"  - クローズ日時: {ticket['closed_at']}")
    else:
        print("✗ チケットクローズ失敗")
        return False
    print()

    print("=" * 70)
    print("✅ 全テスト成功!")
    print("=" * 70)
    return True


if __name__ == "__main__":
    try:
        success = test_ticket_client()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ テスト中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
