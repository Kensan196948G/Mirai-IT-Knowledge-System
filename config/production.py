"""
Production Configuration
本番環境設定
"""

from .base import BaseConfig


class ProductionConfig(BaseConfig):
    """本番環境設定"""

    # 環境識別
    ENVIRONMENT = 'production'

    # Flask設定
    DEBUG = False
    TESTING = False
    ENV = 'production'

    # ネットワーク設定
    HOST = '192.168.0.187'
    PORT = 5000
    BASE_URL = f'https://{HOST}:{PORT}'

    # データベース設定
    DATABASE_PATH = BaseConfig.PROJECT_ROOT / 'db' / 'knowledge.db'
    DATABASE_BACKUP_PATH = BaseConfig.PROJECT_ROOT / 'backups' / 'prod'

    # ログ設定
    LOG_LEVEL = 'INFO'
    LOG_PATH = BaseConfig.PROJECT_ROOT / 'data' / 'logs' / 'prod'
    LOG_FILE = 'mirai_knowledge_prod.log'
    LOG_MAX_BYTES = 50 * 1024 * 1024  # 50MB
    LOG_BACKUP_COUNT = 10

    # SSL/TLS設定
    SSL_ENABLED = True
    SSL_CERT = '/etc/ssl/mirai-knowledge/prod-cert.pem'
    SSL_KEY = '/etc/ssl/mirai-knowledge/prod-key.pem'

    # サンプルデータ設定
    USE_SAMPLE_DATA = False
    SAMPLE_DATA_COUNT = 0

    # セキュリティ設定（本番環境は厳格な設定）
    SESSION_COOKIE_SAMESITE = 'Strict'
    SESSION_COOKIE_SECURE = True
    # 警告: 本番環境では必ずランダムなSECRET_KEYに変更してください
    # SECRET_KEY = os.urandom(32).hex()

    # デバッグツール（本番では無効）
    DEBUG_TB_ENABLED = False

    # Git設定
    GIT_BRANCH = 'main'
    GIT_AUTO_COMMIT = False

    # パフォーマンス設定
    CACHE_TYPE = 'filesystem'
    CACHE_DIR = '/tmp/mirai-knowledge-cache'
    CACHE_DEFAULT_TIMEOUT = 600  # 10分

    # バックアップ設定（本番は長期保存）
    BACKUP_INTERVAL = 86400  # 24時間
    BACKUP_RETENTION_DAYS = 30

    @classmethod
    def init_app(cls, app):
        """本番環境用の初期化"""
        super().init_app(app)
        print("\n" + "="*60)
        print(f"🚀 本番環境で起動しています")
        print(f"   URL: {cls.BASE_URL}")
        print(f"   ポート: {cls.PORT}")
        print(f"   データベース: {cls.DATABASE_PATH}")
        print(f"   サンプルデータ: {'有効' if cls.USE_SAMPLE_DATA else '無効'}")
        print("="*60 + "\n")

        # 本番環境でのセキュリティ警告
        if cls.SECRET_KEY == 'default-secret-key-change-me':
            print("⚠️  警告: SECRET_KEYがデフォルト値です。本番環境では必ず変更してください。")
