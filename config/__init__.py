"""
Configuration Package
設定パッケージ
"""

from .base import BaseConfig
from .development import DevelopmentConfig
from .production import ProductionConfig
from .test import TestConfig

# 環境名から設定クラスを取得
CONFIG_MAP = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'test': TestConfig,
}


def get_config_class(environment: str = 'development'):
    """
    環境名から設定クラスを取得

    Args:
        environment: 環境名（development, production, test）

    Returns:
        設定クラス
    """
    return CONFIG_MAP.get(environment, DevelopmentConfig)


__all__ = [
    'BaseConfig',
    'DevelopmentConfig',
    'ProductionConfig',
    'TestConfig',
    'get_config_class',
]
