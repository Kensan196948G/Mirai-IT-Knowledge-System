-- システム設定スキーマ
-- Settings Schema

-- システム設定テーブル
CREATE TABLE IF NOT EXISTS system_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_key TEXT NOT NULL UNIQUE,
    setting_value TEXT,
    setting_type TEXT CHECK(setting_type IN ('string', 'integer', 'boolean', 'json')) DEFAULT 'string',
    description TEXT,
    category TEXT CHECK(category IN ('ai', 'system', 'ui', 'security', 'notification')),
    is_encrypted BOOLEAN DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by TEXT
);

-- ユーザーテーブル（簡易認証用）
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    full_name TEXT,
    email TEXT,
    role TEXT CHECK(role IN ('admin', 'user', 'viewer')) DEFAULT 'user',
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- セッションテーブル
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_token TEXT NOT NULL UNIQUE,
    user_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 設定変更履歴テーブル
CREATE TABLE IF NOT EXISTS settings_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_key TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    changed_by TEXT,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (setting_key) REFERENCES system_settings(setting_key)
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_settings_category ON system_settings(category);
CREATE INDEX IF NOT EXISTS idx_settings_key ON system_settings(setting_key);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(session_token);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_settings_history_key ON settings_history(setting_key);

-- トリガー: settings updated_at 自動更新
CREATE TRIGGER IF NOT EXISTS settings_updated_at
AFTER UPDATE ON system_settings
BEGIN
    UPDATE system_settings SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- トリガー: 設定変更履歴の自動記録
CREATE TRIGGER IF NOT EXISTS settings_history_trigger
AFTER UPDATE ON system_settings
BEGIN
    INSERT INTO settings_history (setting_key, old_value, new_value, changed_by)
    VALUES (NEW.setting_key, OLD.setting_value, NEW.setting_value, NEW.updated_by);
END;

-- 初期設定データ
INSERT OR IGNORE INTO system_settings (setting_key, setting_value, setting_type, description, category) VALUES
-- AI設定
('ai_provider', 'none', 'string', 'AI APIプロバイダー（none/anthropic/openai/openrouter/deepseek）', 'ai'),
('ai_model_chat', 'claude-3-5-haiku-20241022', 'string', 'AI対話用モデル', 'ai'),
('ai_model_search', 'claude-3-5-haiku-20241022', 'string', 'AI検索用モデル', 'ai'),
('ai_max_tokens', '4096', 'integer', '最大トークン数', 'ai'),
('ai_temperature', '0.7', 'string', '温度パラメータ', 'ai'),

-- システム設定
('system_name', 'Mirai IT Knowledge Systems', 'string', 'システム名', 'system'),
('items_per_page', '50', 'integer', '1ページあたりの表示件数', 'system'),
('auto_backup_enabled', 'true', 'boolean', '自動バックアップ有効化', 'system'),

-- UI設定
('theme', 'light', 'string', 'テーマ（light/dark）', 'ui'),
('show_menu_descriptions', 'true', 'boolean', 'メニュー説明を表示', 'ui'),
('keyboard_shortcuts_enabled', 'true', 'boolean', 'キーボードショートカット有効化', 'ui'),

-- セキュリティ設定
('require_auth_for_create', 'false', 'boolean', 'ナレッジ作成に認証必須', 'security'),
('require_auth_for_settings', 'true', 'boolean', '設定変更に認証必須', 'security'),
('session_timeout_minutes', '60', 'integer', 'セッションタイムアウト（分）', 'security');

-- デフォルト管理者ユーザー（パスワード: admin123）
-- 注意: 本番環境では必ず変更してください
INSERT OR IGNORE INTO users (username, password_hash, full_name, email, role)
VALUES ('admin', 'pbkdf2:sha256:600000$hR2vK8Qx$d5e8f4c3b2a1', 'システム管理者', 'admin@example.com', 'admin');
