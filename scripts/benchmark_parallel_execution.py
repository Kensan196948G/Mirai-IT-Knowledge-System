#!/usr/bin/env python3
"""
並列実行パフォーマンスベンチマーク
Phase 7検証用
"""

import sys
import time
from pathlib import Path

# モジュールパスを追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.workflow import WorkflowEngine


def benchmark_workflow(test_case_name: str, title: str, content: str, itsm_type: str, iterations: int = 3):
    """ワークフローのベンチマーク実行"""
    print(f"\n{'=' * 80}")
    print(f"ベンチマーク: {test_case_name}")
    print(f"{'=' * 80}")

    engine = WorkflowEngine()
    execution_times = []

    for i in range(iterations):
        print(f"\nIteration {i + 1}/{iterations}...")
        start_time = time.time()

        try:
            result = engine.process_knowledge(
                title=title,
                content=content,
                itsm_type=itsm_type,
                created_by="benchmark"
            )

            elapsed_ms = int((time.time() - start_time) * 1000)
            execution_times.append(elapsed_ms)

            print(f"  ✅ 完了: {elapsed_ms}ms")
            print(f"  - ナレッジID: {result.get('knowledge_id')}")
            print(f"  - 成功: {result.get('success')}")

        except Exception as e:
            print(f"  ❌ エラー: {e}")
            elapsed_ms = int((time.time() - start_time) * 1000)
            execution_times.append(elapsed_ms)

    # 統計計算
    avg_time = sum(execution_times) / len(execution_times)
    min_time = min(execution_times)
    max_time = max(execution_times)

    print(f"\n📊 統計:")
    print(f"  - 平均実行時間: {avg_time:.0f}ms")
    print(f"  - 最小実行時間: {min_time}ms")
    print(f"  - 最大実行時間: {max_time}ms")

    return {
        "test_case": test_case_name,
        "avg_time_ms": avg_time,
        "min_time_ms": min_time,
        "max_time_ms": max_time,
        "iterations": iterations
    }


def main():
    """メイン実行"""
    print("=" * 80)
    print("Phase 7 成果検証: 並列実行パフォーマンスベンチマーク")
    print("=" * 80)

    # テストケース1: 簡単なインシデント
    result1 = benchmark_workflow(
        test_case_name="簡単なインシデント",
        title="メール送信エラー",
        content="ユーザーからメール送信ができないとの報告あり。SMTPサーバーのログを確認したところ、認証エラーが発生していた。",
        itsm_type="Incident",
        iterations=2  # 時間短縮のため2回
    )

    # テストケース2: 複雑な問題管理
    result2 = benchmark_workflow(
        test_case_name="複雑な問題管理",
        title="データベース接続プールの枯渇問題",
        content="""
        繰り返し発生するデータベース接続エラーの根本原因を分析。

        症状:
        - ピーク時に接続プール枯渇
        - タイムアウトエラー多発

        根本原因:
        - 接続プール最大数が少なすぎる
        - 長時間実行クエリによる接続占有

        対策:
        - 接続プール最大数を20→50に増加
        - スロークエリログ有効化
        - インデックス最適化
        """,
        itsm_type="Problem",
        iterations=2
    )

    # 結果サマリー
    print("\n" + "=" * 80)
    print("📊 ベンチマーク結果サマリー")
    print("=" * 80)

    for result in [result1, result2]:
        print(f"\n{result['test_case']}:")
        print(f"  - 平均実行時間: {result['avg_time_ms']:.0f}ms")
        print(f"  - 範囲: {result['min_time_ms']}ms - {result['max_time_ms']}ms")

    # 期待値との比較
    print("\n" + "=" * 80)
    print("🎯 Phase 7目標達成度")
    print("=" * 80)
    print(f"目標: 処理時間50%削減（5000ms → 2500ms）")
    print(f"実測平均: {result1['avg_time_ms']:.0f}ms - {result2['avg_time_ms']:.0f}ms")

    if result2['avg_time_ms'] < 2500:
        print("✅ 目標達成！")
    elif result2['avg_time_ms'] < 3500:
        print("⚠️  目標に近い（許容範囲）")
    else:
        print("❌ 要改善")

    print("\n" + "=" * 80)
    print("✅ ベンチマーク完了")
    print("=" * 80)


if __name__ == "__main__":
    main()
