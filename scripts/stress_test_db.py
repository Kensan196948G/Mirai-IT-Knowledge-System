#!/usr/bin/env python3
"""
Database Stress Test Script
データベースストレステストスクリプト

指定した時間と同時ユーザー数でデータベースへの負荷をかけ、
パフォーマンスメトリクスを収集します。

Usage:
    python scripts/stress_test_db.py --users 10 --duration 60
    python scripts/stress_test_db.py --users 10 --duration 300 --env production
    python scripts/stress_test_db.py --report-only
"""

import argparse
import json
import sqlite3
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Dict, List, Any

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class StressTestMetrics:
    """スレッドセーフなメトリクス収集クラス"""

    def __init__(self):
        self._lock = Lock()
        self.operations: Dict[str, List[float]] = {
            'search': [],
            'view': [],
            'create': [],
            'feedback': []
        }
        self.errors: Dict[str, int] = {
            'search': 0,
            'view': 0,
            'create': 0,
            'feedback': 0
        }
        self.start_time = time.time()
        self.end_time = None

    def record(self, operation_type: str, latency_ms: float, success: bool = True):
        """メトリクスを記録（スレッドセーフ）"""
        with self._lock:
            if success:
                self.operations[operation_type].append(latency_ms)
            else:
                self.errors[operation_type] += 1

    def finalize(self):
        """テスト終了を記録"""
        self.end_time = time.time()

    def get_percentile(self, latencies: List[float], percentile: float) -> float:
        """パーセンタイル計算"""
        if not latencies:
            return 0
        sorted_latencies = sorted(latencies)
        idx = int(len(sorted_latencies) * percentile / 100)
        return sorted_latencies[min(idx, len(sorted_latencies) - 1)]

    def generate_report(self) -> Dict[str, Any]:
        """詳細レポートを生成"""
        duration = (self.end_time or time.time()) - self.start_time

        report = {
            'summary': {
                'duration_seconds': round(duration, 2),
                'total_operations': sum(len(v) for v in self.operations.values()),
                'total_errors': sum(self.errors.values()),
                'operations_per_second': round(
                    sum(len(v) for v in self.operations.values()) / duration, 2
                ) if duration > 0 else 0
            },
            'by_operation': {}
        }

        for op_type, latencies in self.operations.items():
            if latencies:
                report['by_operation'][op_type] = {
                    'count': len(latencies),
                    'errors': self.errors[op_type],
                    'error_rate': f"{self.errors[op_type] / (len(latencies) + self.errors[op_type]) * 100:.2f}%",
                    'latency_ms': {
                        'avg': round(statistics.mean(latencies), 2),
                        'min': round(min(latencies), 2),
                        'max': round(max(latencies), 2),
                        'p50': round(self.get_percentile(latencies, 50), 2),
                        'p95': round(self.get_percentile(latencies, 95), 2),
                        'p99': round(self.get_percentile(latencies, 99), 2)
                    }
                }

        return report


class StressTestRunner:
    """ストレステスト実行クラス"""

    def __init__(self, db_path: Path, num_users: int, duration_seconds: int):
        self.db_path = db_path
        self.num_users = num_users
        self.duration_seconds = duration_seconds
        self.metrics = StressTestMetrics()
        self.running = True

    def get_connection(self) -> sqlite3.Connection:
        """DB接続を取得"""
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=30000")
        return conn

    def operation_search(self, user_id: int) -> bool:
        """検索オペレーション"""
        start_time = time.time()
        queries = ['VPN', 'メール', 'Windows', 'セキュリティ', 'ネットワーク']
        query = queries[user_id % len(queries)]

        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT ke.id, ke.title
                FROM knowledge_entries ke
                JOIN knowledge_fts fts ON ke.id = fts.rowid
                WHERE knowledge_fts MATCH ?
                LIMIT 10
            """, (query,))
            cursor.fetchall()

            cursor.execute("""
                INSERT INTO search_history (search_query, search_type, user_id)
                VALUES (?, 'stress_test', ?)
            """, (query, f"stress_user_{user_id}"))
            conn.commit()
            conn.close()

            latency_ms = (time.time() - start_time) * 1000
            self.metrics.record('search', latency_ms, True)
            return True

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            self.metrics.record('search', latency_ms, False)
            return False

    def operation_view(self, user_id: int, knowledge_ids: List[int]) -> bool:
        """閲覧オペレーション"""
        if not knowledge_ids:
            return False

        start_time = time.time()
        kid = knowledge_ids[user_id % len(knowledge_ids)]

        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM knowledge_entries WHERE id = ?
            """, (kid,))
            cursor.fetchone()

            cursor.execute("""
                INSERT INTO knowledge_usage_stats (knowledge_id, user_id, action_type)
                VALUES (?, ?, 'view')
            """, (kid, f"stress_user_{user_id}"))
            conn.commit()
            conn.close()

            latency_ms = (time.time() - start_time) * 1000
            self.metrics.record('view', latency_ms, True)
            return True

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            self.metrics.record('view', latency_ms, False)
            return False

    def operation_create(self, user_id: int, iteration: int) -> bool:
        """作成オペレーション"""
        start_time = time.time()
        max_retries = 3

        for retry in range(max_retries):
            try:
                conn = self.get_connection()
                cursor = conn.cursor()

                cursor.execute("""
                    INSERT INTO knowledge_entries (
                        title, itsm_type, content, created_by
                    )
                    VALUES (?, 'Other', ?, ?)
                """, (
                    f"StressTest {user_id}-{iteration}-{int(time.time())}",
                    "Stress test content",
                    f"stress_test_user_{user_id}"
                ))
                conn.commit()
                conn.close()

                latency_ms = (time.time() - start_time) * 1000
                self.metrics.record('create', latency_ms, True)
                return True

            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and retry < max_retries - 1:
                    time.sleep(0.1 * (retry + 1))
                    continue
                latency_ms = (time.time() - start_time) * 1000
                self.metrics.record('create', latency_ms, False)
                return False

            except Exception as e:
                latency_ms = (time.time() - start_time) * 1000
                self.metrics.record('create', latency_ms, False)
                return False

        return False

    def operation_feedback(self, user_id: int, knowledge_ids: List[int]) -> bool:
        """フィードバックオペレーション"""
        if not knowledge_ids:
            return False

        start_time = time.time()
        kid = knowledge_ids[user_id % len(knowledge_ids)]

        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO knowledge_feedback (knowledge_id, user_id, rating, feedback_type)
                VALUES (?, ?, ?, 'helpful')
            """, (kid, f"stress_user_{user_id}", (user_id % 5) + 1))
            conn.commit()
            conn.close()

            latency_ms = (time.time() - start_time) * 1000
            self.metrics.record('feedback', latency_ms, True)
            return True

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            self.metrics.record('feedback', latency_ms, False)
            return False

    def user_workload(self, user_id: int, knowledge_ids: List[int]):
        """1ユーザーのワークロード"""
        iteration = 0
        while self.running:
            # ワークロード配分: 50%検索、30%閲覧、10%作成、10%フィードバック
            op_type = iteration % 10
            if op_type < 5:
                self.operation_search(user_id)
            elif op_type < 8:
                self.operation_view(user_id, knowledge_ids)
            elif op_type < 9:
                self.operation_create(user_id, iteration)
            else:
                self.operation_feedback(user_id, knowledge_ids)

            iteration += 1
            time.sleep(0.1)  # 100ms間隔

    def run(self) -> Dict[str, Any]:
        """ストレステストを実行"""
        print(f"\n🚀 ストレステスト開始")
        print(f"   DB: {self.db_path}")
        print(f"   ユーザー数: {self.num_users}")
        print(f"   継続時間: {self.duration_seconds}秒")

        # 既存のナレッジIDを取得
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM knowledge_entries WHERE status = 'active' LIMIT 100")
        knowledge_ids = [row['id'] for row in cursor.fetchall()]
        conn.close()

        if not knowledge_ids:
            print("⚠️  ナレッジデータがありません。サンプルデータを使用します。")
            knowledge_ids = [1]

        print(f"   対象ナレッジ数: {len(knowledge_ids)}")
        print()

        # ワーカースレッド起動
        with ThreadPoolExecutor(max_workers=self.num_users) as executor:
            futures = []
            for user_id in range(self.num_users):
                futures.append(executor.submit(self.user_workload, user_id, knowledge_ids))

            # 指定時間待機
            start_time = time.time()
            while time.time() - start_time < self.duration_seconds:
                elapsed = time.time() - start_time
                total_ops = sum(len(v) for v in self.metrics.operations.values())
                ops_per_sec = total_ops / elapsed if elapsed > 0 else 0
                print(f"\r   進捗: {elapsed:.0f}/{self.duration_seconds}秒 "
                      f"| 総オペレーション: {total_ops} | {ops_per_sec:.1f} ops/sec", end='')
                time.sleep(1)

            # 停止シグナル
            self.running = False

        self.metrics.finalize()
        print("\n")

        # クリーンアップ
        self.cleanup()

        return self.metrics.generate_report()

    def cleanup(self):
        """テストデータのクリーンアップ"""
        print("🧹 テストデータをクリーンアップ中...")
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM knowledge_entries WHERE created_by LIKE 'stress_test_user_%'")
        deleted_knowledge = cursor.rowcount

        cursor.execute("DELETE FROM search_history WHERE user_id LIKE 'stress_user_%'")
        deleted_search = cursor.rowcount

        cursor.execute("DELETE FROM knowledge_usage_stats WHERE user_id LIKE 'stress_user_%'")
        deleted_usage = cursor.rowcount

        cursor.execute("DELETE FROM knowledge_feedback WHERE user_id LIKE 'stress_user_%'")
        deleted_feedback = cursor.rowcount

        conn.commit()
        conn.close()

        print(f"   削除: ナレッジ {deleted_knowledge}件, 検索履歴 {deleted_search}件, "
              f"使用統計 {deleted_usage}件, フィードバック {deleted_feedback}件")


def get_db_path(environment: str) -> Path:
    """環境に応じたDBパスを取得"""
    db_paths = {
        'development': PROJECT_ROOT / 'db' / 'knowledge_dev.db',
        'production': PROJECT_ROOT / 'db' / 'knowledge.db',
        'test': PROJECT_ROOT / 'db' / 'knowledge_test.db'
    }
    return db_paths.get(environment, db_paths['development'])


def print_report(report: Dict[str, Any]):
    """レポートを出力"""
    print("\n" + "=" * 60)
    print("📊 ストレステスト結果レポート")
    print("=" * 60)

    summary = report['summary']
    print(f"\n📋 サマリー:")
    print(f"   実行時間: {summary['duration_seconds']}秒")
    print(f"   総オペレーション数: {summary['total_operations']}")
    print(f"   総エラー数: {summary['total_errors']}")
    print(f"   スループット: {summary['operations_per_second']} ops/sec")

    print(f"\n📈 オペレーション別詳細:")
    for op_type, data in report['by_operation'].items():
        print(f"\n   【{op_type.upper()}】")
        print(f"   実行回数: {data['count']} (エラー: {data['errors']}, エラー率: {data['error_rate']})")
        latency = data['latency_ms']
        print(f"   レイテンシ: avg={latency['avg']}ms, p50={latency['p50']}ms, "
              f"p95={latency['p95']}ms, p99={latency['p99']}ms, max={latency['max']}ms")

    print("\n" + "=" * 60)

    # パフォーマンス基準との比較
    print("\n📏 パフォーマンス基準チェック:")
    targets = {
        'search': {'p50': 200, 'p95': 500},
        'view': {'p50': 50, 'p95': 150},
        'create': {'p50': 2000, 'p95': 5000},
        'feedback': {'p50': 100, 'p95': 300}
    }

    for op_type, data in report['by_operation'].items():
        if op_type in targets:
            target = targets[op_type]
            p50_ok = data['latency_ms']['p50'] <= target['p50']
            p95_ok = data['latency_ms']['p95'] <= target['p95']
            status = "✅" if p50_ok and p95_ok else "⚠️"
            print(f"   {status} {op_type}: P50 {'OK' if p50_ok else 'NG'}, P95 {'OK' if p95_ok else 'NG'}")


def main():
    parser = argparse.ArgumentParser(
        description='データベースストレステストスクリプト',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
例:
  python scripts/stress_test_db.py --users 10 --duration 60
  python scripts/stress_test_db.py --users 10 --duration 300 --env production
        """
    )

    parser.add_argument('--users', '-u', type=int, default=10,
                        help='同時ユーザー数 (default: 10)')
    parser.add_argument('--duration', '-d', type=int, default=60,
                        help='テスト継続時間（秒） (default: 60)')
    parser.add_argument('--env', '-e', choices=['development', 'production', 'test'],
                        default='test', help='実行環境 (default: test)')
    parser.add_argument('--output', '-o', help='JSONレポート出力ファイル')

    args = parser.parse_args()

    db_path = get_db_path(args.env)

    if not db_path.exists():
        print(f"❌ データベースが見つかりません: {db_path}")
        print(f"   先に init_db.py を実行してください")
        sys.exit(1)

    # ストレステスト実行
    runner = StressTestRunner(db_path, args.users, args.duration)
    report = runner.run()

    # レポート出力
    print_report(report)

    # JSONレポート保存
    if args.output:
        output_path = Path(args.output)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n📄 JSONレポートを保存しました: {output_path}")


if __name__ == "__main__":
    main()
