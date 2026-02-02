import json
import multiprocessing
import signal
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

import zmq
from peewee import Function

import kalorda.utils.logger as logger
from kalorda.database.database import (
    ZmqMessageDB,
)

DEFAULT_PORT = 5557

FINETUNE_TOPIC = "sse/finetune_{0}_topic"
MODELTEST_TOPIC = "sse/modeltest_{0}_topic"
MODELDOWN_TOPIC = "sse/modeldown_{0}_topic"


def get_message_id() -> str:
    """生成唯一的消息ID"""
    return f"msg_{int(datetime.now().timestamp())}_{str(uuid4())[:8]}"


def datetime_converter(o):
    if isinstance(o, datetime):
        return o.isoformat()


@dataclass
class Message:
    """消息类，用于封装发送给客户端的消息"""

    type: str = "message"  # 消息类型，默认是"message" 其他 "connected" "heartbeat" "trainlog" "trainstatus"
    msg_id: str = ""  # 消息ID
    data: Any = None  # 消息数据
    priority: Optional[int] = 0  # 优先级，默认为0
    created_at: Optional[float] = None  # 消息创建的时间，默认为None
    timestamp: float = datetime.now().timestamp()  # 消息发送的时间戳，默认为None

    def to_dict(self) -> Dict[str, Any]:
        """将消息转换为字典格式"""
        return {
            "type": self.type,
            "msg_id": self.msg_id,
            "data": self.data,
            "priority": self.priority,
            "created_at": self.created_at,
            "timestamp": self.timestamp,
        }


def zmq_message_publisher():
    """zmq消息处理函数"""
    try:
        # 从数据库中查询最新的zmq消息
        zmq_messages = ZmqMessageDB.select_active().order_by(ZmqMessageDB.created_at.asc()).limit(10)
        if not zmq_messages:
            return None

        topic_message_pairs = []
        for zmq_message in zmq_messages:
            topic = f"{zmq_message.topic}"
            # 转换为字典
            message = Message(
                type=zmq_message.type,
                msg_id=zmq_message.msg_id,
                data=zmq_message.data,
                priority=zmq_message.priority,
                created_at=zmq_message.created_at.timestamp(),
            )
            # 转换为JSON字符串
            message = f"{json.dumps(message.to_dict())}"
            topic_message_pairs.append((topic, message))

        # 删除已提取的zmq消息（根据id批量物理删除）
        ZmqMessageDB.delete().where(ZmqMessageDB.id.in_([zmq_message.id for zmq_message in zmq_messages])).execute()
        return topic_message_pairs

    except Exception as e:
        logger.error(f"查询zmq消息失败: {str(e)}")
        return None


# 发布zmq消息入口
def zmq_publish(pub_port: int = DEFAULT_PORT, callback: Function = None):
    """打开发布者套接字"""
    p = multiprocessing.Process(target=_open_pub_socket, kwargs={"pub_port": pub_port, "callback": callback})
    p.daemon = True
    p.start()


def _open_pub_socket(pub_port: int = DEFAULT_PORT, callback: Function = None):
    """打开发布者套接字"""
    if callback is None:
        logger.error("zmq发布者回调函数不能为空")
        return
    context = zmq.Context()
    pub_socket = context.socket(zmq.PUB)
    pub_socket.setsockopt(zmq.LINGER, 0)
    # 设置发送缓冲区大小（单位为字节）
    pub_socket.setsockopt(zmq.SNDBUF, 10 * 1024 * 1024)  # 10M
    # 设置发送端高水位标记
    pub_socket.sndhwm = 5000
    pub_socket.bind(f"tcp://*:{pub_port}")

    def _close_pub_socket(sign: int = signal.SIGINT, frame=None):
        """关闭ZMQ套接字"""

        if pub_socket:
            logger.info("开始关闭发布者...")
            pub_socket.close()
        if context:
            context.term()
            context.destroy()
        logger.info("发布者已关闭")

    # 当收到退出信号时，关闭套接字
    signal.signal(signal.SIGINT, _close_pub_socket)
    signal.signal(signal.SIGTERM, _close_pub_socket)

    while True:
        try:
            if not pub_socket or pub_socket.closed:
                logger.error("zmq发布者已关闭")
                break
            topic_message_pairs = callback()
            if not topic_message_pairs:
                # logger.debug("没有zmq消息")
                time.sleep(1)
                continue
            for topic, message in topic_message_pairs:
                pub_socket.send_string(f"{topic} {message}")
                # logger.debug(f"zmq发布消息 {topic} {message}")
            # time.sleep(0.5)  # 放慢便于观察
        except Exception as e:
            logger.error(f"zmq发布消息失败: {str(e)}")
            _close_pub_socket()
            break


class ZmqSubscriber:
    """ZMQ订阅者类，用于订阅zmq消息"""

    def __init__(self, sub_port: int = DEFAULT_PORT, sub_topic: str = None):
        """初始化ZMQ订阅者"""
        self.context = None
        self.sub_socket = None
        self.sub_port = sub_port
        self.sub_topic = sub_topic

    def open_sub_socket(self):
        """打开ZMQ订阅套接字"""
        try:
            logger.info("开始打开订阅者套接字...")
            self.context = zmq.Context()
            self.sub_socket = self.context.socket(zmq.SUB)
            self.sub_socket.setsockopt(zmq.LINGER, 0)  # 避免在套接字关闭时阻塞
            self.sub_socket.setsockopt_string(zmq.SUBSCRIBE, self.sub_topic)
            # 设置接收缓冲区大小（单位为字节）
            self.sub_socket.setsockopt(zmq.RCVBUF, 10 * 1024 * 1024)  # 10M
            # 设置接收端高水位标记
            self.sub_socket.rcvhwm = 5000
            self.sub_socket.setsockopt(zmq.RCVTIMEO, 1000)  # 非阻塞设置：设置接收超时为1000毫秒
            self.sub_socket.connect(f"tcp://localhost:{self.sub_port}")
        except Exception as e:
            logger.error(f"打开订阅者套接字时出错: {str(e)}")

    # 非阻塞模式接收
    def receive_message(self):
        """接收ZMQ消息"""
        try:
            if not self.sub_socket or self.sub_socket.closed:
                logger.error("zmq订阅者已关闭")
                return None
            # 使用 poll 检查是否可以接收消息
            if self.sub_socket.poll(timeout=10):  # timeout=0 表示非阻塞检查
                message = self.sub_socket.recv_string(flags=zmq.NOBLOCK)  # 非阻塞接收
                # logger.info(f"接收到ZMQ消息: {message}")
                topic, data = message.split(" ", 1)
                return json.loads(data)
        except Exception as e:
            logger.error(f"接收ZMQ消息时出错: {str(e)}")
            return None

    def close_sub_socket(self, sign: int = signal.SIGINT, frame=None):
        """关闭ZMQ订阅套接字"""
        try:
            if self.sub_socket:
                self.sub_socket.disconnect(f"tcp://localhost:{self.sub_port}")
                self.sub_socket.close()
                self.sub_socket = None
            if self.context:
                self.context.term()
                self.context.destroy()
                self.context = None
            logger.info("已执行关闭订阅者套接字...")
        except Exception as e:
            logger.error(f"关闭订阅者套接字时出错: {str(e)}")
