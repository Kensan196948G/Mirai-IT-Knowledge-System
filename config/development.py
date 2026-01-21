"""
Development Configuration
開発環境設定
"""

from .base import BaseConfig


class DevelopmentConfig(BaseConfig):
    """開発環境設定"""

    # 環境識別
    ENVIRONMENT = 'development'

    # Flask設定
    DEBUG = True
    TESTING = False
    ENV = 'development'

    # ネットワーク設定
    HOST = '192.168.0.187'
    PORT = 8888
    BASE_URL = f'https://{HOST}:{PORT}'

    # データベース設定
    DATABASE_PATH = BaseConfig.PROJECT_ROOT / 'db' / 'knowledge_dev.db'
    DATABASE_BACKUP_PATH = BaseConfig.PROJECT_ROOT / 'backups' / 'dev'

    # ログ設定
    LOG_LEVEL = 'DEBUG'
    LOG_PATH = BaseConfig.PROJECT_ROOT / 'data' / 'logs' / 'dev'
    LOG_FILE = 'mirai_knowledge_dev.log'

    # SSL/TLS設定
    SSL_ENABLED = True
    SSL_CERT = '/etc/ssl/mirai-knowledge/dev-cert.pem'
    SSL_KEY = '/etc/ssl/mirai-knowledge/dev-key.pem'

    # サンプルデータ設定
    USE_SAMPLE_DATA = True
    SAMPLE_DATA_COUNT = 7

    # セキュリティ設定（開発環境は緩い設定）
    SESSION_COOKIE_SAMESITE = 'Lax'
    SECRET_KEY = 'dev-secret-key-for-development-only'

    # デバッグツール
    DEBUG_TB_ENABLED = True
    DEBUG_TB_INTERCEPT_REDIRECTS = False

    # Git設定
    GIT_BRANCH = 'develop'
    GIT_AUTO_COMMIT = False

    # パフォーマンス設定
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300

    @classmethod
    def init_app(cls, app):
        """開発環境用の初期化"""
        super().init_app(app)
        print("\n" + "="*60)
        print(f"🔧 開発環境で起動しています")
        print(f"   URL: {cls.BASE_URL}")
        print(f"   ポート: {cls.PORT}")
        print(f"   データベース: {cls.DATABASE_PATH}")
        print(f"   サンプルデータ: {'有効' if cls.USE_SAMPLE_DATA else '無効'}")
        print("="*60 + "\n")
