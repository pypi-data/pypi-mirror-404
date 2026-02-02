from .base import BaseConfig


class DevelopmentConfig(BaseConfig):
    """开发环境配置类"""

    # 环境标识
    ENVIRONMENT = "development"

    # 调试模式
    DEBUG = True

    # 日志级别 - 开发环境设置为DEBUG以便更详细的日志
    LOG_LEVEL = "DEBUG"

    # 数据库配置 - 开发环境可以使用独立的数据库文件
    # DB_PATH = BaseConfig.DB_PATH.replace(".db", "_dev.db")

    # 跨域配置 - 开发环境允许所有来源
    CORS_ORIGINS = ["*"]

    # JWT配置 - 开发环境可以延长令牌有效期以便测试
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24小时
    JWT_REFRESH_TOKEN_EXPIRE_DAYS = 30  # 30天

    # 开发环境特有配置
    DEVELOPMENT_ONLY = {
        "show_detailed_errors": True,
        "enable_hot_reload": True,
        "auto_create_tables": True,
        "auto_generate_admin": True,
        "seed_test_data": False,  # 是否自动生成测试数据
    }

    # 安全配置 - 开发环境可以降低密码复杂度要求
    PASSWORD_COMPLEXITY = {
        "min_length": 6,  # 开发环境降低密码长度要求
        "require_uppercase": False,  # 不强制要求大写字母
        "require_lowercase": False,  # 不强制要求小写字母
        "require_digit": False,  # 不强制要求数字
        "require_special": False,  # 不强制要求特殊字符
    }

    # 开发环境日志配置
    DEV_LOG_CONFIG = {
        "console": {"enabled": True, "level": "DEBUG"},
        "file": {"enabled": True, "level": "DEBUG", "rotate": {"enabled": True, "when": "midnight", "backup_count": 7}},
    }

    # 开发环境API配置
    DEV_API_CONFIG = {
        "enable_request_logging": True,
        "enable_response_logging": True,
        "enable_sql_logging": True,
        "pretty_print_json": True,
    }

    # 开发环境测试配置
    DEV_TEST_CONFIG = {
        "enable_test_endpoints": True,
        "test_user_credentials": {"username": "test", "password": "test123"},
    }


# 导出配置类
__all__ = ["DevelopmentConfig"]
