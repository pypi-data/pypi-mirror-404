import logging
import sys
from typing import Optional, Dict, Any
import json
from datetime import datetime
from pythonjsonlogger import jsonlogger


class ServiceLoggerAdapter(logging.LoggerAdapter):
    """服务日志适配器，自动在每条日志中添加服务名称和版本信息"""
    
    def __init__(self, logger: logging.Logger, service_name: str, version: Optional[str] = None):
        super().__init__(logger, {})
        self.service_name = service_name
        self.version = version
    
    def process(self, msg, kwargs):
        """处理日志消息，添加服务信息"""
        # 确保 extra 字典存在
        if 'extra' not in kwargs:
            kwargs['extra'] = {}
        
        # 添加服务名称和版本信息
        kwargs['extra']['service'] = self.service_name
        if self.version:
            kwargs['extra']['version'] = self.version
        
        return msg, kwargs


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """自定义 JSON 格式化器"""

    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]):
        super().add_fields(log_record, record, message_dict)

        # 添加时间戳
        if not log_record.get('timestamp'):
            log_record['timestamp'] = datetime.utcnow().isoformat()

        # 添加日志级别
        if not log_record.get('level'):
            log_record['level'] = record.levelname

        # 添加进程信息
        log_record['pid'] = record.process
        log_record['process_name'] = record.processName

        # 添加文件位置
        log_record['file'] = record.filename
        log_record['line'] = record.lineno
        log_record['function'] = record.funcName
        
        # 确保服务信息在 JSON 日志中（如果 extra 中有的话）
        if 'service' in log_record:
            log_record['service'] = log_record['service']
        if 'version' in log_record:
            log_record['version'] = log_record['version']


# 全局变量：存储日志文件路径
_log_file_path: Optional[str] = None


def get_log_file_path() -> Optional[str]:
    """
    获取当前日志文件路径
    
    Returns:
        日志文件路径，如果未创建日志文件则返回 None
    """
    return _log_file_path


def setup_logging(
        level: str = "INFO",
        json_format: bool = False,
        service_name: str = "unknown",
        version: Optional[str] = None
) -> Optional[str]:
    """
    设置日志配置
    
    兼容 Ray 分布式计算框架：日志输出到 stdout/stderr，Ray 会自动收集这些日志。

    Args:
        level: 日志级别
        json_format: 是否使用 JSON 格式
        service_name: 服务名称
        version: 服务版本（可选）
        
    Returns:
        日志文件路径，如果未创建日志文件则返回 None
    """
    global _log_file_path
    
    # 检测是否在 Ray 环境中运行
    is_ray_env = False
    try:
        import ray
        is_ray_env = ray.is_initialized()
    except ImportError:
        pass
    
    # 移除所有现有的处理器
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # 设置日志级别
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO

    root_logger.setLevel(numeric_level)

    # 创建处理器
    if json_format:
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s',
            rename_fields={
                'level': 'levelname',
                'timestamp': 'asctime'
            }
        )
    else:
        # 改进日志格式，包含服务名称和版本
        version_str = f" v{version}" if version else ""
        formatter = logging.Formatter(
            f'%(asctime)s - [{service_name}{version_str}] - %(levelname)s - '
            f'%(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    # 控制台处理器（输出到 stdout，Ray 会自动捕获）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 错误日志输出到 stderr（Ray 也会捕获）
    error_handler = logging.StreamHandler(sys.stderr)
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)
    root_logger.addHandler(error_handler)

    # 文件处理器（在 Ray 环境中可能不可用，优雅处理）
    log_file_path = None
    if not is_ray_env:
        # 非 Ray 环境才尝试创建文件日志
        try:
            log_file_path = f"{service_name}.log"
            file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            _log_file_path = log_file_path
        except (IOError, PermissionError):
            pass  # 无法创建日志文件，只输出到控制台
    
    return log_file_path


def get_service_logger(name: str, version: Optional[str] = None) -> ServiceLoggerAdapter:
    """
    获取服务专用的日志器（带服务名称和版本信息）
    
    兼容 Ray 分布式计算框架：日志输出到 stdout/stderr，Ray 会自动收集。

    Args:
        name: 服务名称
        version: 服务版本（可选）

    Returns:
        配置好的日志适配器
    """
    logger = logging.getLogger(f"service.{name}")

    # 如果还没有处理器，添加一个默认的
    if not logger.handlers:
        # 检测是否在 Ray 环境中运行
        is_ray_env = False
        try:
            import ray
            is_ray_env = ray.is_initialized()
        except ImportError:
            pass
        
        # stdout 处理器（Ray 会自动捕获）
        console_handler = logging.StreamHandler(sys.stdout)
        # 改进日志格式，包含服务名称和版本
        version_str = f" v{version}" if version else ""
        formatter = logging.Formatter(
            f'%(asctime)s - [{name}{version_str}] - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # stderr 处理器用于错误日志（Ray 也会捕获）
        error_handler = logging.StreamHandler(sys.stderr)
        error_handler.setFormatter(formatter)
        error_handler.setLevel(logging.ERROR)
        logger.addHandler(error_handler)
        
        logger.setLevel(logging.INFO)
        
        # 在非 Ray 环境中，尝试添加文件处理器
        if not is_ray_env:
            try:
                file_handler = logging.FileHandler(f"{name}.log", encoding='utf-8')
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
            except (IOError, PermissionError):
                pass

    # 返回适配器，自动添加服务信息
    return ServiceLoggerAdapter(logger, name, version)


# 全局 logger 实例，方便用户直接导入使用
_global_logger: Optional[ServiceLoggerAdapter] = None
_global_service_name: Optional[str] = None
_global_version: Optional[str] = None


def set_service_context(service_name: str, version: Optional[str] = None):
    """
    设置全局服务上下文（服务名称和版本）
    
    当服务初始化时，会自动调用此函数设置上下文。
    设置后，全局 logger 会自动包含服务信息。
    
    Args:
        service_name: 服务名称
        version: 服务版本（可选）
    """
    global _global_logger, _global_service_name, _global_version
    _global_service_name = service_name
    _global_version = version
    # 重新创建 logger 以应用新的上下文
    _global_logger = get_service_logger(service_name, version)


def get_logger() -> ServiceLoggerAdapter:
    """
    获取全局 logger 实例
    
    如果已经设置了服务上下文（通过 set_service_context），返回带服务信息的 logger。
    否则返回一个默认的 logger。
    
    Returns:
        日志适配器实例
    """
    global _global_logger, _global_service_name, _global_version
    
    if _global_logger is None:
        # 如果还没有设置服务上下文，创建一个默认的 logger
        if _global_service_name:
            _global_logger = get_service_logger(_global_service_name, _global_version)
        else:
            # 使用默认名称创建 logger
            _global_logger = get_service_logger("unknown", None)
    
    return _global_logger


# 创建一个延迟加载的 logger 包装类，确保在 Ray 环境中也能正常工作
class _LazyLogger:
    """
    延迟加载的 logger 包装类，确保在 Ray 环境中也能正常工作
    
    这个类通过 __getattr__ 代理所有方法调用到底层的 ServiceLoggerAdapter 实例，
    避免了模块级别全局变量在 Ray 序列化时可能出现的问题。
    """
    
    def __getattr__(self, name):
        """
        延迟获取 logger 实例的属性
        
        每次访问属性时都会获取最新的 logger 实例，确保在 Ray 环境中
        即使模块被重新导入，也能获取到正确的 logger。
        """
        logger_instance = get_logger()
        attr = getattr(logger_instance, name)
        # 如果属性是可调用的，返回一个包装函数以确保每次调用都使用最新的 logger
        if callable(attr):
            def wrapper(*args, **kwargs):
                current_logger = get_logger()
                method = getattr(current_logger, name)
                return method(*args, **kwargs)
            return wrapper
        return attr
    
    def __call__(self, *args, **kwargs):
        """如果 logger 被当作函数调用"""
        logger_instance = get_logger()
        return logger_instance(*args, **kwargs)
    
    def __repr__(self):
        """返回 logger 的字符串表示"""
        logger_instance = get_logger()
        return repr(logger_instance)
    
    def __str__(self):
        """返回 logger 的字符串表示"""
        logger_instance = get_logger()
        return str(logger_instance)
    
    def __dir__(self):
        """返回 logger 的所有属性，用于 IDE 自动补全"""
        logger_instance = get_logger()
        return dir(logger_instance)

# 创建延迟加载的 logger 实例
logger = _LazyLogger()