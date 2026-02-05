-- ================================================================================
-- チケット管理システム スキーマ
-- Mirai IT Knowledge Systems - Phase 10
-- 作成日: 2026-02-05
-- ================================================================================

-- ================================================================================
-- 1. チケットテーブル
-- ================================================================================

CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_number TEXT UNIQUE NOT NULL,      -- 例: TKT-20260205-001
    session_id TEXT NOT NULL,                -- 会話セッションID

    -- 分類
    category TEXT CHECK(category IN
        ('incident', 'problem', 'request', 'question', 'consultation')) NOT NULL,
    subcategory TEXT,                        -- サブカテゴリ（ネットワーク、AD、VPNなど）
    priority TEXT DEFAULT 'medium' CHECK(priority IN
        ('low', 'medium', 'high', 'critical')),

    -- 内容
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    current_symptoms TEXT,                   -- 現在の症状（JSON array）

    -- 状態管理
    status TEXT DEFAULT 'new' CHECK(status IN
        ('new', 'analyzing', 'in_progress', 'pending_user', 'resolved', 'closed', 'cancelled')),

    -- 診断ステージ
    diagnostic_stage TEXT DEFAULT 'symptom_collection',
    diagnostic_step INTEGER DEFAULT 0,       -- 現在の診断ステップ番号

    -- 追跡
    assigned_to TEXT,                        -- 担当者（AI/人間）
    created_by TEXT,                         -- 作成者
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    closed_at TIMESTAMP,

    -- 関連
    knowledge_id INTEGER,                    -- 作成されたナレッジID
    parent_ticket_id INTEGER,                -- 親チケット（エスカレーション）
    related_ticket_ids TEXT,                 -- 関連チケットID（JSON array）

    -- 解決
    resolution TEXT,                         -- 解決策・対応内容
    resolution_type TEXT,                    -- 解決タイプ（workaround/permanent/escalated）

    -- メタデータ
    tags TEXT,                               -- タグ（JSON array）
    ai_confidence REAL,                      -- AI診断の信頼度（0.0-1.0）
    metadata TEXT,                           -- その他メタデータ（JSON）

    FOREIGN KEY (session_id) REFERENCES conversation_sessions(session_id) ON DELETE CASCADE,
    FOREIGN KEY (knowledge_id) REFERENCES knowledge_entries(id) ON DELETE SET NULL,
    FOREIGN KEY (parent_ticket_id) REFERENCES tickets(id) ON DELETE SET NULL
);

-- ================================================================================
-- 2. チケット履歴テーブル
-- ================================================================================

CREATE TABLE IF NOT EXISTS ticket_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL,
    action TEXT NOT NULL,                    -- 'status_change', 'assignment', 'priority_change', 'comment'
    from_value TEXT,
    to_value TEXT,
    comment TEXT,
    created_by TEXT,                         -- 'ai' or ユーザー名
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE
);

-- ================================================================================
-- 3. チケットコメントテーブル
-- ================================================================================

CREATE TABLE IF NOT EXISTS ticket_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL,
    author TEXT NOT NULL,                    -- 'ai', 'user', 'system'
    author_type TEXT DEFAULT 'user' CHECK(author_type IN
        ('user', 'ai', 'system')),
    content TEXT NOT NULL,
    is_internal BOOLEAN DEFAULT 0,           -- 内部コメント（ユーザーに非表示）
    is_solution BOOLEAN DEFAULT 0,           -- 解決策コメント
    ai_generated BOOLEAN DEFAULT 0,          -- AI生成コメント
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE
);

-- ================================================================================
-- 4. フォローアップスケジュールテーブル
-- ================================================================================

CREATE TABLE IF NOT EXISTS ticket_followups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL,
    followup_type TEXT CHECK(followup_type IN
        ('resolution_check', 'satisfaction_survey', 'auto_close_warning')),
    scheduled_at TIMESTAMP NOT NULL,
    executed_at TIMESTAMP,
    response TEXT,                           -- ユーザー応答
    status TEXT DEFAULT 'pending' CHECK(status IN
        ('pending', 'sent', 'responded', 'expired')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE
);

-- ================================================================================
-- 5. インデックス
-- ================================================================================

CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tickets_session ON tickets(session_id);
CREATE INDEX IF NOT EXISTS idx_tickets_category ON tickets(category, priority);
CREATE INDEX IF NOT EXISTS idx_tickets_assigned ON tickets(assigned_to, status);
CREATE INDEX IF NOT EXISTS idx_tickets_number ON tickets(ticket_number);

CREATE INDEX IF NOT EXISTS idx_ticket_history_ticket ON ticket_history(ticket_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ticket_comments_ticket ON ticket_comments(ticket_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ticket_followups_scheduled ON ticket_followups(scheduled_at, status);

-- ================================================================================
-- 6. トリガー
-- ================================================================================

-- updated_at自動更新
CREATE TRIGGER IF NOT EXISTS ticket_updated_at
AFTER UPDATE ON tickets
FOR EACH ROW
BEGIN
    UPDATE tickets SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

-- ステータス変更時に履歴記録
CREATE TRIGGER IF NOT EXISTS ticket_status_change_log
AFTER UPDATE OF status ON tickets
FOR EACH ROW
WHEN OLD.status != NEW.status
BEGIN
    INSERT INTO ticket_history (ticket_id, action, from_value, to_value, created_by)
    VALUES (OLD.id, 'status_change', OLD.status, NEW.status, 'system');
END;

-- ================================================================================
-- 7. 初期データ
-- ================================================================================

-- サンプルチケット（開発・テスト用）
INSERT OR IGNORE INTO tickets (
    ticket_number, session_id, category, priority, title, description,
    status, assigned_to, created_by
) VALUES
    ('TKT-SAMPLE-001', 'sample_session_1', 'incident', 'high',
     'VPN接続エラー', 'Cisco AnyConnect で認証に失敗します',
     'resolved', 'ai', 'sample_user'),
    ('TKT-SAMPLE-002', 'sample_session_2', 'request', 'medium',
     'パスワードリセット依頼', 'ADパスワードを忘れました',
     'in_progress', 'ai', 'sample_user');

-- ================================================================================
-- ビュー: チケット統計
-- ================================================================================

CREATE VIEW IF NOT EXISTS ticket_stats AS
SELECT
    category,
    status,
    priority,
    COUNT(*) as count,
    AVG(CAST((julianday(COALESCE(resolved_at, CURRENT_TIMESTAMP)) -
              julianday(created_at)) * 24 AS REAL)) as avg_resolution_hours
FROM tickets
GROUP BY category, status, priority;
