from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# 测试文件响应
class TestOCRFileResponse(BaseModel):
    id: int = Field(..., description="文件ID")
    original_filename: str = Field(..., description="原始文件名")
    file_path: str = Field(..., description="文件路径")
    file_size: int = Field(..., description="文件大小")
    remark: Optional[str] = Field(None, description="文件备注")
    images: List[Dict[str, Any]] = Field(..., description="图片信息列表")
    create_at: datetime = Field(..., description="创建时间")
    update_at: datetime = Field(..., description="更新时间")
