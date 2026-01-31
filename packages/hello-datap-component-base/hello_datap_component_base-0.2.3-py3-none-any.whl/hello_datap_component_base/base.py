import asyncio
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict


class ServiceConfig(BaseModel):
    """服务配置基类"""
    name: str
    version: Optional[str] = None
    params: Dict[str, Any] = {}
    runtime_env: Optional[Dict[str, Any]] = None
    work_flow_id: Optional[int] = None
    work_flow_instance_id: Optional[int] = None
    task_id: Optional[str] = None

    model_config = ConfigDict(extra="ignore")


class BaseService(ABC):
    """服务基类，所有用户服务必须继承此类"""

    _config: Optional[ServiceConfig] = None
    _logger = None

    def __init__(self, config: ServiceConfig):
        self._config = config
        self._setup_logger()
        self._setup_runtime_env()
        # 记录服务初始化日志（版本信息会自动添加）
        self.logger.info("Service initialized")

    def _setup_logger(self):
        """设置日志器"""
        from .logger import get_service_logger, set_service_context
        # 设置全局服务上下文，使全局 logger 自动包含服务信息
        set_service_context(self._config.name, self._config.version)
        self._logger = get_service_logger(self._config.name, self._config.version)

    def _setup_runtime_env(self):
        """设置运行时环境"""
        if self._config.runtime_env:
            # 这里可以设置环境变量等
            import os
            env_vars = self._config.runtime_env.get("env_vars")
            if env_vars and isinstance(env_vars, dict):
                for key, value in env_vars.items():
                    os.environ[key] = str(value)

    @property
    def config(self) -> ServiceConfig:
        """获取配置"""
        if self._config is None:
            raise ValueError("Service not initialized with config")
        return self._config

    @property
    def logger(self):
        """获取日志器"""
        if self._logger is None:
            self._setup_logger()
        return self._logger

    @property
    def params(self) -> Dict[str, Any]:
        """获取参数"""
        return self.config.params

    @abstractmethod
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理请求的抽象方法，子类必须实现

        Args:
            data: 输入数据

        Returns:
            处理结果
        """
        pass


    async def pre_process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        预处理钩子，子类可重写

        Args:
            data: 原始数据

        Returns:
            处理后的数据
        """
        return data

    async def post_process(self, data: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        """
        后处理钩子，子类可重写

        Args:
            data: 原始数据
            result: 处理结果

        Returns:
            最终结果
        """
        return result

    def _format_result(
        self,
        code: int,
        message: str,
        output: Optional[Dict[str, Any]] = None,
        processing_time: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        格式化返回结果
        
        Args:
            code: 返回码，0 表示成功，非 0 表示失败
            message: 返回消息
            output: 用户程序的输出结果
            processing_time: 处理时间（秒）
            
        Returns:
            格式化后的结果字典
        """
        result = {
            "code": code,
            "message": message,
            "data": {
                "work_flow_id": self._config.work_flow_id,
                "work_flow_instance_id": self._config.work_flow_instance_id,
                "task_id": self._config.task_id,
                "out_put": output
            }
        }
        if processing_time is not None:
            result["processing_time"] = processing_time
        return result

    async def handle_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        完整的请求处理流程

        Args:
            data: 输入数据

        Returns:
            封装后的处理结果
        """
        import json
        
        # 记录开始时间
        start_time = time.time()
        
        try:
            # 记录入参日志（服务名称和版本会自动添加）
            self.logger.info(
                f"Processing request - Input: {json.dumps(data, ensure_ascii=False)}",
                extra={"input_data": data}
            )

            # 预处理
            processed_data = await self.pre_process(data)

            # 执行业务逻辑
            result = await self.process(processed_data)

            # 后处理
            final_result = await self.post_process(processed_data, result)

            # 计算处理时间
            processing_time = time.time() - start_time

            # 记录结果日志（服务名称和版本会自动添加）
            self.logger.info(
                f"Request processed successfully - Result: {json.dumps(final_result, ensure_ascii=False)}, Processing time: {processing_time:.3f}s",
                extra={"result": final_result, "processing_time": processing_time}
            )

            # 封装返回结果
            formatted_result = self._format_result(
                code=0,
                message="success",
                output=final_result,
                processing_time=processing_time
            )

            return formatted_result

        except Exception as e:
            # 计算处理时间（即使发生异常也记录）
            processing_time = time.time() - start_time
            
            # 记录错误日志（服务名称和版本会自动添加）
            error_msg = str(e)
            self.logger.error(
                f"Error processing request: {error_msg}, Processing time: {processing_time:.3f}s",
                extra={"error": error_msg, "error_type": type(e).__name__, "processing_time": processing_time}
            )
            
            # 封装异常返回结果
            formatted_result = self._format_result(
                code=-1,
                message=error_msg,
                output=None,
                processing_time=processing_time
            )
            
            return formatted_result