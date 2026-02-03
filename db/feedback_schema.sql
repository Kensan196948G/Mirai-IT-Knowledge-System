-- ユーザーフィードバック機能のスキーマ拡張

-- ナレッジフィードバックテーブル
CREATE TABLE IF NOT EXISTS knowledge_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    knowledge_id INTEGER NOT NULL,
    user_id TEXT,
    rating INTEGER CHECK(rating BETWEEN 1 AND 5),
    feedback_type TEXT CHECK(feedback_type IN ('helpful', 'not_helpful', 'incorrect', 'incomplete', 'suggestion')),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (knowledge_id) REFERENCES knowledge_entries(id) ON DELETE CASCADE
);

-- ナレッジ評価サマリービュー
CREATE VIEW IF NOT EXISTS knowledge_ratings AS
SELECT
    knowledge_id,
    COUNT(*) as feedback_count,
    AVG(rating) as avg_rating,
    SUM(CASE WHEN feedback_type = 'helpful' THEN 1 ELSE 0 END) as helpful_count,
    SUM(CASE WHEN feedback_type = 'not_helpful' THEN 1 ELSE 0 END) as not_helpful_count
FROM knowledge_feedback
WHERE rating IS NOT NULL
GROUP BY knowledge_id;

-- システムフィードバックテーブル
CREATE TABLE IF NOT EXISTS system_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    feedback_category TEXT CHECK(feedback_category IN ('ui', 'search', 'quality', 'performance', 'feature_request', 'bug', 'other')),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    priority TEXT CHECK(priority IN ('low', 'medium', 'high', 'critical')) DEFAULT 'medium',
    status TEXT CHECK(status IN ('new', 'reviewing', 'planned', 'in_progress', 'completed', 'rejected')) DEFAULT 'new',
    assigned_to TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

-- ナレッジ使用統計テーブル
CREATE TABLE IF NOT EXISTS knowledge_usage_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    knowledge_id INTEGER NOT NULL,
    user_id TEXT,
    action_type TEXT CHECK(action_type IN ('view', 'search_result_click', 'copy', 'export', 'share')),
    session_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (knowledge_id) REFERENCES knowledge_entries(id) ON DELETE CASCADE
);

-- インデックス作成
CREATE INDEX IF NOT EXISTS idx_feedback_knowledge ON knowledge_feedback(knowledge_id);
CREATE INDEX IF NOT EXISTS idx_feedback_user ON knowledge_feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_feedback_type ON knowledge_feedback(feedback_type);
CREATE INDEX IF NOT EXISTS idx_system_feedback_status ON system_feedback(status);
CREATE INDEX IF NOT EXISTS idx_system_feedback_category ON system_feedback(feedback_category);
CREATE INDEX IF NOT EXISTS idx_usage_stats_knowledge ON knowledge_usage_stats(knowledge_id);
CREATE INDEX IF NOT EXISTS idx_usage_stats_action ON knowledge_usage_stats(action_type);
CREATE INDEX IF NOT EXISTS idx_usage_stats_created ON knowledge_usage_stats(created_at DESC);

-- トリガー: system_feedback の updated_at 自動更新
CREATE TRIGGER IF NOT EXISTS system_feedback_updated_at
AFTER UPDATE ON system_feedback
BEGIN
    UPDATE system_feedback SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
