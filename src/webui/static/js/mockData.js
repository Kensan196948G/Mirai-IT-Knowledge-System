/**
 * Mock Data Generator
 * サンプルナレッジデータ（16件）とServer Fault質問データ（20件）を提供
 */

class MockDataGenerator {
  /**
   * サンプルナレッジデータを生成（16件）
   * 既存のdata/knowledge/*.mdの構造を参考
   * @returns {Array} ナレッジデータの配列
   */
  static generateKnowledgeData() {
    return [
      // Incident 系（5件）
      {
        id: '00001',
        itsm_type: 'Incident',
        title: 'Webサーバーの503エラー発生',
        content: `## 発生事象
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
- 負荷分散の検討`,
        tags: ['apache', 'web-server', '503-error', 'incident'],
        severity: 'high',
        status: 'resolved',
        created_at: '2025-12-31T10:50:27Z',
        updated_at: '2025-12-31T11:15:00Z'
      },
      {
        id: '00003',
        itsm_type: 'Incident',
        title: 'データベース接続タイムアウトエラー',
        content: `## 発生事象
データベースへの接続が頻繁にタイムアウトし、アプリケーションがエラーを返す。

## 影響範囲
- 影響対象: Webアプリケーション全体
- 影響時間: 14:00〜15:30（約1.5時間）

## 対応内容
1. データベースのコネクションプール設定を確認
2. スロークエリログを分析
3. インデックスが欠落していたクエリを特定
4. 緊急メンテナンスでインデックスを追加
5. アプリケーションを再起動

## 一時対応
コネクションプールサイズを一時的に増加

## 今後の対応
- 定期的なクエリパフォーマンスレビュー
- 監視アラートの追加`,
        tags: ['database', 'mysql', 'timeout', 'incident'],
        severity: 'high',
        status: 'resolved',
        created_at: '2025-12-30T14:00:00Z',
        updated_at: '2025-12-30T15:30:00Z'
      },
      {
        id: '00008',
        itsm_type: 'Incident',
        title: 'メール送信サービスの停止',
        content: `## 発生事象
メール送信サービスが停止し、システムからのメール通知が送信されない。

## 影響範囲
- 影響対象: メール通知機能を使用する全サービス
- 影響時間: 09:00〜09:45（約45分）

## 対応内容
1. メール送信サーバーのログ確認
2. SMTPサービスの再起動を試みるも失敗
3. ディスク容量が満杯であることを確認
4. 不要なログファイルを削除
5. SMTPサービスを再起動
6. メール送信テストで正常性を確認`,
        tags: ['email', 'smtp', 'disk-space', 'incident'],
        severity: 'medium',
        status: 'resolved',
        created_at: '2025-12-29T09:00:00Z',
        updated_at: '2025-12-29T09:45:00Z'
      },
      {
        id: '00010',
        itsm_type: 'Incident',
        title: 'ロードバランサーのヘルスチェック失敗',
        content: `## 発生事象
ロードバランサーが特定のWebサーバーをアンヘルシーと判定し、トラフィックを振り分けない。

## 影響範囲
- 影響対象: Web-prod-02サーバー
- 影響時間: 16:30〜17:00（約30分）

## 対応内容
1. ロードバランサーのログ確認
2. Web-prod-02のヘルスチェックエンドポイントを確認
3. アプリケーションログでエラーを発見
4. アプリケーションの再起動
5. ヘルスチェックが正常に戻ることを確認`,
        tags: ['load-balancer', 'health-check', 'web-server', 'incident'],
        severity: 'medium',
        status: 'resolved',
        created_at: '2025-12-28T16:30:00Z',
        updated_at: '2025-12-28T17:00:00Z'
      },
      {
        id: '00015',
        itsm_type: 'Incident',
        title: 'APIレスポンスタイムの異常増加',
        content: `## 発生事象
APIのレスポンスタイムが通常の10倍以上に増加し、ユーザー体験が著しく低下。

## 影響範囲
- 影響対象: 全APIエンドポイント
- 影響時間: 13:00〜14:30（約1.5時間）

## 対応内容
1. APMツールでボトルネックを分析
2. 外部API呼び出しがタイムアウトしていることを確認
3. サードパーティAPIの障害を確認
4. キャッシュ機能を有効化して影響を軽減
5. サードパーティAPIの復旧後、正常化を確認`,
        tags: ['api', 'performance', 'third-party', 'incident'],
        severity: 'high',
        status: 'resolved',
        created_at: '2025-12-27T13:00:00Z',
        updated_at: '2025-12-27T14:30:00Z'
      },

      // Problem 系（4件）
      {
        id: '00002',
        itsm_type: 'Problem',
        title: 'Webサーバー503エラーの根本原因分析',
        content: `## 関連インシデント
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
- 四半期ごとに設定値を見直し`,
        tags: ['apache', 'capacity-planning', 'root-cause', 'problem'],
        severity: 'medium',
        status: 'resolved',
        created_at: '2025-12-31T10:50:29Z',
        updated_at: '2025-12-31T12:00:00Z'
      },
      {
        id: '00004',
        itsm_type: 'Problem',
        title: 'データベースパフォーマンス劣化の根本原因',
        content: `## 関連インシデント
- INC-2025-003: データベース接続タイムアウトエラー

## 根本原因
データベーステーブルの適切なインデックスが欠落しており、フルテーブルスキャンが頻発。

## 原因分析
1. スロークエリログの分析
2. EXPLAINで実行計画を確認
3. 複数のテーブルでインデックス未使用を確認
4. データ量の増加に伴いパフォーマンスが悪化

## 恒久対策
1. 必要なインデックスを追加
2. クエリの最適化
3. 定期的なパフォーマンスレビュープロセスの確立
4. データベース監視の強化`,
        tags: ['database', 'performance', 'indexing', 'problem'],
        severity: 'high',
        status: 'resolved',
        created_at: '2025-12-30T16:00:00Z',
        updated_at: '2025-12-30T18:00:00Z'
      },
      {
        id: '00009',
        itsm_type: 'Problem',
        title: 'ディスク容量枯渇の再発防止対策',
        content: `## 関連インシデント
- INC-2025-008: メール送信サービスの停止

## 根本原因
ログローテーション設定が不適切で、古いログファイルが削除されずディスクを圧迫。

## 原因分析
1. ログファイルが無制限に保存されていた
2. ログローテーション設定が機能していない
3. ディスク使用量の監視が不十分

## 恒久対策
1. ログローテーション設定の修正（7日保持、圧縮）
2. ディスク使用量の監視アラート設定
3. 定期的なディスククリーンアップジョブの設定`,
        tags: ['disk-space', 'log-rotation', 'monitoring', 'problem'],
        severity: 'medium',
        status: 'resolved',
        created_at: '2025-12-29T10:00:00Z',
        updated_at: '2025-12-29T12:00:00Z'
      },
      {
        id: '00011',
        itsm_type: 'Problem',
        title: 'アプリケーションメモリリークの調査',
        content: `## 関連インシデント
- INC-2025-010: ロードバランサーのヘルスチェック失敗

## 根本原因
アプリケーションコードにメモリリークが存在し、長時間稼働でメモリ不足に。

## 原因分析
1. ヒープダンプの解析
2. 特定のオブジェクトがGC対象にならない
3. イベントリスナーの解除漏れを発見

## 恒久対策
1. コード修正（イベントリスナーの適切な解除）
2. メモリ使用量の監視強化
3. 定期的なメモリプロファイリングの実施`,
        tags: ['memory-leak', 'application', 'heap-dump', 'problem'],
        severity: 'high',
        status: 'in-progress',
        created_at: '2025-12-28T18:00:00Z',
        updated_at: '2026-01-05T10:00:00Z'
      },

      // Change 系（3件）
      {
        id: '00005',
        itsm_type: 'Change',
        title: 'Webサーバー証明書の更新作業',
        content: `## 変更内容
本番Webサーバー（3台）のSSL/TLS証明書を更新する。
現在の証明書が2026-01-31に期限切れとなるため、事前に更新を実施。

## 対象システム
- web-prod-01.example.com
- web-prod-02.example.com
- web-prod-03.example.com

## 作業手順
1. 新規証明書の取得（Let's Encrypt）
2. ステージング環境での動作確認
3. 本番環境への適用
4. ブラウザでの証明書確認
5. 監視アラートの確認

## リスク評価
- リスクレベル: 中
- 影響度: ユーザーアクセスへの影響なし

## ロールバック計画
新証明書で問題が発生した場合、旧証明書に即座に切り戻し可能。`,
        tags: ['ssl', 'certificate', 'web-server', 'change'],
        severity: 'medium',
        status: 'scheduled',
        created_at: '2025-12-31T10:59:26Z',
        updated_at: '2026-01-05T09:00:00Z'
      },
      {
        id: '00012',
        itsm_type: 'Change',
        title: 'データベースバージョンアップグレード',
        content: `## 変更内容
MySQL 5.7から8.0へのバージョンアップグレード。

## 対象システム
- db-prod-01（マスター）
- db-prod-02（スレーブ）

## 作業手順
1. フルバックアップの取得
2. ステージング環境での検証
3. スレーブサーバーのアップグレード
4. マスター昇格とフェイルオーバー
5. 旧マスターのアップグレード

## リスク評価
- リスクレベル: 高
- 影響度: サービス停止30分想定

## ロールバック計画
バックアップからの完全復元（RTO: 2時間）`,
        tags: ['database', 'mysql', 'upgrade', 'change'],
        severity: 'high',
        status: 'approved',
        created_at: '2026-01-03T10:00:00Z',
        updated_at: '2026-01-08T14:00:00Z'
      },
      {
        id: '00016',
        itsm_type: 'Change',
        title: 'ファイアウォールルールの追加',
        content: `## 変更内容
新規サービス導入に伴うファイアウォールルールの追加。

## 対象システム
- ファイアウォール（FW-01, FW-02）

## 作業手順
1. ルール設定のレビュー
2. テスト環境での動作確認
3. 本番環境への適用
4. 疎通テストの実施

## リスク評価
- リスクレベル: 低
- 影響度: 既存サービスへの影響なし

## ロールバック計画
設定変更の即座の削除が可能。`,
        tags: ['firewall', 'network', 'security', 'change'],
        severity: 'low',
        status: 'completed',
        created_at: '2026-01-04T11:00:00Z',
        updated_at: '2026-01-06T15:00:00Z'
      },

      // Release 系（2件）
      {
        id: '00006',
        itsm_type: 'Release',
        title: 'APIレート制限機能のリリース',
        content: `## リリース概要
外部APIに対するレート制限機能を実装し、本番環境にリリースする。

## リリース内容
- バージョン: v2.3.0
- 機能: APIレート制限（IP単位、ユーザー単位）
- リリース日時: 2026-01-20 21:00

## 新機能
1. IPベースレート制限: 1000リクエスト/時間
2. ユーザーベースレート制限: 無料100/有料10000リクエスト/時間
3. 管理画面: レート制限状況の可視化

## リリース手順
1. データベースマイグレーション実行
2. アプリケーションサーバーの順次更新
3. レート制限設定の適用
4. 動作確認`,
        tags: ['api', 'rate-limiting', 'redis', 'release'],
        severity: 'high',
        status: 'scheduled',
        created_at: '2025-12-31T10:59:27Z',
        updated_at: '2026-01-15T10:00:00Z'
      },
      {
        id: '00013',
        itsm_type: 'Release',
        title: 'モバイルアプリv3.0のリリース',
        content: `## リリース概要
モバイルアプリケーションの新バージョンをリリース。

## リリース内容
- バージョン: v3.0.0
- 機能: UI刷新、ダークモード対応、オフライン機能

## リリース手順
1. App Store/Google Playへの申請
2. 段階的ロールアウト（10% → 50% → 100%）
3. ユーザーフィードバックの監視
4. バグ修正の即座対応

## 影響分析
- ユーザー影響: 既存ユーザーは自動更新`,
        tags: ['mobile-app', 'ios', 'android', 'release'],
        severity: 'medium',
        status: 'in-progress',
        created_at: '2026-01-07T09:00:00Z',
        updated_at: '2026-01-18T16:00:00Z'
      },

      // Request 系（2件）
      {
        id: '00007',
        itsm_type: 'Request',
        title: '新規ユーザーのVPNアクセス権限申請',
        content: `## 申請内容
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
1. VPN接続（SSL-VPN、開発環境セグメント）
2. アクセス可能リソース: 開発用サーバー、Gitリポジトリ、開発DB

## セキュリティ要件
- 多要素認証（MFA）必須
- パスワードポリシー準拠`,
        tags: ['vpn', 'access-request', 'onboarding', 'request'],
        severity: 'medium',
        status: 'approved',
        created_at: '2025-12-31T10:59:28Z',
        updated_at: '2026-01-09T14:00:00Z'
      },
      {
        id: '00014',
        itsm_type: 'Request',
        title: 'データベースアクセス権限の追加申請',
        content: `## 申請内容
新規プロジェクトのためのデータベースアクセス権限追加。

## 申請者情報
- 申請者: 開発部 佐藤
- 申請日: 2026-01-10

## 対象ユーザー
- 氏名: 鈴木花子
- 社員番号: EMP-2024-123
- 部署: 開発部

## 必要なアクセス権限
- データベース: analytics-db
- 権限レベル: 読み取り専用
- 利用期間: 2026-01-15 〜 2026-06-30

## 承認フロー
1. 直属上長承認: 完了
2. DBA承認: 待機中`,
        tags: ['database', 'access-request', 'permissions', 'request'],
        severity: 'low',
        status: 'pending',
        created_at: '2026-01-10T09:00:00Z',
        updated_at: '2026-01-11T10:00:00Z'
      }
    ];
  }

  /**
   * Server Fault質問データを生成（20件）
   * @returns {Array} 質問データの配列
   */
  static generateServerFaultQuestions() {
    return [
      {
        id: 'sf-001',
        title: 'Apache server running out of memory',
        content: 'Our Apache web server keeps running out of memory after a few hours of operation. We have 8GB RAM and MaxRequestWorkers set to 150. How can I troubleshoot this?',
        tags: ['apache', 'memory', 'troubleshooting'],
        created_at: '2026-01-15T10:00:00Z',
        auto_classified: null
      },
      {
        id: 'sf-002',
        title: 'MySQL slow query performance issue',
        content: 'We are experiencing slow query performance on our MySQL database. Some queries are taking over 10 seconds. What should I check first?',
        tags: ['mysql', 'performance', 'slow-query'],
        created_at: '2026-01-15T11:30:00Z',
        auto_classified: null
      },
      {
        id: 'sf-003',
        title: 'SSL certificate renewal procedure',
        content: 'Our SSL certificate is expiring next month. What is the best practice for renewing and updating certificates on production servers without downtime?',
        tags: ['ssl', 'certificate', 'renewal'],
        created_at: '2026-01-15T13:00:00Z',
        auto_classified: null
      },
      {
        id: 'sf-004',
        title: 'Email server disk space full',
        content: 'Our email server disk is completely full and emails are not being sent. How do I quickly free up space and prevent this from happening again?',
        tags: ['email', 'disk-space', 'smtp'],
        created_at: '2026-01-15T14:30:00Z',
        auto_classified: null
      },
      {
        id: 'sf-005',
        title: 'Load balancer health check failing',
        content: 'One of our web servers is being marked as unhealthy by the load balancer, but when I check manually it seems to be working fine. How do I debug this?',
        tags: ['load-balancer', 'health-check', 'debugging'],
        created_at: '2026-01-15T16:00:00Z',
        auto_classified: null
      },
      {
        id: 'sf-006',
        title: 'API response time suddenly increased',
        content: 'Our API response time has increased from 100ms to over 2 seconds. This started happening this morning. Where should I start investigating?',
        tags: ['api', 'performance', 'latency'],
        created_at: '2026-01-16T09:00:00Z',
        auto_classified: null
      },
      {
        id: 'sf-007',
        title: 'Database replication lag issue',
        content: 'We are experiencing significant replication lag between our master and slave database servers. The lag is currently at 5 minutes. How can we resolve this?',
        tags: ['database', 'replication', 'mysql'],
        created_at: '2026-01-16T10:30:00Z',
        auto_classified: null
      },
      {
        id: 'sf-008',
        title: 'Firewall rule change request process',
        content: 'We need to add new firewall rules for a new application. What is the recommended process to ensure we do not break existing services?',
        tags: ['firewall', 'network', 'security'],
        created_at: '2026-01-16T11:45:00Z',
        auto_classified: null
      },
      {
        id: 'sf-009',
        title: 'Application memory leak diagnosis',
        content: 'Our Java application memory usage keeps growing until it crashes. We suspect a memory leak. What tools and techniques should we use to diagnose this?',
        tags: ['memory-leak', 'java', 'troubleshooting'],
        created_at: '2026-01-16T13:15:00Z',
        auto_classified: null
      },
      {
        id: 'sf-010',
        title: 'MySQL version upgrade planning',
        content: 'We want to upgrade from MySQL 5.7 to 8.0. What are the major things we need to consider and test before the upgrade?',
        tags: ['mysql', 'upgrade', 'planning'],
        created_at: '2026-01-16T14:30:00Z',
        auto_classified: null
      },
      {
        id: 'sf-011',
        title: 'Redis cache eviction strategy',
        content: 'Our Redis cache keeps evicting data too frequently. We have 4GB allocated but it seems insufficient. How should we optimize our eviction policy?',
        tags: ['redis', 'cache', 'optimization'],
        created_at: '2026-01-17T09:00:00Z',
        auto_classified: null
      },
      {
        id: 'sf-012',
        title: 'VPN access for new employee',
        content: 'We have a new employee starting next week who needs VPN access to development servers. What is the standard procedure for granting access?',
        tags: ['vpn', 'access-control', 'onboarding'],
        created_at: '2026-01-17T10:15:00Z',
        auto_classified: null
      },
      {
        id: 'sf-013',
        title: 'Docker container keeps restarting',
        content: 'One of our Docker containers keeps restarting every few minutes. The logs show an out of memory error. How do I increase the memory limit?',
        tags: ['docker', 'container', 'memory'],
        created_at: '2026-01-17T11:30:00Z',
        auto_classified: null
      },
      {
        id: 'sf-014',
        title: 'MongoDB high CPU usage investigation',
        content: 'MongoDB is consuming 90% CPU constantly. We have not made any recent changes. What queries or operations should I look at to find the cause?',
        tags: ['mongodb', 'cpu', 'performance'],
        created_at: '2026-01-17T13:00:00Z',
        auto_classified: null
      },
      {
        id: 'sf-015',
        title: 'Backup restoration testing procedure',
        content: 'We need to test our backup restoration process. What is the best way to do this without affecting production systems?',
        tags: ['backup', 'disaster-recovery', 'testing'],
        created_at: '2026-01-17T14:45:00Z',
        auto_classified: null
      },
      {
        id: 'sf-016',
        title: 'DNS propagation delay issue',
        content: 'We updated our DNS records 6 hours ago but some users are still seeing the old IP address. How long should DNS propagation take?',
        tags: ['dns', 'networking', 'propagation'],
        created_at: '2026-01-18T09:30:00Z',
        auto_classified: null
      },
      {
        id: 'sf-017',
        title: 'Nginx reverse proxy configuration',
        content: 'We want to set up Nginx as a reverse proxy in front of our application servers. What are the essential configuration options we should set?',
        tags: ['nginx', 'reverse-proxy', 'configuration'],
        created_at: '2026-01-18T11:00:00Z',
        auto_classified: null
      },
      {
        id: 'sf-018',
        title: 'SSL/TLS version deprecation planning',
        content: 'We need to deprecate TLS 1.0 and 1.1 support. How do we identify which clients are still using these old versions?',
        tags: ['ssl', 'tls', 'security'],
        created_at: '2026-01-18T12:30:00Z',
        auto_classified: null
      },
      {
        id: 'sf-019',
        title: 'Kubernetes pod eviction problem',
        content: 'Our Kubernetes pods are being evicted due to resource pressure. How do we properly set resource requests and limits?',
        tags: ['kubernetes', 'pod', 'resources'],
        created_at: '2026-01-18T14:00:00Z',
        auto_classified: null
      },
      {
        id: 'sf-020',
        title: 'Log aggregation system selection',
        content: 'We are looking to implement a centralized log aggregation system. Should we use ELK stack, Splunk, or something else?',
        tags: ['logging', 'elk', 'monitoring'],
        created_at: '2026-01-18T15:30:00Z',
        auto_classified: null
      }
    ];
  }

  /**
   * LocalStorageにモックデータを初期化
   * @param {boolean} force - 既存データがあっても上書きするか
   * @returns {boolean} 成功したかどうか
   */
  static initializeMockData(force = false) {
    try {
      const storage = new StorageManager();

      // 既存データチェック
      const existingKnowledge = storage.getAllKnowledge();
      const existingQuestions = storage.getAllQuestions();

      if (!force && (existingKnowledge.length > 0 || existingQuestions.length > 0)) {
        console.log('Mock data already exists. Use force=true to overwrite.');
        return false;
      }

      // ナレッジデータを保存
      const knowledgeData = this.generateKnowledgeData();
      storage.saveAllKnowledge(knowledgeData);

      // 質問データを保存
      const questionData = this.generateServerFaultQuestions();
      storage.saveAllQuestions(questionData);

      console.log(`Initialized ${knowledgeData.length} knowledge items and ${questionData.length} questions.`);
      return true;
    } catch (error) {
      console.error('Failed to initialize mock data:', error);
      return false;
    }
  }
}
