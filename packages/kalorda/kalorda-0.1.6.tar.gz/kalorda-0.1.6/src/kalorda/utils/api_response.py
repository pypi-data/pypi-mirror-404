import time
from typing import Any, Dict, Generic, Optional, TypeVar

from fastapi import HTTPException, status

from kalorda.utils.i18n import _, t

T = TypeVar("T")


class Code:
    """自定义的HTTP业务响应状态码"""

    SUCCESS = 2000
    ERROR = 4000
    AUTHORIZED_ERROR = 4001
    PERMISSION_ERROR = 4002


class ApiResponse(Generic[T]):
    """统一的API响应格式

    用于标准化API返回格式，包含状态码、消息、数据和元数据
    """

    def __init__(
        self,
        code: int = Code.SUCCESS,
        message: str = _("成功"),
        data: Optional[T] = None,
        time: float = time.time(),
    ):
        self.code = code
        self.message = message
        self.data = data
        self.time = time

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {
            "code": self.code,
            "message": t(self.message),
            "data": t(self.data),
            "time": time.time(),
        }
        return result


def success_response(
    data: Optional[Any] = None,
    message: str = _("成功"),
) -> Dict[str, T]:
    response = ApiResponse[T](
        code=Code.SUCCESS,
        message=message,
        data=data,
    )
    return response.to_dict()


def error_response(message: str = _("错误"), code: int = Code.ERROR) -> Dict[str, T]:
    response = ApiResponse[T](
        code=code,
        message=message,
    )
    return response.to_dict()


def raise_http_error(message: str = _("错误"), headers: Dict = None) -> None:
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message, headers=headers)


def pagination_response(
    records: Any,
    total: int,
    page: int,
    page_size: int,
) -> Dict[str, Any]:
    # 计算总页数
    total_pages = (total + page_size - 1) // page_size
    data = {
        "records": records,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }
    return success_response(data=data)


def validate_pagination_params(page: int, page_size: int) -> tuple:
    """验证分页参数

    Args:
        page: 页码
        page_size: 每页条数

    Returns:
        验证后的页码和每页条数
    """
    # 页码至少为1
    if page < 1:
        page = 1

    # 每页条数限制在1-100之间
    if page_size < 1:
        page_size = 1
    elif page_size > 100:
        page_size = 100

    return page, page_size


def get_pagination_offset(page: int, page_size: int) -> int:
    """获取分页的偏移量

    Args:
        page: 页码
        page_size: 每页条数

    Returns:
        偏移量
    """
    return (page - 1) * page_size
