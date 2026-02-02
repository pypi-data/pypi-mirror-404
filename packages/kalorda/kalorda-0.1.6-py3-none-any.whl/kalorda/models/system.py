from pydantic import BaseModel, field_validator

from kalorda.utils.i18n import _


class ModelDownloadRequest(BaseModel):
    down_from: str = ""
    model_code: str = ""

    @field_validator("down_from")
    def validate_down_from(cls, v):
        if v not in ["huggingface", "modelscope"]:
            raise ValueError(_("模型来源错误"))
        return v

    @field_validator("model_code")
    def validate_model_code(cls, v):
        if len(v) == 0:
            raise ValueError(_("模型代码错误"))
        return v


class ModelConfigRequest(BaseModel):
    model_code: str = ""
    weights_dir: str = ""

    @field_validator("model_code")
    def validate_model_code(cls, v):
        if len(v) == 0:
            raise ValueError(_("模型代码错误"))
        return v
