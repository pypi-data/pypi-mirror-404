from pydantic import BaseModel, field_validator

from kalorda.utils.data_verify import is_valid_email, is_valid_password, is_valid_username
from kalorda.utils.security import sanitize_input


# 请求和响应模型
class UserRegistRequest(BaseModel):
    username: str
    email: str
    password: str

    @field_validator("username")
    def username_validator(cls, v):
        verify = is_valid_username(v)
        if not verify.result:
            raise ValueError(verify.message)
        return sanitize_input(v)

    @field_validator("email")
    def email_validator(cls, v):
        verify = is_valid_email(v)
        if not verify.result:
            raise ValueError(verify.message)
        return sanitize_input(v)

    @field_validator("password")
    def password_validator(cls, v):
        verify = is_valid_password(v)
        if not verify.result:
            raise ValueError(verify.message)
        return v


class LoginRequest(BaseModel):
    username: str
    password: str

    @field_validator("username")
    def username_validator(cls, v):
        verify = is_valid_username(v)
        if not verify.result:
            raise ValueError(verify.message)
        return sanitize_input(v)

    @field_validator("password")
    def password_validator(cls, v):
        verify = is_valid_password(v)
        if not verify.result:
            raise ValueError(verify.message)
        return v


class RefreshTokenRequest(BaseModel):
    refresh_token: str
