-- ================================================================================
-- FTS5全文検索最適化SQL
-- Mirai IT Knowledge Systems
-- 作成日: 2026-02-02
-- ================================================================================

-- ================================================================================
-- 1. FTS5インデックス最適化
-- ================================================================================

-- 現在のFTS5テーブルを最適化（断片化解消）
INSERT INTO knowledge_fts(knowledge_fts) VALUES('optimize');

-- FTS5インデックスを完全再構築
INSERT INTO knowledge_fts(knowledge_fts) VALUES('rebuild');

-- ================================================================================
-- 2. 追加インデックス作成（クエリパフォーマンス向上）
-- ================================================================================

-- 複合インデックス: ITSMタイプ + 作成日時
-- 用途: タイプ別の新着ナレッジ取得
CREATE INDEX IF NOT EXISTS idx_knowledge_itsm_created
ON knowledge_entries(itsm_type, created_at DESC);

-- 複合インデックス: ステータス + ITSMタイプ
-- 用途: アクティブなナレッジのタイプ別フィルタ
CREATE INDEX IF NOT EXISTS idx_knowledge_status_itsm
ON knowledge_entries(status, itsm_type);

-- 作成者インデックス
-- 用途: ユーザー別のナレッジ検索
CREATE INDEX IF NOT EXISTS idx_knowledge_created_by
ON knowledge_entries(created_by);

-- 更新日時インデックス
-- 用途: 最近更新されたナレッジ取得
CREATE INDEX IF NOT EXISTS idx_knowledge_updated_at
ON knowledge_entries(updated_at DESC);

-- ================================================================================
-- 3. FTS5高度な検索クエリサンプル
-- ================================================================================

-- 3.1 BM25ランキングを使用した検索
-- 関連度の高い順にソート
SELECT
    ke.id,
    ke.title,
    ke.itsm_type,
    bm25(knowledge_fts) AS relevance_score
FROM knowledge_entries ke
JOIN knowledge_fts ON ke.id = knowledge_fts.rowid
WHERE knowledge_fts MATCH 'VPN AND 障害'
ORDER BY relevance_score
LIMIT 20;

-- 3.2 フィールド別重み付け検索
-- タイトルに含まれる場合は高スコア
SELECT
    ke.id,
    ke.title,
    ke.itsm_type,
    bm25(knowledge_fts, 10.0, 1.0, 1.0, 1.0) AS weighted_score
FROM knowledge_entries ke
JOIN knowledge_fts ON ke.id = knowledge_fts.rowid
WHERE knowledge_fts MATCH 'セキュリティ'
ORDER BY weighted_score
LIMIT 20;

-- 3.3 複合条件検索（FTS5 + 通常フィルタ）
SELECT
    ke.id,
    ke.title,
    ke.itsm_type,
    ke.created_at,
    bm25(knowledge_fts) AS score
FROM knowledge_entries ke
JOIN knowledge_fts ON ke.id = knowledge_fts.rowid
WHERE knowledge_fts MATCH 'パッチ OR 更新'
  AND ke.itsm_type = 'Change'
  AND ke.status = 'active'
  AND ke.created_at >= datetime('now', '-30 days')
ORDER BY score
LIMIT 20;

-- 3.4 フレーズ検索
-- 完全一致フレーズを検索
SELECT
    ke.id,
    ke.title,
    snippet(knowledge_fts, 0, '<mark>', '</mark>', '...', 30) AS title_snippet
FROM knowledge_entries ke
JOIN knowledge_fts ON ke.id = knowledge_fts.rowid
WHERE knowledge_fts MATCH '"メールサーバー障害"'
LIMIT 10;

-- 3.5 前方一致検索（prefix設定が必要）
SELECT
    ke.id,
    ke.title
FROM knowledge_entries ke
JOIN knowledge_fts ON ke.id = knowledge_fts.rowid
WHERE knowledge_fts MATCH 'ネット*'
LIMIT 10;

-- 3.6 除外検索（NOT演算子）
SELECT
    ke.id,
    ke.title,
    ke.itsm_type
FROM knowledge_entries ke
JOIN knowledge_fts ON ke.id = knowledge_fts.rowid
WHERE knowledge_fts MATCH 'Windows NOT Server'
LIMIT 20;

-- ================================================================================
-- 4. スニペット生成（検索結果のハイライト表示）
-- ================================================================================

-- タイトルと本文のスニペットを生成
SELECT
    ke.id,
    ke.title,
    snippet(knowledge_fts, 0, '<b>', '</b>', '...', 20) AS title_highlight,
    snippet(knowledge_fts, 3, '<mark>', '</mark>', '...', 64) AS content_highlight,
    bm25(knowledge_fts) AS score
FROM knowledge_entries ke
JOIN knowledge_fts ON ke.id = knowledge_fts.rowid
WHERE knowledge_fts MATCH 'VPN 接続'
ORDER BY score
LIMIT 10;

-- ================================================================================
-- 5. 統計クエリ（検索パフォーマンス分析用）
-- ================================================================================

-- 5.1 FTS5テーブルの行数確認
SELECT COUNT(*) AS fts_row_count FROM knowledge_fts;

-- 5.2 ナレッジエントリとFTS5の整合性チェック
SELECT
    (SELECT COUNT(*) FROM knowledge_entries) AS entries_count,
    (SELECT COUNT(*) FROM knowledge_fts) AS fts_count,
    CASE
        WHEN (SELECT COUNT(*) FROM knowledge_entries) = (SELECT COUNT(*) FROM knowledge_fts)
        THEN 'OK'
        ELSE 'MISMATCH'
    END AS sync_status;

-- 5.3 ITSMタイプ別のナレッジ件数
SELECT
    itsm_type,
    COUNT(*) AS count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM knowledge_entries), 2) AS percentage
FROM knowledge_entries
WHERE status = 'active'
GROUP BY itsm_type
ORDER BY count DESC;

-- ================================================================================
-- 6. パフォーマンス計測用クエリ
-- ================================================================================

-- 6.1 実行計画の確認（EXPLAIN QUERY PLAN）
EXPLAIN QUERY PLAN
SELECT
    ke.id,
    ke.title,
    bm25(knowledge_fts) AS score
FROM knowledge_entries ke
JOIN knowledge_fts ON ke.id = knowledge_fts.rowid
WHERE knowledge_fts MATCH 'データベース パフォーマンス'
ORDER BY score
LIMIT 20;

-- 6.2 インデックス使用状況の確認
SELECT
    name,
    tbl_name,
    sql
FROM sqlite_master
WHERE type = 'index'
  AND tbl_name = 'knowledge_entries'
ORDER BY name;

-- ================================================================================
-- 7. メンテナンスクエリ
-- ================================================================================

-- 7.1 VACUUM（データベースサイズの最適化）
-- 注意: 大量のデータがある場合は時間がかかります
-- VACUUM;

-- 7.2 ANALYZE（統計情報の更新）
-- SQLiteクエリオプティマイザが効率的な実行計画を作成するために使用
ANALYZE;

-- 7.3 FTS5インデックスの完全性チェック
INSERT INTO knowledge_fts(knowledge_fts) VALUES('integrity-check');

-- ================================================================================
-- 8. 今後の最適化（MeCab導入後）
-- ================================================================================

-- MeCabトークナイザーを使用したFTS5テーブル作成例
-- 注意: 実行前にMeCabとSQLite拡張をインストール必要
/*
DROP TABLE IF EXISTS knowledge_fts_mecab;

CREATE VIRTUAL TABLE knowledge_fts_mecab USING fts5(
    title,
    summary_technical,
    summary_non_technical,
    content,
    content=knowledge_entries,
    content_rowid=id,
    tokenize='mecab',
    prefix='2,3'
);

-- トリガーの再作成（MeCab版）
CREATE TRIGGER knowledge_fts_mecab_insert AFTER INSERT ON knowledge_entries BEGIN
    INSERT INTO knowledge_fts_mecab(rowid, title, summary_technical, summary_non_technical, content)
    VALUES (new.id, new.title, new.summary_technical, new.summary_non_technical, new.content);
END;

CREATE TRIGGER knowledge_fts_mecab_delete AFTER DELETE ON knowledge_entries BEGIN
    DELETE FROM knowledge_fts_mecab WHERE rowid = old.id;
END;

CREATE TRIGGER knowledge_fts_mecab_update AFTER UPDATE ON knowledge_entries BEGIN
    DELETE FROM knowledge_fts_mecab WHERE rowid = old.id;
    INSERT INTO knowledge_fts_mecab(rowid, title, summary_technical, summary_non_technical, content)
    VALUES (new.id, new.title, new.summary_technical, new.summary_non_technical, new.content);
END;
*/

-- ================================================================================
-- 9. ベンチマーク用クエリ
-- ================================================================================

-- 9.1 単純なFTS5検索（ベースライン）
.timer on
SELECT COUNT(*) FROM knowledge_fts WHERE knowledge_fts MATCH 'VPN';
.timer off

-- 9.2 複雑な条件の検索
.timer on
SELECT
    ke.*,
    bm25(knowledge_fts) AS score
FROM knowledge_entries ke
JOIN knowledge_fts ON ke.id = knowledge_fts.rowid
WHERE knowledge_fts MATCH 'VPN OR メール OR ネットワーク'
  AND ke.status = 'active'
  AND ke.itsm_type IN ('Incident', 'Problem')
ORDER BY score
LIMIT 50;
.timer off

-- 9.3 通常のLIKE検索（比較用）
.timer on
SELECT *
FROM knowledge_entries
WHERE (title LIKE '%VPN%' OR content LIKE '%VPN%')
  AND status = 'active'
LIMIT 50;
.timer off

-- ================================================================================
-- エンドノート
-- ================================================================================
-- このSQLファイルは、FTS5全文検索の最適化とパフォーマンス向上を目的としています。
-- 環境に応じて、適宜クエリを調整してください。
--
-- パフォーマンス目標:
-- - 検索レイテンシ（P50）: <100ms
-- - 検索レイテンシ（P95）: <200ms
-- - インデックスサイズ: データベースサイズの20%以内
-- ================================================================================
