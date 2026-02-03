#!/usr/bin/env python3
"""
ヘルスモニターモジュール
システムヘルスチェックとメトリクス収集

仕様書: 19_自動エラー検知修復システム仕様書.md
"""

import json
import logging
import os
import shutil
import sqlite3
import socket
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.request import urlopen
from urllib.error import URLError, HTTPError

# プロジェクトルートをパスに追加
SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

# psutil は必須ではないがあれば使用
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


@dataclass
class HealthCheckResult:
    """ヘルスチェック結果"""
    name: str
    status: str  # "healthy", "unhealthy", "degraded"
    message: str
    critical: bool
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemMetrics:
    """システムメトリクス"""
    cpu_usage_percent: float = 0.0
    cpu_count: int = 1
    memory_total_gb: float = 0.0
    memory_used_gb: float = 0.0
    memory_usage_percent: float = 0.0
    disk_total_gb: float = 0.0
    disk_used_gb: float = 0.0
    disk_usage_percent: float = 0.0
    network_bytes_sent_mb: float = 0.0
    network_bytes_recv_mb: float = 0.0
    process_count: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class HealthMonitor:
    """
    システムヘルスモニター

    機能:
    - SQLite接続チェック
    - ディスク容量チェック
    - メモリ使用量チェック
    - HTTPエンドポイントチェック
    - ポート使用状況チェック
    - システムメトリクス収集
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        初期化

        Args:
            config_path: 設定ファイルパス（省略時はデフォルト）
        """
        self.project_root = PROJECT_ROOT
        self.config_path = config_path or str(SCRIPT_DIR / "error_patterns.json")
        self.config = self._load_config()
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """ロガーセットアップ"""
        logger = logging.getLogger("HealthMonitor")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - [%(levelname)s] - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def _load_config(self) -> Dict[str, Any]:
        """設定ファイル読み込み"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            # デフォルト設定
            return {
                "health_checks": [],
                "project_config": {
                    "api_port": 8888,
                    "db_path": "db/knowledge.db"
                }
            }

    def check_sqlite_connection(self, db_path: Optional[str] = None) -> HealthCheckResult:
        """
        SQLite接続チェック

        Args:
            db_path: データベースファイルパス

        Returns:
            HealthCheckResult
        """
        if db_path is None:
            db_path = self.config.get("project_config", {}).get("db_path", "db/knowledge.db")

        full_path = self.project_root / db_path

        try:
            if not full_path.exists():
                return HealthCheckResult(
                    name="database_connection",
                    status="unhealthy",
                    message=f"Database file not found: {full_path}",
                    critical=True
                )

            # 接続テスト
            conn = sqlite3.connect(str(full_path), timeout=5)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()

            # テーブル存在確認
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            conn.close()

            return HealthCheckResult(
                name="database_connection",
                status="healthy",
                message="SQLite database accepting connections",
                critical=True,
                details={"tables_count": len(tables), "db_path": str(full_path)}
            )

        except sqlite3.Error as e:
            return HealthCheckResult(
                name="database_connection",
                status="unhealthy",
                message=f"SQLite connection error: {str(e)}",
                critical=True,
                details={"error": str(e)}
            )

    def check_disk_space(self, path: str = "/", threshold: int = 90) -> HealthCheckResult:
        """
        ディスク容量チェック

        Args:
            path: チェック対象パス
            threshold: 警告閾値（%）

        Returns:
            HealthCheckResult
        """
        try:
            usage = shutil.disk_usage(path)
            total_gb = usage.total / (1024 ** 3)
            used_gb = usage.used / (1024 ** 3)
            free_gb = usage.free / (1024 ** 3)
            usage_percent = (usage.used / usage.total) * 100

            status = "healthy" if usage_percent < threshold else "unhealthy"

            return HealthCheckResult(
                name="disk_space",
                status=status,
                message=f"Disk usage: {usage_percent:.1f}% ({free_gb:.1f}GB free)",
                critical=True,
                details={
                    "usage_percent": round(usage_percent, 1),
                    "total_gb": round(total_gb, 1),
                    "used_gb": round(used_gb, 1),
                    "free_gb": round(free_gb, 1),
                    "threshold": threshold
                }
            )

        except OSError as e:
            return HealthCheckResult(
                name="disk_space",
                status="unhealthy",
                message=f"Disk check error: {str(e)}",
                critical=True,
                details={"error": str(e)}
            )

    def check_memory_usage(self, threshold: int = 85) -> HealthCheckResult:
        """
        メモリ使用量チェック

        Args:
            threshold: 警告閾値（%）

        Returns:
            HealthCheckResult
        """
        try:
            if PSUTIL_AVAILABLE:
                memory = psutil.virtual_memory()
                total_gb = memory.total / (1024 ** 3)
                available_gb = memory.available / (1024 ** 3)
                used_gb = memory.used / (1024 ** 3)
                usage_percent = memory.percent
            else:
                # /proc/meminfo から読み取り（Linux）
                with open('/proc/meminfo', 'r') as f:
                    meminfo = {}
                    for line in f:
                        parts = line.split()
                        if len(parts) >= 2:
                            key = parts[0].rstrip(':')
                            value = int(parts[1])
                            meminfo[key] = value

                total_kb = meminfo.get('MemTotal', 0)
                available_kb = meminfo.get('MemAvailable', meminfo.get('MemFree', 0))
                used_kb = total_kb - available_kb

                total_gb = total_kb / (1024 ** 2)
                available_gb = available_kb / (1024 ** 2)
                used_gb = used_kb / (1024 ** 2)
                usage_percent = (used_kb / total_kb * 100) if total_kb > 0 else 0

            status = "healthy" if usage_percent < threshold else "unhealthy"

            return HealthCheckResult(
                name="memory_usage",
                status=status,
                message=f"Memory usage: {usage_percent:.1f}% ({available_gb:.1f}GB available)",
                critical=False,
                details={
                    "usage_percent": round(usage_percent, 1),
                    "total_gb": round(total_gb, 1),
                    "used_gb": round(used_gb, 1),
                    "available_gb": round(available_gb, 1),
                    "threshold": threshold
                }
            )

        except Exception as e:
            return HealthCheckResult(
                name="memory_usage",
                status="unhealthy",
                message=f"Memory check error: {str(e)}",
                critical=False,
                details={"error": str(e)}
            )

    def check_http_endpoint(self, url: str, timeout: int = 10) -> HealthCheckResult:
        """
        HTTPエンドポイントチェック

        Args:
            url: チェック対象URL
            timeout: タイムアウト秒数

        Returns:
            HealthCheckResult
        """
        try:
            start_time = time.time()
            response = urlopen(url, timeout=timeout)
            response_time = (time.time() - start_time) * 1000  # ミリ秒
            status_code = response.getcode()

            if 200 <= status_code < 300:
                return HealthCheckResult(
                    name="http_endpoint",
                    status="healthy",
                    message=f"HTTP endpoint responding: {status_code}",
                    critical=True,
                    details={
                        "url": url,
                        "status_code": status_code,
                        "response_time_ms": round(response_time, 1)
                    }
                )
            else:
                return HealthCheckResult(
                    name="http_endpoint",
                    status="degraded",
                    message=f"HTTP endpoint returned: {status_code}",
                    critical=True,
                    details={"url": url, "status_code": status_code}
                )

        except HTTPError as e:
            return HealthCheckResult(
                name="http_endpoint",
                status="unhealthy",
                message=f"HTTP error: {e.code}",
                critical=True,
                details={"url": url, "error": str(e)}
            )
        except URLError as e:
            return HealthCheckResult(
                name="http_endpoint",
                status="unhealthy",
                message=f"Connection error: {str(e.reason)}",
                critical=True,
                details={"url": url, "error": str(e)}
            )
        except Exception as e:
            return HealthCheckResult(
                name="http_endpoint",
                status="unhealthy",
                message=f"HTTP check error: {str(e)}",
                critical=True,
                details={"url": url, "error": str(e)}
            )

    def check_port(self, port: int, host: str = "localhost") -> HealthCheckResult:
        """
        ポート使用状況チェック

        Args:
            port: チェック対象ポート
            host: ホスト名

        Returns:
            HealthCheckResult
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, port))
            sock.close()

            if result == 0:
                return HealthCheckResult(
                    name=f"port_{port}",
                    status="healthy",
                    message=f"Port {port} is listening",
                    critical=False,
                    details={"port": port, "host": host, "listening": True}
                )
            else:
                return HealthCheckResult(
                    name=f"port_{port}",
                    status="unhealthy",
                    message=f"Port {port} is not listening",
                    critical=False,
                    details={"port": port, "host": host, "listening": False}
                )

        except Exception as e:
            return HealthCheckResult(
                name=f"port_{port}",
                status="unhealthy",
                message=f"Port check error: {str(e)}",
                critical=False,
                details={"port": port, "error": str(e)}
            )

    def check_directory(self, path: str) -> HealthCheckResult:
        """
        ディレクトリ存在・書き込みチェック

        Args:
            path: チェック対象ディレクトリパス

        Returns:
            HealthCheckResult
        """
        full_path = self.project_root / path

        try:
            if not full_path.exists():
                return HealthCheckResult(
                    name=f"directory_{path}",
                    status="unhealthy",
                    message=f"Directory not found: {path}",
                    critical=False,
                    details={"path": str(full_path), "exists": False}
                )

            if not full_path.is_dir():
                return HealthCheckResult(
                    name=f"directory_{path}",
                    status="unhealthy",
                    message=f"Path is not a directory: {path}",
                    critical=False,
                    details={"path": str(full_path), "is_dir": False}
                )

            # 書き込みテスト
            test_file = full_path / ".health_check_test"
            try:
                test_file.touch()
                test_file.unlink()
                writable = True
            except PermissionError:
                writable = False

            status = "healthy" if writable else "degraded"

            return HealthCheckResult(
                name=f"directory_{path}",
                status=status,
                message=f"Directory {path}: exists={True}, writable={writable}",
                critical=False,
                details={"path": str(full_path), "exists": True, "writable": writable}
            )

        except Exception as e:
            return HealthCheckResult(
                name=f"directory_{path}",
                status="unhealthy",
                message=f"Directory check error: {str(e)}",
                critical=False,
                details={"path": str(full_path), "error": str(e)}
            )

    def collect_metrics(self) -> SystemMetrics:
        """
        システムメトリクス収集

        Returns:
            SystemMetrics
        """
        metrics = SystemMetrics()

        try:
            if PSUTIL_AVAILABLE:
                # CPU
                metrics.cpu_usage_percent = psutil.cpu_percent(interval=0.1)
                metrics.cpu_count = psutil.cpu_count()

                # メモリ
                memory = psutil.virtual_memory()
                metrics.memory_total_gb = round(memory.total / (1024 ** 3), 2)
                metrics.memory_used_gb = round(memory.used / (1024 ** 3), 2)
                metrics.memory_usage_percent = memory.percent

                # ディスク
                disk = shutil.disk_usage("/")
                metrics.disk_total_gb = round(disk.total / (1024 ** 3), 2)
                metrics.disk_used_gb = round(disk.used / (1024 ** 3), 2)
                metrics.disk_usage_percent = round(disk.used / disk.total * 100, 1)

                # ネットワーク
                net = psutil.net_io_counters()
                metrics.network_bytes_sent_mb = round(net.bytes_sent / (1024 ** 2), 2)
                metrics.network_bytes_recv_mb = round(net.bytes_recv / (1024 ** 2), 2)

                # プロセス
                metrics.process_count = len(psutil.pids())
            else:
                # psutil なしでの基本メトリクス収集
                disk = shutil.disk_usage("/")
                metrics.disk_total_gb = round(disk.total / (1024 ** 3), 2)
                metrics.disk_used_gb = round(disk.used / (1024 ** 3), 2)
                metrics.disk_usage_percent = round(disk.used / disk.total * 100, 1)

                # CPU count
                metrics.cpu_count = os.cpu_count() or 1

        except Exception as e:
            self.logger.warning(f"Failed to collect some metrics: {e}")

        return metrics

    def run_all_checks(self) -> Dict[str, Any]:
        """
        全ヘルスチェック実行

        Returns:
            ヘルスチェック結果の辞書
        """
        results = {}

        # 設定からチェック項目を取得
        health_checks = self.config.get("health_checks", [])
        project_config = self.config.get("project_config", {})

        # SQLite チェック
        db_check = next((c for c in health_checks if c.get("type") == "sqlite"), None)
        if db_check:
            result = self.check_sqlite_connection(db_check.get("db_path"))
        else:
            result = self.check_sqlite_connection()
        results[result.name] = result

        # ディスクチェック
        disk_check = next((c for c in health_checks if c.get("type") == "disk"), None)
        if disk_check:
            result = self.check_disk_space(
                disk_check.get("path", "/"),
                disk_check.get("threshold", 90)
            )
        else:
            result = self.check_disk_space()
        results[result.name] = result

        # メモリチェック
        memory_check = next((c for c in health_checks if c.get("type") == "memory"), None)
        if memory_check:
            result = self.check_memory_usage(memory_check.get("threshold", 85))
        else:
            result = self.check_memory_usage()
        results[result.name] = result

        # HTTPエンドポイントチェック
        http_check = next((c for c in health_checks if c.get("type") == "http"), None)
        if http_check:
            result = self.check_http_endpoint(
                http_check.get("url", f"http://localhost:{project_config.get('api_port', 8888)}/api/health"),
                http_check.get("timeout", 10)
            )
            results[result.name] = result

        # ディレクトリチェック
        for check in health_checks:
            if check.get("type") == "directory":
                result = self.check_directory(check.get("path", "logs"))
                results[result.name] = result

        # APIポートチェック
        api_port = project_config.get("api_port", 8888)
        port_result = self.check_port(api_port)
        results[port_result.name] = port_result

        # メトリクス収集
        metrics = self.collect_metrics()

        # 全体ステータス判定
        overall_status = self._determine_overall_status(results)

        return {
            "timestamp": datetime.now().isoformat(),
            "checks": {name: {
                "status": r.status,
                "message": r.message,
                "critical": r.critical,
                "details": r.details
            } for name, r in results.items()},
            "overall_status": overall_status,
            "metrics": {
                "cpu": {"usage_percent": metrics.cpu_usage_percent, "count": metrics.cpu_count},
                "memory": {"total_gb": metrics.memory_total_gb, "used_gb": metrics.memory_used_gb},
                "disk": {"total_gb": metrics.disk_total_gb, "used_gb": metrics.disk_used_gb},
                "network": {
                    "bytes_sent_mb": metrics.network_bytes_sent_mb,
                    "bytes_recv_mb": metrics.network_bytes_recv_mb
                },
                "processes": {"count": metrics.process_count}
            }
        }

    def _determine_overall_status(self, results: Dict[str, HealthCheckResult]) -> str:
        """
        全体ステータス判定

        判定ロジック:
        - クリティカルなチェックが失敗 → "critical"
        - いずれかが unhealthy → "degraded"
        - すべて healthy → "healthy"
        """
        for result in results.values():
            if result.status == "unhealthy" and result.critical:
                return "critical"

        for result in results.values():
            if result.status == "unhealthy":
                return "degraded"

        for result in results.values():
            if result.status == "degraded":
                return "degraded"

        return "healthy"


def main():
    """メイン実行"""
    import argparse

    parser = argparse.ArgumentParser(description="Health Monitor for Mirai IT Knowledge System")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--check", help="Run specific check (sqlite, disk, memory, http, port)")
    parser.add_argument("--port", type=int, default=8888, help="Port number for port check")
    parser.add_argument("--url", help="URL for HTTP check")

    args = parser.parse_args()

    monitor = HealthMonitor(config_path=args.config)

    if args.check:
        # 個別チェック
        if args.check == "sqlite":
            result = monitor.check_sqlite_connection()
        elif args.check == "disk":
            result = monitor.check_disk_space()
        elif args.check == "memory":
            result = monitor.check_memory_usage()
        elif args.check == "http":
            url = args.url or "http://localhost:8888/api/health"
            result = monitor.check_http_endpoint(url)
        elif args.check == "port":
            result = monitor.check_port(args.port)
        else:
            print(f"Unknown check type: {args.check}")
            sys.exit(1)

        if args.json:
            print(json.dumps({
                "name": result.name,
                "status": result.status,
                "message": result.message,
                "critical": result.critical,
                "details": result.details
            }, indent=2, ensure_ascii=False))
        else:
            status_icon = "✅" if result.status == "healthy" else "❌"
            print(f"{status_icon} {result.name}: {result.status}")
            print(f"   {result.message}")
    else:
        # 全チェック
        results = monitor.run_all_checks()

        if args.json:
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            print(f"\n{'='*60}")
            print(f" Health Check Results - {results['timestamp']}")
            print(f"{'='*60}\n")

            for name, check in results["checks"].items():
                status_icon = "✅" if check["status"] == "healthy" else ("⚠️" if check["status"] == "degraded" else "❌")
                critical_mark = "[CRITICAL]" if check["critical"] else ""
                print(f"{status_icon} {name} {critical_mark}")
                print(f"   Status: {check['status']}")
                print(f"   {check['message']}")
                print()

            print(f"\n📊 Overall Status: {results['overall_status'].upper()}")

            metrics = results["metrics"]
            print(f"\n📈 System Metrics:")
            print(f"   CPU: {metrics['cpu']['usage_percent']}% ({metrics['cpu']['count']} cores)")
            print(f"   Memory: {metrics['memory']['used_gb']:.1f}GB / {metrics['memory']['total_gb']:.1f}GB")
            print(f"   Disk: {metrics['disk']['used_gb']:.1f}GB / {metrics['disk']['total_gb']:.1f}GB")

    # 終了コード
    if not args.check:
        if results["overall_status"] == "critical":
            sys.exit(2)
        elif results["overall_status"] == "degraded":
            sys.exit(1)
    else:
        if result.status == "unhealthy":
            sys.exit(2 if result.critical else 1)


if __name__ == "__main__":
    main()
