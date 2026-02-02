from datetime import datetime, timedelta
from typing import Dict, Optional, Union

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from kalorda.config import config
from kalorda.constant import SysRole

# 导入数据库和模型
from kalorda.database.database import SystemConfigDB, UserDB, db_manager, with_db_transaction
from kalorda.models.auth import (
    LoginRequest,
    RefreshTokenRequest,
    UserRegistRequest,
)
from kalorda.utils.aes_crypto import aes_encode
from kalorda.utils.api_response import (
    Code,
    error_response,
    raise_http_error,
    success_response,
)
from kalorda.utils.data_verify import (
    is_valid_email,
    is_valid_password,
    is_valid_username,
)
from kalorda.utils.i18n import _, t

# 设置日志 - 使用全局日志记录器
from kalorda.utils.logger import logger
from kalorda.utils.security import (
    CurrentUser,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_active_user,
    get_password_hash,
    verify_password,
)

# 创建路由
router = APIRouter(
    prefix="/auth",
    tags=["认证"],
    responses={
        404: {"description": _("未找到")},
        422: {"description": _("请求参数验证失败")},
    },
)


# 检查是否可以外部注册
@router.get("/freeRegist")
def free_regist():
    try:
        # 确保数据库连接已打开
        db_manager.get_connection()
        db_config = SystemConfigDB.select().where(SystemConfigDB.config_key == "free_regist").first()
        if not db_config or db_config.config_value == "False":
            return success_response(False)
        return success_response(True)
    except Exception as e:
        logger.error(f"检查是否允许注册失败: {str(e)}")
        return error_response(_("检查注册状态失败"))


# 用户自行注册
@router.post("/register")
def register_user(user: UserRegistRequest):
    # 检查系统配置：是否允许外部注册
    db_config = SystemConfigDB.select().where(SystemConfigDB.config_key == "free_regist").first()
    if not db_config or db_config.config_value == "False":
        return error_response(_("系统已禁止外部注册"))

    # 检查用户名是否已存在
    existing_user = UserDB.select().where(UserDB.username == user.username).first()
    if existing_user:
        return error_response(_("用户名已存在"))

    # 检查邮箱是否已存在
    existing_email = UserDB.select().where(UserDB.email == user.email).first()
    if existing_email:
        return error_response(_("邮箱已被注册"))

    # 创建新用户
    try:
        data = UserDB.create(
            username=user.username,
            email=user.email,
            password=get_password_hash(user.password),
            role=SysRole.annotator.get("code"),  # 默认是普通用户 标注员
            status="active",
            password_updated_at=datetime.now(),
        )
        logger.info(f"新用户注册成功: {user.username}")
        return success_response(data)
    except Exception as e:
        logger.error(f"用户注册失败: {str(e)}")
        return error_response(_("用户注册失败，请稍后重试"))


@router.post("/createResetPasswdCode")
def create_reset_passwd_code(
    request: Dict = Body(..., description="发送重置密码验证码到用户邮箱"),
):
    email = request.get("email")
    if not is_valid_email(email):
        return error_response(_("邮箱格式错误"))
    # 检查邮箱是否存在
    existing_email = UserDB.select().where(UserDB.email == email).first()
    if not existing_email:
        return error_response(_("邮箱不存在"))
    # 生成重置密码验证码
    # 随机生成6位数字和字母混合的验证码
    import random
    import string

    reset_code = "".join(random.choices(string.ascii_letters + string.digits, k=6))
    # 缓存重置密码验证码
    from kalorda.utils.cache import set_cache
    from kalorda.utils.email_send import send_email

    reset_code_prefix = "reset_code_"
    set_cache(f"{reset_code_prefix}{reset_code}", email)

    # 发送重置密码验证码
    result = send_email(
        email,
        _("密码重置验证码"),
        t(_("您的密码重置验证码为: {reset_code}")).format(reset_code=reset_code),
    )
    if not result.get("status"):
        return error_response(result.get("message"))
    return success_response(_("重置密码链接已发送"))


@router.post("/resetPassword")
def reset_password(
    request: Dict = Body(..., description="重置密码"),
):
    reset_code = request.get("resetCode")
    password1 = request.get("password1")
    password2 = request.get("password2")
    if not reset_code or not password1 or not password2:
        return error_response(_("参数错误"))

    verify = is_valid_password(password1)
    if not verify.result:
        return error_response(verify.message)

    if password1 != password2:
        return error_response(_("两次密码不一致"))

    # 检查重置密码验证码
    from utils.cache import clear_cache, get_cache

    reset_code_prefix = "reset_code_"
    email = get_cache(f"{reset_code_prefix}{reset_code}")
    if not email:
        return error_response(_("重置密码验证码错误"))
    # 重置密码
    user = UserDB.select().where(UserDB.email == email).first()
    if not user:
        return error_response(_("用户不存在"))
    user.password = get_password_hash(password1)
    user.password_updated_at = datetime.now()
    user.save()
    clear_cache(f"{reset_code_prefix}{reset_code}")
    return success_response(_("密码重置成功"))


# 用户登录
@router.post("/token")  # 添加token路径以兼容前端请求
@router.post("/login")  # 添加token路径以兼容前端请求
@with_db_transaction(retry_count=2)
def login_for_access_token(request: LoginRequest):
    """
    用户登录获取访问令牌

    - **username**: 用户名或邮箱
    - **password**: 密码
    """
    # 查找用户（支持用户名或邮箱登录）
    user = UserDB.select().where((UserDB.username == request.username) | (UserDB.email == request.username)).first()

    # 验证用户和密码
    if not user:
        return error_response(_("用户名或密码错误"))

    try:
        # 验证密码
        is_valid = verify_password(request.password, user.password)
        if not is_valid:
            return error_response(_("用户名或密码错误"))
    except Exception as e:
        logger.error(f"登录验证异常: {str(e)}")
        return error_response(_("用户名或密码错误"))

    # 检查用户状态
    if user.status != "active":
        return error_response(_("用户账号已禁用"))

    # 更新登录信息
    user.last_login = datetime.now()
    user.login_count = user.login_count + 1
    user.save()

    # 创建访问令牌和刷新令牌
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"username": user.username, "user_id": user.id, "role": user.role},
        expires_delta=access_token_expires,
    )

    refresh_token = create_refresh_token(data={"username": user.username, "user_id": user.id})

    logger.info(f"用户登录成功: {user.username}")

    data = {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token,
        "expires_in": access_token_expires.seconds,
        "user_id": user.id,
        "role": aes_encode(user.role, config.AES_KEY),
    }
    return success_response(data)


# 刷新访问令牌
@router.post("/refresh")
def refresh_access_token(request: RefreshTokenRequest):
    """
    使用刷新令牌获取新的访问令牌

    - **refresh_token**: 刷新令牌
    """
    try:
        # 解码刷新令牌
        payload = decode_token(request.refresh_token)

        # 检查令牌类型
        if payload.get("type") != "refresh":
            return error_response(_("无效的刷新令牌"), Code.AUTHORIZED_ERROR)

        # 获取用户信息
        username: str = payload.get("username")
        user_id: int = payload.get("user_id")

        if not username or not user_id:
            return error_response(_("无效的刷新令牌"), Code.AUTHORIZED_ERROR)

        # 验证用户是否存在
        user = UserDB.select().where(UserDB.id == user_id).first()

        if not user or user.username != username:
            return error_response(_("无效的刷新令牌"), Code.AUTHORIZED_ERROR)

        # 创建新的访问令牌
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"username": user.username, "user_id": user.id, "role": user.role},
            expires_delta=access_token_expires,
        )

        # 创建新的刷新令牌
        refresh_token = create_refresh_token(data={"username": user.username, "user_id": user.id})

        logger.info(f"用户令牌刷新成功: {user.username}")

        data = {
            "access_token": access_token,
            "token_type": "bearer",
            "refresh_token": refresh_token,
            "expires_in": access_token_expires.seconds,
            "user_id": user.id,
            "role": aes_encode(user.role, config.AES_KEY),  # 避免直接明文给前端
        }
        return success_response(data)

    except Exception as e:
        logger.error(f"令牌刷新失败: {str(e)}")
        return error_response(_("令牌刷新失败"), Code.AUTHORIZED_ERROR)


# 退出登录
@router.post("/logout")
def logout_access_token():
    return success_response(message=_("退出登录成功"))


# 获取用户信息
@router.post("/userInfo")
def read_users_me(
    user_id: int = Body(None),
    current_user: CurrentUser = Depends(get_current_active_user),
):
    """
    获取用户的信息
    """
    try:
        # 确保数据库连接已打开
        db_manager.get_connection()
        if not user_id:
            user_id = current_user.user_id

        # 查询用户信息
        user = UserDB.select().where(UserDB.id == user_id).first()
        if not user:
            return error_response(_("用户不存在"))

        # 构建响应数据
        data = {
            "user": {
                "userid": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,  # 字符串
            },
            # 获取SysRole全部角色
            "roles": SysRole.get_all_roles(),
        }
        return success_response(data)
    except Exception as e:
        logger.error(f"获取用户信息失败: {str(e)}")
        return error_response(_("获取用户信息失败"))


@router.post("/editUserInfo")
def edit_user_info(
    username: str = Body(None),
    email: str = Body(None),
    current_user: dict = Depends(get_current_active_user),
):
    """
    用户修改信息

    - **username**: 用户名
    - **email**: 邮箱
    """
    verify = is_valid_username(username)
    if not verify.result:
        return error_response(verify.message)
    verify = is_valid_email(email)
    if not verify.result:
        return error_response(verify.message)

    # 查询当前用户信息
    user = UserDB.select().where(UserDB.id == current_user.user_id).first()
    if not user:
        return error_response(_("用户不存在"))

    if username != user.username:
        user1 = UserDB.select().where(UserDB.username == username).first()
        if user1:
            return error_response(t(_("用户 {username} 已存在")).format(username=username))

    if email != user.email:
        user2 = UserDB.select().where(UserDB.email == email).first()
        if user2:
            return error_response(t(_("邮箱 {email} 已存在")).format(email=email))

    user.username = username
    user.email = email
    user.save()

    return success_response(message=_("用户信息修改成功"))


# 用户修改密码
@router.post("/editPassword")
def edit_password(
    current_user: CurrentUser = Depends(get_current_active_user),
    old_password: str = Body(None),
    new_password: str = Body(None),
):
    """
    用户修改密码

    - **old_password**: 当前密码
    - **new_password**: 新密码
    """
    # 验证参数
    verify = is_valid_password(new_password)
    if not verify.result:
        return error_response(verify.message)

    if not old_password or not new_password:
        return error_response(_("密码错误"))

    if old_password == new_password:
        return error_response(_("新密码不能与旧密码相同"))

    user = UserDB.select().where(UserDB.id == current_user.user_id).first()
    if not user:
        return error_response(_("用户不存在"))

    is_valid = verify_password(old_password, user.password)
    if not is_valid:
        return error_response(_("当前密码错误"))

    # 更新密码
    user.password = get_password_hash(new_password)
    user.password_updated_at = datetime.now()
    user.save()

    logger.info(f"用户id={current_user.user_id}密码修改成功")

    return success_response(message=_("密码修改成功"))
