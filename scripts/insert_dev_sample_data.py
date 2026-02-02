#!/usr/bin/env python3
"""
開発環境用サンプルデータ投入スクリプト
ナレッジ10件 + FAQ10件を投入
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.mcp.sqlite_client import SQLiteClient

# 開発環境用DBパス
DEV_DB_PATH = str(project_root / "db" / "knowledge_dev.db")


# ============================================================
# ナレッジサンプルデータ（10件）
# ============================================================
KNOWLEDGE_DATA = [
    {
        "title": "Webサーバー503エラー障害対応",
        "content": """## 発生事象
2026-01-15 10:30 本番WebサーバーでHTTP 503エラーが発生。ユーザーからのアクセス不可。

## 影響範囲
- 影響システム: 社内ポータルサイト
- 影響ユーザー: 全社員約300名
- 影響時間: 10:30〜11:15（約45分）

## 対応手順
1. Apacheエラーログの確認
2. MaxRequestWorkersが上限に到達していることを確認
3. Apache設定を変更（MaxRequestWorkers: 150→300）
4. サービス再起動
5. 動作確認

## 原因
同時接続数が設定上限を超過

## 再発防止策
- 接続数監視アラートの設定
- 定期的な負荷テストの実施""",
        "itsm_type": "Incident",
        "tags": ["Web", "Apache", "503エラー", "障害対応"]
    },
    {
        "title": "データベースパフォーマンス低下問題",
        "content": """## 問題概要
過去1ヶ月で5件のDB遅延インシデントが発生。根本原因の特定が必要。

## 関連インシデント
INC-001, INC-003, INC-007, INC-012, INC-015

## 根本原因分析
1. インデックス不足（users_tableにINDEXなし）
2. N+1クエリの発生（ORMの設定不備）
3. スロークエリ（3秒以上）が日次で100件以上

## 恒久対策
1. 必要なインデックスを追加
2. ORMのEager Loadingを適用
3. スロークエリログの監視設定

## 実施スケジュール
2026-02-01 計画停止にて対応予定""",
        "itsm_type": "Problem",
        "tags": ["データベース", "パフォーマンス", "MySQL", "チューニング"]
    },
    {
        "title": "Active Directory グループポリシー変更",
        "content": """## 変更内容
パスワードポリシーの強化対応

## 変更項目
- 最小パスワード長: 8文字→12文字
- 複雑性要件: 有効化
- パスワード履歴: 12世代
- 有効期限: 90日→60日

## 影響範囲
全社員（約500名）

## 実施日時
2026-01-20 02:00（計画メンテナンス時間）

## ロールバック手順
GPOを旧設定に復元（バックアップ済み）

## 承認
情報セキュリティ委員会承認済み（2026-01-10）""",
        "itsm_type": "Change",
        "tags": ["ActiveDirectory", "セキュリティ", "パスワードポリシー"]
    },
    {
        "title": "メールサーバー証明書更新",
        "content": """## 作業概要
メールサーバーのSSL証明書が2026-02-28に期限切れのため更新

## 対象サーバー
- mail-01.example.com
- mail-02.example.com

## 作業手順
1. Let's Encryptで新証明書取得
2. ステージング環境でテスト
3. 本番環境に適用
4. メールクライアントでの接続確認

## 作業予定
2026-02-15 03:00（深夜メンテナンス時間）

## リスク
証明書エラーでメール送受信不可の可能性（ロールバック対応可）""",
        "itsm_type": "Change",
        "tags": ["メール", "SSL", "証明書", "Postfix"]
    },
    {
        "title": "VPN接続障害（認証サーバー過負荷）",
        "content": """## 発生事象
2026-01-10 09:00 リモートワーク開始時間帯にVPN接続できない報告が多発

## 影響
- 影響ユーザー: リモートワーク社員約150名
- 業務影響: 約2時間の業務遅延

## 原因
RADIUS認証サーバーの同時認証処理が上限超過

## 対応
1. RADIUS設定の同時接続数を増加
2. サーバーリソース（メモリ）を増強
3. 認証キャッシュ時間を延長

## 恒久対策
RADIUS冗長化構成への移行を検討中""",
        "itsm_type": "Incident",
        "tags": ["VPN", "認証", "RADIUS", "リモートワーク"]
    },
    {
        "title": "ファイルサーバーディスク容量逼迫",
        "content": """## 発生事象
ファイルサーバーのディスク使用率が90%を超過

## 現状
- 総容量: 10TB
- 使用量: 9.2TB（92%）
- 空き: 800GB

## 対応
1. 古いファイル（2年以上未アクセス）をアーカイブストレージへ移行
2. 重複ファイルの検出・削除
3. 部門別クォータの見直し

## 今後の計画
- 2026-03末までにストレージ増設（+5TB）
- ファイル自動アーカイブポリシーの導入""",
        "itsm_type": "Incident",
        "tags": ["ファイルサーバー", "ストレージ", "容量管理"]
    },
    {
        "title": "社内Wikiシステムアップグレード",
        "content": """## アップグレード内容
Confluenceを6.xから8.xへメジャーアップグレード

## 主な変更点
- UIの刷新
- パフォーマンス向上（20%高速化）
- 新機能: リアルタイム共同編集

## 移行計画
1. ステージング環境構築・テスト
2. データ移行テスト
3. 本番移行（計画停止4時間）
4. ユーザー説明会実施

## スケジュール
- テスト: 2026-02-01〜14
- 本番移行: 2026-02-20（土曜日）""",
        "itsm_type": "Release",
        "tags": ["Confluence", "Wiki", "アップグレード"]
    },
    {
        "title": "セキュリティパッチ適用（緊急）",
        "content": """## 概要
CVE-2026-XXXXに対応する緊急セキュリティパッチ適用

## 脆弱性情報
- CVSSスコア: 9.8（Critical）
- 影響: リモートコード実行の可能性
- 対象: Apache Log4j

## 対象システム
- アプリケーションサーバー 5台
- バッチサーバー 2台

## 適用日時
2026-01-12 01:00（緊急対応）

## 確認事項
- 全システムでのパッチ適用確認
- 動作確認テスト実施済み""",
        "itsm_type": "Change",
        "tags": ["セキュリティ", "パッチ", "脆弱性", "Log4j"]
    },
    {
        "title": "バックアップジョブ失敗調査",
        "content": """## 問題
週次フルバックアップが3週連続で失敗

## 失敗原因
1. ディスクI/O待ちによるタイムアウト
2. 同時実行される他ジョブとの競合
3. バックアップ対象データ量の増加

## 対策
1. バックアップスケジュールの見直し
2. 差分バックアップの導入
3. ストレージのIOPS向上

## 実施計画
2026-01-25 新バックアップ構成に移行""",
        "itsm_type": "Problem",
        "tags": ["バックアップ", "ジョブ管理", "ストレージ"]
    },
    {
        "title": "ネットワーク機器ファームウェア更新",
        "content": """## 更新内容
コアスイッチ・ルーターのファームウェア更新

## 対象機器
- Core-SW-01, Core-SW-02（Cisco Catalyst）
- Router-01, Router-02（Cisco ISR）

## 更新理由
- セキュリティ修正
- バグフィックス
- 新機能追加

## 作業計画
- 日時: 2026-02-01 02:00-06:00
- 方式: ローリングアップデート（冗長構成維持）
- ダウンタイム: 各機器5分程度

## ロールバック
旧ファームウェアの即時復元可能""",
        "itsm_type": "Change",
        "tags": ["ネットワーク", "Cisco", "ファームウェア"]
    }
]


# ============================================================
# FAQサンプルデータ（10件）
# ============================================================
FAQ_DATA = [
    {
        "title": "パスワードを忘れた場合の対処法",
        "content": """## 質問
社内システムのパスワードを忘れてしまいました。どうすればいいですか？

## 回答
以下の手順でパスワードをリセットできます：

1. **セルフサービスポータルを利用**
   - https://password.example.com にアクセス
   - 社員番号とメールアドレスを入力
   - 登録済みメールに届くリセットリンクからリセット

2. **ヘルプデスクに連絡**
   - 内線: 9999
   - メール: helpdesk@example.com
   - 本人確認後、仮パスワードを発行

## 注意事項
- パスワードは90日ごとに変更が必要です
- 過去12回分のパスワードは再利用できません""",
        "itsm_type": "Request",
        "tags": ["パスワード", "FAQ", "アカウント"]
    },
    {
        "title": "VPN接続方法（Windows）",
        "content": """## 質問
自宅からVPNに接続する方法を教えてください。

## 回答
### 初回セットアップ
1. VPNクライアント（Cisco AnyConnect）をダウンロード
   - ソフトウェアポータル: https://software.example.com
2. インストール後、接続先を設定
   - サーバー: vpn.example.com

### 接続手順
1. AnyConnectを起動
2. 「vpn.example.com」を選択して「Connect」
3. 社員番号とパスワードを入力
4. MFAコード（Google Authenticatorから取得）を入力
5. 「Connected」と表示されたら接続完了

## トラブルシューティング
- 接続できない場合は、ファイアウォール設定を確認
- それでも解決しない場合はヘルプデスクへ""",
        "itsm_type": "Request",
        "tags": ["VPN", "FAQ", "リモートワーク", "接続方法"]
    },
    {
        "title": "プリンター追加方法",
        "content": """## 質問
新しいプリンターを自分のPCに追加するにはどうすればいいですか？

## 回答
### 手順
1. 「設定」→「デバイス」→「プリンターとスキャナー」
2. 「プリンターまたはスキャナーを追加します」をクリック
3. ネットワークプリンター一覧から選択

### 主なプリンター名
- 3F複合機: PRINT-3F-MFP01
- 4F複合機: PRINT-4F-MFP01
- 5F複合機: PRINT-5F-MFP01

### 表示されない場合
「プリンターが一覧にない場合」をクリックし、以下を入力：
- `\\\\printserver\\プリンター名`""",
        "itsm_type": "Request",
        "tags": ["プリンター", "FAQ", "設定"]
    },
    {
        "title": "Teams会議の予約方法",
        "content": """## 質問
Microsoft Teamsで会議を予約するにはどうすればいいですか？

## 回答
### Outlookから予約（推奨）
1. Outlookカレンダーを開く
2. 「新しいTeams会議」をクリック
3. 件名、日時、参加者を入力
4. 「送信」で招待を送付

### Teamsから予約
1. Teamsの「カレンダー」を開く
2. 右上の「新しい会議」をクリック
3. 必要事項を入力して「保存」

## Tips
- 外部参加者がいる場合は「ロビーで待機」設定を確認
- 録画する場合は事前に参加者へ周知必須""",
        "itsm_type": "Request",
        "tags": ["Teams", "会議", "FAQ", "Microsoft365"]
    },
    {
        "title": "ファイル共有の権限申請",
        "content": """## 質問
共有フォルダへのアクセス権限を申請したいです。

## 回答
### 申請方法
1. 社内申請システム（https://request.example.com）にログイン
2. 「アクセス権限申請」を選択
3. 以下を入力：
   - フォルダパス
   - 必要な権限（読み取り/書き込み）
   - 申請理由
4. 上長承認後、システム管理者が設定

### 処理時間
- 通常: 2営業日以内
- 緊急時: ヘルプデスクに連絡

### 注意事項
- 個人情報を含むフォルダは追加承認が必要""",
        "itsm_type": "Request",
        "tags": ["ファイル共有", "権限", "FAQ", "申請"]
    },
    {
        "title": "社用PCのバックアップ方法",
        "content": """## 質問
重要なファイルをバックアップする方法を教えてください。

## 回答
### 推奨バックアップ先
1. **OneDrive（自動同期）**
   - デスクトップ、ドキュメントは自動バックアップ
   - 容量: 1TB

2. **共有フォルダ**
   - 部門別共有フォルダを利用
   - パス: `\\\\fileserver\\部門名`

### 手動バックアップ
重要ファイルは以下にもコピーを保管：
- USBドライブ（暗号化必須）
- OneDriveの「バックアップ」フォルダ

### 注意
- ローカルのみに保存は避けてください
- 機密情報の外部持ち出しは申請必要""",
        "itsm_type": "Request",
        "tags": ["バックアップ", "OneDrive", "FAQ", "データ保護"]
    },
    {
        "title": "メール署名の設定方法",
        "content": """## 質問
Outlookでメール署名を設定するにはどうすればいいですか？

## 回答
### 設定手順
1. Outlookを開く
2. 「ファイル」→「オプション」→「メール」
3. 「署名」ボタンをクリック
4. 「新規作成」で署名を作成

### 署名テンプレート
```
─────────────────────
株式会社サンプル
情報システム部 山田太郎
TEL: 03-XXXX-XXXX（内線: 1234）
Email: yamada@example.com
─────────────────────
```

### 自動挿入設定
- 「新しいメッセージ」: 作成した署名を選択
- 「返信/転送」: 必要に応じて設定""",
        "itsm_type": "Request",
        "tags": ["Outlook", "メール", "署名", "FAQ"]
    },
    {
        "title": "リモートデスクトップ接続方法",
        "content": """## 質問
自宅から会社のPCにリモートデスクトップで接続したいです。

## 回答
### 前提条件
- VPN接続済みであること
- 会社PCの電源がON（WoL設定済みの場合は起動可）

### 接続手順
1. VPNに接続
2. 「リモートデスクトップ接続」を起動
3. 会社PCのIPアドレスまたはホスト名を入力
   - 例: PC-YAMADA.corp.example.com
4. 社内の資格情報でログイン

### 接続できない場合
- ファイアウォール例外設定を確認
- 会社PCがスリープになっていないか確認
- VPN接続状況を確認""",
        "itsm_type": "Request",
        "tags": ["リモートデスクトップ", "RDP", "FAQ", "リモートワーク"]
    },
    {
        "title": "ソフトウェアインストール申請",
        "content": """## 質問
業務に必要なソフトウェアをインストールしたいです。

## 回答
### 申請方法
1. ソフトウェアカタログ（https://software.example.com）を確認
2. カタログにある場合：そのままダウンロード可能
3. カタログにない場合：申請が必要

### 申請フロー
1. 「ソフトウェア追加申請」フォームに記入
2. 上長承認
3. 情報セキュリティ部門審査
4. 承認後、インストール許可

### 処理時間
- カタログ内: 即時利用可能
- 新規申請: 5〜10営業日

### 注意事項
- フリーソフトもセキュリティ審査が必要
- 無断インストールはポリシー違反""",
        "itsm_type": "Request",
        "tags": ["ソフトウェア", "インストール", "申請", "FAQ"]
    },
    {
        "title": "Wi-Fi接続トラブル対処法",
        "content": """## 質問
社内Wi-Fiに接続できません。どうすればいいですか？

## 回答
### 基本的な対処法
1. **Wi-Fiを一度オフにして再度オン**
2. **正しいSSIDを選択**
   - 社員用: CORP-WIFI
   - ゲスト用: GUEST-WIFI
3. **パスワード確認**
   - 社員用: ADパスワードと同じ
   - ゲスト用: 当日発行のパスワード

### それでも接続できない場合
1. 「ネットワーク設定のリセット」を実行
2. 保存済みネットワークを削除して再接続
3. 他の端末で接続できるか確認

### ヘルプデスクに連絡する際の情報
- PCの機種名
- エラーメッセージ
- いつから発生しているか""",
        "itsm_type": "Request",
        "tags": ["Wi-Fi", "ネットワーク", "トラブル", "FAQ"]
    }
]


def insert_sample_data():
    """サンプルデータを開発DBに投入"""
    print("🌸 Mirai IT Knowledge Systems - 開発環境サンプルデータ投入")
    print("=" * 80)
    print(f"データベース: {DEV_DB_PATH}")
    print()

    client = SQLiteClient(DEV_DB_PATH)

    # ナレッジデータ投入
    print("📚 ナレッジデータ投入中...")
    print("-" * 40)
    knowledge_count = 0
    for i, data in enumerate(KNOWLEDGE_DATA, 1):
        try:
            result = client.create_knowledge(
                title=data["title"],
                content=data["content"],
                itsm_type=data["itsm_type"],
                tags=data["tags"],
                summary_technical=f"技術要約: {data['title'][:50]}",
                summary_non_technical=f"概要: {data['title'][:50]}",
                created_by="sample_script"
            )
            knowledge_count += 1
            print(f"  ✅ [{data['itsm_type']}] {data['title'][:40]}...")
        except Exception as e:
            print(f"  ❌ エラー: {data['title'][:30]} - {e}")

    print()
    print("📋 FAQデータ投入中...")
    print("-" * 40)
    faq_count = 0
    for i, data in enumerate(FAQ_DATA, 1):
        try:
            result = client.create_knowledge(
                title=data["title"],
                content=data["content"],
                itsm_type=data["itsm_type"],
                tags=data["tags"],
                summary_technical=f"FAQ: {data['title'][:50]}",
                summary_non_technical=f"よくある質問: {data['title'][:50]}",
                created_by="sample_script"
            )
            faq_count += 1
            print(f"  ✅ [FAQ] {data['title'][:40]}...")
        except Exception as e:
            print(f"  ❌ エラー: {data['title'][:30]} - {e}")

    print()
    print("=" * 80)
    print("📊 投入結果:")
    print(f"   ナレッジ: {knowledge_count}件")
    print(f"   FAQ: {faq_count}件")
    print(f"   合計: {knowledge_count + faq_count}件")
    print()
    print("✨ サンプルデータ投入完了！")

    # 確認クエリ
    print()
    print("📈 データベース確認:")
    with client.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT itsm_type, COUNT(*) FROM knowledge_entries GROUP BY itsm_type")
        rows = cursor.fetchall()
        for row in rows:
            print(f"   {row[0]}: {row[1]}件")


if __name__ == "__main__":
    insert_sample_data()
