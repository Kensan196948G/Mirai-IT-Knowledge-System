#!/usr/bin/env python3
"""
ストレステスト用サンプルデータ生成スクリプト
大量のナレッジデータを生成します
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta
import random

# プロジェクトルート
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.mcp.sqlite_client import SQLiteClient


# サンプルタイトル生成用のパターン
INCIDENT_PATTERNS = [
    "サーバー障害: {system}システムで{error}が発生",
    "{service}サービス停止障害 - {error}",
    "アプリケーション{error}によるサービス影響",
    "{system}における{error}障害対応",
    "緊急: {service}で{error}を検知"
]

PROBLEM_PATTERNS = [
    "{system}における{issue}の根本原因分析",
    "繰り返し発生する{service}の{issue}問題",
    "{error}の恒久対策検討",
    "{system}パフォーマンス{issue}の調査",
    "{service}安定性向上のための{issue}分析"
]

CHANGE_PATTERNS = [
    "{system}の{action}作業計画",
    "{service}における{component}の{action}",
    "セキュリティ対策: {system}の{action}",
    "{component}{action}による機能改善",
    "定期メンテナンス: {system}の{action}"
]

REQUEST_PATTERNS = [
    "{service}へのアクセス権限申請",
    "{resource}の追加リクエスト",
    "{tool}の利用申請手順",
    "{service}アカウント発行依頼",
    "{resource}容量増設申請"
]

# パターン要素
SYSTEMS = ["Web", "DB", "API", "メール", "ファイル", "認証", "バックアップ", "監視", "ログ", "バッチ"]
SERVICES = ["VPN", "プリンター", "共有フォルダ", "Teams", "Slack", "Git", "CI/CD", "Wiki", "チケット", "カレンダー"]
ERRORS = ["503エラー", "タイムアウト", "メモリリーク", "接続エラー", "認証失敗", "レスポンス遅延", "デッドロック", "ディスク満杯"]
ISSUES = ["遅延", "不安定性", "リソース枯渇", "同期エラー", "データ不整合", "設定ミス"]
ACTIONS = ["アップグレード", "パッチ適用", "設定変更", "増設", "移行", "最適化"]
COMPONENTS = ["OS", "ミドルウェア", "ネットワーク機器", "ストレージ", "SSL証明書", "ライブラリ"]
RESOURCES = ["ストレージ", "メモリ", "CPU", "ライセンス", "アカウント"]
TOOLS = ["開発ツール", "分析ツール", "監視ツール", "バックアップツール"]

TAGS = [
    ["障害対応", "緊急"],
    ["パフォーマンス", "チューニング"],
    ["セキュリティ", "パッチ"],
    ["ネットワーク", "インフラ"],
    ["データベース", "SQL"],
    ["メンテナンス", "定期作業"],
    ["バックアップ", "リストア"],
    ["監視", "アラート"],
    ["アクセス制御", "権限"],
    ["リモートワーク", "VPN"]
]


def generate_content(title: str, itsm_type: str) -> str:
    """ナレッジ本文を生成"""
    if itsm_type == "Incident":
        return f"""## 発生事象
{title}

## 影響範囲
- 影響システム: 本番環境
- 影響時間: 約{random.randint(10, 120)}分
- 影響ユーザー: 約{random.randint(10, 500)}名

## 対応手順
1. ログ確認
2. 原因特定
3. 暫定対応実施
4. サービス復旧確認
5. 事後レポート作成

## 原因
{random.choice(['設定ミス', 'リソース不足', 'ソフトウェアバグ', 'ネットワーク障害', '外部サービス影響'])}

## 再発防止策
- 監視強化
- 設定レビュー
- 定期点検
"""
    elif itsm_type == "Problem":
        return f"""## 問題概要
{title}

## 発生頻度
過去{random.randint(1, 12)}ヶ月で{random.randint(3, 20)}回発生

## 根本原因分析
調査の結果、{random.choice(['設計不備', 'キャパシティ不足', 'プロセス未整備', 'ツール不足'])}が判明

## 恒久対策
1. アーキテクチャ見直し
2. 監視体制強化
3. 運用手順整備
4. 定期レビュー実施

## 実施予定
次期メンテナンス期間中に対応予定
"""
    elif itsm_type == "Change":
        return f"""## 変更内容
{title}

## 目的
{random.choice(['セキュリティ向上', 'パフォーマンス改善', '機能追加', '安定性向上'])}

## 実施計画
- 実施日時: {(datetime.now() + timedelta(days=random.randint(1, 60))).strftime('%Y-%m-%d %H:00')}
- ダウンタイム: 約{random.randint(0, 240)}分

## リスク評価
リスクレベル: {random.choice(['低', '中', '高'])}

## ロールバック手順
変更前の設定をバックアップ済み
"""
    else:  # Request
        return f"""## リクエスト内容
{title}

## 申請方法
1. 申請システムにログイン
2. 必要情報を入力
3. 上長承認取得
4. システム管理者が対応

## 処理時間
通常{random.randint(1, 10)}営業日

## 注意事項
- 業務上の必要性を明記
- セキュリティポリシー遵守
"""


def generate_knowledge_data(count: int, itsm_type: str = None) -> list:
    """ナレッジデータを生成"""
    knowledge_list = []

    for i in range(count):
        # ITSMタイプをランダムまたは指定
        if itsm_type:
            current_type = itsm_type
        else:
            current_type = random.choice(["Incident", "Problem", "Change", "Request"])

        # タイトル生成
        if current_type == "Incident":
            pattern = random.choice(INCIDENT_PATTERNS)
            title = pattern.format(
                system=random.choice(SYSTEMS),
                service=random.choice(SERVICES),
                error=random.choice(ERRORS)
            )
        elif current_type == "Problem":
            pattern = random.choice(PROBLEM_PATTERNS)
            title = pattern.format(
                system=random.choice(SYSTEMS),
                service=random.choice(SERVICES),
                issue=random.choice(ISSUES),
                error=random.choice(ERRORS)
            )
        elif current_type == "Change":
            pattern = random.choice(CHANGE_PATTERNS)
            title = pattern.format(
                system=random.choice(SYSTEMS),
                service=random.choice(SERVICES),
                component=random.choice(COMPONENTS),
                action=random.choice(ACTIONS)
            )
        else:  # Request
            pattern = random.choice(REQUEST_PATTERNS)
            title = pattern.format(
                service=random.choice(SERVICES),
                resource=random.choice(RESOURCES),
                tool=random.choice(TOOLS)
            )

        # タイトルに番号を追加してユニーク性を確保
        title = f"{title} #{i+1:04d}"

        # 本文生成
        content = generate_content(title, current_type)

        # タグ選択
        tags = random.choice(TAGS) + [current_type]

        knowledge_list.append({
            "title": title,
            "content": content,
            "itsm_type": current_type,
            "tags": tags
        })

    return knowledge_list


def insert_data(db_path: str, count: int, itsm_type: str = None):
    """データを投入"""
    import sqlite3
    import json

    print("🚀 ストレステスト用データ生成")
    print("=" * 80)
    print(f"データベース: {db_path}")
    print(f"生成件数: {count}件")
    if itsm_type:
        print(f"ITSMタイプ: {itsm_type}")
    print()

    # データ生成
    print("📝 データ生成中...")
    knowledge_data = generate_knowledge_data(count, itsm_type)
    print(f"✅ {len(knowledge_data)}件のデータを生成しました")
    print()

    # DB投入（直接SQLiteを使用）
    print("💾 データベースに投入中...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    success_count = 0
    error_count = 0

    for i, data in enumerate(knowledge_data, 1):
        try:
            cursor.execute("""
                INSERT INTO knowledge_entries (
                    title, itsm_type, content, tags,
                    summary_technical, summary_non_technical,
                    created_by, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                data["title"],
                data["itsm_type"],
                data["content"],
                json.dumps(data["tags"], ensure_ascii=False),
                f"技術要約: {data['title'][:50]}",
                f"概要: {data['title'][:50]}",
                "stress_test_generator"
            ))
            success_count += 1

            # 進捗表示
            if i % 100 == 0:
                conn.commit()
                print(f"  進捗: {i}/{count}件 ({i*100//count}%)")

        except Exception as e:
            error_count += 1
            if error_count <= 5:  # 最初の5件のみエラー詳細を表示
                print(f"  ⚠️ エラー ({i}件目): {e}")

    conn.commit()

    print()
    print("=" * 80)
    print("📊 投入結果:")
    print(f"   成功: {success_count}件")
    print(f"   エラー: {error_count}件")
    print()

    # 確認クエリ
    print("📈 データベース確認:")
    cursor.execute("SELECT itsm_type, COUNT(*) FROM knowledge_entries GROUP BY itsm_type ORDER BY COUNT(*) DESC")
    rows = cursor.fetchall()
    for row in rows:
        print(f"   {row[0]}: {row[1]}件")

    cursor.execute("SELECT COUNT(*) FROM knowledge_entries")
    total = cursor.fetchone()[0]
    print(f"   ---")
    print(f"   合計: {total}件")

    conn.close()

    print()
    print("✨ データ投入完了！")


def main():
    parser = argparse.ArgumentParser(
        description='ストレステスト用サンプルデータ生成',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--count', '-c', type=int, default=1000,
                        help='生成件数 (default: 1000)')
    parser.add_argument('--db-path', type=str,
                        default=str(project_root / 'db' / 'knowledge_dev.db'),
                        help='データベースパス (default: db/knowledge_dev.db)')
    parser.add_argument('--itsm-type', choices=['Incident', 'Problem', 'Change', 'Request'],
                        help='特定のITSMタイプのみ生成')

    args = parser.parse_args()

    # データベースファイルの確認
    db_path = Path(args.db_path)
    if not db_path.exists():
        print(f"❌ データベースが見つかりません: {db_path}")
        print(f"   先に init_db.py を実行してください")
        sys.exit(1)

    insert_data(str(db_path), args.count, args.itsm_type)


if __name__ == "__main__":
    main()
