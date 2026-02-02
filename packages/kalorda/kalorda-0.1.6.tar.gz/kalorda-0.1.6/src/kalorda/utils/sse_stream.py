import asyncio
import json
import threading
from datetime import datetime
from typing import Any, Dict
from uuid import uuid4

from fastapi import Request

from kalorda.utils.logger import logger
from kalorda.utils.zmq_pubsub import DEFAULT_PORT, Message, ZmqSubscriber, get_message_id

# 常量定义
HEARTBEAT_INTERVAL = 15  # 心跳间隔（秒）

# 本地客户端存储
_local_clients: Dict[str, Dict[str, Any]] = {}


async def sse_stream_generator(request: Request, client_id: str, sub_topic: str):
    """SSE流式响应生成器，用于建立和维护服务器发送事件的连接"""
    worker_id = str(uuid4())[:8]
    send_queue: asyncio.Queue[Message] = asyncio.Queue()

    # 注册客户端
    _local_clients[client_id] = {
        "client_id": client_id,
        "worker_id": worker_id,
        "send_queue": send_queue,
        "last_seen": datetime.now().timestamp(),
        "connected_at": datetime.now().isoformat(),
    }
    logger.info(f"已注册客户端: {client_id}")

    # 心跳任务
    heartbeat_task = asyncio.create_task(send_heartbeats(client_id))

    subscriber = ZmqSubscriber(DEFAULT_PORT, sub_topic)
    subscriber.open_sub_socket()

    def sse_stream_close():
        """关闭SSE流"""
        if heartbeat_task:
            heartbeat_task.cancel()
        if subscriber:
            subscriber.close_sub_socket()
        if client_id in _local_clients:
            del _local_clients[client_id]
        logger.info(f"已关闭客户端: {client_id}")

    try:
        # 发送sse连接成功消息
        connected_message = Message(
            type="connected",
            msg_id=get_message_id(),
            data={"worker_id": worker_id, "client_id": client_id},
            priority=0,
            created_at=datetime.now().timestamp(),
        )

        yield json.dumps(connected_message.to_dict())

        # 处理发送消息
        while True:
            # 检查客户端是否断开连接
            if await request.is_disconnected():
                logger.info(f"客户端 {client_id} 已断开连接")
                break

            # 更新客户端最后活动时间
            if client_id in _local_clients:
                _local_clients[client_id]["last_seen"] = datetime.now().timestamp()

            # 处理队列中的消息
            try:
                # 1、从自己的队列中获取消息sse推送到前端
                send_queue_len = send_queue.qsize()
                if send_queue_len > 0:
                    message = await asyncio.wait_for(send_queue.get(), timeout=1)  # 单位秒
                    yield json.dumps(message.to_dict())
                    send_queue.task_done()

                # 2、订阅的zmq的消息通过sse通道推送到前端
                zmq_message = subscriber.receive_message()
                if zmq_message:
                    message = Message(
                        type=zmq_message["type"],
                        msg_id=zmq_message["msg_id"] or get_message_id(),
                        data=zmq_message["data"],
                        priority=zmq_message["priority"],
                        created_at=zmq_message["created_at"],
                    )
                    yield json.dumps(message.to_dict())

            except asyncio.TimeoutError:
                logger.info(f"获取sse asyncio.Queue队列 {client_id} 超时，继续循环")
                pass  # 超时，继续循环

    except asyncio.CancelledError as e:
        logger.info(f"SSE流处理取消 (客户端 {client_id}): {str(e)}")
    except Exception as e:
        logger.error(f"SSE流处理错误 (客户端 {client_id}): {str(e)}")

    finally:
        sse_stream_close()


def send_client_message(client_id: str, message: Message):
    """向特定客户端发送消息"""
    try:
        # 检查客户端是否存在
        if client_id in _local_clients:
            # 直接发送给本地客户端
            try:
                if message.msg_id == "":
                    message.msg_id = get_message_id()

                _local_clients[client_id]["send_queue"].put_nowait(message)
                logger.info(f"消息已发送到客户端 {client_id}: {message}")
                return True
            except Exception as queue_error:
                logger.error(f"将消息加入队列失败 (客户端 {client_id}): {str(queue_error)}")
                return False
        else:
            logger.warning(f"客户端不存在: {client_id}")
            return False

    except Exception as e:
        logger.error(f"发送消息失败 (客户端 {client_id}): {str(e)}")
        return False


def send_user_message(user_id: int, message: Message):
    """向特定用户发送消息，根据client_id格式 'client_${user_id}-${task_id}-${rnd_id}' 匹配用户的所有客户端"""
    try:
        # 构造用户前缀，格式为 'client_${user_id}-'
        user_prefix = f"client_{user_id}-"

        # 获取匹配用户的所有客户端ID
        user_clients = [cid for cid in _local_clients.keys() if cid.startswith(user_prefix)]

        logger.info(f"==========================所有客户端ID: {_local_clients.keys()}")
        for cid in _local_clients.keys():
            logger.info(f"==========================当前已存在的客户端 {cid}")

        if not user_clients or len(user_clients) == 0:
            logger.debug(f"{threading.current_thread().native_id}未找到用户 user_id = {user_id} 的任何客户端连接")
            return False
        else:
            logger.debug(
                f"{threading.current_thread().native_id}已找到用户 user_id = {user_id} 的{len(user_clients)}个客户端连接"
            )

        # 向所有匹配的客户端发送消息
        success_count = 0
        for client_id in user_clients:
            result = send_client_message(client_id, message)
            if result:
                success_count += 1

        logger.info(f"向用户 {user_id} 的 {success_count}/{len(user_clients)} 个客户端发送消息成功")
        return success_count > 0

    except Exception as e:
        logger.error(f"发送消息失败 (用户 {user_id}): {str(e)}")
        return False


async def send_heartbeats(client_id: str):
    """定期发送心跳消息（内部方法）"""
    while True:
        try:
            await asyncio.sleep(HEARTBEAT_INTERVAL)
            heartbeat_message = Message(
                type="heartbeat",
                msg_id=get_message_id(),
                data={},
                priority=0,
                created_at=datetime.now().timestamp(),
                timestamp=datetime.now().timestamp(),
            )
            # 发送心跳
            if client_id in _local_clients:
                _local_clients[client_id]["send_queue"].put_nowait(heartbeat_message)
        except Exception as e:
            logger.error(f"发送心跳失败 (客户端 {client_id}): {str(e)}")
            await asyncio.sleep(5)  # 出错后重试间隔


# 导出需要的类和方法
__all__ = [
    "Message",
    "sse_stream_generator",
    "send_client_message",
    "send_user_message",
    "HEARTBEAT_INTERVAL",
]
