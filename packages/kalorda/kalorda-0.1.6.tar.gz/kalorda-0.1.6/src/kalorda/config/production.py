import os

from .base import BaseConfig


class ProductionConfig(BaseConfig):
    """生产环境配置类"""

    # 环境标识
    ENVIRONMENT = "production"

    # 调试模式 - 生产环境应关闭调试模式
    DEBUG = False

    # 日志级别 - 生产环境设置为INFO以减少日志量
    LOG_LEVEL = "INFO"

    # 密钥配置 - 生产环境必须通过环境变量设置安全的密钥
    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        raise ValueError("生产环境必须设置SECRET_KEY环境变量")

    # 数据库配置 - 生产环境可以使用更强大的数据库
    # 这里仍然使用SQLite，但可以根据需要替换为PostgreSQL、MySQL等
    # 示例：如果使用PostgreSQL
    # DB_URL = os.getenv("DATABASE_URL")

    # 跨域配置 - 生产环境应限制来源
    CORS_ORIGINS = [
        "https://kalorda.com",
        "https://www.kalorda.com",
        # 添加其他允许的域名
    ]

    # JWT配置 - 生产环境使用默认的较短有效期
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7

    # API文档配置 - 生产环境可以禁用或限制访问API文档
    # API_DOCS_URL = None  # 禁用Swagger UI
    # API_REDOC_URL = None  # 禁用ReDoc

    # 安全配置 - 生产环境应提高安全要求
    SECURE_COOKIES = True
    CSRF_PROTECTION = True

    # 生产环境日志配置
    PROD_LOG_CONFIG = {
        "console": {
            "enabled": False,  # 生产环境通常关闭控制台日志
        },
        "file": {
            "enabled": True,
            "level": "INFO",
            "path": os.path.join(BaseConfig.LOG_DIR, "app.log"),
            "rotate": {"enabled": True, "when": "midnight", "backup_count": 30},
        },
        "error_file": {
            "enabled": True,
            "level": "ERROR",
            "path": os.path.join(BaseConfig.LOG_DIR, "error.log"),
            "rotate": {"enabled": True, "when": "midnight", "backup_count": 90},
        },
    }

    # 生产环境API配置
    PROD_API_CONFIG = {
        "enable_request_logging": False,  # 生产环境通常关闭请求日志
        "enable_response_logging": False,  # 生产环境通常关闭响应日志
        "enable_sql_logging": False,  # 生产环境通常关闭SQL日志
        "hide_error_details": True,  # 隐藏详细错误信息
        "enable_rate_limiting": True,  # 启用请求限流
        "cors_allow_credentials": True,  # 允许跨域请求携带凭证
    }

    # 生产环境性能配置
    PROD_PERFORMANCE_CONFIG = {
        "enable_caching": True,
        "cache_ttl": 3600,  # 缓存过期时间（秒）
        "use_gzip_compression": True,
        "workers": 4,  # uvicorn工作进程数
        "preload_app": True,  # 预加载应用
    }

    # 生产环境监控配置
    PROD_MONITORING_CONFIG = {
        "enable_metrics": True,
        "metrics_endpoint": "/metrics",
        "enable_health_checks": True,
        "health_check_endpoint": "/health",
        "enable_stats": True,
    }


# 导出配置类
__all__ = ["ProductionConfig"]
