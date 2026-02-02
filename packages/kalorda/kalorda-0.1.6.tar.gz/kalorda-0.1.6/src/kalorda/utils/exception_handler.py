import time
import traceback
from datetime import datetime

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from kalorda.utils.i18n import _

# 设置日志 - 使用全局日志记录器
from kalorda.utils.logger import logger


def setup_exception_handlers(app):
    """设置应用的异常处理器

    Args:
        app: FastAPI应用实例
    """

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """全局异常处理器

        处理所有未捕获的异常
        """
        # 记录异常信息
        error_id = log_exception(request, exc)

        # 返回统一格式的错误响应
        return JSONResponse(
            status_code=500,
            content={
                "code": 500,
                "message": _("服务器内部错误，请稍后重试"),
                "data": {"error_id": error_id},
                "time": time.time(),
            },
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """HTTP异常处理器

        处理FastAPI的HTTPException异常
        """
        # 记录HTTP异常
        log_http_exception(request, exc)

        # 返回HTTP异常的响应
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": exc.status_code,
                "message": exc.detail or _("HTTP错误"),
                "data": None,
                "time": time.time(),
            },
        )


def log_exception(request: Request, exc: Exception) -> str:
    """记录异常信息

    Args:
        request: 请求对象
        exc: 异常对象

    Returns:
        错误ID，用于追踪
    """
    # 生成错误ID（时间戳+随机数的后6位）
    error_id = generate_error_id()

    # 获取请求信息
    method = request.method
    url = str(request.url)
    headers = dict(request.headers)
    path_params = dict(request.path_params)
    query_params = dict(request.query_params)

    # 记录异常详情
    logger.error(
        f"[错误ID: {error_id}] {method} {url}\n"
        f"请求头: {headers}\n"
        f"路径参数: {path_params}\n"
        f"查询参数: {query_params}\n"
        f"异常类型: {type(exc).__name__}\n"
        f"异常信息: {str(exc)}\n"
        f"堆栈跟踪:\n{traceback.format_exc()}"
    )

    return error_id


def log_http_exception(request: Request, exc: HTTPException) -> None:
    """记录HTTP异常信息

    Args:
        request: 请求对象
        exc: HTTP异常对象
    """
    # 获取请求信息
    method = request.method
    url = str(request.url)

    # 根据状态码决定日志级别
    if exc.status_code >= 500:
        log_method = logger.error
    elif exc.status_code >= 400:
        log_method = logger.warning
    else:
        log_method = logger.info

    log_method(f"HTTP异常: [{exc.status_code}] {exc.detail}\n请求: {method} {url}")


def generate_error_id() -> str:
    """生成唯一的错误ID

    Returns:
        错误ID字符串
    """
    # 使用当前时间戳和随机数生成错误ID
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    # 为了简化，这里使用当前时间戳后6位作为错误ID的一部分
    # 在实际应用中，可以考虑使用UUID或其他更随机的方式
    import random

    random_suffix = str(random.randint(100000, 999999))

    return f"{timestamp}{random_suffix}"


def handle_database_exception(request: Request, exc: Exception) -> tuple:
    """处理数据库异常

    Args:
        request: 请求对象
        exc: 数据库异常对象

    Returns:
        (状态码, 错误消息)
    """
    # 记录数据库异常
    error_id = log_exception(request, exc)

    # 解析数据库异常信息，返回适当的状态码和消息
    # 这里可以根据不同类型的数据库异常返回不同的错误信息
    return 500, f"数据库操作失败，请稍后重试 (错误ID: {error_id})"


def handle_validation_exception(request: Request, exc: Exception) -> tuple:
    """处理验证异常

    Args:
        request: 请求对象
        exc: 验证异常对象

    Returns:
        (状态码, 错误消息)
    """
    # 记录验证异常（使用较低的日志级别）
    logger.warning(f"验证异常: {str(exc)}\n请求: {request.method} {request.url}")

    # 返回验证错误信息
    return 400, str(exc)


def handle_permission_denied(request: Request) -> tuple:
    """处理权限拒绝

    Args:
        request: 请求对象

    Returns:
        (状态码, 错误消息)
    """
    # 记录权限拒绝信息
    logger.warning(
        f"权限拒绝\n" f"请求: {request.method} {request.url}\n" f"用户: {getattr(request.state, 'user', '未认证')}"
    )

    return 403, "权限不足，无法执行此操作"
