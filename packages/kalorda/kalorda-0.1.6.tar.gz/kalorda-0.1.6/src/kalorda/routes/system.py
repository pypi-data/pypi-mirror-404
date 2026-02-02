import json
import os
import platform
import shutil
import threading
import time
from datetime import datetime
from fileinput import filename
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, status
from huggingface_hub import snapshot_download as hf_snapshot_download
from modelscope import snapshot_download as ms_snapshot_download
from pydantic import BaseModel, EmailStr, field_validator

from kalorda.config import config
from kalorda.constant import OcrModel, SysRole
from kalorda.core.system_env_info import (  # get_vllm_version,; get_swift_version,; get_transformers_version,
    get_cuda_version,
    get_flash_attn_available,
    get_gpu_info,
    get_package_versions,
    get_torch_version,
    get_virtual_env,
)

# 导入数据库和模型
from kalorda.database.database import (
    OperationLogDB,
    SystemConfigDB,
    ZmqMessageDB,
    with_db_transaction,
)
from kalorda.models.system import ModelConfigRequest, ModelDownloadRequest
from kalorda.utils.api_response import error_response, success_response
from kalorda.utils.i18n import _

# 设置日志 - 使用全局日志记录器
# 设置日志 - 使用全局日志记录器
from kalorda.utils.logger import logger
from kalorda.utils.security import (
    CurrentUser,
    get_admin_user,
    get_current_active_user,
    get_password_hash,
    sanitize_input,
)
from kalorda.utils.zmq_pubsub import (
    MODELDOWN_TOPIC,
    Message,
    datetime_converter,
    get_message_id,
)

# 创建路由
router = APIRouter(
    prefix="/system",
    tags=["系统管理"],
    responses={
        404: {"description": _("未找到")},
        422: {"description": _("请求参数验证失败")},
    },
)


# 下载模型权重
def download_model_weights(user_id: int, model_code: str, down_from: str):
    """
    下载模型权重
    """
    # 从模型列表中找到对应的模型
    model = None
    for _model in OcrModel.get_all_models():
        if model_code == _model["code"]:
            model = _model
            break

    if not model:
        return

    model_id = ""
    if down_from == "huggingface":
        model_id = model["hf_id"]
    elif down_from == "modelscope":
        model_id = model["ms_id"]

    weights_dir = ""

    try:
        home_dir = os.path.expanduser("~")
        # 保存模型权重的总目录
        cache_dir = os.path.join(home_dir, "kalorda-models")
        # 总目录不存在则创建
        os.makedirs(cache_dir, exist_ok=True)

        # 检查当前是否正在下载该模型
        lock_file = os.path.join(cache_dir, f"{model_code}.lock")
        if os.path.exists(lock_file):
            return
        # 创建文件
        with open(lock_file, "w") as f:
            f.write("")

        # 下载器自动下载保存的文件夹
        weights_dir_auto = ""
        if down_from == "huggingface":
            weights_dir_auto = hf_snapshot_download(model_id, cache_dir=cache_dir)
        elif down_from == "modelscope":
            weights_dir_auto = ms_snapshot_download(model_id, cache_dir=cache_dir)

        # 模型目录中如果有下划线需要替换为短横线，否则ms-swift微调会报错
        # 下划线替换为短横线
        weights_dir = weights_dir_auto.replace("_", "-") if "_" in weights_dir_auto else weights_dir_auto
        # dotsocr模型目录中包含多个-，需要替换为一个-
        weights_dir = weights_dir.replace("---", "-")
        if weights_dir != weights_dir_auto:
            try:
                if os.path.exists(weights_dir):
                    shutil.rmtree(weights_dir)
            except OSError as e:
                logger.error(f"删除旧权重目录失败: {e}")
            # 模型目录重命名
            os.rename(weights_dir_auto, weights_dir)

        # 保存到数据库
        SystemConfigDB.update(config_value=weights_dir).where(
            SystemConfigDB.config_key == f"{model_code}_weights_dir"
        ).execute()
        # 针对不同模型的权重目录打补丁
        patch_model_weight(model_code, weights_dir)

    except Exception as e:
        logger.error(f"模型权重下载失败: {e}")
    finally:
        # 删除锁文件
        if os.path.exists(lock_file):
            os.remove(lock_file)

        # 下载完成结果写入zmq消息自动会被sse_stream_generator订阅到，前端会收到下载完成的sse通知
        msg_id = get_message_id()
        ZmqMessageDB.create(
            topic=MODELDOWN_TOPIC.format(user_id),  # zmq消息转sse消息的模型下载任务的主题
            type="modeldown",  # 消息类型：模型下载消息
            msg_id=msg_id,
            data=json.dumps(
                {
                    "model_code": model_code,
                    "down_from": down_from,
                    "weights_dir": weights_dir,
                    "status": weights_dir != "",
                },
                default=datetime_converter,
            ),
        )


# 下载模型权重
@router.post("/model/download")
def model_download(
    download: ModelDownloadRequest,
    current_user: CurrentUser = Depends(get_admin_user),
):
    """
    下载模型权重
    """
    user_id = current_user.user_id
    down_from = download.down_from
    model_code = download.model_code

    # 检查是否正在下载该模型
    home_dir = os.path.expanduser("~")
    # 保存模型权重的总目录
    cache_dir = os.path.join(home_dir, "kalorda-models")
    # 总目录不存在则创建
    os.makedirs(cache_dir, exist_ok=True)

    # 检查当前是否正在下载该模型
    lock_file = os.path.join(cache_dir, f"{model_code}.lock")
    if os.path.exists(lock_file):
        return error_response(message=_("该模型权重正在后台下载，不用重复下载"))

    try:
        # 启动子线程下载模型权重，避免阻塞主线程，及时返回响应
        # 子线程中执行下载模型权重的函数，下载完成后通过sse通知前端
        download_thread = threading.Thread(
            target=download_model_weights,
            args=(user_id, model_code, down_from),
        )
        download_thread.start()

    except Exception as e:
        logger.error(f"模型权重下载过程失败: {e}")
        return error_response(message=_("模型权重下载过程失败"))

    return success_response(True, message=_("模型权重下载已启动"))


def patch_model_weight(model_code: str, model_dir: str):
    """
    针对不同模型的权重目录打补丁, 主要是针对got_ocr和dotsocr模型
    """
    if model_dir is None or model_dir == "":
        return

    if model_dir.endswith("/"):
        model_dir = model_dir[:-1]

    if model_code == OcrModel.got_ocr["code"]:
        patch_file = config.BASE_DIR + "/vllm_infer/got_ocr/config.json"
        target_file = model_dir + "/config.json"
        shutil.copy(patch_file, target_file)

    if model_code == OcrModel.dotsocr["code"]:
        patch_file = config.BASE_DIR + "/vllm_infer/dotsocr/configuration_dots.py"
        target_file = model_dir + "/configuration_dots.py"
        shutil.copy(patch_file, target_file)


# 获取系统运行环境信息
@router.get("/info")
def get_users(current_user: dict = Depends(get_admin_user)):
    """
    获取系统运行环境信息
    """
    time1 = time.time()  # 耗时统计开始
    # 操作系统以及版本
    os_name = platform.system()
    os_version = platform.version()
    # PYTHON版本
    python_version = platform.python_version()
    #  torch版本
    torch_version = get_torch_version()
    #  cuda版本
    cuda_version = get_cuda_version()
    # GPU信息
    gpu_info = get_gpu_info()
    # 虚拟环境名称
    virtual_env = get_virtual_env()

    # 所有pip包版本
    package_versions = get_package_versions()
    # vllm版本
    vllm_version = next((v for p, v in package_versions if p == "vllm"), "")
    # swift版本
    swift_version = next((v for p, v in package_versions if p == "ms_swift"), "")
    # transformers版本
    transformers_version = next((v for p, v in package_versions if p == "transformers"), "")
    # flash_attn版本
    flash_attn_version = next((v for p, v in package_versions if p == "flash_attn"), "")

    ocr_models = OcrModel.get_all_models()

    for model in ocr_models:
        config = (
            SystemConfigDB.select_active().where(SystemConfigDB.config_key == f"{model['code']}_weights_dir").first()
        )
        model["weights_dir"] = config.config_value if config else ""

    data = {
        # 系统软硬件环境信息
        "os_name": os_name,
        "os_version": os_version,
        "python_version": python_version,
        "torch_version": torch_version,
        "cuda_version": cuda_version,
        "virtual_env": virtual_env,
        "vllm_version": vllm_version,
        "swift_version": swift_version,
        "transformers_version": transformers_version,
        "flash_attn_version": flash_attn_version,
        "flash_attn_available": get_flash_attn_available(),
        "gpu_info": gpu_info,
        "ocr_models": ocr_models,
    }
    time2 = time.time()  # 耗时统计结束
    logger.info(f"获取系统运行环境信息耗时: {time2 - time1}秒")
    return success_response(data)


@router.post("/config/save")
@with_db_transaction(use_transaction=True, retry_count=2)
def model_config_save(
    model_config_list: List[ModelConfigRequest],
    current_user: CurrentUser = Depends(get_admin_user),
):
    # 权限检查：判断用户是否有系统配置的权限
    if not SysRole.check_role_permission(current_user.role, [SysRole.admin]):
        return error_response(_("您当前没有系统配置的权限"))

    for model_config in model_config_list:
        model_code = model_config.model_code
        weights_dir = model_config.weights_dir
        SystemConfigDB.update(config_value=weights_dir).where(
            SystemConfigDB.config_key == f"{model_code}_weights_dir"
        ).execute()
        patch_model_weight(model_code, weights_dir)

    # 记录操作日志
    OperationLogDB.create(
        user=current_user.user_id,
        action="保存系统配置",
        resource_type="system_config",
        details="管理员更新了全部模型权重目录",
    )

    return success_response(True)
