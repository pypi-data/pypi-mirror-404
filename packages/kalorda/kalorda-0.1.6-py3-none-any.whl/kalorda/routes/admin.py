import json
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Json, field_validator

from kalorda.constant import SysRole

# 导入数据库和模型
from kalorda.database.database import OperationLogDB, SystemConfigDB, UserDB, db_manager
from kalorda.models.user import (
    UserSaveRequest,
)
from kalorda.utils.api_response import error_response, success_response
from kalorda.utils.i18n import _

# 设置日志 - 使用全局日志记录器
from kalorda.utils.logger import logger
from kalorda.utils.security import (
    CurrentUser,
    get_admin_user,
    get_current_active_user,
    get_password_hash,
    sanitize_input,
)

# 创建路由
router = APIRouter(
    prefix="/admin",
    tags=["用户管理"],
    responses={
        404: {"description": _("未找到")},
        422: {"description": _("请求参数验证失败")},
    },
)


# 管理端控制开放或关闭外部注册功能
@router.post("/changeFreeRegist", summary="控制开放或关闭外部注册功能")
def change_free_regist(
    request: Dict = Body(..., description="是否开放外部注册"),
    current_user: CurrentUser = Depends(get_admin_user),
):
    """
    开放或关闭外部注册功能（需要管理员权限）
    """
    try:
        # 确保数据库连接已打开
        db_manager.get_connection()
        free_regist = request.get("free_regist")
        if free_regist is None or not isinstance(free_regist, bool):
            return error_response(_("参数错误"))

        # 更新系统配置
        db_config = SystemConfigDB.select_active().where(SystemConfigDB.config_key == "free_regist").first()
        db_config.config_value = str(free_regist)
        db_config.save()
        return success_response(_("修改成功"))
    except Exception as e:
        logger.error(f"修改外部注册功能失败: {str(e)}")
        return error_response(_("修改外部注册功能失败"))


# 管理端分页获取用户列表，目前后端是一次性返第一页(5000条)数据，前端再重新自己分页
@router.post("/allUsers")
def all_users(
    skip: int = Body(0, description="跳过数量"),
    limit: int = Body(5000, description="限制查询量"),
    role: Optional[str] = Body(None, description="角色"),
    search: Optional[str] = Body(None, description="搜索"),
    current_user: dict = Depends(get_admin_user),
):
    """
    获取用户列表（需要管理员权限）
    """

    try:
        # 确保数据库连接已打开
        db_manager.get_connection()
        # 构建查询
        query = UserDB.select_active()

        # 搜索过滤
        if search and search != "":
            query = query.where((UserDB.username.contains(search)) | (UserDB.email.contains(search)))

        # 角色过滤
        if role and role != "":
            query = query.where(UserDB.role.contains(role))

        # 排序和分页
        users = query.order_by(UserDB.created_at.desc()).offset(skip).limit(limit)

        # 转换为响应模型
        user_list = []
        for user in users:
            user_list.append(
                {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,
                    "status": user.status,
                    "login_count": user.login_count,
                    "created_at": user.created_at,
                    "last_login": user.last_login,
                }
            )

        # 是否开放外部注册
        free_regist = SystemConfigDB.select().where(SystemConfigDB.config_key == "free_regist").first().config_value
        data = {
            "user_list": user_list,
            "total": users.count(),
            "roles": SysRole.get_all_roles(),
            "free_regist": free_regist,
        }

        logger.info(f"管理员 {current_user.username} 获取用户列表")
        return success_response(data)
    except Exception as e:
        logger.error(f"获取用户列表失败: {str(e)}")
        return error_response(_("获取用户列表失败"))


# 管理端硬删除用户
@router.post("/delUser")
def del_user(
    user_id: int = Body(..., description="用户ID"),
    current_user: CurrentUser = Depends(get_admin_user),
):
    # 检查用户是否存在
    user = UserDB.select_active().where(UserDB.id == user_id).first()
    if not user:
        return error_response(_("用户不存在"))

    # 检查是否删除自己
    if user.id == current_user.user_id:
        return error_response(_("不能删除自己的账户"))
    # 硬删除
    # UserDB.delete().where(UserDB.id == user_id).execute()
    user.is_deleted = True  # 软删除
    user.save()

    # 记录操作日志
    OperationLogDB.create(
        user=current_user.user_id,
        action="删除用户",
        resource_type="user",
        details=f"用户ID={user_id}",
    )

    return success_response(_("用户删除成功"))


# 管理端新增或修改用户
@router.post("/saveUser")
def save_user(
    user_data: UserSaveRequest,
    current_user: CurrentUser = Depends(get_admin_user),
):
    """
    保存（新增或修改）用户（需要管理员权限）

    - **user_id**: 用户ID
    - **username**: 用户名
    - **email**: 邮箱
    - **password**: 密码
    - **role**: 用户角色
    """
    try:
        # 修改
        if user_data.user_id:
            user = UserDB.select_active().where(UserDB.id == user_data.user_id).first()
            if not user:
                return error_response("用户不存在")
            user.username = user_data.username
            user.email = user_data.email
            user.role = user_data.role
            if user_data.password:
                user.password = get_password_hash(user_data.password)
                user.password_updated_at = datetime.now()
            user.save()
            return success_response(_("修改用户信息成功"))
        # 新增
        if not user_data.user_id:
            user = UserDB.create(
                username=user_data.username,
                email=user_data.email,
                password=get_password_hash(user_data.password),
                role=user_data.role,
                status="active",
                password_updated_at=datetime.now(),
            )
            user.save()
            return success_response(_("新增用户信息成功"))
    except Exception as e:
        logger.error(f"保存用户信息失败: {str(e)}")
        return error_response(_("新增或修改用户失败"))


# 删除用户（软删除）
@router.post("/softDelUser/{user_id}")
def soft_del_User(user_id: int, current_user: CurrentUser = Depends(get_admin_user)):
    """
    删除用户（需要管理员权限）

    - **user_id**: 用户ID
    """
    try:
        # 查询用户
        user = UserDB.select_active().where(UserDB.id == user_id).first()

        # 检查用户是否存在
        if not user:
            return error_response(_("用户不存在"))

        # 检查是否删除自己
        if user.id == current_user.user_id:
            return error_response(_("不能删除自己的账户"))

        # 软删除用户
        user.deleted = True
        user.save()

        logger.info(f"管理员 {current_user.username} 软删除用户: {user_id}")

        OperationLogDB.create(
            user_id=current_user.user_id,
            action="soft_delete_user",
            resource_type="user",
            resource_id=str(user.id),
        )

        return success_response(message=_("用户已成功删除"))
    except Exception as e:
        logger.error(f"删除用户失败: {str(e)}")
        # 记录操作日志
        OperationLogDB.create(
            user_id=current_user.user_id,
            action="soft_delete_user",
            resource_type="user",
            resource_id=str(user_id),
        )
        return error_response(_("删除用户失败"))


# 恢复软删除的用户
@router.post("/restoreUser/{user_id}")
def restore_user(user_id: int, current_user: CurrentUser = Depends(get_admin_user)):
    """
    恢复已删除的用户（需要管理员权限）

    - **user_id**: 用户ID
    """
    try:
        # 查询已删除的用户
        user = UserDB.select().where((UserDB.id == user_id) & (UserDB.is_deleted)).first()

        # 检查用户是否存在
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=_("未找到已删除的用户"))

        # 恢复用户
        user.deleted = False
        user.save()

        logger.info(f"管理员 {current_user.username} 恢复用户: {user_id}")

        # 记录操作日志
        try:
            log = OperationLogDB.create(
                user=current_user.user_id,
                action="restore_user",
                resource_type="user",
                resource_id=str(user.id),
            )
            log.save()
        except Exception as log_error:
            logger.warning(f"记录操作日志失败: {str(log_error)}")

        return success_response(message=_("用户已成功恢复"))
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"恢复用户失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=_("恢复用户失败，请稍后重试"),
        )


# 获取SMTP设置
@router.post("/getSmtpSetting")
def get_smtp_setting(current_user: CurrentUser = Depends(get_admin_user)):
    """
    获取SMTP设置（需要管理员权限）
    """
    try:
        smtp_host = SystemConfigDB.select_active().where(SystemConfigDB.config_key == "smtp_host").first()
        if not smtp_host:
            smtp_host = ""
        else:
            smtp_host = smtp_host.config_value
        smtp_port = SystemConfigDB.select_active().where(SystemConfigDB.config_key == "smtp_port").first()
        if not smtp_port:
            smtp_port = ""
        else:
            smtp_port = smtp_port.config_value
        smtp_user = SystemConfigDB.select_active().where(SystemConfigDB.config_key == "smtp_user").first()
        if not smtp_user:
            smtp_user = ""
        else:
            smtp_user = smtp_user.config_value
        smtp_password = SystemConfigDB.select_active().where(SystemConfigDB.config_key == "smtp_password").first()
        if not smtp_password:
            smtp_password = ""
        else:
            smtp_password = smtp_password.config_value

        data = {
            "smtp_host": smtp_host,
            "smtp_port": smtp_port,
            "smtp_user": smtp_user,
            "smtp_password": smtp_password,
        }

        return success_response(data=data)
    except Exception as e:
        logger.error(f"获取SMTP设置失败: {str(e)}")
        return error_response(_("获取SMTP设置失败"))


# 保存SMTP设置
@router.post("/saveSmtpSetting")
def save_smtp_setting(
    request: Dict = Body(..., description="SMTP设置"),
    current_user: CurrentUser = Depends(get_admin_user),
):
    """
    保存SMTP设置（需要管理员权限）
    """
    try:
        smtp_host = request.get("smtp_host", "")
        smtp_port = request.get("smtp_port", "")
        smtp_user = request.get("smtp_user", "")
        smtp_password = request.get("smtp_password", "")

        if not smtp_host or not smtp_port or not smtp_user or not smtp_password:
            return error_response(_("SMTP设置不能为空"))

        # 保存SMTP设置
        SystemConfigDB.update(config_value=smtp_host).where(SystemConfigDB.config_key == "smtp_host").execute()
        SystemConfigDB.update(config_value=smtp_port).where(SystemConfigDB.config_key == "smtp_port").execute()
        SystemConfigDB.update(config_value=smtp_user).where(SystemConfigDB.config_key == "smtp_user").execute()
        SystemConfigDB.update(config_value=smtp_password).where(SystemConfigDB.config_key == "smtp_password").execute()
        # 记录操作日志
        try:
            log = OperationLogDB.create(
                user=current_user.user_id,
                action="save_smtp_setting",
                resource_type="system_config",
                resource_id="smtp_setting",
            )
            log.save()
        except Exception as log_error:
            logger.warning(f"记录操作日志失败: {str(log_error)}")

        logger.info(f"管理员 {current_user.username} 保存SMTP设置")
        return success_response(message=_("SMTP设置已成功保存"))
    except Exception as e:
        logger.error(f"保存SMTP设置失败: {str(e)}")
        return error_response(_("保存SMTP设置失败"))
