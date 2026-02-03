#!/usr/bin/env python3
"""
ワークフローテストスクリプト
Workflow Test Script
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.workflow import WorkflowEngine
from src.core.itsm_classifier import ITSMClassifier


def test_incident_case():
    """インシデント事例のテスト"""
    print("=" * 80)
    print("テストケース1: インシデント（障害対応）")
    print("=" * 80)

    title = "Webサーバーの503エラー発生"
    content = """
## 発生事象
2025年12月31日 10:30頃、本番WebサーバーでHTTP 503エラーが発生。
全ユーザーがWebサイトにアクセスできない状況となった。

## 影響範囲
- 影響対象: 全ユーザー（約1000名）
- 影響時間: 10:30〜11:15（約45分間）

## 対応内容
1. 10:32 監視アラートを検知
2. 10:35 Webサーバーのログ確認
3. 10:40 原因特定: Apacheのプロセス数上限に到達
4. 10:45 Apacheの設定を変更（MaxRequestWorkers: 150 → 300）
5. 10:50 Apacheを再起動
6. 11:00 サービス復旧を確認
7. 11:15 正常性確認完了

## 一時対応
Apacheを再起動してサービスを復旧

## 今後の対応
- 根本原因調査（問題管理へ）
- Apacheの設定最適化
- 負荷分散の検討
"""

    # ITSM分類
    classifier = ITSMClassifier()
    classification = classifier.classify(title, content)
    print(f"\n📋 ITSM分類結果:")
    print(f"  タイプ: {classification['itsm_type']}")
    print(f"  信頼度: {classification['confidence']:.0%}")

    # ワークフロー実行
    engine = WorkflowEngine()
    result = engine.process_knowledge(
        title=title,
        content=content,
        itsm_type=classification['itsm_type'],
        created_by='test_user'
    )

    if result['success']:
        print(f"\n✅ 処理成功:")
        print(f"  ナレッジID: {result['knowledge_id']}")
        print(f"  実行時間: {result['execution_time_ms']}ms")
        print(f"  Markdownパス: {result['markdown_path']}")

        # 品質評価
        assessment = result.get('post_task_assessment', {})
        print(f"\n📊 品質評価:")
        print(f"  総合スコア: {assessment.get('quality_score', 0):.0%}")
        print(f"  レベル: {assessment.get('quality_level', 'unknown')}")
        print(f"  警告: {assessment.get('warnings', 0)}件")
        print(f"  重大問題: {assessment.get('critical_issues', 0)}件")
    else:
        print(f"\n❌ 処理失敗: {result.get('error')}")

    print("\n" + "=" * 80 + "\n")


def test_problem_case():
    """問題管理事例のテスト"""
    print("=" * 80)
    print("テストケース2: 問題管理（根本原因分析）")
    print("=" * 80)

    title = "Webサーバー503エラーの根本原因分析"
    content = """
## 関連インシデント
- INC-2025-001: Webサーバーの503エラー発生

## 根本原因
Webサーバー（Apache）のMaxRequestWorkers設定値が不足していた。
アクセス数の増加に伴い、プロセス数上限に到達していた。

## 原因分析
1. アクセスログ分析の結果、過去1ヶ月でアクセス数が2倍に増加
2. Apache設定は初期設定のまま（MaxRequestWorkers: 150）
3. ピーク時のアクセス数が設定値を超過
4. 新規接続が拒否され503エラーが発生

## 恒久対策
1. Apacheの設定を最適化（MaxRequestWorkers: 300に変更）
2. アクセス数の監視アラート設定
3. 定期的な設定見直しプロセスの確立
4. 負荷分散構成の検討（中長期的対応）

## 再発防止
- 月次でアクセス数トレンドをレビュー
- 閾値の80%でアラート通知
- 四半期ごとに設定値を見直し

## 実施計画
恒久対策を変更管理として実施（CHG-2025-001）
"""

    classifier = ITSMClassifier()
    classification = classifier.classify(title, content)

    engine = WorkflowEngine()
    result = engine.process_knowledge(
        title=title,
        content=content,
        itsm_type=classification['itsm_type'],
        created_by='test_user'
    )

    if result['success']:
        print(f"\n✅ 処理成功: ナレッジID {result['knowledge_id']}")

        # 集約されたナレッジを表示
        knowledge = result['aggregated_knowledge']
        print(f"\n📝 生成された要約:")
        print(f"  技術者向け: {knowledge['summary_technical'][:100]}...")
        print(f"  非技術者向け: {knowledge['summary_non_technical'][:100]}...")
        print(f"\n🏷️  タグ: {', '.join(knowledge['tags'][:5])}")
        print(f"\n💡 知見（{len(knowledge['insights'])}件）:")
        for i, insight in enumerate(knowledge['insights'][:3], 1):
            print(f"  {i}. {insight}")

    print("\n" + "=" * 80 + "\n")


def main():
    """メイン処理"""
    print("\n🚀 Mirai IT Knowledge Systems - ワークフローテスト\n")

    try:
        # テストケース1: インシデント
        test_incident_case()

        # テストケース2: 問題管理
        test_problem_case()

        print("✨ 全テスト完了！\n")

    except Exception as e:
        print(f"\n❌ エラーが発生しました: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
