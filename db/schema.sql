-- Mirai IT Knowledge Systems - Database Schema
-- SQLite Database for Knowledge Management

-- ナレッジエントリテーブル
CREATE TABLE IF NOT EXISTS knowledge_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    itsm_type TEXT NOT NULL CHECK(itsm_type IN ('Incident', 'Problem', 'Change', 'Release', 'Request', 'Other')),
    summary_technical TEXT,
    summary_non_technical TEXT,
    insights TEXT, -- JSON形式で保存
    content TEXT, -- 元の内容
    tags TEXT, -- JSON形式で保存
    related_ids TEXT, -- JSON形式で関連ID配列
    markdown_path TEXT UNIQUE,
    status TEXT DEFAULT 'active' CHECK(status IN ('active', 'archived', 'draft')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    updated_by TEXT
);

-- ナレッジ間の関係テーブル
CREATE TABLE IF NOT EXISTS relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id INTEGER NOT NULL,
    target_id INTEGER NOT NULL,
    relationship_type TEXT NOT NULL CHECK(relationship_type IN (
        'Incident→Problem',
        'Problem→Change',
        'Change→Release',
        'Request→Change',
        'Duplicate',
        'Related',
        'Parent→Child',
        'Reference'
    )),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_id) REFERENCES knowledge_entries(id) ON DELETE CASCADE,
    FOREIGN KEY (target_id) REFERENCES knowledge_entries(id) ON DELETE CASCADE,
    UNIQUE(source_id, target_id, relationship_type)
);

-- ITSMタグテーブル
CREATE TABLE IF NOT EXISTS itsm_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tag_name TEXT NOT NULL UNIQUE,
    itsm_category TEXT CHECK(itsm_category IN ('Incident', 'Problem', 'Change', 'Release', 'Request', 'General')),
    description TEXT,
    color TEXT, -- UIでの表示色
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ワークフロー実行履歴テーブル
CREATE TABLE IF NOT EXISTS workflow_executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    knowledge_id INTEGER,
    workflow_type TEXT NOT NULL,
    status TEXT CHECK(status IN ('running', 'completed', 'failed', 'cancelled')),
    subagents_used TEXT, -- JSON形式でサブエージェント名配列
    hooks_triggered TEXT, -- JSON形式でフック名配列
    execution_time_ms INTEGER,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (knowledge_id) REFERENCES knowledge_entries(id) ON DELETE SET NULL
);

-- サブエージェント実行ログテーブル
CREATE TABLE IF NOT EXISTS subagent_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_execution_id INTEGER NOT NULL,
    subagent_name TEXT NOT NULL,
    role TEXT NOT NULL,
    input_data TEXT, -- JSON形式
    output_data TEXT, -- JSON形式
    execution_time_ms INTEGER,
    status TEXT CHECK(status IN ('success', 'failed', 'warning')),
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workflow_execution_id) REFERENCES workflow_executions(id) ON DELETE CASCADE
);

-- フック実行ログテーブル
CREATE TABLE IF NOT EXISTS hook_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_execution_id INTEGER NOT NULL,
    hook_name TEXT NOT NULL,
    hook_type TEXT CHECK(hook_type IN ('pre-task', 'on-change', 'post-task', 'quality')),
    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    result TEXT CHECK(result IN ('pass', 'warning', 'error')),
    message TEXT,
    details TEXT, -- JSON形式
    FOREIGN KEY (workflow_execution_id) REFERENCES workflow_executions(id) ON DELETE CASCADE
);

-- 重複検知結果テーブル
CREATE TABLE IF NOT EXISTS duplicate_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    knowledge_id INTEGER NOT NULL,
    potential_duplicate_id INTEGER NOT NULL,
    similarity_score REAL NOT NULL CHECK(similarity_score BETWEEN 0.0 AND 1.0),
    check_type TEXT CHECK(check_type IN ('title', 'content', 'semantic')),
    status TEXT CHECK(status IN ('pending', 'confirmed', 'dismissed')),
    reviewed_by TEXT,
    reviewed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (knowledge_id) REFERENCES knowledge_entries(id) ON DELETE CASCADE,
    FOREIGN KEY (potential_duplicate_id) REFERENCES knowledge_entries(id) ON DELETE CASCADE
);

-- 逸脱検知結果テーブル
CREATE TABLE IF NOT EXISTS deviation_checks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    knowledge_id INTEGER NOT NULL,
    deviation_type TEXT NOT NULL,
    severity TEXT CHECK(severity IN ('info', 'warning', 'error')),
    itsm_principle TEXT,
    description TEXT NOT NULL,
    recommendation TEXT,
    status TEXT CHECK(status IN ('pending', 'acknowledged', 'resolved', 'dismissed')),
    reviewed_by TEXT,
    reviewed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (knowledge_id) REFERENCES knowledge_entries(id) ON DELETE CASCADE
);

-- 検索履歴テーブル
CREATE TABLE IF NOT EXISTS search_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    search_query TEXT NOT NULL,
    search_type TEXT CHECK(search_type IN ('natural_language', 'keyword', 'tag', 'itsm_type')),
    filters TEXT, -- JSON形式
    results_count INTEGER,
    selected_result_id INTEGER,
    user_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (selected_result_id) REFERENCES knowledge_entries(id) ON DELETE SET NULL
);

-- 対話セッションテーブル
CREATE TABLE IF NOT EXISTS conversation_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE NOT NULL,
    user_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    knowledge_id INTEGER,
    FOREIGN KEY (knowledge_id) REFERENCES knowledge_entries(id) ON DELETE SET NULL
);

-- 対話メッセージテーブル
CREATE TABLE IF NOT EXISTS conversation_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT CHECK(role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES conversation_sessions(session_id) ON DELETE CASCADE
);

-- インデックス作成
CREATE INDEX IF NOT EXISTS idx_knowledge_itsm_type ON knowledge_entries(itsm_type);
CREATE INDEX IF NOT EXISTS idx_knowledge_status ON knowledge_entries(status);
CREATE INDEX IF NOT EXISTS idx_knowledge_created_at ON knowledge_entries(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_relationships_source ON relationships(source_id);
CREATE INDEX IF NOT EXISTS idx_relationships_target ON relationships(target_id);
CREATE INDEX IF NOT EXISTS idx_relationships_type ON relationships(relationship_type);
CREATE INDEX IF NOT EXISTS idx_workflow_knowledge ON workflow_executions(knowledge_id);
CREATE INDEX IF NOT EXISTS idx_workflow_status ON workflow_executions(status);
CREATE INDEX IF NOT EXISTS idx_subagent_workflow ON subagent_logs(workflow_execution_id);
CREATE INDEX IF NOT EXISTS idx_hook_workflow ON hook_logs(workflow_execution_id);
CREATE INDEX IF NOT EXISTS idx_duplicate_knowledge ON duplicate_checks(knowledge_id);
CREATE INDEX IF NOT EXISTS idx_duplicate_score ON duplicate_checks(similarity_score DESC);
CREATE INDEX IF NOT EXISTS idx_deviation_knowledge ON deviation_checks(knowledge_id);
CREATE INDEX IF NOT EXISTS idx_deviation_status ON deviation_checks(status);
CREATE INDEX IF NOT EXISTS idx_search_created ON search_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_conversation_session ON conversation_sessions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_conversation_message ON conversation_messages(session_id, created_at DESC);

-- 全文検索用仮想テーブル（FTS5）
CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
    title,
    summary_technical,
    summary_non_technical,
    content,
    content=knowledge_entries,
    content_rowid=id
);

-- FTS5同期用トリガー
CREATE TRIGGER IF NOT EXISTS knowledge_fts_insert AFTER INSERT ON knowledge_entries BEGIN
    INSERT INTO knowledge_fts(rowid, title, summary_technical, summary_non_technical, content)
    VALUES (new.id, new.title, new.summary_technical, new.summary_non_technical, new.content);
END;

CREATE TRIGGER IF NOT EXISTS knowledge_fts_delete AFTER DELETE ON knowledge_entries BEGIN
    DELETE FROM knowledge_fts WHERE rowid = old.id;
END;

CREATE TRIGGER IF NOT EXISTS knowledge_fts_update AFTER UPDATE ON knowledge_entries BEGIN
    DELETE FROM knowledge_fts WHERE rowid = old.id;
    INSERT INTO knowledge_fts(rowid, title, summary_technical, summary_non_technical, content)
    VALUES (new.id, new.title, new.summary_technical, new.summary_non_technical, new.content);
END;

-- updated_at自動更新用トリガー
CREATE TRIGGER IF NOT EXISTS knowledge_updated_at AFTER UPDATE ON knowledge_entries BEGIN
    UPDATE knowledge_entries SET updated_at = CURRENT_TIMESTAMP WHERE id = new.id;
END;

-- 初期ITSMタグデータ
INSERT OR IGNORE INTO itsm_tags (tag_name, itsm_category, description, color) VALUES
('障害対応', 'Incident', 'システム障害・インシデント対応', '#FF5252'),
('緊急対応', 'Incident', '緊急度の高いインシデント', '#D32F2F'),
('計画停止', 'Change', '計画的なシステム停止', '#FF9800'),
('定期メンテナンス', 'Change', '定期メンテナンス作業', '#FFA726'),
('根本原因分析', 'Problem', '問題の根本原因分析', '#2196F3'),
('再発防止', 'Problem', '再発防止策の実施', '#1976D2'),
('リリース', 'Release', 'システムリリース', '#4CAF50'),
('ロールバック', 'Release', 'リリースロールバック', '#F44336'),
('サービスリクエスト', 'Request', 'ユーザーからのサービス要求', '#9C27B0'),
('アクセス権限', 'Request', 'アクセス権限関連', '#7B1FA2'),
('ネットワーク', 'General', 'ネットワーク関連', '#00BCD4'),
('データベース', 'General', 'データベース関連', '#009688'),
('セキュリティ', 'General', 'セキュリティ関連', '#795548'),
('パフォーマンス', 'General', 'パフォーマンス関連', '#607D8B'),
('バックアップ', 'General', 'バックアップ・リストア', '#3F51B5');
