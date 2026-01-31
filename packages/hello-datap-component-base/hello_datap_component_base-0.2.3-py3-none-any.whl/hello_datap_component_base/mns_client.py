"""
阿里云 MNS 消息队列客户端
"""
import json
import os
import time
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# MNS 消息体最大长度（64KB），预留一些空间给 JSON 结构
MNS_MAX_MESSAGE_SIZE = 64 * 1024
# 错误消息最大长度（预留空间给其他字段）
MAX_ERROR_MESSAGE_LENGTH = 8 * 1024  # 8KB


class MNSClient:
    """阿里云 MNS 消息队列客户端"""
    
    def __init__(
        self, 
        queue_name: str = "aiinfra-data-process-component-result-queue",
        max_retries: int = 3,
        retry_delay: float = 1.0,
        retry_backoff: float = 2.0
    ):
        """
        初始化 MNS 客户端
        
        Args:
            queue_name: 队列名称，默认为 aiinfra-data-process-component-result-queue
            max_retries: 最大重试次数，默认 3 次（可通过环境变量 MNS_MAX_RETRIES 配置）
            retry_delay: 初始重试延迟（秒），默认 1.0 秒（可通过环境变量 MNS_RETRY_DELAY 配置）
            retry_backoff: 重试延迟的指数退避倍数，默认 2.0（可通过环境变量 MNS_RETRY_BACKOFF 配置）
        """
        self.queue_name = queue_name
        
        # 从环境变量读取重试配置，如果没有则使用默认值
        self.max_retries = int(os.environ.get('MNS_MAX_RETRIES', max_retries))
        self.retry_delay = float(os.environ.get('MNS_RETRY_DELAY', retry_delay))
        self.retry_backoff = float(os.environ.get('MNS_RETRY_BACKOFF', retry_backoff))
        
        self._client = None
        self._queue = None
        self._initialized = False
        self._Message = None  # Message 类，延迟加载
        
    def _init_client(self):
        """初始化 MNS 客户端（延迟加载）"""
        if self._initialized:
            return
            
        try:
            # 尝试导入阿里云 MNS SDK
            from mns.account import Account
            from mns.queue import Queue, Message
            
            # 保存 Message 类供后续使用
            self._Message = Message
            
            # 从环境变量获取 MNS 配置
            endpoint = os.environ.get('MNS_ENDPOINT')
            access_key_id = os.environ.get('MNS_ACCESS_KEY_ID')
            access_key_secret = os.environ.get('MNS_ACCESS_KEY_SECRET')
            
            if not all([endpoint, access_key_id, access_key_secret]):
                # 如果 MNS_ENDPOINT 不存在，静默跳过（已在 get_mns_client 中检查）
                # 如果 MNS_ENDPOINT 存在但其他配置不完整，记录警告
                if endpoint:
                    logger.warning(
                        "MNS 配置不完整，无法发送消息到队列。"
                        "需要设置环境变量: MNS_ACCESS_KEY_ID, MNS_ACCESS_KEY_SECRET"
                    )
                self._initialized = True  # 标记为已初始化，避免重复警告
                return
            
            # 创建 MNS 账户
            account = Account(endpoint, access_key_id, access_key_secret)
            # 获取队列（使用 get_queue 方法）
            self._queue = account.get_queue(self.queue_name)
            self._client = account
            self._initialized = True
            logger.info(f"MNS 客户端初始化成功，队列: {self.queue_name}")
            
        except ImportError:
            logger.warning(
                "未安装阿里云 MNS SDK，无法发送消息到队列。"
                "请安装: pip install aliyun-mns"
            )
            self._initialized = True  # 标记为已初始化，避免重复警告
        except Exception as e:
            logger.error(f"初始化 MNS 客户端失败: {e}")
            self._initialized = True  # 标记为已初始化，避免重复警告
    
    def _is_retryable_exception(self, exception: Exception) -> bool:
        """
        判断异常是否可重试
        
        Args:
            exception: 异常对象
            
        Returns:
            是否可重试
        """
        exception_str = str(exception)
        exception_type = type(exception).__name__
        
        # 网络相关异常，可重试
        retryable_keywords = [
            'NetworkException',
            'NetWorkException',
            'Connection reset',
            'Connection refused',
            'Connection timeout',
            'timeout',
            'ConnectionError',
            'ConnectTimeout',
            'ReadTimeout',
            'Errno 104',  # Connection reset by peer
            'Errno 111',  # Connection refused
            'Errno 110',  # Connection timed out
        ]
        
        # 检查异常类型和消息中是否包含可重试的关键词
        for keyword in retryable_keywords:
            if keyword in exception_type or keyword in exception_str:
                return True
        
        return False
    
    def _send_message_once(self, message_body: str) -> bool:
        """
        发送消息的单次尝试
        
        Args:
            message_body: JSON 格式的消息字符串
            
        Returns:
            是否发送成功
        """
        # 创建 Message 对象（MNS SDK 要求使用 Message 对象）
        if self._Message is None:
            from mns.queue import Message
            self._Message = Message
        
        msg = self._Message(message_body)
        
        # 发送消息
        self._queue.send_message(msg)
        return True
    
    def _truncate_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        截断消息中过长的字段，确保消息体不超过 MNS 限制
        
        Args:
            message: 原始消息字典
            
        Returns:
            截断后的消息字典
        """
        # 深拷贝，避免修改原始数据
        import copy
        truncated = copy.deepcopy(message)
        
        # 截断 message 字段（错误信息）
        if 'message' in truncated and isinstance(truncated['message'], str):
            original_len = len(truncated['message'])
            if original_len > MAX_ERROR_MESSAGE_LENGTH:
                truncated['message'] = (
                    truncated['message'][:MAX_ERROR_MESSAGE_LENGTH] + 
                    f"\n... [truncated, original length: {original_len}]"
                )
                logger.warning(
                    f"消息的 message 字段过长（{original_len} 字符），已截断至 {MAX_ERROR_MESSAGE_LENGTH} 字符"
                )
        
        # 检查整体消息大小，如果仍然过大，进一步截断 out_put
        message_body = json.dumps(truncated, ensure_ascii=False)
        if len(message_body.encode('utf-8')) > MNS_MAX_MESSAGE_SIZE:
            if 'data' in truncated and isinstance(truncated['data'], dict):
                if 'out_put' in truncated['data'] and truncated['data']['out_put'] is not None:
                    out_put_str = json.dumps(truncated['data']['out_put'], ensure_ascii=False)
                    if len(out_put_str) > MAX_ERROR_MESSAGE_LENGTH:
                        truncated['data']['out_put'] = {
                            '_truncated': True,
                            '_message': f'Output too large ({len(out_put_str)} chars), truncated'
                        }
                        logger.warning(
                            f"消息的 out_put 字段过大（{len(out_put_str)} 字符），已截断"
                        )
        
        return truncated

    def send_message(self, message: Dict[str, Any]) -> bool:
        """
        发送消息到队列（带重试逻辑）
        
        Args:
            message: 要发送的消息字典
            
        Returns:
            是否发送成功
        """
        self._init_client()
        
        if not self._queue:
            logger.warning("MNS 队列未初始化，跳过消息发送")
            return False
        
        # 截断过长的消息字段
        truncated_message = self._truncate_message(message)
        
        # 将消息转换为 JSON 字符串
        message_body = json.dumps(truncated_message, ensure_ascii=False)
        
        # 重试逻辑
        last_exception = None
        delay = self.retry_delay
        
        for attempt in range(self.max_retries + 1):  # 总共尝试 max_retries + 1 次
            try:
                success = self._send_message_once(message_body)
                if success:
                    if attempt > 0:
                        logger.info(
                            f"消息已成功发送到队列 {self.queue_name} "
                            f"（第 {attempt + 1} 次尝试）"
                        )
                    else:
                        logger.info(f"消息已发送到队列 {self.queue_name}")
                    return True
                    
            except Exception as e:
                last_exception = e
                
                # 判断是否可重试
                if not self._is_retryable_exception(e):
                    # 不可重试的异常，直接返回失败
                    logger.error(
                        f"发送消息到队列失败（不可重试的异常）: {e}",
                        exc_info=True
                    )
                    return False
                
                # 可重试的异常
                if attempt < self.max_retries:
                    # 还有重试机会
                    logger.warning(
                        f"发送消息到队列失败（第 {attempt + 1} 次尝试）: {e}，"
                        f"{delay:.2f} 秒后重试..."
                    )
                    time.sleep(delay)
                    delay *= self.retry_backoff  # 指数退避
                else:
                    # 已用完所有重试机会
                    logger.error(
                        f"发送消息到队列失败（已重试 {self.max_retries} 次）: {e}",
                        exc_info=True
                    )
        
        # 所有重试都失败了
        if last_exception:
            logger.error(
                f"发送消息到队列最终失败（共尝试 {self.max_retries + 1} 次）: {last_exception}",
                exc_info=True
            )
        return False
    
    def send_result(
        self,
        code: int,
        message: str,
        work_flow_id: Optional[int],
        work_flow_instance_id: Optional[int],
        task_id: Optional[str],
        output: Optional[Dict[str, Any]] = None,
        processing_time: Optional[float] = None
    ) -> bool:
        """
        发送处理结果到队列
        
        Args:
            code: 返回码，0 表示成功，非 0 表示失败
            message: 返回消息
            work_flow_id: 工作流ID
            work_flow_instance_id: 工作流实例ID
            task_id: 任务ID
            output: 用户程序的输出结果（正常时为结果，异常时为 None）
            processing_time: 处理时间（秒）
            
        Returns:
            是否发送成功
        """
        result_message = {
            "code": code,
            "message": message,
            "data": {
                "work_flow_id": work_flow_id,
                "work_flow_instance_id": work_flow_instance_id,
                "task_id": task_id,
                "out_put": output
            }
        }
        if processing_time is not None:
            result_message["processing_time"] = processing_time
        
        return self.send_message(result_message)


def get_mns_client(queue_name: Optional[str] = None) -> Optional[MNSClient]:
    """
    获取 MNS 客户端实例
    
    Args:
        queue_name: 队列名称，如果为 None 则使用默认队列名
        
    Returns:
        MNSClient 实例，如果配置不完整则返回 None
    """
    # 如果环境变量中没有 MNS_ENDPOINT 配置，则不发送 MNS，直接返回 None
    if not os.environ.get('MNS_ENDPOINT'):
        return None
    
    if queue_name is None:
        queue_name = os.environ.get('MNS_QUEUE_NAME', 'aiinfra-data-process-component-result-queue')
    
    client = MNSClient(queue_name)
    client._init_client()
    
    # 如果客户端未正确初始化，返回 None
    if not client._queue:
        return None
    
    return client

