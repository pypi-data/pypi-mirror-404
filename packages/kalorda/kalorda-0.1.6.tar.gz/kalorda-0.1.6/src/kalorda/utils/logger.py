import logging
import os
import traceback
from datetime import datetime
from typing import Any, Dict, Optional, Union


class Logger:
    """自定义日志工具类

    提供统一的日志记录接口，支持不同级别的日志输出、文件日志和控制台日志
    """

    def __init__(
        self,
        name: str = "app",
        log_file: Optional[str] = None,
        log_level: int = logging.INFO,
        enable_console: bool = True,
        log_format: Optional[str] = None,
    ):
        """初始化日志工具

        Args:
            name: 日志名称
            log_file: 日志文件路径，如果为None则不输出到文件
            log_level: 日志级别
            enable_console: 是否启用控制台输出
            log_format: 日志格式
        """
        # 创建logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)
        self.logger.propagate = False  # 避免重复记录

        # 清除已有的处理器
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

        # 定义日志格式
        if log_format is None:
            log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

        formatter = logging.Formatter(log_format)

        # 添加控制台处理器
        if enable_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

        # 添加文件处理器
        if log_file:
            # 确保日志目录存在
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)

            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def debug(self, message: str, **kwargs) -> None:
        """记录调试日志

        Args:
            message: 日志消息
            **kwargs: 额外的日志信息
        """
        if kwargs:
            message = f"{message} | {kwargs}"
        self.logger.debug(message)

    def info(self, message: str, **kwargs) -> None:
        """记录信息日志

        Args:
            message: 日志消息
            **kwargs: 额外的日志信息
        """
        if kwargs:
            message = f"{message} | {kwargs}"
        self.logger.info(message)

    def warning(self, message: str, **kwargs) -> None:
        """记录警告日志

        Args:
            message: 日志消息
            **kwargs: 额外的日志信息
        """
        if kwargs:
            message = f"{message} | {kwargs}"
        self.logger.warning(message)

    def error(self, message: str, exc_info: bool = False, **kwargs) -> None:
        """记录错误日志

        Args:
            message: 日志消息
            exc_info: 是否包含异常信息
            **kwargs: 额外的日志信息
        """
        if kwargs:
            message = f"{message} | {kwargs}"
        self.logger.error(message, exc_info=exc_info)

    def critical(self, message: str, exc_info: bool = False, **kwargs) -> None:
        """记录严重错误日志

        Args:
            message: 日志消息
            exc_info: 是否包含异常信息
            **kwargs: 额外的日志信息
        """
        if kwargs:
            message = f"{message} | {kwargs}"
        self.logger.critical(message, exc_info=exc_info)


def setup_logger(
    name: str = "kalorda", log_dir: Optional[str] = None, log_level: Union[int, str] = logging.INFO
) -> Logger:
    """设置并返回日志记录器实例

    Args:
        name: 日志名称
        log_dir: 日志目录，如果为None则使用默认目录
        log_level: 日志级别

    Returns:
        Logger实例
    """
    # 默认日志目录
    if log_dir is None:
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")

    # 确保日志目录存在
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 创建按日期命名的日志文件
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(log_dir, f"{name}_{today}.log")

    # 解析日志级别
    if isinstance(log_level, str):
        log_level = getattr(logging, log_level.upper(), logging.INFO)

    # 创建日志记录器
    logger = Logger(name=name, log_file=log_file, log_level=log_level, enable_console=True)

    return logger


def log_api_request(request: Any, response: Any, execution_time: float) -> None:
    """记录API请求日志

    Args:
        request: 请求对象
        response: 响应对象
        execution_time: 执行时间（毫秒）
    """
    # 获取基本日志记录器
    logger = logging.getLogger("kalorda.api")

    # 尝试从请求对象中获取相关信息
    try:
        method = getattr(request, "method", "Unknown")
        url = getattr(request, "url", "Unknown")
        if hasattr(url, "path"):
            url = url.path

        # 获取状态码
        status_code = getattr(response, "status_code", 0)

        # 获取用户信息
        user = "Unknown"
        if hasattr(request, "state") and hasattr(request.state, "user"):
            user = getattr(request.state.user, "username", str(request.state.user))

        # 构建日志消息
        message = f"[{method}] {url} - Status: {status_code} - User: {user} - Time: {execution_time:.2f}ms"

        # 根据状态码选择日志级别
        if status_code >= 500:
            logger.error(message)
        elif status_code >= 400:
            logger.warning(message)
        else:
            logger.info(message)

    except Exception as e:
        logger.error(f"Failed to log API request: {str(e)}", exc_info=True)


def log_exception(error: Exception, context: Dict[str, Any] = None) -> str:
    """记录异常日志并生成错误ID

    Args:
        error: 异常对象
        context: 上下文信息

    Returns:
        错误ID
    """
    # 获取异常日志记录器
    logger = logging.getLogger("kalorda.exceptions")

    # 生成错误ID
    error_id = f"ERR_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hash(str(error)) % 1000000:06d}"

    # 构建异常信息
    exception_type = type(error).__name__
    exception_message = str(error)
    traceback_info = traceback.format_exc()

    # 构建日志消息
    message = f"Error ID: {error_id}\nType: {exception_type}\nMessage: {exception_message}"

    # 添加上下文信息
    if context:
        message += f"\nContext: {context}"

    # 添加堆栈跟踪
    message += f"\nTraceback:\n{traceback_info}"

    # 记录错误日志
    logger.error(message)

    return error_id


# 创建默认日志记录器实例
default_logger = setup_logger()
logger = default_logger  # 导出logger供其他模块使用

# 导出常用的日志方法
debug = default_logger.debug
info = default_logger.info
warning = default_logger.warning
error = default_logger.error
critical = default_logger.critical
