"""
这是一个工作流引擎的封装，如果一个项目需要集成到工作流中，可以通过引入该类 就可以通过该类
工作流引擎交互
这个类的运行机制
1. 从环境变量中获取链接工作流的信息 (KAFKA ADDRESS)
2. 建立一个全局的对象 Workflow 实例
3. send_message() 发送进度消息
4. write_output(key,value) 会将结果写回到工作流引擎，工作流引擎保存該值并在合适的时候传递
   到下一个节点

"""
import atexit
import json
import os
import sys
import threading
from abc import ABC
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum
from typing import Self

from kafka import KafkaProducer
from loguru import logger

# 移除默认配置，重新添加并开启 flush=True 确保实时性
logger.remove()
# 获取环境变量中的日志级别，默认为 INFO
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logger.add(
    sys.stdout,
    level=log_level, # 动态级别
    colorize=True,
    enqueue=True,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>"
)

"""
  消息来源
"""
class SourceType(str,Enum):
    ENGINE = "engine"
    MODULE = "module"


class RunningStatus(str,Enum):
    RUNNING = "running"
    COMPLETED = "completed"

"""
    消息类型
"""
class MessageType(str, Enum):
    UNKNOWN  =  "unknown"
    PROGRESS = "progress"
    OUTPUT   = "output" #输出消息

@dataclass
class WorkflowMessage(ABC):
    taskId: str = field(init=False)
    sendTime: str = field(init=False)
    messageType: MessageType = MessageType.UNKNOWN

    def __post_init__(self):
        # 1. 核心修复：确保父类初始化基础字段
        self.taskId = os.getenv("KAFKA_TASK_ID", "")
        self.sendTime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def to_dict(self):
        return asdict(self)




@dataclass
class ProgressContent:
    version: str = 3
    progress: int = 0
    runningStatus: RunningStatus = RunningStatus.RUNNING  # running, completed
    runningInfo: str = ""  ## Anything starting
    title: str = ""  # Anything module name
    titleId: str = ""  # Anything module id
    source: SourceType = SourceType.MODULE  # [module, engine]
    rank: int = 0
    totalProgress: int = 0
    totalRunningStatus: RunningStatus = RunningStatus.RUNNING  # running, completed
    totalRunningInfo: str = ""  # Anything module @str
    inferProgress: int = 0
    inferFilename: str = ""  # somefile.tif
    inferPreviewFilename: str = ""  # somefile_id.tif
    inferGeoInfo: str = "POLYGON EMPTY"  # POLYGON(({x1} {y1}, {x2} {y2}, {x3} {y3}, {x4} {y4}, {x1} {y1})) @str - list
    inferObjectGeoInfo: str = "POLYGON EMPTY"  # POLYGON(({x1} {y1}, {x2} {y2}, {x3} {y3}, {x4} {y4}, {x1} {y1})) @str - list


@dataclass
class ProgressMessage(WorkflowMessage):
    messageContent: ProgressContent = field(default_factory=ProgressContent)

    def __post_init__(self):
        # 2. 核心修复：显式调用父类，防止 taskId 丢失
        super().__post_init__()
        self.messageType = MessageType.PROGRESS

    def set_source(self, source=None, rank=None) ->Self:
        if source is not None:
            self.messageContent.source = source
        if rank is not None:
            self.messageContent.rank = rank
        return self

    def set_title(self, title:str|None=None, title_id:str|None=None) ->Self:
        if title is not None:
            self.messageContent.title = title
        if title_id is not None:
            self.messageContent.titleId = title_id
        return self
    """
        引擎消息
        
    """
    def engine_message(self,rank=None) -> Self:
        self.messageContent.source = SourceType.ENGINE
        if rank is not None:
            self.messageContent.rank = rank
        return self
    """
        子节点消息
    """
    def module_message(self,rank=None) -> Self:
        self.messageContent.source = SourceType.MODULE
        if rank is not None:
            self.messageContent.rank = rank
        return self

@dataclass
class OutputMessage(WorkflowMessage):
    kvList: list = field(default_factory=list)

    def __post_init__(self):
        # 2. 核心修复：显式调用父类，防止 taskId 丢失
        super().__post_init__()
        self.messageType = MessageType.OUTPUT



class Workflow:
    _instance = None
    _lock = threading.Lock()

    # 私有变量定义
    _kafka_address: str | None = None
    _kafka_topic: str | None = None
    _kafka_taskid: str | None = None
    _producer: KafkaProducer | None = None

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(Workflow, cls).__new__(cls)
                    # 1. 在 __new__ 中完成配置加载
                    cls._instance._load_config()
                    # 2. 初始化连接
                    cls._instance._init_connection()
        return cls._instance

    def __init__(self):
        # 防止重复初始化逻辑（虽然 __new__ 已经处理了核心部分）
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        atexit.register(self.close)

    def close(self):
        """确保所有消息已发出并关闭连接"""
        if self._producer is not None:
            try:
                logger.info("[WORKFLOW] 正在关闭 Kafka 连接，正在冲刷剩余消息...")
                self._producer.flush(timeout=10) # 设置超时，防止无限等待
                self._producer.close()
                self._producer = None
                logger.success("[WORKFLOW] Kafka 连接已安全关闭")
            except Exception as e:
                logger.error(f"[WORKFLOW] 关闭连接时发生异常: {e}")

    def _load_config(self):
        """内部逻辑：从环境变量加载配置"""
        self._kafka_address = os.getenv("KAFKA_SERVER_IP_PORT")
        self._kafka_topic = os.getenv("KAFKA_TOPIC")
        self._kafka_taskid = os.getenv("KAFKA_TASK_ID")


    def _is_config_invalid(self) -> bool:
        """校验配置是否完整（非空且不全是空格）"""
        configs = [self._kafka_address, self._kafka_topic]
        return any(c is None or c.strip() == "" for c in configs)

    def _init_connection(self):
        """建立真正的 Kafka 连接"""
        if self._is_config_invalid():
            logger.error(f"[WORKFLOW]环境变量 KAFKA_SERVER_IP_PORT 或 KAFKA_TOPIC 未设置")
            return

        try:
            # 初始化 KafkaProducer
            self._producer = KafkaProducer(
                bootstrap_servers=self._kafka_address,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                # 设置超时时间，防止进程卡死
                retries=3
            )
            logger.info(f"[WORKFLOW] 成功连接至 Kafka: {self._kafka_address}")
            logger.info(f"[WORKFLOW] 发送消息到 {self._kafka_topic}")
        except Exception as e:
            logger.error(f"[WORKFLOW] Kafka 连接失败: {e}")

    def write_output(self,**kwargs):
        message = OutputMessage()
        message.kvList=[{k: v} for k, v in kwargs.items()]
        self.send_message(message)

    def send_message(self, message: WorkflowMessage):
        self._send_message(message.to_dict())

    def _send_message(self, data: dict):
        """外部调用的主方法"""
        if self._producer is None:
            logger.info("[WF-OFFLINE] {}", json.dumps(data, ensure_ascii=False))
            return
        try:
            # 补丁：如果由于某种原因 taskId 没取到，给个默认值防止 Kafka 消费端崩溃
            if not data.get("taskId"):
                data["taskId"] = self._kafka_taskid or "unknown-task"

            self._producer.send(self._kafka_topic, value=data)
            # 注意：在高频发送时，建议去掉这里的 self._producer.flush() 提高性能
            # 已经在 atexit 中处理了退出时的冲刷
            logger.debug("[WF-SENT] {}", data.get("messageType"))
        except Exception as e:
            logger.warning(f"[WORKFLOW] 发送任务异常: {e}")

    @staticmethod
    def info(msg):
        logger.info(f"[WORKFLOW] {msg}")

    @staticmethod
    def warn(msg):
        logger.warning(f"[WORKFLOW] {msg}")

    @staticmethod
    def error(msg):
        logger.error(f"[WORKFLOW] {msg}")

    @staticmethod
    def debug(msg):
        logger.debug(f"[WORKFLOW] {msg}")
# 使用示例
if __name__ == "__main__":
    wf = Workflow()
    # 构造进度消息
    pm = ProgressMessage().engine_message(1)
    pm.set_title(title="遥感影像处理模块", title_id="mod-001")

    # 更新具体进度
    pm.messageContent.progress = 50
    pm.messageContent.runningInfo = "正在解析 GeoTIFF 头部信息..."

    wf.write_output(FINAL_DATA="HELLO_WORLD",PIXEL_SIZE="3568")
