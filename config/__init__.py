"""Configuration module for Estronix E-Commerce Platform."""

from config.settings import Config, DevelopmentConfig, ProductionConfig, TestingConfig

config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}

__all__ = ["Config", "DevelopmentConfig", "ProductionConfig", "TestingConfig", "config"]
