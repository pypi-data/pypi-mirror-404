import os
from collections import UserDict
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

# 导入配置模块
from kalorda.config import config
from kalorda.constant import SysRole


class CurrentUser(BaseModel):
    username: str = ""
    user_id: int = 0
    role: str = ""  # 从数据库获取的实际是角色code(多个role_code用,隔开)


# 密码上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 使用配置中的密钥和算法
SECRET_KEY = config.SECRET_KEY
ALGORITHM = config.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = config.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = config.JWT_REFRESH_TOKEN_EXPIRE_DAYS

# OAuth2密码Bearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


# 密码哈希和验证
def get_password_hash(password: str) -> str:
    """获取密码的哈希值"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码是否正确"""
    return pwd_context.verify(plain_password, hashed_password)


# 创建JWT令牌
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建刷新令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# 解码和验证JWT令牌
def decode_token(token: str) -> dict:
    """解码JWT令牌"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return {}


def get_current_user(token: str = Depends(oauth2_scheme)) -> CurrentUser:
    """获取当前登录用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("username")
        user_id: int = payload.get("user_id")
        role: str = payload.get("role")
        if username is None or user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    return CurrentUser(username=username, user_id=user_id, role=role)


def get_current_active_user(current_user: CurrentUser = Depends(get_current_user)):
    """获取当前活跃的用户"""
    # 这里应该检查用户是否活跃
    # 实际应用中，应该从数据库中查询用户的活跃状态
    return current_user


def get_admin_user(current_user: CurrentUser = Depends(get_current_active_user)):
    """获取当前管理员用户"""
    # 这里应该检查用户是否具有管理员角色权限
    if not SysRole.check_role_permission(current_user.role, [SysRole.admin]):
        raise HTTPException(status_code=403, detail="您当前没有管理员权限")
    return current_user


def get_annotator_user(current_user: CurrentUser = Depends(get_current_active_user)):
    """获取当前标注用户"""
    # 这里应该检查用户是否具有标注员角色权限
    if not SysRole.check_role_permission(current_user.role, [SysRole.annotator, SysRole.admin]):
        raise HTTPException(status_code=403, detail="您当前没有标注员权限")
    return current_user


def get_reviewer_user(current_user: CurrentUser = Depends(get_current_active_user)):
    """获取当前标注审核用户"""
    # 这里应该检查用户是否是标注审核用户
    if not SysRole.check_role_permission(current_user.role, [SysRole.reviewer, SysRole.admin]):
        raise HTTPException(status_code=403, detail="您当前没有审核员权限")
    return current_user


def get_trainer_user(current_user: CurrentUser = Depends(get_current_active_user)):
    """获取当前模型训练用户"""
    # 这里应该检查用户是否具有模型训练员角色权限
    if not SysRole.check_role_permission(current_user.role, [SysRole.trainer, SysRole.admin]):
        raise HTTPException(status_code=403, detail="您当前没有训练员权限")
    return current_user


# 生成随机字符串
def generate_random_string(length: int = 32) -> str:
    """生成指定长度的随机字符串"""
    import secrets
    import string

    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


# 安全的文件上传验证
def validate_file_upload(file_name: str, file_size: int = 0) -> tuple[bool, str]:
    """验证文件上传"""
    # 从文件类型映射中获取允许的扩展名
    allowed_types = getattr(config, "ALLOWED_FILE_TYPES", [])
    allowed_extensions = set()

    # 从MIME类型中提取扩展名
    for mime_type in allowed_types:
        if "/" in mime_type:
            # 处理常见的MIME类型
            if mime_type == "image/jpeg":
                allowed_extensions.add("jpg")
                allowed_extensions.add("jpeg")
            elif mime_type == "image/png":
                allowed_extensions.add("png")
            elif mime_type == "image/gif":
                allowed_extensions.add("gif")
            elif mime_type == "image/webp":
                allowed_extensions.add("webp")
            elif mime_type == "application/pdf":
                allowed_extensions.add("pdf")
            elif mime_type == "application/msword":
                allowed_extensions.add("doc")
            elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                allowed_extensions.add("docx")
            elif mime_type == "application/vnd.ms-excel":
                allowed_extensions.add("xls")
            elif mime_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
                allowed_extensions.add("xlsx")

    # 检查文件扩展名
    extension = file_name.split(".")[-1].lower() if "." in file_name else ""

    if not extension or extension not in allowed_extensions:
        return False, f"不支持的文件类型，支持的类型: {', '.join(allowed_extensions)}"

    # 检查文件名是否包含不安全字符
    import re

    if re.search(r'[\\/:*?"<>|]', file_name):
        return False, "文件名包含非法字符"

    # 检查文件大小
    max_size = getattr(config, "MAX_FILE_SIZE", 10 * 1024 * 1024)
    if file_size > 0 and file_size > max_size:
        max_size_mb = max_size / (1024 * 1024)
        return False, f"文件大小超过限制({max_size_mb}MB)"

    return True, "文件验证通过"


# CSRF保护
def generate_csrf_token() -> str:
    """生成CSRF令牌"""
    return generate_random_string(32)


def validate_csrf_token(token: str, stored_token: str) -> bool:
    """验证CSRF令牌"""
    return token == stored_token


# 安全的URL参数处理
def sanitize_input(input_string: str, max_length: int = 255) -> str:
    """清理用户输入以防止XSS攻击"""
    if not isinstance(input_string, str):
        input_string = str(input_string)

    # 限制长度
    if len(input_string) > max_length:
        input_string = input_string[:max_length]

    # 移除HTML/JS标签
    import re

    input_string = re.sub(r"<[^>]*>", "", input_string)
    input_string = re.sub(r"&[^;]*;", "", input_string)

    return input_string


# 导出所有函数
export = {
    "pwd_context": pwd_context,
    "get_password_hash": get_password_hash,
    "verify_password": verify_password,
    "create_access_token": create_access_token,
    "create_refresh_token": create_refresh_token,
    "decode_token": decode_token,
    "get_current_user": get_current_user,
    "get_current_active_user": get_current_active_user,
    "get_current_admin_user": get_admin_user,
    "generate_random_string": generate_random_string,
    "validate_file_upload": validate_file_upload,
    "generate_csrf_token": generate_csrf_token,
    "validate_csrf_token": validate_csrf_token,
    "sanitize_input": sanitize_input,
    "CurrentUser": CurrentUser,
}
