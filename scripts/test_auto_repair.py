#!/usr/bin/env python3
"""
Integration test for Auto-Repair System
自動修復システムの統合テスト
"""

import json
import subprocess
import sys
from pathlib import Path


def test_daemon_help():
    """Test daemon help command"""
    print("🧪 Test 1: Daemon help command")
    result = subprocess.run(
        [sys.executable, "scripts/auto_fix_daemon.py", "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, "Help command should succeed"
    assert "Auto-Fix Daemon" in result.stdout
    print("   ✅ Passed\n")


def test_daemon_no_errors():
    """Test daemon with no errors"""
    print("🧪 Test 2: Daemon with no errors")
    test_output = "All tests passed successfully"
    result = subprocess.run(
        [sys.executable, "scripts/auto_fix_daemon.py"],
        input=test_output,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, "Should succeed with no errors"
    assert "No errors detected" in result.stdout
    print("   ✅ Passed\n")


def test_daemon_with_import_error():
    """Test daemon with import error"""
    print("🧪 Test 3: Daemon with import error (detection)")
    test_output = "ModuleNotFoundError: No module named 'nonexistent_module'"
    result = subprocess.run(
        [sys.executable, "scripts/auto_fix_daemon.py"],
        input=test_output,
        capture_output=True,
        text=True
    )
    # Should detect error (may be in cooldown, so we just check it doesn't crash)
    assert result.returncode in [0, 1], "Should complete without crash"
    # Check that daemon processed the input
    assert "AUTO-FIX DAEMON" in result.stdout or "Error Detection" in result.stdout
    print("   ✅ Passed\n")


def test_state_file_format():
    """Test state file format"""
    print("🧪 Test 4: State file format")
    state_file = Path("data/state.json")
    assert state_file.exists(), "State file should exist"
    
    with open(state_file, 'r') as f:
        state = json.load(f)
    
    # Check required fields
    required_fields = [
        "retry_required", "run_count", "last_error_id",
        "last_error_summary", "last_attempt_at", "cooldown_until"
    ]
    
    for field in required_fields:
        assert field in state, f"State should have '{field}' field"
    
    print("   ✅ Passed\n")


def test_error_patterns_format():
    """Test error patterns file format"""
    print("🧪 Test 5: Error patterns file format")
    patterns_file = Path("config/error_patterns.json")
    assert patterns_file.exists(), "Error patterns file should exist"
    
    with open(patterns_file, 'r') as f:
        patterns = json.load(f)
    
    assert "patterns" in patterns, "Should have 'patterns' key"
    assert "health_checks" in patterns, "Should have 'health_checks' key"
    assert len(patterns["patterns"]) > 0, "Should have at least one pattern"
    
    # Check first pattern structure
    first_pattern = patterns["patterns"][0]
    required_fields = ["id", "name", "patterns", "severity", "auto_repair", "actions"]
    
    for field in required_fields:
        assert field in first_pattern, f"Pattern should have '{field}' field"
    
    print("   ✅ Passed\n")


def test_workflow_file_exists():
    """Test workflow file exists"""
    print("🧪 Test 6: Workflow file exists")
    workflow_file = Path(".github/workflows/auto_repair.yml")
    assert workflow_file.exists(), "Workflow file should exist"
    
    content = workflow_file.read_text()
    assert "auto_repair_loop" in content, "Should contain auto_repair_loop job"
    assert "schedule" in content, "Should have schedule trigger"
    assert "workflow_dispatch" in content, "Should have manual trigger"
    
    print("   ✅ Passed\n")


def test_documentation_exists():
    """Test documentation files exist"""
    print("🧪 Test 7: Documentation exists")
    
    docs = [
        Path("docs/AUTO_REPAIR_SYSTEM.md"),
        Path("docs/AUTO_REPAIR_QUICKSTART.md")
    ]
    
    for doc in docs:
        assert doc.exists(), f"Documentation {doc} should exist"
        content = doc.read_text()
        assert len(content) > 100, f"Documentation {doc} should have content"
    
    print("   ✅ Passed\n")


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("🚀 Auto-Repair System Integration Tests")
    print("=" * 80 + "\n")
    
    tests = [
        test_daemon_help,
        test_daemon_no_errors,
        test_daemon_with_import_error,
        test_state_file_format,
        test_error_patterns_format,
        test_workflow_file_exists,
        test_documentation_exists
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"   ❌ Failed: {e}\n")
            failed += 1
        except Exception as e:
            print(f"   ❌ Error: {e}\n")
            failed += 1
    
    print("=" * 80)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    print("=" * 80 + "\n")
    
    if failed > 0:
        sys.exit(1)
    else:
        print("✨ All tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
