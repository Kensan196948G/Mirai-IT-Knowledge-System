#!/usr/bin/env python3
"""
自動エラー検知・修復システム テストコード

仕様書: 19_自動エラー検知修復システム仕様書.md
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# プロジェクトルートをパスに追加
SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(SCRIPT_DIR))

from health_monitor import HealthMonitor, HealthCheckResult, SystemMetrics
from auto_fix_daemon import AutoFixDaemon, DetectedError, FixResult


class TestHealthMonitor(unittest.TestCase):
    """ヘルスモニターのテスト"""

    def setUp(self):
        """テストセットアップ"""
        self.monitor = HealthMonitor()

    def test_check_disk_space(self):
        """ディスク容量チェック"""
        result = self.monitor.check_disk_space("/")

        self.assertIsInstance(result, HealthCheckResult)
        self.assertEqual(result.name, "disk_space")
        self.assertIn(result.status, ["healthy", "unhealthy"])
        self.assertTrue(result.critical)
        self.assertIn("usage_percent", result.details)
        self.assertIn("free_gb", result.details)

    def test_check_memory_usage(self):
        """メモリ使用量チェック"""
        result = self.monitor.check_memory_usage()

        self.assertIsInstance(result, HealthCheckResult)
        self.assertEqual(result.name, "memory_usage")
        self.assertIn(result.status, ["healthy", "unhealthy"])
        self.assertFalse(result.critical)  # メモリはクリティカルではない

    def test_check_sqlite_connection_missing_db(self):
        """SQLite接続チェック（DBなし）"""
        result = self.monitor.check_sqlite_connection("/nonexistent/path.db")

        self.assertEqual(result.status, "unhealthy")
        self.assertIn("not found", result.message.lower())

    def test_check_sqlite_connection_valid_db(self):
        """SQLite接続チェック（有効なDB）"""
        # テスト用の一時DBを作成
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            temp_db = f.name

        try:
            import sqlite3
            conn = sqlite3.connect(temp_db)
            conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY)")
            conn.commit()
            conn.close()

            result = self.monitor.check_sqlite_connection(temp_db)
            self.assertEqual(result.status, "healthy")
        finally:
            os.unlink(temp_db)

    def test_check_port_closed(self):
        """ポートチェック（クローズ）"""
        # 使用されていないであろうポート
        result = self.monitor.check_port(59999)

        self.assertIn(result.status, ["healthy", "unhealthy"])

    def test_check_http_endpoint_invalid(self):
        """HTTPエンドポイントチェック（無効）"""
        result = self.monitor.check_http_endpoint("http://localhost:59999/invalid", timeout=2)

        self.assertEqual(result.status, "unhealthy")
        self.assertTrue(result.critical)

    def test_check_directory_exists(self):
        """ディレクトリチェック（存在）"""
        result = self.monitor.check_directory("scripts")

        self.assertIn(result.status, ["healthy", "degraded"])

    def test_check_directory_not_exists(self):
        """ディレクトリチェック（不存在）"""
        result = self.monitor.check_directory("nonexistent_dir_12345")

        self.assertEqual(result.status, "unhealthy")

    def test_collect_metrics(self):
        """メトリクス収集"""
        metrics = self.monitor.collect_metrics()

        self.assertIsInstance(metrics, SystemMetrics)
        self.assertGreaterEqual(metrics.disk_total_gb, 0)
        self.assertGreaterEqual(metrics.cpu_count, 1)

    def test_run_all_checks(self):
        """全チェック実行"""
        results = self.monitor.run_all_checks()

        self.assertIn("timestamp", results)
        self.assertIn("checks", results)
        self.assertIn("overall_status", results)
        self.assertIn("metrics", results)
        self.assertIn(results["overall_status"], ["healthy", "degraded", "critical"])


class TestAutoFixDaemon(unittest.TestCase):
    """自動修復デーモンのテスト"""

    def setUp(self):
        """テストセットアップ"""
        # 一時ログファイルを使用
        self.temp_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.temp_dir, "test_auto_fix.log")

        # 一時設定ファイル
        self.config = {
            "error_patterns": [
                {
                    "id": "test_error",
                    "name": "Test Error",
                    "pattern": "TEST_ERROR_PATTERN",
                    "severity": "warning",
                    "auto_fix": True,
                    "actions": [
                        {"type": "log_analysis", "description": "Test action"}
                    ]
                }
            ],
            "health_checks": [],
            "auto_fix_config": {
                "max_retries": 3,
                "cooldown_period": 300,
                "backup_before_fix": False
            },
            "monitored_log_files": [],
            "project_config": {
                "api_port": 8888,
                "db_path": "db/knowledge.db"
            }
        }

        self.config_file = os.path.join(self.temp_dir, "test_config.json")
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f)

        self.daemon = AutoFixDaemon(
            config_path=self.config_file,
            log_file=self.log_file
        )

    def tearDown(self):
        """テストクリーンアップ"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization(self):
        """初期化テスト"""
        self.assertIsNotNone(self.daemon.config)
        self.assertIsNotNone(self.daemon.logger)
        self.assertIsNotNone(self.daemon.health_monitor)
        self.assertTrue(self.daemon.running)

    def test_is_in_cooldown_false(self):
        """クールダウン確認（対象外）"""
        result = self.daemon.is_in_cooldown("nonexistent_error")
        self.assertFalse(result)

    def test_is_in_cooldown_true(self):
        """クールダウン確認（対象）"""
        from datetime import datetime
        self.daemon.fix_history["test_error"] = datetime.now()

        result = self.daemon.is_in_cooldown("test_error")
        self.assertTrue(result)

    def test_scan_logs_empty(self):
        """ログスキャン（空）"""
        errors = self.daemon.scan_logs([])
        self.assertEqual(len(errors), 0)

    def test_scan_logs_with_pattern(self):
        """ログスキャン（パターンマッチ）"""
        # テストログファイル作成
        test_log = os.path.join(self.temp_dir, "test.log")
        with open(test_log, 'w') as f:
            f.write("Normal log line\n")
            f.write("TEST_ERROR_PATTERN occurred here\n")
            f.write("Another normal line\n")

        errors = self.daemon.scan_logs([test_log])

        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].id, "test_error")
        self.assertEqual(errors[0].severity, "warning")

    def test_execute_action_log_analysis(self):
        """アクション実行（ログ分析）"""
        action = {"type": "log_analysis", "description": "Test analysis"}
        success, message = self.daemon.execute_action(action)

        self.assertTrue(success)
        self.assertIn("completed", message.lower())

    def test_execute_action_create_missing_dirs(self):
        """アクション実行（ディレクトリ作成）"""
        test_dir = os.path.join(self.temp_dir, "new_dir")
        action = {
            "type": "create_missing_dirs",
            "directories": [test_dir]
        }

        # project_rootを一時ディレクトリに変更
        original_root = self.daemon.project_root
        self.daemon.project_root = Path(self.temp_dir)

        try:
            success, message = self.daemon.execute_action(action)
            self.assertTrue(success)
        finally:
            self.daemon.project_root = original_root

    def test_execute_action_alert(self):
        """アクション実行（アラート）"""
        action = {"type": "alert", "description": "Test alert"}
        success, message = self.daemon.execute_action(action)

        self.assertTrue(success)
        self.assertIn("logged", message.lower())

    def test_execute_action_unknown(self):
        """アクション実行（不明）"""
        action = {"type": "unknown_action_type"}
        success, message = self.daemon.execute_action(action)

        self.assertFalse(success)
        self.assertIn("unknown", message.lower())

    def test_auto_fix_error_cooldown(self):
        """エラー修復（クールダウン中）"""
        from datetime import datetime

        error = DetectedError(
            id="test_error",
            name="Test Error",
            pattern="TEST",
            severity="warning",
            auto_fix=True,
            actions=[],
            source_file="test.log",
            matched_line="TEST_ERROR_PATTERN"
        )

        # クールダウン設定
        self.daemon.fix_history["test_error"] = datetime.now()

        result = self.daemon.auto_fix_error(error)

        self.assertFalse(result.success)
        self.assertIn("cooldown", result.message.lower())

    def test_auto_fix_error_disabled(self):
        """エラー修復（無効）"""
        error = DetectedError(
            id="test_error",
            name="Test Error",
            pattern="TEST",
            severity="warning",
            auto_fix=False,  # 無効
            actions=[],
            source_file="test.log",
            matched_line="TEST_ERROR_PATTERN"
        )

        result = self.daemon.auto_fix_error(error)

        self.assertFalse(result.success)
        self.assertIn("disabled", result.message.lower())

    def test_auto_fix_error_success(self):
        """エラー修復（成功）"""
        error = DetectedError(
            id="new_error",  # クールダウンなし
            name="Test Error",
            pattern="TEST",
            severity="warning",
            auto_fix=True,
            actions=[
                {"type": "log_analysis", "description": "Test"}
            ],
            source_file="test.log",
            matched_line="TEST_ERROR_PATTERN"
        )

        result = self.daemon.auto_fix_error(error)

        self.assertTrue(result.success)
        self.assertEqual(len(result.actions_executed), 1)

    def test_run_detection_cycle(self):
        """検知サイクル実行"""
        result = self.daemon.run_detection_cycle(1)

        self.assertIn("cycle", result)
        self.assertEqual(result["cycle"], 1)
        self.assertIn("timestamp", result)
        self.assertIn("health_check", result)
        self.assertIn("errors_detected", result)
        self.assertIn("fixes_applied", result)


class TestDetectedError(unittest.TestCase):
    """検出エラーデータクラスのテスト"""

    def test_detected_error_creation(self):
        """エラーオブジェクト作成"""
        error = DetectedError(
            id="test_id",
            name="Test Name",
            pattern="test.*pattern",
            severity="critical",
            auto_fix=True,
            actions=[{"type": "alert"}],
            source_file="test.log",
            matched_line="test line"
        )

        self.assertEqual(error.id, "test_id")
        self.assertEqual(error.severity, "critical")
        self.assertTrue(error.auto_fix)
        self.assertIsNotNone(error.timestamp)


class TestFixResult(unittest.TestCase):
    """修復結果データクラスのテスト"""

    def test_fix_result_creation(self):
        """修復結果オブジェクト作成"""
        result = FixResult(
            error_id="test_id",
            success=True,
            actions_executed=[{"type": "alert", "success": True}],
            message="Test complete"
        )

        self.assertEqual(result.error_id, "test_id")
        self.assertTrue(result.success)
        self.assertEqual(len(result.actions_executed), 1)
        self.assertIsNotNone(result.timestamp)


class TestErrorPatterns(unittest.TestCase):
    """エラーパターン設定のテスト"""

    def test_load_error_patterns(self):
        """エラーパターン読み込み"""
        config_path = SCRIPT_DIR / "error_patterns.json"

        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)

            self.assertIn("error_patterns", config)
            self.assertIn("health_checks", config)
            self.assertIn("auto_fix_config", config)

            # パターン数確認
            patterns = config["error_patterns"]
            self.assertGreater(len(patterns), 0)

            # 必須フィールド確認
            for pattern in patterns:
                self.assertIn("id", pattern)
                self.assertIn("name", pattern)
                self.assertIn("pattern", pattern)
                self.assertIn("severity", pattern)
                self.assertIn("auto_fix", pattern)


class TestIntegration(unittest.TestCase):
    """統合テスト"""

    def test_full_detection_cycle(self):
        """完全な検知サイクル"""
        temp_dir = tempfile.mkdtemp()
        log_file = os.path.join(temp_dir, "test.log")

        try:
            daemon = AutoFixDaemon(log_file=log_file)

            # 1サイクル実行
            result = daemon.run_detection_cycle(1)

            self.assertIsNotNone(result)
            self.assertEqual(result["cycle"], 1)

        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    # 詳細出力
    unittest.main(verbosity=2)
