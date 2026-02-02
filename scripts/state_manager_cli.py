#!/usr/bin/env python3
"""
state.json 管理 CLI ツール

state.json の管理を簡単にする運用ツール

主要機能:
- init: state.json の初期化
- show: 現在の状態表示
- reset: 強制リセット
- stats: 統計情報の可視化
- validate: スキーマ検証

使用例:
    # 状態表示
    python state_manager_cli.py show

    # 初期化
    python state_manager_cli.py init

    # リセット
    python state_manager_cli.py reset

    # 統計表示
    python state_manager_cli.py stats
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# プロジェクトルートをパスに追加
SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.auto_fix_daemon import StateManager


# ANSI カラーコード
class Colors:
    """ANSI カラーコード"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

    # 前景色
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

    # 背景色
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'


def print_header(text: str):
    """ヘッダーを表示"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.RESET}\n")


def print_success(text: str):
    """成功メッセージを表示"""
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")


def print_error(text: str):
    """エラーメッセージを表示"""
    print(f"{Colors.RED}❌ {text}{Colors.RESET}", file=sys.stderr)


def print_warning(text: str):
    """警告メッセージを表示"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")


def print_info(text: str):
    """情報メッセージを表示"""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.RESET}")


def print_key_value(key: str, value: Any, indent: int = 0):
    """キー・バリューを整形表示"""
    indent_str = "  " * indent
    key_colored = f"{Colors.BOLD}{Colors.CYAN}{key}{Colors.RESET}"
    print(f"{indent_str}{key_colored}: {value}")


def get_status_color(status: str) -> str:
    """ステータスに応じた色を返す"""
    status_colors = {
        'healthy': Colors.GREEN,
        'degraded': Colors.YELLOW,
        'critical': Colors.RED,
        'unknown': Colors.DIM
    }
    return status_colors.get(status, Colors.RESET)


class StateManagerCLI:
    """state.json 管理 CLI"""

    def __init__(self, state_file: Optional[str] = None):
        """
        初期化

        Args:
            state_file: 状態ファイルパス（省略時はデフォルト）
        """
        self.state_file = state_file or str(PROJECT_ROOT / "state.json")
        self.manager = StateManager(self.state_file)

    def cmd_init(self, force: bool = False) -> int:
        """
        state.json を初期化

        Args:
            force: 既存ファイルを上書きするか

        Returns:
            終了コード
        """
        print_header("state.json 初期化")

        state_path = Path(self.state_file)

        if state_path.exists() and not force:
            print_error(f"state.json が既に存在します: {state_path}")
            print_info("上書きする場合は --force オプションを使用してください")
            return 1

        # 初期状態を取得して保存
        initial_state = self.manager._get_initial_state()
        self.manager.save_state(initial_state)

        print_success(f"state.json を初期化しました: {state_path}")
        print_info(f"作成日時: {initial_state['created_at']}")

        return 0

    def cmd_show(self, verbose: bool = False) -> int:
        """
        現在の状態を表示

        Args:
            verbose: 詳細表示

        Returns:
            終了コード
        """
        print_header("state.json 現在の状態")

        try:
            state = self.manager.load_state()
        except Exception as e:
            print_error(f"state.json の読み込みに失敗: {e}")
            return 1

        # 基本情報
        print(f"{Colors.BOLD}📋 基本情報{Colors.RESET}")
        print_key_value("ファイルパス", self.state_file, 1)
        print_key_value("作成日時", state.get('created_at', 'N/A'), 1)
        print_key_value("更新日時", state.get('updated_at', 'N/A'), 1)
        print()

        # 実行状態
        print(f"{Colors.BOLD}🔄 実行状態{Colors.RESET}")
        retry_required = state.get('retry_required', False)
        retry_color = Colors.RED if retry_required else Colors.GREEN
        retry_text = f"{retry_color}{retry_required}{Colors.RESET}"
        print_key_value("retry_required", retry_text, 1)
        print_key_value("run_count", state.get('run_count', 0), 1)
        print()

        # 最後のエラー
        print(f"{Colors.BOLD}🐛 最後のエラー{Colors.RESET}")
        last_error_id = state.get('last_error_id', '')
        if last_error_id:
            print_key_value("error_id", last_error_id, 1)
            print_key_value("error_summary", state.get('last_error_summary', 'N/A'), 1)
            print_key_value("last_attempt_at", state.get('last_attempt_at', 'N/A'), 1)
        else:
            print_info("  エラーなし")
        print()

        # クールダウン
        print(f"{Colors.BOLD}⏸️  クールダウン{Colors.RESET}")
        cooldown_until = state.get('cooldown_until', '')
        if cooldown_until:
            is_in_cooldown = self.manager.is_in_cooldown()
            cooldown_status = f"{Colors.YELLOW}有効{Colors.RESET}" if is_in_cooldown else f"{Colors.GREEN}解除{Colors.RESET}"
            print_key_value("cooldown_until", cooldown_until, 1)
            print_key_value("status", cooldown_status, 1)
        else:
            print_info("  クールダウンなし")
        print()

        # 統計情報
        print(f"{Colors.BOLD}📊 統計情報{Colors.RESET}")
        print_key_value("total_errors_detected", state.get('total_errors_detected', 0), 1)
        print_key_value("total_fixes_attempted", state.get('total_fixes_attempted', 0), 1)
        print_key_value("total_fixes_succeeded", state.get('total_fixes_succeeded', 0), 1)

        # 成功率計算
        attempted = state.get('total_fixes_attempted', 0)
        succeeded = state.get('total_fixes_succeeded', 0)
        if attempted > 0:
            success_rate = (succeeded * 100) // attempted
            success_rate_colored = f"{Colors.GREEN if success_rate >= 80 else Colors.YELLOW if success_rate >= 50 else Colors.RED}{success_rate}%{Colors.RESET}"
            print_key_value("success_rate", success_rate_colored, 1)
        print()

        # ヘルスステータス
        print(f"{Colors.BOLD}🏥 ヘルスステータス{Colors.RESET}")
        health_status = state.get('last_health_status', 'unknown')
        status_color = get_status_color(health_status)
        health_text = f"{status_color}{health_status.upper()}{Colors.RESET}"
        print_key_value("last_health_status", health_text, 1)
        print_key_value("continuous_failure_count", state.get('continuous_failure_count', 0), 1)
        print()

        # 詳細表示（verbose）
        if verbose:
            print(f"{Colors.BOLD}🔍 詳細情報（JSON）{Colors.RESET}")
            print(json.dumps(state, indent=2, ensure_ascii=False))
            print()

        return 0

    def cmd_reset(self, confirm: bool = False) -> int:
        """
        state.json を強制リセット

        Args:
            confirm: 確認済みフラグ

        Returns:
            終了コード
        """
        print_header("state.json リセット")

        if not confirm:
            print_warning("この操作は state.json を初期状態にリセットします")
            print_info("実行するには --confirm オプションを使用してください")
            return 1

        # バックアップ作成
        state_path = Path(self.state_file)
        if state_path.exists():
            backup_path = state_path.with_suffix('.json.reset_backup')
            try:
                import shutil
                shutil.copy2(state_path, backup_path)
                print_success(f"バックアップを作成しました: {backup_path}")
            except Exception as e:
                print_warning(f"バックアップ作成に失敗: {e}")

        # リセット実行
        initial_state = self.manager._get_initial_state()
        self.manager.save_state(initial_state)

        print_success("state.json をリセットしました")
        print_info("全てのカウンターとフラグが初期値に戻りました")

        return 0

    def cmd_stats(self, format: str = 'text') -> int:
        """
        統計情報を可視化

        Args:
            format: 出力フォーマット（text/json/csv）

        Returns:
            終了コード
        """
        # text 形式の時だけヘッダーを表示
        if format == 'text':
            print_header("state.json 統計情報")

        try:
            state = self.manager.load_state()
        except Exception as e:
            print_error(f"state.json の読み込みに失敗: {e}")
            return 1

        # 統計データ抽出
        stats = {
            'run_count': state.get('run_count', 0),
            'total_errors_detected': state.get('total_errors_detected', 0),
            'total_fixes_attempted': state.get('total_fixes_attempted', 0),
            'total_fixes_succeeded': state.get('total_fixes_succeeded', 0),
            'continuous_failure_count': state.get('continuous_failure_count', 0),
            'last_health_status': state.get('last_health_status', 'unknown'),
            'retry_required': state.get('retry_required', False),
        }

        # 計算フィールド
        if stats['total_fixes_attempted'] > 0:
            stats['success_rate'] = (stats['total_fixes_succeeded'] * 100) // stats['total_fixes_attempted']
        else:
            stats['success_rate'] = 100

        if stats['total_errors_detected'] > 0:
            stats['fix_coverage'] = (stats['total_fixes_attempted'] * 100) // stats['total_errors_detected']
        else:
            stats['fix_coverage'] = 100

        # フォーマット別出力
        if format == 'json':
            print(json.dumps(stats, indent=2, ensure_ascii=False))
        elif format == 'csv':
            # CSV ヘッダー
            print(','.join(stats.keys()))
            # CSV データ
            print(','.join(str(v) for v in stats.values()))
        else:  # text
            self._print_stats_text(stats)

        return 0

    def _print_stats_text(self, stats: Dict[str, Any]):
        """統計情報をテキスト形式で表示"""

        print(f"{Colors.BOLD}📈 実行統計{Colors.RESET}")
        print_key_value("総実行回数", stats['run_count'], 1)
        print()

        print(f"{Colors.BOLD}🐛 エラー統計{Colors.RESET}")
        print_key_value("検出エラー数", stats['total_errors_detected'], 1)
        print_key_value("修復試行数", stats['total_fixes_attempted'], 1)
        print_key_value("修復成功数", stats['total_fixes_succeeded'], 1)
        print()

        print(f"{Colors.BOLD}✅ 成功率{Colors.RESET}")
        success_rate = stats['success_rate']
        success_color = Colors.GREEN if success_rate >= 80 else Colors.YELLOW if success_rate >= 50 else Colors.RED
        print_key_value("修復成功率", f"{success_color}{success_rate}%{Colors.RESET}", 1)

        fix_coverage = stats['fix_coverage']
        coverage_color = Colors.GREEN if fix_coverage >= 80 else Colors.YELLOW if fix_coverage >= 50 else Colors.RED
        print_key_value("修復カバレッジ", f"{coverage_color}{fix_coverage}%{Colors.RESET}", 1)
        print()

        print(f"{Colors.BOLD}🏥 健全性{Colors.RESET}")
        health_status = stats['last_health_status']
        status_color = get_status_color(health_status)
        print_key_value("ヘルスステータス", f"{status_color}{health_status.upper()}{Colors.RESET}", 1)
        print_key_value("連続失敗回数", stats['continuous_failure_count'], 1)
        print_key_value("リトライ要求", f"{'🔴 必要' if stats['retry_required'] else '🟢 不要'}", 1)
        print()

        # プログレスバー（修復成功率）
        self._print_progress_bar("修復成功率", success_rate)
        self._print_progress_bar("修復カバレッジ", fix_coverage)

    def _print_progress_bar(self, label: str, percentage: int, width: int = 40):
        """プログレスバーを表示"""
        filled = int(width * percentage / 100)
        bar = '█' * filled + '░' * (width - filled)

        color = Colors.GREEN if percentage >= 80 else Colors.YELLOW if percentage >= 50 else Colors.RED
        print(f"  {label}: {color}{bar}{Colors.RESET} {percentage}%")

    def cmd_validate(self) -> int:
        """
        state.json のスキーマ検証

        Returns:
            終了コード
        """
        print_header("state.json スキーマ検証")

        # ファイル存在確認
        state_path = Path(self.state_file)
        if not state_path.exists():
            print_error(f"state.json が存在しません: {state_path}")
            print_info("初期化するには: state_manager_cli.py init")
            return 1

        # 直接ファイルを読み込んで検証（load_state はフォールバックするため使わない）
        try:
            with open(state_path, 'r', encoding='utf-8') as f:
                state = json.load(f)
        except json.JSONDecodeError as e:
            print_error(f"JSON パースエラー: {e}")
            return 1
        except Exception as e:
            print_error(f"state.json の読み込みに失敗: {e}")
            return 1

        # 必須フィールドチェック
        required_fields = [
            'retry_required', 'run_count', 'last_error_id',
            'last_error_summary', 'last_attempt_at', 'cooldown_until',
            'total_errors_detected', 'total_fixes_attempted',
            'total_fixes_succeeded', 'last_health_status',
            'continuous_failure_count', 'created_at', 'updated_at'
        ]

        missing_fields = []
        invalid_types = []

        for field in required_fields:
            if field not in state:
                missing_fields.append(field)

        # 型チェック
        type_checks = {
            'retry_required': bool,
            'run_count': int,
            'last_error_id': str,
            'total_errors_detected': int,
            'total_fixes_attempted': int,
            'total_fixes_succeeded': int,
            'continuous_failure_count': int,
        }

        for field, expected_type in type_checks.items():
            if field in state and not isinstance(state[field], expected_type):
                invalid_types.append((field, expected_type.__name__, type(state[field]).__name__))

        # 結果表示
        if missing_fields:
            print_error(f"欠落フィールド: {', '.join(missing_fields)}")

        if invalid_types:
            print_error("型エラー:")
            for field, expected, actual in invalid_types:
                print(f"  - {field}: 期待={expected}, 実際={actual}")

        if not missing_fields and not invalid_types:
            print_success("スキーマ検証に合格しました")
            return 0
        else:
            print_error("スキーマ検証に失敗しました")
            return 1


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description='state.json 管理 CLI ツール',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 状態表示
  %(prog)s show

  # 詳細表示
  %(prog)s show --verbose

  # 初期化
  %(prog)s init

  # リセット（確認付き）
  %(prog)s reset --confirm

  # 統計表示
  %(prog)s stats

  # JSON 形式で統計出力
  %(prog)s stats --format json

  # スキーマ検証
  %(prog)s validate
        """
    )

    parser.add_argument(
        '--state-file',
        help='state.json のパス（デフォルト: プロジェクトルート/state.json）'
    )

    subparsers = parser.add_subparsers(dest='command', help='コマンド')

    # init コマンド
    parser_init = subparsers.add_parser('init', help='state.json を初期化')
    parser_init.add_argument('--force', action='store_true', help='既存ファイルを上書き')

    # show コマンド
    parser_show = subparsers.add_parser('show', help='現在の状態を表示')
    parser_show.add_argument('--verbose', '-v', action='store_true', help='詳細表示')

    # reset コマンド
    parser_reset = subparsers.add_parser('reset', help='state.json を強制リセット')
    parser_reset.add_argument('--confirm', action='store_true', help='リセット確認')

    # stats コマンド
    parser_stats = subparsers.add_parser('stats', help='統計情報を可視化')
    parser_stats.add_argument(
        '--format',
        choices=['text', 'json', 'csv'],
        default='text',
        help='出力フォーマット'
    )

    # validate コマンド
    parser_validate = subparsers.add_parser('validate', help='スキーマ検証')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # CLI インスタンス作成
    cli = StateManagerCLI(state_file=args.state_file)

    # コマンド実行
    if args.command == 'init':
        return cli.cmd_init(force=args.force)
    elif args.command == 'show':
        return cli.cmd_show(verbose=args.verbose)
    elif args.command == 'reset':
        return cli.cmd_reset(confirm=args.confirm)
    elif args.command == 'stats':
        return cli.cmd_stats(format=args.format)
    elif args.command == 'validate':
        return cli.cmd_validate()
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
