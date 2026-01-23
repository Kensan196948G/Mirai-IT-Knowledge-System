"""
Environment Configuration Loader
環境変数読み込みモジュール
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv


class EnvironmentConfig:
    """環境設定クラス"""

    def __init__(self, environment: Optional[str] = None):
        """
        Args:
            environment: 環境名（development, production, test）
                        Noneの場合は環境変数 ENVIRONMENT から取得
        """
        self.environment = environment or os.getenv('ENVIRONMENT', 'development')
        self.project_root = Path(__file__).parent.parent.parent
        self.config = {}
        self._load_environment()

    def _load_environment(self):
        """環境変数を読み込み"""
        # 環境別の .env ファイルを読み込み
        env_file = self.project_root / f'.env.{self.environment}'

        if env_file.exists():
            load_dotenv(env_file)
            print(f"✅ 環境設定読み込み: {env_file}")
        else:
            print(f"⚠️  環境設定ファイルが見つかりません: {env_file}")
            print(f"   デフォルト設定を使用します")

        # 環境変数を辞書に格納
        self.config = {
            # 環境識別
            'environment': self.get_env('ENVIRONMENT', 'development'),
            'flask_env': self.get_env('FLASK_ENV', 'development'),
            'flask_debug': self.get_bool_env('FLASK_DEBUG', True),

            # ネットワーク設定
            'host': self.get_env('HOST', '192.168.0.187'),
            'port': self.get_int_env('PORT', 8888),
            'base_url': self.get_env('BASE_URL', 'https://192.168.0.187:8888'),

            # データベース設定
            'database_path': self.get_path_env('DATABASE_PATH', 'db/knowledge_dev.db'),
            'database_backup_path': self.get_path_env('DATABASE_BACKUP_PATH', 'backups/dev'),

            # ログ設定
            'log_level': self.get_env('LOG_LEVEL', 'DEBUG'),
            'log_path': self.get_path_env('LOG_PATH', 'data/logs/dev'),
            'log_file': self.get_env('LOG_FILE', 'mirai_knowledge_dev.log'),
            'log_max_bytes': self.get_int_env('LOG_MAX_BYTES', 10485760),
            'log_backup_count': self.get_int_env('LOG_BACKUP_COUNT', 5),

            # SSL/TLS設定
            'ssl_enabled': self.get_bool_env('SSL_ENABLED', True),
            'ssl_cert': self.get_env('SSL_CERT', '/etc/ssl/mirai-knowledge/dev-cert.pem'),
            'ssl_key': self.get_env('SSL_KEY', '/etc/ssl/mirai-knowledge/dev-key.pem'),

            # サンプルデータ設定
            'use_sample_data': self.get_bool_env('USE_SAMPLE_DATA', True),
            'sample_data_count': self.get_int_env('SAMPLE_DATA_COUNT', 7),

            # ワークフロー設定
            'workflow_timeout': self.get_int_env('WORKFLOW_TIMEOUT', 300),
            'subagent_parallel': self.get_bool_env('SUBAGENT_PARALLEL', True),
            'subagent_timeout': self.get_int_env('SUBAGENT_TIMEOUT', 60),

            # SubAgent設定
            'subagent_architect_enabled': self.get_bool_env('SUBAGENT_ARCHITECT_ENABLED', True),
            'subagent_knowledge_curator_enabled': self.get_bool_env('SUBAGENT_KNOWLEDGE_CURATOR_ENABLED', True),
            'subagent_itsm_expert_enabled': self.get_bool_env('SUBAGENT_ITSM_EXPERT_ENABLED', True),
            'subagent_devops_enabled': self.get_bool_env('SUBAGENT_DEVOPS_ENABLED', True),
            'subagent_qa_enabled': self.get_bool_env('SUBAGENT_QA_ENABLED', True),
            'subagent_coordinator_enabled': self.get_bool_env('SUBAGENT_COORDINATOR_ENABLED', True),
            'subagent_documenter_enabled': self.get_bool_env('SUBAGENT_DOCUMENTER_ENABLED', True),

            # Hooks設定
            'hook_pre_task_enabled': self.get_bool_env('HOOK_PRE_TASK_ENABLED', True),
            'hook_post_task_enabled': self.get_bool_env('HOOK_POST_TASK_ENABLED', True),
            'hook_duplicate_check_enabled': self.get_bool_env('HOOK_DUPLICATE_CHECK_ENABLED', True),
            'hook_deviation_check_enabled': self.get_bool_env('HOOK_DEVIATION_CHECK_ENABLED', True),
            'hook_auto_summary_enabled': self.get_bool_env('HOOK_AUTO_SUMMARY_ENABLED', True),

            # MCP統合設定
            'mcp_context7_enabled': self.get_bool_env('MCP_CONTEXT7_ENABLED', True),
            'mcp_claude_mem_enabled': self.get_bool_env('MCP_CLAUDE_MEM_ENABLED', True),
            'mcp_github_enabled': self.get_bool_env('MCP_GITHUB_ENABLED', True),
            'mcp_brave_search_enabled': self.get_bool_env('MCP_BRAVE_SEARCH_ENABLED', True),
            'mcp_playwright_enabled': self.get_bool_env('MCP_PLAYWRIGHT_ENABLED', True),

            # セキュリティ設定
            'secret_key': self.get_env('SECRET_KEY', 'dev-secret-key'),
            'session_cookie_secure': self.get_bool_env('SESSION_COOKIE_SECURE', True),
            'session_cookie_httponly': self.get_bool_env('SESSION_COOKIE_HTTPONLY', True),
            'session_cookie_samesite': self.get_env('SESSION_COOKIE_SAMESITE', 'Lax'),

            # パフォーマンス設定
            'cache_enabled': self.get_bool_env('CACHE_ENABLED', True),
            'cache_type': self.get_env('CACHE_TYPE', 'simple'),
            'cache_default_timeout': self.get_int_env('CACHE_DEFAULT_TIMEOUT', 300),

            # Git設定
            'git_branch': self.get_env('GIT_BRANCH', 'develop'),
            'git_auto_commit': self.get_bool_env('GIT_AUTO_COMMIT', False),

            # バックアップ設定
            'auto_backup_enabled': self.get_bool_env('AUTO_BACKUP_ENABLED', True),
            'backup_interval': self.get_int_env('BACKUP_INTERVAL', 3600),
            'backup_retention_days': self.get_int_env('BACKUP_RETENTION_DAYS', 7),

            # メンテナンスモード
            'maintenance_mode': self.get_bool_env('MAINTENANCE_MODE', False),
        }

    def get_env(self, key: str, default: str = '') -> str:
        """環境変数を取得（文字列）"""
        return os.getenv(key, default)

    def get_int_env(self, key: str, default: int = 0) -> int:
        """環境変数を取得（整数）"""
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            return default

    def get_bool_env(self, key: str, default: bool = False) -> bool:
        """環境変数を取得（真偽値）"""
        value = os.getenv(key, str(default)).lower()
        return value in ('true', '1', 'yes', 'on')

    def get_path_env(self, key: str, default: str) -> Path:
        """環境変数を取得（パス）"""
        path_str = os.getenv(key, default)
        return self.project_root / path_str

    def get(self, key: str, default: Any = None) -> Any:
        """設定値を取得"""
        return self.config.get(key, default)

    def get_all(self) -> Dict[str, Any]:
        """すべての設定を取得"""
        return self.config.copy()

    def is_development(self) -> bool:
        """開発環境か判定"""
        return self.environment == 'development'

    def is_production(self) -> bool:
        """本番環境か判定"""
        return self.environment == 'production'

    def is_test(self) -> bool:
        """テスト環境か判定"""
        return self.environment == 'test'

    def display_config(self):
        """設定を表示（デバッグ用）"""
        print("\n" + "="*60)
        print(f"🔧 環境設定: {self.environment.upper()}")
        print("="*60)
        for key, value in sorted(self.config.items()):
            # パスワードやシークレットキーは隠す
            if 'secret' in key.lower() or 'password' in key.lower():
                value = '***HIDDEN***'
            print(f"  {key}: {value}")
        print("="*60 + "\n")


# グローバル設定インスタンス
_config_instance: Optional[EnvironmentConfig] = None


def load_environment(environment: Optional[str] = None) -> EnvironmentConfig:
    """
    環境設定を読み込み

    Args:
        environment: 環境名（development, production, test）

    Returns:
        EnvironmentConfig インスタンス
    """
    global _config_instance
    _config_instance = EnvironmentConfig(environment)
    return _config_instance


def get_config() -> EnvironmentConfig:
    """
    現在の環境設定を取得

    Returns:
        EnvironmentConfig インスタンス
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = EnvironmentConfig()
    return _config_instance


# モジュール初期化時に自動読み込み
if _config_instance is None:
    _config_instance = EnvironmentConfig()
