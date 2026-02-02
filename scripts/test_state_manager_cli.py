#!/usr/bin/env python3
"""
state_manager_cli.py の統合テスト

CLI ツールの全機能をテスト

テスト項目:
1. init コマンド（初期化）
2. show コマンド（状態表示）
3. reset コマンド（リセット）
4. stats コマンド（統計表示）
5. validate コマンド（スキーマ検証）
6. エラーハンドリング
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

# プロジェクトルートをパスに追加
SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

CLI_SCRIPT = SCRIPT_DIR / "state_manager_cli.py"


class TestStateManagerCLI:
    """state_manager_cli.py 統合テストクラス"""

    def __init__(self):
        """初期化"""
        self.test_count = 0
        self.passed_count = 0
        self.failed_count = 0
        self.temp_dir = Path(tempfile.mkdtemp())

    def run_cli(self, *args, expect_error=False) -> subprocess.CompletedProcess:
        """
        CLI を実行

        Args:
            *args: コマンドライン引数
            expect_error: エラーを期待するか

        Returns:
            subprocess.CompletedProcess
        """
        cmd = [sys.executable, str(CLI_SCRIPT)] + list(args)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )

        if not expect_error and result.returncode != 0:
            print(f"  ⚠️  Command failed: {' '.join(args)}")
            print(f"     stdout: {result.stdout}")
            print(f"     stderr: {result.stderr}")

        return result

    def run_test(self, test_name: str, test_func):
        """
        テスト実行

        Args:
            test_name: テスト名
            test_func: テスト関数
        """
        self.test_count += 1
        print(f"\n{'='*60}")
        print(f"Test #{self.test_count}: {test_name}")
        print('='*60)

        try:
            test_func()
            print(f"✅ PASSED: {test_name}")
            self.passed_count += 1
        except AssertionError as e:
            print(f"❌ FAILED: {test_name}")
            print(f"   Error: {e}")
            self.failed_count += 1
        except Exception as e:
            print(f"❌ ERROR: {test_name}")
            print(f"   Exception: {e}")
            self.failed_count += 1

    def test_help_command(self):
        """ヘルプ表示テスト"""
        result = self.run_cli('--help')
        assert result.returncode == 0, "Help should return 0"
        assert 'state.json 管理 CLI ツール' in result.stdout, "Help should contain description"
        assert 'init' in result.stdout, "Help should list init command"
        assert 'show' in result.stdout, "Help should list show command"
        print("   ✓ Help command works correctly")

    def test_init_command(self):
        """init コマンドテスト"""
        state_file = self.temp_dir / "test_init.json"

        # 初回初期化
        result = self.run_cli('--state-file', str(state_file), 'init', '--force')
        assert result.returncode == 0, "Init should succeed"
        assert state_file.exists(), "State file should be created"

        # state.json の内容確認
        with open(state_file, 'r') as f:
            state = json.load(f)
        assert state['retry_required'] == False, "Initial retry_required should be False"
        assert state['run_count'] == 0, "Initial run_count should be 0"

        print("   ✓ Init command works correctly")

    def test_show_command(self):
        """show コマンドテスト"""
        state_file = self.temp_dir / "test_show.json"

        # state.json 作成
        self.run_cli('--state-file', str(state_file), 'init', '--force')

        # show コマンド実行
        result = self.run_cli('--state-file', str(state_file), 'show')
        assert result.returncode == 0, "Show should succeed"
        assert '基本情報' in result.stdout, "Should show basic info"
        assert '実行状態' in result.stdout, "Should show execution state"
        assert '統計情報' in result.stdout, "Should show statistics"

        print("   ✓ Show command works correctly")

    def test_show_verbose(self):
        """show --verbose テスト"""
        state_file = self.temp_dir / "test_verbose.json"

        self.run_cli('--state-file', str(state_file), 'init', '--force')
        result = self.run_cli('--state-file', str(state_file), 'show', '--verbose')

        assert result.returncode == 0, "Show verbose should succeed"
        assert '詳細情報' in result.stdout, "Should show detailed info"

        print("   ✓ Show verbose command works correctly")

    def test_reset_command(self):
        """reset コマンドテスト"""
        state_file = self.temp_dir / "test_reset.json"

        # state.json 作成・変更
        self.run_cli('--state-file', str(state_file), 'init', '--force')

        with open(state_file, 'r') as f:
            state = json.load(f)
        state['run_count'] = 100
        state['retry_required'] = True
        with open(state_file, 'w') as f:
            json.dump(state, f)

        # リセット実行
        result = self.run_cli('--state-file', str(state_file), 'reset', '--confirm')
        assert result.returncode == 0, "Reset should succeed"

        # リセット後の確認
        with open(state_file, 'r') as f:
            reset_state = json.load(f)
        assert reset_state['run_count'] == 0, "run_count should be reset to 0"
        assert reset_state['retry_required'] == False, "retry_required should be reset to False"

        print("   ✓ Reset command works correctly")

    def test_reset_without_confirm(self):
        """reset コマンド（確認なし）テスト"""
        state_file = self.temp_dir / "test_reset_no_confirm.json"

        self.run_cli('--state-file', str(state_file), 'init', '--force')

        # 確認なしでリセット → 失敗すべき
        result = self.run_cli('--state-file', str(state_file), 'reset', expect_error=True)
        assert result.returncode != 0, "Reset without confirm should fail"

        print("   ✓ Reset without confirm fails as expected")

    def test_stats_text_format(self):
        """stats コマンド（text）テスト"""
        state_file = self.temp_dir / "test_stats_text.json"

        self.run_cli('--state-file', str(state_file), 'init', '--force')

        result = self.run_cli('--state-file', str(state_file), 'stats')
        assert result.returncode == 0, "Stats should succeed"
        assert '実行統計' in result.stdout, "Should show execution stats"
        assert '成功率' in result.stdout, "Should show success rate"
        assert '修復成功率' in result.stdout, "Should show fix success rate"

        print("   ✓ Stats text format works correctly")

    def test_stats_json_format(self):
        """stats コマンド（json）テスト"""
        state_file = self.temp_dir / "test_stats_json.json"

        self.run_cli('--state-file', str(state_file), 'init', '--force')

        result = self.run_cli('--state-file', str(state_file), 'stats', '--format', 'json')
        assert result.returncode == 0, "Stats json should succeed"

        # JSON パース確認
        stats = json.loads(result.stdout)
        assert 'run_count' in stats, "Should have run_count"
        assert 'success_rate' in stats, "Should have success_rate"

        print("   ✓ Stats JSON format works correctly")

    def test_stats_csv_format(self):
        """stats コマンド（csv）テスト"""
        state_file = self.temp_dir / "test_stats_csv.json"

        self.run_cli('--state-file', str(state_file), 'init', '--force')

        result = self.run_cli('--state-file', str(state_file), 'stats', '--format', 'csv')
        assert result.returncode == 0, "Stats CSV should succeed"

        lines = result.stdout.strip().split('\n')
        assert len(lines) >= 2, "Should have header and data"
        assert 'run_count' in lines[0], "Header should contain run_count"

        print("   ✓ Stats CSV format works correctly")

    def test_validate_command(self):
        """validate コマンドテスト"""
        state_file = self.temp_dir / "test_validate.json"

        # 正常な state.json
        self.run_cli('--state-file', str(state_file), 'init', '--force')
        result = self.run_cli('--state-file', str(state_file), 'validate')
        assert result.returncode == 0, "Validation should pass"

        # 不正な state.json
        with open(state_file, 'w') as f:
            json.dump({'invalid': 'data'}, f)

        result = self.run_cli('--state-file', str(state_file), 'validate', expect_error=True)
        assert result.returncode != 0, "Validation should fail for invalid state"

        print("   ✓ Validate command works correctly")

    def test_custom_state_file(self):
        """カスタム state.json パステスト"""
        custom_file = self.temp_dir / "custom_state.json"

        result = self.run_cli('--state-file', str(custom_file), 'init', '--force')
        assert result.returncode == 0, "Init with custom path should succeed"
        assert custom_file.exists(), "Custom state file should be created"

        print("   ✓ Custom state file path works correctly")

    def test_missing_state_file_show(self):
        """存在しない state.json の show テスト"""
        missing_file = self.temp_dir / "missing.json"

        # init せずに show → 初期状態を表示すべき
        result = self.run_cli('--state-file', str(missing_file), 'show')
        assert result.returncode == 0, "Show should succeed even if file doesn't exist"
        assert 'エラーなし' in result.stdout, "Should show no errors for initial state"

        print("   ✓ Show with missing file works correctly")

    def print_summary(self):
        """テスト結果サマリーを表示"""
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        print(f"Total Tests:  {self.test_count}")
        print(f"✅ Passed:     {self.passed_count}")
        print(f"❌ Failed:     {self.failed_count}")
        print(f"Success Rate: {self.passed_count * 100 // self.test_count if self.test_count > 0 else 0}%")
        print("="*60)

        if self.failed_count == 0:
            print("\n🎉 All tests passed!")
            return 0
        else:
            print(f"\n⚠️  {self.failed_count} test(s) failed")
            return 1


def main():
    """メイン関数"""
    print("="*60)
    print("🧪 state_manager_cli.py 統合テスト開始")
    print("="*60)

    tester = TestStateManagerCLI()

    # テスト実行
    tester.run_test("ヘルプ表示", tester.test_help_command)
    tester.run_test("init コマンド", tester.test_init_command)
    tester.run_test("show コマンド", tester.test_show_command)
    tester.run_test("show --verbose", tester.test_show_verbose)
    tester.run_test("reset コマンド（確認付き）", tester.test_reset_command)
    tester.run_test("reset コマンド（確認なし）", tester.test_reset_without_confirm)
    tester.run_test("stats コマンド（text）", tester.test_stats_text_format)
    tester.run_test("stats コマンド（json）", tester.test_stats_json_format)
    tester.run_test("stats コマンド（csv）", tester.test_stats_csv_format)
    tester.run_test("validate コマンド", tester.test_validate_command)
    tester.run_test("カスタム state.json パス", tester.test_custom_state_file)
    tester.run_test("存在しないファイルの show", tester.test_missing_state_file_show)

    # サマリー表示
    exit_code = tester.print_summary()

    # 一時ファイルクリーンアップ
    import shutil
    shutil.rmtree(tester.temp_dir, ignore_errors=True)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
