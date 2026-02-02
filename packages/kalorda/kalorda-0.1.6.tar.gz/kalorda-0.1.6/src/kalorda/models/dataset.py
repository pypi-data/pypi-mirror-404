from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from kalorda.constant import OcrModel
from kalorda.utils.security import sanitize_input


# 数据集创建请求模型
class DatasetCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    model_type: int = Field(..., ge=1, le=len(OcrModel.get_all_models()))

    @field_validator("name")
    def validate_name(cls, v):
        if not 2 <= len(v) <= 50:
            raise ValueError("数据集名称长度必须在2-20个字符之间")
        return sanitize_input(v)

    @field_validator("description")
    def validate_description(cls, v):
        if v and len(v) > 500:
            raise ValueError("数据集备注不能超过500个字符")
        return sanitize_input(v) if v else None

    @field_validator("model_type")
    def validate_model_type(cls, v):
        if v <= 0 or v > len(OcrModel.get_all_models()):
            raise ValueError("目标模型不正确")
        return v


# 数据集更新请求模型
class DatasetUpdateRequest(BaseModel):
    id: int = Field(..., description="数据集ID")
    name: str = Field(..., min_length=2, max_length=50)
    description: Optional[str] = Field(None, max_length=500)

    @field_validator("name")
    def validate_name(cls, v):
        if not 2 <= len(v) <= 50:
            raise ValueError("数据集名称长度必须在2-20个字符之间")
        return sanitize_input(v)

    @field_validator("description")
    def validate_description(cls, v):
        if v and len(v) > 500:
            raise ValueError("数据集备注不能超过500个字符")
        return sanitize_input(v) if v else None


# 数据集查询请求模型
class DatasetQueryRequest(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)
    name: Optional[str] = None
    model_type: Optional[int] = None


# 数据集图片更新请求模型
class DatasetImageUpdateRequest(BaseModel):
    ocr_label: Optional[str] = None
    is_preocr_completed: Optional[bool] = True
    is_correct: bool
    train_data_type: int = Field(..., ge=0, le=2)


# 数据集响应模型
class DatasetResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    model_type: int
    pre_ocr_status: int
    total_images: int
    train_images: int
    val_images: int
    total_tokens: int
    train_tokens: int
    val_tokens: int
    last_upload_time: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    # Pydantic v2 配置替代旧的 orm_mode
    model_config = {"from_attributes": True}


# 数据集图片响应模型
class DatasetImageResponse(BaseModel):
    id: int
    dataset_id: int
    file_path: str
    file_name: str
    file_size: int
    width: Optional[int]
    height: Optional[int]
    tokens: Optional[int]
    ocr_result: Optional[str]  # 原始OCR识别结果
    ocr_label: Optional[str]  # 校对后的OCR标注结果
    is_preocr_completed: Optional[bool] = False
    is_correct: Optional[bool]
    train_data_type: int = Field(..., ge=0, le=2)
    processed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    # Pydantic v2 配置替代旧的 orm_mode
    model_config = {"from_attributes": True}


# 数据集分页响应模型
class DatasetPageResponse(BaseModel):
    total: int
    page: int
    page_size: int
    datasets: List[DatasetResponse]


# 数据集图片/文档分页响应模型
class DatasetImagePageResponse(BaseModel):
    total: int
    page: int
    page_size: int
    images: List[DatasetImageResponse]
