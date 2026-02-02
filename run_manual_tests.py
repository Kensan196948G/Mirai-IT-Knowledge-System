#!/usr/bin/env python3
"""
SubAgents 手動テストスクリプト
pytest環境問題を回避して直接テスト実行
"""

import sys
sys.path.insert(0, '.')

from src.subagents.itsm_expert import ITSMExpertSubAgent
from src.subagents.qa import QASubAgent
from src.subagents.architect import ArchitectSubAgent
from src.subagents.knowledge_curator import KnowledgeCuratorSubAgent
from src.subagents.documenter import DocumenterSubAgent
from src.subagents.devops import DevOpsSubAgent
from src.subagents.coordinator import CoordinatorSubAgent


def test_itsm_expert():
    """ITSMExpert テスト"""
    print("\n=== ITSMExpertSubAgent テスト ===")
    agent = ITSMExpertSubAgent()

    # 初期化テスト
    assert agent.name == "itsm_expert"
    assert agent.role == "compliance"
    assert agent.priority == "high"
    print("✓ 初期化テスト成功")

    # 正常系テスト
    input_data = {
        'title': 'DBサーバー障害対応',
        'content': '発生時刻: 10:00, 影響範囲: 全体, 復旧手順あり, 原因調査実施',
        'itsm_type': 'Incident'
    }
    result = agent.process(input_data)
    assert result.status in ['success', 'warning']
    assert 'compliance_score' in result.data
    print("✓ 正常系テスト成功")

    # 異常系テスト
    result2 = agent.process({'title': 'テスト'})
    assert result2.status == 'failed'
    print("✓ 異常系テスト成功")

    return True


def test_qa():
    """QA テスト"""
    print("\n=== QASubAgent テスト ===")
    agent = QASubAgent()

    # 初期化テスト
    assert agent.name == "qa"
    assert agent.role == "quality_validation"
    print("✓ 初期化テスト成功")

    # 正常系テスト
    input_data = {
        'title': 'データベース接続エラーの対処法',
        'content': '発生状況について詳しく説明します。' * 10,
        'existing_knowledge': []
    }
    result = agent.process(input_data)
    assert result.status in ['success', 'warning']
    assert 'quality_score' in result.data
    print("✓ 正常系テスト成功")

    # 異常系テスト
    result2 = agent.process({'title': 'テスト'})
    assert result2.status == 'failed'
    print("✓ 異常系テスト成功")

    return True


def test_architect():
    """Architect テスト"""
    print("\n=== ArchitectSubAgent テスト ===")
    agent = ArchitectSubAgent()

    # 初期化テスト
    assert agent.name == "architect"
    assert agent.role == "design_coherence"
    print("✓ 初期化テスト成功")

    # 正常系テスト
    input_data = {
        'title': 'データベース障害対応',
        'content': 'データベースエラーが発生しました。原因を特定し対策を実施しました。',
        'itsm_type': 'Incident'
    }
    result = agent.process(input_data)
    assert result.status in ['success', 'warning']
    assert 'coherence_score' in result.data
    print("✓ 正常系テスト成功")

    # 異常系テスト
    result2 = agent.process({'title': 'テスト'})
    assert result2.status == 'failed'
    print("✓ 異常系テスト成功")

    return True


def test_knowledge_curator():
    """KnowledgeCurator テスト"""
    print("\n=== KnowledgeCuratorSubAgent テスト ===")
    agent = KnowledgeCuratorSubAgent()

    # 初期化テスト
    assert agent.name == "knowledge_curator"
    assert agent.role == "organization"
    print("✓ 初期化テスト成功")

    # 正常系テスト
    input_data = {
        'title': 'データベース接続エラー',
        'content': 'MySQL データベースでネットワークエラーが発生しました。',
        'itsm_type': 'Incident'
    }
    result = agent.process(input_data)
    assert result.status == 'success'
    assert 'tags' in result.data
    assert 'categories' in result.data
    print("✓ 正常系テスト成功")

    # 異常系テスト
    result2 = agent.process({'title': 'テスト'})
    assert result2.status == 'failed'
    print("✓ 異常系テスト成功")

    return True


def test_documenter():
    """Documenter テスト"""
    print("\n=== DocumenterSubAgent テスト ===")
    agent = DocumenterSubAgent()

    # 初期化テスト
    assert agent.name == "documenter"
    assert agent.role == "formatting"
    print("✓ 初期化テスト成功")

    # 正常系テスト
    input_data = {
        'title': 'データベース障害対応',
        'content': '発生時刻: 10:00, 原因を特定し対応完了しました。',
        'itsm_type': 'Incident'
    }
    result = agent.process(input_data)
    assert result.status == 'success'
    assert 'summary_technical' in result.data
    assert 'markdown' in result.data
    print("✓ 正常系テスト成功")

    # 異常系テスト
    result2 = agent.process({'title': 'テスト'})
    assert result2.status == 'failed'
    print("✓ 異常系テスト成功")

    return True


def test_devops():
    """DevOps テスト"""
    print("\n=== DevOpsSubAgent テスト ===")
    agent = DevOpsSubAgent()

    # 初期化テスト
    assert agent.name == "devops"
    assert agent.role == "technical_analysis"
    print("✓ 初期化テスト成功")

    # 正常系テスト
    input_data = {
        'title': 'Apacheサーバー再起動',
        'content': '''
        定期的にApacheサーバーを再起動します。
        ```bash
        systemctl restart apache2
        ```
        ''',
        'itsm_type': 'Change'
    }
    result = agent.process(input_data)
    assert result.status == 'success'
    assert 'technical_elements' in result.data
    assert 'automation_potential' in result.data
    print("✓ 正常系テスト成功")

    # 異常系テスト
    result2 = agent.process({'title': 'テスト'})
    assert result2.status == 'failed'
    print("✓ 異常系テスト成功")

    return True


def test_coordinator():
    """Coordinator テスト"""
    print("\n=== CoordinatorSubAgent テスト ===")
    agent = CoordinatorSubAgent()

    # 初期化テスト
    assert agent.name == "coordinator"
    assert agent.role == "coordination_review"
    print("✓ 初期化テスト成功")

    # 正常系テスト
    input_data = {
        'title': 'データベース障害対応記録',
        'content': '影響範囲: 全体, 担当者: 田中, 時刻: 10:00, 対策: 実施済み',
        'itsm_type': 'Incident'
    }
    result = agent.process(input_data)
    assert result.status in ['success', 'warning']
    assert 'missing_items' in result.data
    print("✓ 正常系テスト成功")

    # 異常系テスト
    result2 = agent.process({'title': 'テスト'})
    assert result2.status == 'failed'
    print("✓ 異常系テスト成功")

    return True


def main():
    """メインテスト実行"""
    print("\n" + "="*60)
    print("SubAgents 単体テスト実行")
    print("="*60)

    tests = [
        ("ITSMExpert", test_itsm_expert),
        ("QA", test_qa),
        ("Architect", test_architect),
        ("KnowledgeCurator", test_knowledge_curator),
        ("Documenter", test_documenter),
        ("DevOps", test_devops),
        ("Coordinator", test_coordinator)
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✓ {name} テスト完了")
        except Exception as e:
            failed += 1
            print(f"✗ {name} テスト失敗: {e}")

    print("\n" + "="*60)
    print(f"テスト結果: {passed}/{len(tests)} 成功, {failed} 失敗")
    print("="*60)

    if failed == 0:
        print("\n✓ すべてのSubAgentテストが成功しました！")
        return 0
    else:
        print(f"\n✗ {failed}個のテストが失敗しました")
        return 1


if __name__ == "__main__":
    sys.exit(main())
