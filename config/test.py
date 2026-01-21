"""
Test Configuration
テスト環境設定
"""

from .base import BaseConfig


class TestConfig(BaseConfig):
    """テスト環境設定"""

    # 環境識別
    ENVIRONMENT = 'test'

    # Flask設定
    DEBUG = True
    TESTING = True
    ENV = 'testing'

    # ネットワーク設定
    HOST = 'localhost'
    PORT = 9999
    BASE_URL = f'http://{HOST}:{PORT}'

    # データベース設定（テスト用インメモリDB）
    DATABASE_PATH = ':memory:'
    DATABASE_BACKUP_PATH = BaseConfig.PROJECT_ROOT / 'backups' / 'test'

    # ログ設定
    LOG_LEVEL = 'DEBUG'
    LOG_PATH = BaseConfig.PROJECT_ROOT / 'data' / 'logs' / 'test'
    LOG_FILE = 'mirai_knowledge_test.log'

    # SSL/TLS設定（テストでは無効）
    SSL_ENABLED = False

    # サンプルデータ設定
    USE_SAMPLE_DATA = True
    SAMPLE_DATA_COUNT = 3

    # セキュリティ設定（テスト用）
    SESSION_COOKIE_SAMESITE = 'Lax'
    SECRET_KEY = 'test-secret-key'

    # Git設定
    GIT_BRANCH = 'test'
    GIT_AUTO_COMMIT = False

    # キャッシュ無効化
    CACHE_ENABLED = False

    # バックアップ無効化
    AUTO_BACKUP_ENABLED = False

    @classmethod
    def init_app(cls, app):
        """テスト環境用の初期化"""
        super().init_app(app)
        print("\n" + "="*60)
        print(f"🧪 テスト環境で起動しています")
        print(f"   データベース: {cls.DATABASE_PATH}")
        print("="*60 + "\n")
