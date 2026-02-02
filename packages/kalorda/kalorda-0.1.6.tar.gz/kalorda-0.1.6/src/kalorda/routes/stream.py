from datetime import datetime

from fastapi import APIRouter, HTTPException, Request
from sse_starlette.sse import EventSourceResponse

import kalorda.utils.logger as logger
from kalorda.utils.i18n import _, t
from kalorda.utils.sse_stream import send_user_message, sse_stream_generator
from kalorda.utils.zmq_pubsub import (
    FINETUNE_TOPIC,
    MODELDOWN_TOPIC,
    MODELTEST_TOPIC,
    Message,
    get_message_id,
)

# 创建路由器
router = APIRouter(prefix="/stream", tags=["SSE"])


# API接口路由
# client_id = 'client_${user_id}-${rnd_id}'
@router.get("/trainrun/{client_id}/{task_id}")
async def trainrun_client_sse(request: Request, client_id: str, task_id: int):
    """建立SSE连接"""
    if not client_id:
        raise HTTPException(status_code=400, detail=_("客户端ID不能为空"))

    logger.info(f"客户端 {client_id} 请求建立SSE连接")
    # user_id = client_id.split("-")[0].replace("client_", "")
    sub_topic = FINETUNE_TOPIC.format(task_id)  # sse消息从zmq的指定主题处订阅得到
    logger.info(f"客户端 {client_id} 订阅主题 {sub_topic}")

    # 创建并返回EventSourceResponse
    return EventSourceResponse(
        sse_stream_generator(request, client_id, sub_topic),
        media_type="text/event-stream",
    )


# client_id = 'client_${user_id}-${rnd_id}'
@router.get("/modeltest/{client_id}")
async def modeltest_client_sse(request: Request, client_id: str):
    """建立SSE连接"""
    if not client_id:
        raise HTTPException(status_code=400, detail=_("客户端ID不能为空"))

    logger.info(f"客户端 {client_id} 请求建立SSE连接")
    user_id = client_id.split("-")[0].replace("client_", "")
    sub_topic = MODELTEST_TOPIC.format(user_id)  # sse消息从zmq的指定主题处订阅得到
    logger.info(f"客户端 {client_id} 订阅主题 {sub_topic}")

    # 创建并返回EventSourceResponse
    return EventSourceResponse(
        sse_stream_generator(request, client_id, sub_topic),
        media_type="text/event-stream",
    )


# client_id = 'client_${user_id}-${rnd_id}'
@router.get("/modeldown/{client_id}")
async def modeldown_client_sse(request: Request, client_id: str):
    """建立SSE连接"""
    if not client_id:
        raise HTTPException(status_code=400, detail=_("客户端ID不能为空"))

    logger.info(f"客户端 {client_id} 请求建立SSE连接")
    user_id = client_id.split("-")[0].replace("client_", "")
    sub_topic = MODELDOWN_TOPIC.format(user_id)  # sse消息从zmq的指定主题处订阅得到
    logger.info(f"客户端 {client_id} 订阅主题 {sub_topic}")

    # 创建并返回EventSourceResponse
    return EventSourceResponse(
        sse_stream_generator(request, client_id, sub_topic),
        media_type="text/event-stream",
    )
