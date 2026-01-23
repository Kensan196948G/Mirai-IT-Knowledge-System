#!/usr/bin/env python3
"""
Database Initialization Script
データベース初期化スクリプト（環境対応版）

Usage:
    python3 scripts/init_db.py --env development --with-samples
    python3 scripts/init_db.py --env production --no-samples
    python3 scripts/init_db.py --env test --with-samples
"""

import argparse
import sqlite3
import sys
from pathlib import Path
from datetime import datetime

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def get_db_path(environment: str) -> Path:
    """環境に応じたデータベースパスを取得"""
    if environment == 'development':
        return PROJECT_ROOT / 'db' / 'knowledge_dev.db'
    elif environment == 'production':
        return PROJECT_ROOT / 'db' / 'knowledge.db'
    elif environment == 'test':
        return PROJECT_ROOT / 'db' / 'knowledge_test.db'
    else:
        raise ValueError(f"Unknown environment: {environment}")


def create_schema(conn: sqlite3.Connection):
    """データベーススキーマを作成"""
    cursor = conn.cursor()

    # ナレッジテーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS knowledge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            itsm_type TEXT NOT NULL,
            tags TEXT,
            created_by TEXT DEFAULT 'system',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'active',
            view_count INTEGER DEFAULT 0,
            summary TEXT,
            related_ids TEXT
        )
    ''')

    # ITSMタグテーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS itsm_tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            itsm_type TEXT NOT NULL,
            description TEXT,
            keywords TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # ワークフロー実行テーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS workflow_executions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            knowledge_id INTEGER,
            workflow_type TEXT NOT NULL,
            status TEXT DEFAULT 'running',
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            result_summary TEXT,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (knowledge_id) REFERENCES knowledge(id)
        )
    ''')

    # SubAgentログテーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subagent_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            execution_id INTEGER NOT NULL,
            agent_name TEXT NOT NULL,
            input_data TEXT,
            output_data TEXT,
            execution_time_ms INTEGER,
            status TEXT DEFAULT 'success',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (execution_id) REFERENCES workflow_executions(id)
        )
    ''')

    # Hookログテーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hook_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            execution_id INTEGER NOT NULL,
            hook_name TEXT NOT NULL,
            hook_type TEXT NOT NULL,
            input_data TEXT,
            output_data TEXT,
            execution_time_ms INTEGER,
            status TEXT DEFAULT 'success',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (execution_id) REFERENCES workflow_executions(id)
        )
    ''')

    # フィードバックテーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS knowledge_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            knowledge_id INTEGER NOT NULL,
            user_id TEXT,
            rating INTEGER CHECK(rating >= 1 AND rating <= 5),
            feedback_type TEXT,
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (knowledge_id) REFERENCES knowledge(id)
        )
    ''')

    # システムフィードバックテーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            feedback_category TEXT,
            priority TEXT DEFAULT 'medium',
            status TEXT DEFAULT 'open',
            user_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP
        )
    ''')

    # 使用統計テーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usage_statistics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            knowledge_id INTEGER NOT NULL,
            action_type TEXT NOT NULL,
            user_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (knowledge_id) REFERENCES knowledge(id)
        )
    ''')

    # 検索履歴テーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            search_query TEXT NOT NULL,
            search_type TEXT DEFAULT 'keyword',
            filters TEXT,
            results_count INTEGER,
            user_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 会話セッションテーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversation_sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            knowledge_id INTEGER,
            FOREIGN KEY (knowledge_id) REFERENCES knowledge(id)
        )
    ''')

    # 会話メッセージテーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversation_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES conversation_sessions(id)
        )
    ''')

    # インデックス作成
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_knowledge_itsm_type ON knowledge(itsm_type)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_knowledge_created_at ON knowledge(created_at)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_knowledge_status ON knowledge(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_workflow_executions_status ON workflow_executions(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_subagent_logs_execution_id ON subagent_logs(execution_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_hook_logs_execution_id ON hook_logs(execution_id)')

    conn.commit()
    print("✅ スキーマ作成完了")


def insert_itsm_tags(conn: sqlite3.Connection):
    """ITSMタグの初期データを挿入"""
    cursor = conn.cursor()

    itsm_tags = [
        ('Incident', 'Incident', '障害・インシデント対応', 'エラー,障害,復旧,緊急'),
        ('Problem', 'Problem', '問題管理・根本原因分析', '原因,分析,恒久対策'),
        ('Change', 'Change', '変更管理', '変更,移行,アップグレード'),
        ('Release', 'Release', 'リリース管理', 'リリース,展開,デプロイ'),
        ('Service Request', 'Service Request', 'サービス要求', '申請,依頼,リクエスト'),
        ('その他', 'Other', 'その他のナレッジ', '一般,情報,参考'),
    ]

    for name, itsm_type, description, keywords in itsm_tags:
        cursor.execute('''
            INSERT OR IGNORE INTO itsm_tags (name, itsm_type, description, keywords)
            VALUES (?, ?, ?, ?)
        ''', (name, itsm_type, description, keywords))

    conn.commit()
    print("✅ ITSMタグ挿入完了")


def insert_sample_data(conn: sqlite3.Connection):
    """サンプルデータを挿入（開発環境用）"""
    cursor = conn.cursor()

    # サンプルナレッジデータ
    sample_knowledge = [
        {
            'title': 'VPN接続エラー「認証失敗」の対処法',
            'content': '''## 問題
VPN接続時に「認証に失敗しました」エラーが発生する。

## 原因
1. パスワードの有効期限切れ
2. 多要素認証（MFA）トークンの同期ズレ
3. VPNクライアントのキャッシュ破損

## 解決手順
1. Active Directoryでパスワード有効期限を確認
2. MFAトークンを再同期（管理者に依頼）
3. VPNクライアントの設定をリセット

## 予防策
- パスワード有効期限の通知設定を有効化
- MFAバックアップコードを安全に保管''',
            'itsm_type': 'Incident',
            'tags': 'VPN,認証,ネットワーク',
            'created_by': 'sample_data'
        },
        {
            'title': 'メールサーバー高負荷の根本原因分析',
            'content': '''## 問題の概要
メールサーバーのCPU使用率が90%を超え、メール送受信に遅延が発生。

## 調査結果
### 直接原因
- スパムメールの大量受信（1時間あたり10,000通以上）

### 根本原因
- スパムフィルタのルール更新が3ヶ月間行われていなかった
- 外部IPブラックリストの同期が無効化されていた

## 恒久対策
1. スパムフィルタルールの自動更新設定
2. IPブラックリスト同期の再有効化
3. メールサーバー監視の閾値見直し''',
            'itsm_type': 'Problem',
            'tags': 'メール,パフォーマンス,スパム,監視',
            'created_by': 'sample_data'
        },
        {
            'title': 'Windows 11 23H2へのアップグレード手順',
            'content': '''## 変更概要
社内PCのWindows 11 22H2から23H2へのアップグレード

## 前提条件
- TPM 2.0対応
- セキュアブート有効
- 空きディスク容量20GB以上

## 作業手順
### 1. 事前準備
- 重要データのバックアップ
- ドライバー互換性確認

### 2. アップグレード実行
Windows Updateから実行

### 3. 事後確認
- 基幹システム接続確認
- プリンター動作確認
- VPN接続確認''',
            'itsm_type': 'Change',
            'tags': 'Windows,アップグレード,OS',
            'created_by': 'sample_data'
        },
        {
            'title': 'セキュリティパッチ2024年1月版リリース',
            'content': '''## リリース概要
Microsoft 2024年1月セキュリティ更新プログラム

## 対象システム
- Windows Server 2019/2022
- SQL Server 2019
- Exchange Server 2019

## 展開スケジュール
| 環境 | 日付 |
|------|------|
| 開発環境 | 1/10 |
| ステージング | 1/15 |
| 本番環境 | 1/20 |''',
            'itsm_type': 'Release',
            'tags': 'セキュリティ,パッチ,Windows',
            'created_by': 'sample_data'
        },
        {
            'title': '新入社員向けPC初期設定依頼フロー',
            'content': '''## サービス概要
新入社員向けPCの初期設定とアカウント発行

## 申請方法
1. ServiceNowからリクエスト起票
2. 上長承認
3. IT部門にて作業実施

## 標準リードタイム
- 通常: 5営業日
- 緊急: 2営業日（要追加承認）''',
            'itsm_type': 'Service Request',
            'tags': '新入社員,PC,セットアップ',
            'created_by': 'sample_data'
        },
        {
            'title': 'ファイルサーバー容量不足対応',
            'content': '''## インシデント概要
ファイルサーバーの容量が95%に達し、新規ファイル保存ができない状態

## 緊急対応
1. 不要な一時ファイルの削除
2. 古いバックアップファイルのアーカイブ
3. 大容量ファイルの特定と移動

## 根本対策
1. ストレージ増設（500GB追加）
2. 自動クリーンアップスクリプトの導入''',
            'itsm_type': 'Incident',
            'tags': 'ストレージ,ファイルサーバー,容量',
            'created_by': 'sample_data'
        },
        {
            'title': 'ネットワーク構成変更（VLAN追加）',
            'content': '''## 変更概要
新規部門設立に伴うVLAN追加

## 変更内容
- VLAN ID: 150
- サブネット: 192.168.150.0/24
- ゲートウェイ: 192.168.150.1

## 作業手順
1. スイッチへのVLAN設定追加
2. ルーター設定更新
3. DHCPスコープ追加
4. ファイアウォールルール追加
5. 通信テスト''',
            'itsm_type': 'Change',
            'tags': 'ネットワーク,VLAN,構成変更',
            'created_by': 'sample_data'
        }
    ]

    for knowledge in sample_knowledge:
        cursor.execute('''
            INSERT INTO knowledge (title, content, itsm_type, tags, created_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            knowledge['title'],
            knowledge['content'],
            knowledge['itsm_type'],
            knowledge['tags'],
            knowledge['created_by'],
            datetime.now().isoformat()
        ))

    conn.commit()
    print(f"✅ サンプルデータ挿入完了（{len(sample_knowledge)}件）")


def init_database(environment: str, with_samples: bool = False, force: bool = False):
    """データベースを初期化"""
    db_path = get_db_path(environment)

    # ディレクトリ作成
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # 既存ファイルの確認
    if db_path.exists() and not force:
        print(f"⚠️  データベースが既に存在します: {db_path}")
        response = input("上書きしますか？ (y/N): ")
        if response.lower() != 'y':
            print("キャンセルしました")
            return False
        db_path.unlink()

    # データベース作成
    print(f"\n🗄️  データベース初期化: {environment}")
    print(f"   パス: {db_path}")
    print(f"   サンプルデータ: {'あり' if with_samples else 'なし'}")

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    try:
        create_schema(conn)
        insert_itsm_tags(conn)

        if with_samples:
            insert_sample_data(conn)

        # 統計情報表示
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM knowledge")
        knowledge_count = cursor.fetchone()['count']
        cursor.execute("SELECT COUNT(*) as count FROM itsm_tags")
        tag_count = cursor.fetchone()['count']

        print(f"\n📊 データベース統計:")
        print(f"   ナレッジ件数: {knowledge_count}")
        print(f"   ITSMタグ件数: {tag_count}")

        print(f"\n✅ データベース初期化完了: {db_path}")
        return True

    except Exception as e:
        print(f"\n❌ エラー: {e}")
        return False

    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description='データベース初期化スクリプト（環境対応版）')
    parser.add_argument('--env', '-e', choices=['development', 'production', 'test'],
                       default='development', help='環境名（default: development）')
    parser.add_argument('--with-samples', action='store_true',
                       help='サンプルデータを挿入')
    parser.add_argument('--no-samples', action='store_true',
                       help='サンプルデータを挿入しない（本番環境用）')
    parser.add_argument('--force', '-f', action='store_true',
                       help='確認なしで上書き')

    args = parser.parse_args()

    # サンプルデータの判定
    if args.no_samples:
        with_samples = False
    elif args.with_samples:
        with_samples = True
    else:
        # デフォルト: 開発環境はサンプルあり、本番環境はサンプルなし
        with_samples = args.env == 'development'

    # 初期化実行
    success = init_database(args.env, with_samples, args.force)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
