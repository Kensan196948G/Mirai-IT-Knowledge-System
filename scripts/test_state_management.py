#!/usr/bin/env python3
"""
state.json 統合テストスクリプト

Run間状態管理の正常動作を検証

テスト項目:
1. StateManager の基本動作（load/save）
2. エラー検出後の状態更新
3. 修復後の状態更新（成功/失敗）
4. クールダウン管理
5. 連続失敗カウント
6. state.json の初期化と復元
7. 壊れた state.json のハンドリング
"""

import json
import sys
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path

# プロジェクトルートをパスに追加
SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

# auto_fix_daemon から StateManager をインポート
from scripts.auto_fix_daemon import StateManager


class TestStateManagement:
    """state.json 統合テストクラス"""

    def __init__(self):
        """初期化"""
        self.test_count = 0
        self.passed_count = 0
        self.failed_count = 0
        self.temp_dir = Path(tempfile.mkdtemp())

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

    def test_basic_load_save(self):
        """基本的な読み書きテスト"""
        state_file = self.temp_dir / "test_basic.json"
        manager = StateManager(str(state_file))

        # 初回読み込み（ファイル未存在）
        state = manager.load_state()
        assert state['retry_required'] == False, "Initial retry_required should be False"
        assert state['run_count'] == 0, "Initial run_count should be 0"

        # 状態を変更して保存
        state['retry_required'] = True
        state['run_count'] = 5
        manager.save_state(state)

        # 再読み込みして確認
        state2 = manager.load_state()
        assert state2['retry_required'] == True, "retry_required should be True"
        assert state2['run_count'] == 5, "run_count should be 5"

        print("   ✓ Basic load/save works correctly")

    def test_error_detection_update(self):
        """エラー検出後の状態更新テスト"""
        state_file = self.temp_dir / "test_detection.json"
        manager = StateManager(str(state_file))

        # エラー検出を記録
        manager.update_after_detection(
            error_id="test_error_001",
            error_summary="Test error occurred",
            errors_detected=1
        )

        state = manager.load_state()
        assert state['retry_required'] == True, "retry_required should be True after error detection"
        assert state['last_error_id'] == "test_error_001", "error_id should match"
        assert state['total_errors_detected'] == 1, "total_errors_detected should be 1"
        assert "Test error occurred" in state['last_error_summary'], "error_summary should be recorded"

        print("   ✓ Error detection updates state correctly")

    def test_fix_success(self):
        """修復成功時の状態更新テスト"""
        state_file = self.temp_dir / "test_fix_success.json"
        manager = StateManager(str(state_file))

        # エラー検出 → 修復成功
        manager.update_after_detection("test_error", "Test error", 1)
        manager.update_after_fix("test_error", success=True, message="Fixed successfully")

        state = manager.load_state()
        assert state['retry_required'] == False, "retry_required should be False after successful fix"
        assert state['total_fixes_attempted'] == 1, "total_fixes_attempted should be 1"
        assert state['total_fixes_succeeded'] == 1, "total_fixes_succeeded should be 1"
        assert state['continuous_failure_count'] == 0, "continuous_failure_count should be 0"
        assert state['last_health_status'] == 'healthy', "health_status should be healthy"

        print("   ✓ Successful fix updates state correctly")

    def test_fix_failure(self):
        """修復失敗時の状態更新テスト"""
        state_file = self.temp_dir / "test_fix_failure.json"
        manager = StateManager(str(state_file))

        # エラー検出 → 修復失敗
        manager.update_after_detection("test_error", "Test error", 1)
        manager.update_after_fix("test_error", success=False, message="Fix failed")

        state = manager.load_state()
        assert state['retry_required'] == True, "retry_required should be True after failed fix"
        assert state['total_fixes_attempted'] == 1, "total_fixes_attempted should be 1"
        assert state['total_fixes_succeeded'] == 0, "total_fixes_succeeded should be 0"
        assert state['continuous_failure_count'] == 1, "continuous_failure_count should be 1"
        assert state['last_health_status'] == 'degraded', "health_status should be degraded"
        assert state['cooldown_until'] != '', "cooldown_until should be set"

        print("   ✓ Failed fix updates state correctly")

    def test_cooldown_management(self):
        """クールダウン管理テスト"""
        state_file = self.temp_dir / "test_cooldown.json"
        manager = StateManager(str(state_file))

        # 修復失敗（クールダウン設定）
        manager.update_after_fix("test_error", success=False)

        # クールダウン中かチェック
        assert manager.is_in_cooldown() == True, "Should be in cooldown period"

        # クールダウン期間を過去に設定
        state = manager.load_state()
        state['cooldown_until'] = (datetime.now() - timedelta(seconds=10)).isoformat()
        manager.save_state(state)

        # クールダウン解除を確認
        assert manager.is_in_cooldown() == False, "Should not be in cooldown period"

        print("   ✓ Cooldown management works correctly")

    def test_continuous_failure_count(self):
        """連続失敗カウントテスト"""
        state_file = self.temp_dir / "test_continuous_failure.json"
        manager = StateManager(str(state_file))

        # 3回連続失敗
        for i in range(3):
            manager.update_after_fix(f"test_error_{i}", success=False)

        state = manager.load_state()
        assert state['continuous_failure_count'] == 3, "continuous_failure_count should be 3"
        assert state['last_health_status'] == 'critical', "health_status should be critical after 3 failures"

        # 成功でリセット
        manager.update_after_fix("test_error", success=True)
        state = manager.load_state()
        assert state['continuous_failure_count'] == 0, "continuous_failure_count should be reset to 0"

        print("   ✓ Continuous failure count works correctly")

    def test_corrupted_json_handling(self):
        """壊れた JSON のハンドリングテスト"""
        state_file = self.temp_dir / "test_corrupted.json"

        # 壊れた JSON を書き込み
        with open(state_file, 'w') as f:
            f.write("{invalid json content}")

        manager = StateManager(str(state_file))
        state = manager.load_state()

        # 初期状態にフォールバック
        assert state['retry_required'] == False, "Should fallback to initial state"
        assert state['run_count'] == 0, "Should fallback to initial state"

        print("   ✓ Corrupted JSON handling works correctly")

    def test_missing_fields_handling(self):
        """必須フィールド欠落のハンドリングテスト"""
        state_file = self.temp_dir / "test_missing_fields.json"

        # 必須フィールドが欠けた JSON を書き込み
        with open(state_file, 'w') as f:
            json.dump({"retry_required": True}, f)

        manager = StateManager(str(state_file))
        state = manager.load_state()

        # 初期状態にフォールバック
        assert 'run_count' in state, "Should have run_count field"
        assert 'last_error_id' in state, "Should have last_error_id field"

        print("   ✓ Missing fields handling works correctly")

    def test_backup_creation(self):
        """バックアップ作成テスト"""
        state_file = self.temp_dir / "test_backup.json"
        backup_file = self.temp_dir / "test_backup.json.bak"
        manager = StateManager(str(state_file))

        # 初回保存
        state = manager.load_state()
        state['run_count'] = 10
        manager.save_state(state)

        # 2回目保存（バックアップ作成）
        state['run_count'] = 20
        manager.save_state(state)

        # バックアップファイルが存在するか確認
        assert backup_file.exists(), "Backup file should exist"

        # バックアップの内容を確認
        with open(backup_file, 'r') as f:
            backup_state = json.load(f)
        assert backup_state['run_count'] == 10, "Backup should contain previous state"

        print("   ✓ Backup creation works correctly")

    def test_timestamp_updates(self):
        """タイムスタンプ更新テスト"""
        state_file = self.temp_dir / "test_timestamp.json"
        manager = StateManager(str(state_file))

        # 初回読み込み
        state1 = manager.load_state()
        created_at = state1['created_at']
        updated_at1 = state1['updated_at']

        time.sleep(0.1)  # 時間差を作る

        # 保存
        manager.save_state(state1)

        # 再読み込み
        state2 = manager.load_state()
        updated_at2 = state2['updated_at']

        # created_at は変わらない、updated_at は更新される
        assert state2['created_at'] == created_at, "created_at should not change"
        assert updated_at2 > updated_at1, "updated_at should be updated"

        print("   ✓ Timestamp updates work correctly")

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
    print("🧪 state.json 統合テスト開始")
    print("="*60)

    tester = TestStateManagement()

    # テスト実行
    tester.run_test("基本的な読み書き", tester.test_basic_load_save)
    tester.run_test("エラー検出後の状態更新", tester.test_error_detection_update)
    tester.run_test("修復成功時の状態更新", tester.test_fix_success)
    tester.run_test("修復失敗時の状態更新", tester.test_fix_failure)
    tester.run_test("クールダウン管理", tester.test_cooldown_management)
    tester.run_test("連続失敗カウント", tester.test_continuous_failure_count)
    tester.run_test("壊れたJSONのハンドリング", tester.test_corrupted_json_handling)
    tester.run_test("必須フィールド欠落のハンドリング", tester.test_missing_fields_handling)
    tester.run_test("バックアップ作成", tester.test_backup_creation)
    tester.run_test("タイムスタンプ更新", tester.test_timestamp_updates)

    # サマリー表示
    exit_code = tester.print_summary()

    # 一時ファイルクリーンアップ
    import shutil
    shutil.rmtree(tester.temp_dir, ignore_errors=True)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
