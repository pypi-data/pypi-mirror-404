import os

# 根据环境变量选择配置类
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# 动态导入对应环境的配置类
try:
    if ENVIRONMENT == "production":
        from .production import ProductionConfig as Config
    else:
        from .development import DevelopmentConfig as Config

except ImportError:
    # 如果导入失败，使用基础配置
    from .base import BaseConfig as Config

# 导出配置实例
config = Config()

# 导出配置类
__all__ = ["Config", "config", "ENVIRONMENT"]
