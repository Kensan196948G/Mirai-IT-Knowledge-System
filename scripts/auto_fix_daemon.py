#!/usr/bin/env python3
"""
自動エラー検知・修復デーモン
5分間隔・無限ループでシステムを監視し、エラーを自動修復

仕様書: 19_自動エラー検知修復システム仕様書.md

基本仕様:
- 検知ループ回数: 15回/イテレーション
- 待機時間: 5分（イテレーション間）
- 動作モード: 無限ループ（永続実行）
- 実行間隔: 約2秒（ループ間）、5分（イテレーション間）
- 最大リトライ: 3回（同一エラー）
- クールダウン: 300秒（5分）（同一エラー再修復禁止）
"""

import argparse
import json
import logging
import os
import re
import shutil
import signal
import sqlite3
import subprocess
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# プロジェクトルートをパスに追加
SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from health_monitor import HealthMonitor


@dataclass
class DetectedError:
    """検出されたエラー"""
    id: str
    name: str
    pattern: str
    severity: str
    auto_fix: bool
    actions: List[Dict[str, Any]]
    source_file: str
    matched_line: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class FixResult:
    """修復結果"""
    error_id: str
    success: bool
    actions_executed: List[Dict[str, Any]]
    message: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class AutoFixDaemon:
    """
    エラー自動検知・自動修復デーモン

    動作フロー:
    1. 15回の検知サイクルを実行
    2. 各サイクルで:
       - ヘルスチェック実行
       - ログファイルスキャン
       - エラーパターンマッチング
       - 自動修復実行
    3. 5分間待機
    4. 1に戻る（無限ループ）
    """

    # 定数
    DEFAULT_LOOP_COUNT = 15
    DEFAULT_WAIT_MINUTES = 5
    CYCLE_INTERVAL_SECONDS = 2
    MAX_LOG_LINES = 1000
    COOLDOWN_PERIOD = 300  # 5分

    def __init__(
        self,
        config_path: Optional[str] = None,
        log_file: Optional[str] = None
    ):
        """
        初期化

        Args:
            config_path: 設定ファイルパス
            log_file: ログファイルパス
        """
        self.project_root = PROJECT_ROOT
        self.config_path = config_path or str(SCRIPT_DIR / "error_patterns.json")
        self.log_file = log_file or str(PROJECT_ROOT / "logs" / "auto_fix.log")

        # ログディレクトリ作成
        Path(self.log_file).parent.mkdir(parents=True, exist_ok=True)

        self.config = self._load_config()
        self.logger = self._setup_logger()
        self.health_monitor = HealthMonitor(config_path=self.config_path)

        # 修復履歴（クールダウン管理用）
        self.fix_history: Dict[str, datetime] = {}
        # リトライカウント
        self.retry_counts: Dict[str, int] = defaultdict(int)
        # 停止フラグ
        self.running = True

        # シグナルハンドラ設定
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        self.logger.info("AutoFixDaemon initialized")
        self.logger.info(f"Project root: {self.project_root}")
        self.logger.info(f"Config: {self.config_path}")

    def _signal_handler(self, signum, frame):
        """シグナルハンドラ"""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False

    def _setup_logger(self) -> logging.Logger:
        """ロガーセットアップ"""
        logger = logging.getLogger("AutoFixDaemon")
        logger.setLevel(logging.INFO)

        # 既存ハンドラをクリア
        logger.handlers.clear()

        # フォーマッタ
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - [%(levelname)s] - %(message)s'
        )

        # ファイルハンドラ
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # コンソールハンドラ
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        return logger

    def _load_config(self) -> Dict[str, Any]:
        """設定ファイル読み込み"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Failed to load config: {e}")
            return {"error_patterns": [], "auto_fix_config": {}}

    def scan_logs(self, log_paths: Optional[List[str]] = None) -> List[DetectedError]:
        """
        ログファイルをスキャンしてエラーを検出

        Args:
            log_paths: スキャン対象のログファイルパス

        Returns:
            検出されたエラーのリスト
        """
        if log_paths is None:
            log_paths = self.config.get("monitored_log_files", [
                "logs/app.log",
                "logs/auto_fix.log",
                "logs/workflow.log"
            ])

        detected_errors = []
        error_patterns = self.config.get("error_patterns", [])

        for log_path in log_paths:
            full_path = self.project_root / log_path

            if not full_path.exists():
                continue

            try:
                # 最後の1000行を読み込み
                lines = self._read_last_lines(full_path, self.MAX_LOG_LINES)

                for line in lines:
                    for pattern_config in error_patterns:
                        pattern = pattern_config.get("pattern", "")
                        try:
                            if re.search(pattern, line, re.IGNORECASE):
                                error = DetectedError(
                                    id=pattern_config.get("id", "unknown"),
                                    name=pattern_config.get("name", "Unknown Error"),
                                    pattern=pattern,
                                    severity=pattern_config.get("severity", "warning"),
                                    auto_fix=pattern_config.get("auto_fix", False),
                                    actions=pattern_config.get("actions", []),
                                    source_file=str(log_path),
                                    matched_line=line[:200]  # 最大200文字
                                )
                                detected_errors.append(error)
                                break  # 同じ行に複数パターンマッチは避ける
                        except re.error:
                            continue

            except Exception as e:
                self.logger.warning(f"Failed to scan log {log_path}: {e}")

        return detected_errors

    def _read_last_lines(self, file_path: Path, n: int) -> List[str]:
        """ファイルの最後n行を読み込み"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # 効率的に最後のn行を取得
                lines = []
                for line in f:
                    lines.append(line.strip())
                    if len(lines) > n:
                        lines.pop(0)
                return lines
        except Exception:
            return []

    def is_in_cooldown(self, error_id: str) -> bool:
        """
        クールダウン期間中かどうかを確認

        Args:
            error_id: エラーID

        Returns:
            クールダウン中ならTrue
        """
        if error_id not in self.fix_history:
            return False

        last_fix_time = self.fix_history[error_id]
        cooldown_period = self.config.get("auto_fix_config", {}).get(
            "cooldown_period", self.COOLDOWN_PERIOD
        )

        return datetime.now() - last_fix_time < timedelta(seconds=cooldown_period)

    def execute_action(self, action: Dict[str, Any]) -> Tuple[bool, str]:
        """
        修復アクション実行

        Args:
            action: アクション定義

        Returns:
            (成功フラグ, メッセージ)
        """
        action_type = action.get("type", "")
        description = action.get("description", action_type)

        self.logger.info(f"Executing action: {action_type} - {description}")

        try:
            if action_type == "service_restart":
                return self._action_service_restart(action)
            elif action_type == "log_rotate":
                return self._action_log_rotate(action)
            elif action_type == "cache_clear":
                return self._action_cache_clear(action)
            elif action_type == "temp_file_cleanup":
                return self._action_temp_file_cleanup(action)
            elif action_type == "create_missing_dirs":
                return self._action_create_missing_dirs(action)
            elif action_type == "fix_permissions":
                return self._action_fix_permissions(action)
            elif action_type == "check_port":
                return self._action_check_port(action)
            elif action_type == "kill_process_on_port":
                return self._action_kill_process_on_port(action)
            elif action_type == "database_vacuum":
                return self._action_database_vacuum(action)
            elif action_type == "backup_and_fix_json":
                return self._action_backup_and_fix_json(action)
            elif action_type == "old_file_cleanup":
                return self._action_old_file_cleanup(action)
            elif action_type == "alert":
                return self._action_alert(action)
            elif action_type == "log_analysis":
                return self._action_log_analysis(action)
            else:
                return False, f"Unknown action type: {action_type}"

        except Exception as e:
            return False, f"Action failed: {str(e)}"

    def _action_service_restart(self, action: Dict) -> Tuple[bool, str]:
        """サービス再起動"""
        service = action.get("service", "mirai-knowledge")
        env = os.environ.get("ENVIRONMENT", "production")

        # 環境に応じたサービス名
        if env == "development":
            service_name = f"{service}-dev"
        else:
            service_name = f"{service}-prod"

        try:
            result = subprocess.run(
                ["sudo", "systemctl", "restart", service_name],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                return True, f"Service {service_name} restarted successfully"
            else:
                return False, f"Failed to restart {service_name}: {result.stderr}"
        except subprocess.TimeoutExpired:
            return False, f"Service restart timed out"
        except FileNotFoundError:
            return False, "systemctl not found"

    def _action_log_rotate(self, action: Dict) -> Tuple[bool, str]:
        """ログローテーション"""
        max_size_mb = self.config.get("auto_fix_config", {}).get("max_log_size_mb", 10)
        max_size_bytes = max_size_mb * 1024 * 1024
        rotated_count = 0

        log_dir = self.project_root / "logs"
        if log_dir.exists():
            for log_file in log_dir.glob("*.log"):
                try:
                    if log_file.stat().st_size > max_size_bytes:
                        # バックアップ
                        backup_name = f"{log_file.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
                        backup_path = log_file.parent / backup_name
                        shutil.copy2(log_file, backup_path)

                        # 元ファイルをクリア
                        with open(log_file, 'w') as f:
                            f.write(f"# Log rotated at {datetime.now().isoformat()}\n")

                        rotated_count += 1
                except Exception as e:
                    self.logger.warning(f"Failed to rotate {log_file}: {e}")

        return True, f"Rotated {rotated_count} log files"

    def _action_cache_clear(self, action: Dict) -> Tuple[bool, str]:
        """キャッシュクリア"""
        cleared_count = 0

        # __pycache__ ディレクトリをクリア
        for cache_dir in self.project_root.rglob("__pycache__"):
            try:
                shutil.rmtree(cache_dir)
                cleared_count += 1
            except Exception:
                pass

        # .pytest_cache
        pytest_cache = self.project_root / ".pytest_cache"
        if pytest_cache.exists():
            try:
                shutil.rmtree(pytest_cache)
                cleared_count += 1
            except Exception:
                pass

        return True, f"Cleared {cleared_count} cache directories"

    def _action_temp_file_cleanup(self, action: Dict) -> Tuple[bool, str]:
        """一時ファイル削除"""
        paths = action.get("paths", [])
        deleted_count = 0

        for pattern in paths:
            if pattern.startswith("/tmp/"):
                # システム一時ファイル
                for f in Path("/tmp").glob(pattern.replace("/tmp/", "")):
                    try:
                        if f.is_file():
                            f.unlink()
                            deleted_count += 1
                    except Exception:
                        pass
            else:
                # プロジェクト内
                for f in self.project_root.glob(pattern):
                    try:
                        if f.is_file():
                            f.unlink()
                            deleted_count += 1
                    except Exception:
                        pass

        return True, f"Deleted {deleted_count} temporary files"

    def _action_create_missing_dirs(self, action: Dict) -> Tuple[bool, str]:
        """ディレクトリ作成"""
        directories = action.get("directories", [])
        created_count = 0

        for dir_path in directories:
            full_path = self.project_root / dir_path
            try:
                full_path.mkdir(parents=True, exist_ok=True)
                created_count += 1
            except Exception as e:
                self.logger.warning(f"Failed to create directory {dir_path}: {e}")

        return True, f"Created/verified {created_count} directories"

    def _action_fix_permissions(self, action: Dict) -> Tuple[bool, str]:
        """権限修正"""
        paths = action.get("paths", [])
        mode = action.get("mode", "755")
        fixed_count = 0

        for path_pattern in paths:
            full_path = self.project_root / path_pattern

            try:
                if full_path.exists():
                    os.chmod(full_path, int(mode, 8))
                    fixed_count += 1
            except Exception as e:
                self.logger.warning(f"Failed to fix permissions for {path_pattern}: {e}")

        return True, f"Fixed permissions for {fixed_count} paths"

    def _action_check_port(self, action: Dict) -> Tuple[bool, str]:
        """ポート確認"""
        port = action.get("port", 8888)
        result = self.health_monitor.check_port(port)
        return True, f"Port {port}: {result.status}"

    def _action_kill_process_on_port(self, action: Dict) -> Tuple[bool, str]:
        """ポート使用プロセス終了"""
        port = action.get("port", 8888)

        try:
            # lsofでプロセスを特定
            result = subprocess.run(
                ["lsof", "-t", f"-i:{port}"],
                capture_output=True,
                text=True
            )
            pids = result.stdout.strip().split()

            killed = 0
            for pid in pids:
                try:
                    subprocess.run(["kill", "-9", pid], check=True)
                    killed += 1
                except Exception:
                    pass

            return True, f"Killed {killed} processes on port {port}"
        except Exception as e:
            return False, f"Failed to kill processes: {e}"

    def _action_database_vacuum(self, action: Dict) -> Tuple[bool, str]:
        """データベースVACUUM"""
        db_path = self.config.get("project_config", {}).get("db_path", "db/knowledge.db")
        full_path = self.project_root / db_path

        if not full_path.exists():
            return False, f"Database not found: {db_path}"

        try:
            conn = sqlite3.connect(str(full_path))
            conn.execute("VACUUM")
            conn.close()
            return True, f"Database VACUUM completed: {db_path}"
        except Exception as e:
            return False, f"VACUUM failed: {e}"

    def _action_backup_and_fix_json(self, action: Dict) -> Tuple[bool, str]:
        """JSONバックアップ・修復"""
        # 主要なJSONファイルをバックアップ
        json_files = list(self.project_root.glob("**/*.json"))
        backed_up = 0

        for json_file in json_files[:10]:  # 最大10ファイル
            try:
                backup_path = json_file.with_suffix(".json.bak")
                shutil.copy2(json_file, backup_path)
                backed_up += 1
            except Exception:
                pass

        return True, f"Backed up {backed_up} JSON files"

    def _action_old_file_cleanup(self, action: Dict) -> Tuple[bool, str]:
        """古いファイル削除"""
        paths = action.get("paths", ["backups/"])
        days = action.get("days", 30)
        cutoff_time = datetime.now() - timedelta(days=days)
        deleted_count = 0

        for path_pattern in paths:
            search_path = self.project_root / path_pattern
            if search_path.is_dir():
                for f in search_path.iterdir():
                    try:
                        if f.is_file():
                            mtime = datetime.fromtimestamp(f.stat().st_mtime)
                            if mtime < cutoff_time:
                                f.unlink()
                                deleted_count += 1
                    except Exception:
                        pass

        return True, f"Deleted {deleted_count} old files (older than {days} days)"

    def _action_alert(self, action: Dict) -> Tuple[bool, str]:
        """アラート送信"""
        description = action.get("description", "Alert triggered")

        # アラートログに記録
        alert_log = self.project_root / "logs" / "alerts.log"
        alert_log.parent.mkdir(parents=True, exist_ok=True)

        alert_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "auto_fix_alert",
            "description": description
        }

        with open(alert_log, 'a', encoding='utf-8') as f:
            f.write(json.dumps(alert_entry, ensure_ascii=False) + "\n")

        return True, f"Alert logged: {description}"

    def _action_log_analysis(self, action: Dict) -> Tuple[bool, str]:
        """ログ分析"""
        description = action.get("description", "Log analysis")
        self.logger.info(f"Log analysis: {description}")
        return True, f"Log analysis completed: {description}"

    def auto_fix_error(self, error: DetectedError) -> FixResult:
        """
        エラー修復のオーケストレーション

        Args:
            error: 検出されたエラー

        Returns:
            FixResult
        """
        # クールダウン確認
        if self.is_in_cooldown(error.id):
            return FixResult(
                error_id=error.id,
                success=False,
                actions_executed=[],
                message=f"Error {error.id} is in cooldown period"
            )

        # 自動修復が無効
        if not error.auto_fix:
            return FixResult(
                error_id=error.id,
                success=False,
                actions_executed=[],
                message=f"Auto-fix is disabled for {error.id}"
            )

        # リトライ上限チェック
        max_retries = self.config.get("auto_fix_config", {}).get("max_retries", 3)
        if self.retry_counts[error.id] >= max_retries:
            return FixResult(
                error_id=error.id,
                success=False,
                actions_executed=[],
                message=f"Max retries ({max_retries}) reached for {error.id}"
            )

        # バックアップ作成（設定されている場合）
        backup_before_fix = self.config.get("auto_fix_config", {}).get("backup_before_fix", True)
        if backup_before_fix:
            self._create_backup()

        # アクション実行
        actions_executed = []
        all_success = True

        for action in error.actions:
            success, message = self.execute_action(action)
            actions_executed.append({
                "type": action.get("type"),
                "success": success,
                "message": message
            })

            if not success:
                all_success = False
                self.logger.warning(f"Action failed: {action.get('type')} - {message}")

        # 修復履歴を更新
        self.fix_history[error.id] = datetime.now()

        if all_success:
            self.retry_counts[error.id] = 0  # リセット
        else:
            self.retry_counts[error.id] += 1

        return FixResult(
            error_id=error.id,
            success=all_success,
            actions_executed=actions_executed,
            message=f"Executed {len(actions_executed)} actions, success: {all_success}"
        )

    def _create_backup(self):
        """簡易バックアップ作成"""
        backup_dir = self.project_root / "backups" / "auto_fix"
        backup_dir.mkdir(parents=True, exist_ok=True)

        # DBバックアップ
        db_path = self.project_root / self.config.get("project_config", {}).get("db_path", "db/knowledge.db")
        if db_path.exists():
            backup_name = f"knowledge_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            try:
                shutil.copy2(db_path, backup_dir / backup_name)
            except Exception as e:
                self.logger.warning(f"Backup failed: {e}")

    def run_detection_cycle(self, cycle_num: int) -> Dict[str, Any]:
        """
        1回の検知サイクル実行

        Args:
            cycle_num: サイクル番号

        Returns:
            サイクル結果
        """
        self.logger.info(f"=== 検知サイクル {cycle_num} 開始 ===")

        cycle_result = {
            "cycle": cycle_num,
            "timestamp": datetime.now().isoformat(),
            "health_check": None,
            "errors_detected": [],
            "fixes_applied": []
        }

        # 1. ヘルスチェック
        try:
            health_result = self.health_monitor.run_all_checks()
            cycle_result["health_check"] = health_result["overall_status"]

            if health_result["overall_status"] != "healthy":
                self.logger.warning(f"Health check status: {health_result['overall_status']}")
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            cycle_result["health_check"] = "error"

        # 2. ログスキャン
        try:
            errors = self.scan_logs()
            cycle_result["errors_detected"] = [
                {"id": e.id, "name": e.name, "severity": e.severity}
                for e in errors
            ]

            if errors:
                self.logger.warning(f"Detected {len(errors)} errors")

            # 3. 自動修復
            for error in errors:
                self.logger.info(f"Processing error: {error.name} ({error.severity})")

                fix_result = self.auto_fix_error(error)
                cycle_result["fixes_applied"].append({
                    "error_id": fix_result.error_id,
                    "success": fix_result.success,
                    "message": fix_result.message
                })

                if fix_result.success:
                    self.logger.info(f"Fixed: {error.name}")
                else:
                    self.logger.warning(f"Fix failed: {error.name} - {fix_result.message}")

        except Exception as e:
            self.logger.error(f"Error detection/fix failed: {e}")

        self.logger.info(f"=== 検知サイクル {cycle_num} 完了 ===")
        return cycle_result

    def run_continuous(
        self,
        loop_count: int = DEFAULT_LOOP_COUNT,
        wait_minutes: int = DEFAULT_WAIT_MINUTES
    ):
        """
        継続的監視モード（無限ループ）

        Args:
            loop_count: 1イテレーションあたりのループ回数
            wait_minutes: イテレーション間の待機時間（分）
        """
        self.logger.info("=" * 60)
        self.logger.info("自動エラー検知・修復デーモン開始")
        self.logger.info(f"ループ回数: {loop_count}, 待機時間: {wait_minutes}分")
        self.logger.info("=" * 60)

        iteration = 0

        while self.running:
            iteration += 1
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"イテレーション {iteration} 開始")
            self.logger.info(f"{'='*60}")

            iteration_results = []

            # loop_count 回のサイクルを実行
            for cycle in range(1, loop_count + 1):
                if not self.running:
                    break

                result = self.run_detection_cycle(cycle)
                iteration_results.append(result)

                # サイクル間待機
                if cycle < loop_count and self.running:
                    time.sleep(self.CYCLE_INTERVAL_SECONDS)

            # イテレーションサマリー
            total_errors = sum(len(r.get("errors_detected", [])) for r in iteration_results)
            total_fixes = sum(len(r.get("fixes_applied", [])) for r in iteration_results)
            successful_fixes = sum(
                sum(1 for f in r.get("fixes_applied", []) if f.get("success"))
                for r in iteration_results
            )

            self.logger.info(f"\n📊 イテレーション {iteration} サマリー:")
            self.logger.info(f"   サイクル実行数: {len(iteration_results)}")
            self.logger.info(f"   検出エラー数: {total_errors}")
            self.logger.info(f"   修復試行数: {total_fixes}")
            self.logger.info(f"   修復成功数: {successful_fixes}")

            # 待機
            if self.running:
                self.logger.info(f"\n⏳ {wait_minutes}分間待機中...")
                wait_seconds = wait_minutes * 60

                # 1秒ごとにチェック（シグナル対応）
                for _ in range(wait_seconds):
                    if not self.running:
                        break
                    time.sleep(1)

        self.logger.info("\n🛑 デーモン停止")

    def run_once(self):
        """1回のみ実行"""
        self.logger.info("単発実行モード")
        result = self.run_detection_cycle(1)
        return result


def main():
    """メイン実行"""
    parser = argparse.ArgumentParser(
        description="自動エラー検知・修復デーモン (Mirai IT Knowledge System)"
    )
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="継続的監視モード（無限ループ）"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="1回のみ実行"
    )
    parser.add_argument(
        "--config",
        help="設定ファイルパス",
        default=None
    )
    parser.add_argument(
        "--log-file",
        help="ログファイルパス",
        default=None
    )
    parser.add_argument(
        "--loop-count",
        type=int,
        default=15,
        help="1イテレーションあたりのループ回数（デフォルト: 15）"
    )
    parser.add_argument(
        "--wait-minutes",
        type=int,
        default=5,
        help="イテレーション間の待機時間（分）（デフォルト: 5）"
    )

    args = parser.parse_args()

    daemon = AutoFixDaemon(
        config_path=args.config,
        log_file=args.log_file
    )

    if args.once:
        result = daemon.run_once()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif args.continuous:
        daemon.run_continuous(
            loop_count=args.loop_count,
            wait_minutes=args.wait_minutes
        )
    else:
        # デフォルト: 1イテレーション（15サイクル）のみ
        daemon.run_continuous(
            loop_count=args.loop_count,
            wait_minutes=0  # 待機なし
        )


if __name__ == "__main__":
    main()
