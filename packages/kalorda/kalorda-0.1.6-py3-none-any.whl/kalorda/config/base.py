import os
import secrets
from datetime import timedelta


class BaseConfig:
    """基础配置类，包含所有环境共用的配置项"""

    # JWT密钥配置
    # 在生产环境中，应通过环境变量设置
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-me")
    if not SECRET_KEY or SECRET_KEY == "your-secret-key-change-me":
        # 生产环境建议通过环境变量设置安全的密钥
        SECRET_KEY = "exaX7W5hPjnjdST6TaSyfMXERcQu2MG-R0VrpCCufVs"  # secrets.token_urlsafe(32)

    # JWT配置
    JWT_ALGORITHM = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30  # 访问令牌有效期30分钟
    JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7  # 刷新令牌有效期7天

    # AES密钥配置，如果环境变量没配置，使用默认值
    AES_KEY = os.getenv("AES_KEY", "your-secret-key-change-me")
    if not AES_KEY or AES_KEY == "your-secret-key-change-me":
        # 注意：修改后端AES_KEY默认值，前端AES_KEY的值也需要同步修改
        AES_KEY = "kalarda@#.com8la"

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # SQLite 数据库配置
    DB_PATH = os.path.join(BASE_DIR, "database", "database.db")

    # MySQL 数据库配置
    DB_NAME = os.getenv("DB_NAME", "kalorda_db")  # 数据库名称
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")  # 数据库主机
    DB_PORT = int(os.getenv("DB_PORT", "3306"))  # 数据库端口
    DB_USER = os.getenv("DB_USER", "root")  # 数据库用户名
    DB_PASSWORD = os.getenv("DB_PASSWORD", "your-password-change-me")  # 数据库密码

    # 数据库类型选择
    # DB_TYPE = "sqlite" 使用SQLite数据库
    # DB_TYPE = "mysql" 使用MySQL数据库
    DB_TYPE = os.getenv("DB_TYPE", "sqlite")

    # 日志配置
    LOG_DIR = os.path.join(BASE_DIR, "logs")
    LOG_LEVEL = "INFO"

    # 上传目录
    UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

    # 模型微调工作目录
    FINETUNE_WORK_DIR = os.path.join(BASE_DIR, "finetune_works")

    # API文档配置
    API_DOCS_URL = "/docs"
    API_REDOC_URL = "/redoc"

    # 跨域配置
    CORS_ORIGINS = ["*"]  # 开发环境允许所有来源，生产环境应限制
    CORS_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    CORS_HEADERS = ["*"]

    # 文件上传配置
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    ALLOWED_FILE_TYPES = [
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ]
    UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
    # 模型微调工作目录
    FINETUNE_WORK_DIR = os.path.join(BASE_DIR, "finetune_works")

    # 分页配置
    DEFAULT_PAGE_SIZE = 10
    MAX_PAGE_SIZE = 100

    # 安全配置
    PASSWORD_HASHER = "bcrypt"
    MIN_PASSWORD_LENGTH = 8
    PASSWORD_COMPLEXITY = {
        "min_length": MIN_PASSWORD_LENGTH,
        "require_uppercase": True,
        "require_lowercase": True,
        "require_digit": True,
        "require_special": False,
    }

    # 缓存配置
    CACHE_EXPIRE = 3600  # 1小时

    # 限流配置
    RATE_LIMIT = "100/minute"  # 每分钟最多100次请求

    # 系统配置项
    SYSTEM_CONFIG = {
        "login_attempts": 5,  # 连续登录失败次数上限
        "lockout_duration": 30,  # 账户锁定时间（分钟）
        "session_timeout": 1800,  # 会话超时时间（秒）
        "password_expiry_days": 90,  # 密码过期时间（天）
    }

    # 辅助方法：获取配置值
    @classmethod
    def get(cls, key, default=None):
        """获取配置值"""
        return getattr(cls, key, default)

    # 辅助方法：设置配置值（谨慎使用）
    @classmethod
    def set(cls, key, value):
        """设置配置值"""
        setattr(cls, key, value)

    # 辅助方法：检查配置是否存在
    @classmethod
    def has(cls, key):
        """检查配置是否存在"""
        return hasattr(cls, key)


# 导出配置类
__all__ = ["BaseConfig"]
