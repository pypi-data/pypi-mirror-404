"""
数据处理平台组件基类 - 统一的服务管理框架

提供标准化的数据处理组件开发框架，统一用户代码的入参和出参以及程序执行入口。
"""

from .base import BaseService, ServiceConfig
from .runner import ServiceRunner
from .config import ServerConfig, RuntimeEnv
from .logger import setup_logging, get_service_logger
from .discover import find_service_classes, get_single_service_class

# 导入 logger 实例
from .logger import logger

__version__ = "0.2.3"
__author__ = "zhaohaidong"
__email__ = "zhaohaidong389@hellobike.com"

__all__ = [
    "BaseService",
    "ServiceConfig",
    "ServerConfig",
    "RuntimeEnv",
    "ServiceRunner",
    "setup_logging",
    "get_service_logger",
    "logger",
    "find_service_classes",
    "get_single_service_class",
]