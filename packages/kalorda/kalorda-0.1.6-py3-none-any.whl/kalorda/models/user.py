from typing import Optional

from pydantic import BaseModel, field_validator

from kalorda.utils.data_verify import is_valid_email, is_valid_password, is_valid_username
from kalorda.utils.security import sanitize_input


# 请求和响应模型
class UserSaveRequest(BaseModel):
    user_id: Optional[int] = None
    password: Optional[str] = ""
    username: str = ""
    email: str = ""
    role: str = ""

    @field_validator("username")
    def username_validator(cls, v):
        verify = is_valid_username(v)
        if not verify.result:
            raise ValueError(verify.message)
        return sanitize_input(v)

    @field_validator("password")
    def password_validator(cls, v):
        # 没密码不验证，管理员端是可改可不改密码的逻辑
        if not v or len(v) == 0:
            return ""
        # 有密码则需要验证
        verify = is_valid_password(v)
        if not verify.result:
            raise ValueError(verify.message)
        return sanitize_input(v)

    @field_validator("email")
    def email_validator(cls, v):
        verify = is_valid_email(v)
        if not verify.result:
            raise ValueError(verify.message)
        return sanitize_input(v)
