"""
Base Configuration
基本設定クラス
"""

import os
from pathlib import Path


class BaseConfig:
    """基本設定（すべての環境で共通）"""

    # プロジェクトルート
    PROJECT_ROOT = Path(__file__).parent.parent

    # アプリケーション基本設定
    APP_NAME = "Mirai IT Knowledge System"
    APP_VERSION = "3.0.0"

    # Flask設定
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key-change-me')
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 3600  # 1時間

    # データベース設定
    DATABASE_PATH = PROJECT_ROOT / 'db' / 'knowledge.db'
    DATABASE_BACKUP_PATH = PROJECT_ROOT / 'backups'

    # ログ設定
    LOG_LEVEL = 'INFO'
    LOG_PATH = PROJECT_ROOT / 'data' / 'logs'
    LOG_FILE = 'mirai_knowledge.log'
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5

    # ワークフロー設定
    WORKFLOW_TIMEOUT = 300  # 5分
    SUBAGENT_PARALLEL = True
    SUBAGENT_TIMEOUT = 60  # 1分

    # SubAgent設定（7体すべて有効）
    SUBAGENTS = {
        'architect': True,
        'knowledge_curator': True,
        'itsm_expert': True,
        'devops': True,
        'qa': True,
        'coordinator': True,
        'documenter': True,
    }

    # Hooks設定（5種すべて有効）
    HOOKS = {
        'pre_task': True,
        'post_task': True,
        'duplicate_check': True,
        'deviation_check': True,
        'auto_summary': True,
    }

    # MCP統合設定
    MCP_ENABLED = {
        'context7': True,
        'claude_mem': True,
        'github': True,
        'brave_search': True,
        'playwright': True,
    }

    # キャッシュ設定
    CACHE_ENABLED = True
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300  # 5分

    # バックアップ設定
    AUTO_BACKUP_ENABLED = True
    BACKUP_INTERVAL = 3600  # 1時間
    BACKUP_RETENTION_DAYS = 7

    # メンテナンスモード
    MAINTENANCE_MODE = False

    @classmethod
    def init_app(cls, app):
        """Flaskアプリケーション初期化"""
        # ログディレクトリ作成
        cls.LOG_PATH.mkdir(parents=True, exist_ok=True)

        # データベースディレクトリ作成
        cls.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

        # バックアップディレクトリ作成
        cls.DATABASE_BACKUP_PATH.mkdir(parents=True, exist_ok=True)
