#!/usr/bin/env python3
"""
VPN接続エラー対応ナレッジをQAサブエージェントで分析
"""

import json
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from src.subagents.qa import QASubAgent


def main():
    # QAサブエージェントのインスタンス化
    qa_agent = QASubAgent()

    # 入力データの準備
    input_data = {
        "title": "VPN接続エラー対応",
        "content": "社外からVPN接続できない問題。原因はVPNクライアント証明書の期限切れ。解決策は証明書の更新手順に従い新しい証明書をインストールする。",
        "existing_knowledge": [
            {
                "id": "00014",
                "title": "新規ユーザーのVPNアクセス権限申請",
                "content": """
## 申請内容
新規入社社員に対するVPNアクセス権限の付与を申請します。

## 申請者情報
- 申請者: 人事部 田中
- 申請日: 2026-01-08

## 対象ユーザー
- 氏名: 山田太郎
- 社員番号: EMP-2026-001
- 部署: 開発部
- 入社日: 2026-01-15

## 必要なアクセス権限
1. **VPN接続**
   - 接続プロトコル: SSL-VPN
   - アクセス範囲: 開発環境セグメント

2. **アクセス可能リソース**
   - 開発用サーバー(dev-server-01〜05)
   - Git リポジトリサーバー
   - 開発用データベース

3. **利用期間**
   - 開始日: 2026-01-15
   - 終了日: 無期限(退職まで)

## セキュリティ要件
- 多要素認証(MFA)必須
- パスワードポリシー準拠
- 定期的なパスワード変更(90日ごと)

## 承認フロー
1. 直属上長承認: ✅ 完了(2026-01-08)
2. 情報セキュリティ部門承認: 待機中
3. システム管理者による設定: 承認後実施

## 作業内容
1. ADアカウント作成
2. VPN証明書発行
3. アクセス権限設定
4. MFA設定支援
5. 利用マニュアル送付

## 期限
入社日(2026-01-15)までに設定完了必須
"""
            },
            {
                "id": "00007",
                "title": "新規ユーザーのVPNアクセス権限申請",
                "content": """
## 申請内容
新規入社社員に対するVPNアクセス権限の付与を申請します。

## 申請者情報
- 申請者: 人事部 田中
- 申請日: 2026-01-08

## 対象ユーザー
- 氏名: 山田太郎
- 社員番号: EMP-2026-001
- 部署: 開発部
- 入社日: 2026-01-15

## 必要なアクセス権限
1. **VPN接続**
   - 接続プロトコル: SSL-VPN
   - アクセス範囲: 開発環境セグメント

2. **アクセス可能リソース**
   - 開発用サーバー(dev-server-01〜05)
   - Git リポジトリサーバー
   - 開発用データベース

3. **利用期間**
   - 開始日: 2026-01-15
   - 終了日: 無期限(退職まで)

## セキュリティ要件
- 多要素認証(MFA)必須
- パスワードポリシー準拠
- 定期的なパスワード変更(90日ごと)

## 承認フロー
1. 直属上長承認: ✅ 完了(2026-01-08)
2. 情報セキュリティ部門承認: 待機中
3. システム管理者による設定: 承認後実施

## 作業内容
1. ADアカウント作成
2. VPN証明書発行
3. アクセス権限設定
4. MFA設定支援
5. 利用マニュアル送付

## 期限
入社日(2026-01-15)までに設定完了必須
"""
            }
        ]
    }

    # QAサブエージェントで処理
    print("=" * 80)
    print("QAサブエージェント分析開始")
    print("=" * 80)
    print(f"\n入力タイトル: {input_data['title']}")
    print(f"入力内容: {input_data['content']}\n")

    result = qa_agent.process(input_data)

    # 結果をJSON形式で整形
    analysis_result = {
        "status": result.status,
        "message": result.message,
        "analysis": {
            "1_completeness_check": {
                "overall_rate": result.data["completeness"]["rate"],
                "passed_count": result.data["completeness"]["passed_count"],
                "total_count": result.data["completeness"]["total_count"],
                "details": result.data["completeness"]["checks"]
            },
            "2_duplicate_detection": {
                "high_similarity_count": result.data["duplicates"]["high_similarity_count"],
                "total_similar_count": result.data["duplicates"]["total_similar_count"],
                "similar_knowledge": result.data["duplicates"]["similar_knowledge"]
            },
            "3_quality_score": {
                "score": result.data["quality_score"]["score"],
                "level": result.data["quality_score"]["level"],
                "factors": result.data["quality_score"]["factors"]
            },
            "4_improvement_suggestions": result.data["improvements"]
        }
    }

    # JSON出力
    print("=" * 80)
    print("分析結果 (JSON形式)")
    print("=" * 80)
    print(json.dumps(analysis_result, indent=2, ensure_ascii=False))

    # サマリー出力
    print("\n" + "=" * 80)
    print("サマリー")
    print("=" * 80)
    print(f"ステータス: {result.status}")
    print(f"メッセージ: {result.message}")
    print(f"\n【1. 完全性チェック】")
    print(f"  - 完全性スコア: {result.data['completeness']['rate']:.0%}")
    print(f"  - 合格項目: {result.data['completeness']['passed_count']}/{result.data['completeness']['total_count']}")
    for check in result.data["completeness"]["checks"]:
        status_mark = "✅" if check["passed"] else "❌"
        print(f"  {status_mark} {check['item']}: {check['message']}")

    print(f"\n【2. 重複検知】")
    print(f"  - 高類似度(80%以上): {result.data['duplicates']['high_similarity_count']}件")
    print(f"  - 類似ナレッジ合計: {result.data['duplicates']['total_similar_count']}件")
    for similar in result.data["duplicates"]["similar_knowledge"]:
        print(f"  - {similar['knowledge_id']}: {similar['title']}")
        print(f"    類似度={similar['overall_similarity']:.0%} (タイトル={similar['title_similarity']:.0%}, 内容={similar['content_similarity']:.0%})")

    print(f"\n【3. 品質スコア】")
    print(f"  - 総合スコア: {result.data['quality_score']['score']:.2f}/1.0 ({result.data['quality_score']['score']:.0%})")
    print(f"  - 品質レベル: {result.data['quality_score']['level']}")
    print(f"  - 要因分析:")
    for factor in result.data["quality_score"]["factors"]:
        print(f"    • {factor['factor']}: 重み={factor['weight']:.0%}, 貢献度={factor['contribution']:.2f}")

    print(f"\n【4. 改善提案】")
    if result.data["improvements"]:
        for i, improvement in enumerate(result.data["improvements"], 1):
            print(f"  {i}. {improvement}")
    else:
        print("  特になし (高品質なナレッジです)")

    print("\n" + "=" * 80)

    # 結果をファイルに保存
    output_file = Path(__file__).parent / "vpn_knowledge_qa_analysis.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(analysis_result, f, indent=2, ensure_ascii=False)
    print(f"\n結果を保存しました: {output_file}")


if __name__ == "__main__":
    main()
