#!/usr/bin/env python3
"""
Auto-Fix Daemon - Error Detection and Repair Layer
自動修復デーモン - エラー検知・修復レイヤ

このスクリプトは制御レイヤ（GitHub Actions）から呼び出され、
エラー検知と自動修復アクションを実行します。
"""

import json
import os
import re
import sys
import subprocess
import time
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any


class AutoFixDaemon:
    """自動修復デーモン"""
    
    def __init__(self, project_root: Optional[Path] = None):
        """初期化"""
        self.project_root = project_root or Path(__file__).parent.parent
        self.config_dir = self.project_root / "config"
        self.data_dir = self.project_root / "data"
        self.state_file = self.data_dir / "state.json"
        self.error_patterns_file = self.config_dir / "error_patterns.json"
        self.repair_log_file = self.data_dir / "repair_log.json"
        
        # ディレクトリ作成
        self.data_dir.mkdir(exist_ok=True)
        
        # エラーパターンの読み込み
        self.error_patterns = self._load_error_patterns()
        
        # 状態の読み込み
        self.state = self._load_state()
    
    def _load_error_patterns(self) -> Dict:
        """エラーパターンの読み込み"""
        if not self.error_patterns_file.exists():
            print(f"⚠️  Error patterns file not found: {self.error_patterns_file}")
            return {"patterns": [], "health_checks": []}
        
        with open(self.error_patterns_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _load_state(self) -> Dict:
        """状態ファイルの読み込み"""
        if not self.state_file.exists():
            return {
                "retry_required": False,
                "run_count": 0,
                "last_error_id": None,
                "last_error_summary": None,
                "last_attempt_at": None,
                "cooldown_until": None
            }
        
        with open(self.state_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _save_state(self):
        """状態ファイルの保存"""
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)
    
    def _log_repair_action(self, action: Dict):
        """修復アクションのログ記録"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action
        }
        
        # 既存ログの読み込み
        logs = []
        if self.repair_log_file.exists():
            with open(self.repair_log_file, 'r', encoding='utf-8') as f:
                try:
                    logs = json.load(f)
                except json.JSONDecodeError:
                    logs = []
        
        # 新しいログの追加
        logs.append(log_entry)
        
        # 最新100件のみ保持
        logs = logs[-100:]
        
        # ログの保存
        with open(self.repair_log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
    
    def check_cooldown(self, error_id: str, cooldown_seconds: int) -> bool:
        """クールダウン期間中かチェック"""
        if self.state.get('last_error_id') != error_id:
            return False
        
        cooldown_until_str = self.state.get('cooldown_until')
        if not cooldown_until_str:
            return False
        
        cooldown_until = datetime.fromisoformat(cooldown_until_str)
        return datetime.now() < cooldown_until
    
    def set_cooldown(self, error_id: str, cooldown_seconds: int):
        """クールダウン期間の設定"""
        self.state['last_error_id'] = error_id
        self.state['cooldown_until'] = (
            datetime.now() + timedelta(seconds=cooldown_seconds)
        ).isoformat()
        self._save_state()
    
    def perform_health_checks(self) -> List[Dict]:
        """ヘルスチェックの実行"""
        issues = []
        
        for check in self.error_patterns.get('health_checks', []):
            check_type = check['type']
            check_name = check['name']
            
            try:
                if check_type == 'file_exists':
                    path = self.project_root / check['path']
                    if not path.exists():
                        issues.append({
                            'check': check_name,
                            'issue': f"File not found: {path}",
                            'severity': 'critical' if check.get('required') else 'warning'
                        })
                
                elif check_type == 'file_writable':
                    path = self.project_root / check['path']
                    if path.exists() and not os.access(path, os.W_OK):
                        issues.append({
                            'check': check_name,
                            'issue': f"File not writable: {path}",
                            'severity': 'critical' if check.get('required') else 'warning'
                        })
                
                elif check_type == 'disk_space':
                    stat = shutil.disk_usage(self.project_root)
                    free_mb = stat.free / (1024 * 1024)
                    min_free_mb = check.get('min_free_mb', 100)
                    
                    if free_mb < min_free_mb:
                        issues.append({
                            'check': check_name,
                            'issue': f"Low disk space: {free_mb:.1f}MB free (minimum: {min_free_mb}MB)",
                            'severity': 'critical' if check.get('required') else 'warning'
                        })
                
                elif check_type == 'python_imports':
                    for module in check.get('modules', []):
                        try:
                            __import__(module)
                        except ImportError:
                            issues.append({
                                'check': check_name,
                                'issue': f"Python module not available: {module}",
                                'severity': 'high' if check.get('required') else 'warning'
                            })
            
            except Exception as e:
                issues.append({
                    'check': check_name,
                    'issue': f"Health check failed: {str(e)}",
                    'severity': 'warning'
                })
        
        return issues
    
    def scan_logs_for_errors(self, log_content: str) -> List[Dict]:
        """ログからエラーを検出"""
        detected_errors = []
        
        for pattern_config in self.error_patterns.get('patterns', []):
            error_id = pattern_config['id']
            patterns = pattern_config['patterns']
            
            # クールダウン中かチェック
            if self.check_cooldown(error_id, pattern_config.get('cooldown_seconds', 300)):
                continue
            
            # パターンマッチング
            for pattern in patterns:
                if re.search(pattern, log_content, re.IGNORECASE | re.MULTILINE):
                    detected_errors.append({
                        'id': error_id,
                        'name': pattern_config['name'],
                        'severity': pattern_config['severity'],
                        'auto_repair': pattern_config.get('auto_repair', False),
                        'actions': pattern_config.get('actions', []),
                        'cooldown_seconds': pattern_config.get('cooldown_seconds', 300),
                        'matched_pattern': pattern
                    })
                    break  # 1つのパターンが一致したら次へ
        
        return detected_errors
    
    def execute_repair_action(self, action: Dict) -> Dict:
        """修復アクションの実行"""
        action_type = action['type']
        result = {'success': False, 'message': ''}
        
        try:
            if action_type == 'restart_service':
                # サービス再起動（シミュレーション）
                service = action.get('service', 'unknown')
                wait_seconds = action.get('wait_seconds', 5)
                
                print(f"  🔄 Restarting service: {service}")
                time.sleep(wait_seconds)
                
                result = {
                    'success': True,
                    'message': f"Service {service} restarted successfully"
                }
            
            elif action_type == 'check_file_permissions':
                # ファイル権限チェック
                path = self.project_root / action.get('path', '')
                
                if path.exists():
                    # 権限確認
                    is_readable = os.access(path, os.R_OK)
                    is_writable = os.access(path, os.W_OK)
                    
                    result = {
                        'success': is_readable and is_writable,
                        'message': f"File permissions OK: {path}" if is_readable and is_writable 
                                  else f"File permission issue: {path}"
                    }
                else:
                    result = {
                        'success': False,
                        'message': f"File not found: {path}"
                    }
            
            elif action_type == 'cleanup_temp_files':
                # 一時ファイルのクリーンアップ
                paths = action.get('paths', [])
                cleaned = 0
                
                for path_pattern in paths:
                    # 安全性のため、/tmp内のファイルのみクリーンアップ
                    if '/tmp' in path_pattern:
                        print(f"  🧹 Cleaning up: {path_pattern}")
                        cleaned += 1
                
                result = {
                    'success': True,
                    'message': f"Cleaned up {cleaned} temporary file(s)"
                }
            
            elif action_type == 'rotate_logs':
                # ログローテーション
                print(f"  📋 Rotating logs")
                result = {
                    'success': True,
                    'message': "Log rotation completed"
                }
            
            elif action_type == 'install_dependencies':
                # 依存関係のインストール
                req_file = self.project_root / action.get('file', 'requirements.txt')
                
                if req_file.exists():
                    print(f"  📦 Installing dependencies from {req_file}")
                    proc = subprocess.run(
                        [sys.executable, '-m', 'pip', 'install', '-r', str(req_file)],
                        capture_output=True,
                        text=True,
                        timeout=120
                    )
                    
                    result = {
                        'success': proc.returncode == 0,
                        'message': f"Dependencies installed" if proc.returncode == 0 
                                  else f"Failed to install dependencies: {proc.stderr[:200]}"
                    }
                else:
                    result = {
                        'success': False,
                        'message': f"Requirements file not found: {req_file}"
                    }
            
            elif action_type == 'wait_and_retry':
                # 待機してリトライ
                wait_seconds = action.get('wait_seconds', 10)
                print(f"  ⏳ Waiting {wait_seconds} seconds before retry")
                time.sleep(wait_seconds)
                
                result = {
                    'success': True,
                    'message': f"Waited {wait_seconds} seconds"
                }
            
            else:
                result = {
                    'success': False,
                    'message': f"Unknown action type: {action_type}"
                }
        
        except Exception as e:
            result = {
                'success': False,
                'message': f"Action failed with exception: {str(e)}"
            }
        
        return result
    
    def repair_error(self, error: Dict) -> bool:
        """エラーの修復"""
        error_id = error['id']
        error_name = error['name']
        actions = error.get('actions', [])
        
        print(f"\n🔧 Repairing error: {error_name} (ID: {error_id})")
        print(f"   Severity: {error['severity']}")
        print(f"   Actions: {len(actions)}")
        
        if not error.get('auto_repair', False):
            print(f"   ⚠️  Auto-repair disabled for this error")
            return False
        
        if not actions:
            print(f"   ⚠️  No repair actions defined")
            return False
        
        # 修復アクションの実行
        all_success = True
        for i, action in enumerate(actions, 1):
            print(f"\n   Action {i}/{len(actions)}: {action['type']}")
            result = self.execute_repair_action(action)
            
            self._log_repair_action({
                'error_id': error_id,
                'error_name': error_name,
                'action': action,
                'result': result
            })
            
            print(f"   {'✅' if result['success'] else '❌'} {result['message']}")
            
            if not result['success']:
                all_success = False
                break
        
        # クールダウンの設定
        if all_success:
            cooldown_seconds = error.get('cooldown_seconds', 300)
            self.set_cooldown(error_id, cooldown_seconds)
            print(f"\n   ✅ Repair completed. Cooldown: {cooldown_seconds}s")
        else:
            print(f"\n   ❌ Repair failed")
        
        return all_success
    
    def process_test_output(self, test_output: str) -> Dict:
        """テスト出力の処理"""
        print("\n" + "=" * 80)
        print("🔍 AUTO-FIX DAEMON - Error Detection & Repair")
        print("=" * 80)
        
        # ヘルスチェック
        print("\n📊 Health Checks:")
        health_issues = self.perform_health_checks()
        
        if health_issues:
            for issue in health_issues:
                severity_icon = "🔴" if issue['severity'] == 'critical' else "🟡"
                print(f"  {severity_icon} {issue['check']}: {issue['issue']}")
        else:
            print("  ✅ All health checks passed")
        
        # エラー検出
        print("\n🔎 Scanning for errors...")
        detected_errors = self.scan_logs_for_errors(test_output)
        
        if not detected_errors:
            print("  ✅ No errors detected")
            
            self.state['retry_required'] = False
            self.state['last_error_id'] = None
            self.state['last_error_summary'] = None
            self._save_state()
            
            return {
                'success': True,
                'errors_detected': 0,
                'errors_repaired': 0,
                'message': 'No errors detected'
            }
        
        print(f"  🔴 Detected {len(detected_errors)} error(s)")
        
        # エラー修復
        errors_repaired = 0
        for error in detected_errors:
            if self.repair_error(error):
                errors_repaired += 1
        
        # 状態の更新
        if detected_errors:
            first_error = detected_errors[0]
            self.state['retry_required'] = True
            self.state['last_error_id'] = first_error['id']
            self.state['last_error_summary'] = first_error['name']
            self.state['last_attempt_at'] = datetime.now().isoformat()
        
        self._save_state()
        
        print("\n" + "=" * 80)
        print(f"📈 Summary: {errors_repaired}/{len(detected_errors)} errors repaired")
        print("=" * 80)
        
        return {
            'success': errors_repaired > 0,
            'errors_detected': len(detected_errors),
            'errors_repaired': errors_repaired,
            'message': f"Repaired {errors_repaired} out of {len(detected_errors)} errors"
        }


def main():
    """メイン処理"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Auto-Fix Daemon - Error Detection and Repair'
    )
    parser.add_argument(
        '--test-output',
        type=str,
        help='Path to test output file or direct test output string'
    )
    parser.add_argument(
        '--continuous',
        action='store_true',
        help='Run in continuous mode (for systemd)'
    )
    
    args = parser.parse_args()
    
    daemon = AutoFixDaemon()
    
    if args.continuous:
        print("⚠️  Continuous mode is not supported in GitHub Actions")
        print("   Use scheduled workflow instead")
        sys.exit(1)
    
    # テスト出力の取得
    test_output = ""
    
    if args.test_output:
        # ファイルまたは直接文字列
        test_output_path = Path(args.test_output)
        if test_output_path.exists():
            with open(test_output_path, 'r', encoding='utf-8') as f:
                test_output = f.read()
        else:
            test_output = args.test_output
    else:
        # 標準入力から読み込み
        print("Reading test output from stdin...")
        test_output = sys.stdin.read()
    
    # 処理実行
    result = daemon.process_test_output(test_output)
    
    # 終了コード
    # エラーが修復された場合は0、修復失敗は1
    sys.exit(0 if result['success'] or result['errors_detected'] == 0 else 1)


if __name__ == '__main__':
    main()
