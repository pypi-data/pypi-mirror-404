"""
阿里云 OSS（对象存储）客户端
用于上传日志文件到 OSS
"""
import os
import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class OSSClient:
    """阿里云 OSS 客户端"""
    
    def __init__(self):
        """初始化 OSS 客户端（延迟加载）"""
        self._client = None
        self._bucket = None
        self._initialized = False
        
    def _init_client(self):
        """初始化 OSS 客户端（延迟加载）"""
        if self._initialized:
            return
            
        try:
            # 尝试导入阿里云 OSS SDK
            import oss2
            
            # 从环境变量获取 OSS 配置
            endpoint = os.environ.get('OSS_ENDPOINT_FOR_LOG')
            access_key_id = os.environ.get('OSS_ACCESS_KEY_ID_FOR_LOG')
            access_key_secret = os.environ.get('OSS_ACCESS_KEY_SECRET_FOR_LOG')
            bucket_name = os.environ.get('OSS_BUCKET_NAME_FOR_LOG')
            
            # 如果 OSS_ENDPOINT 不存在，静默跳过（向下兼容）
            if not endpoint:
                self._initialized = True
                return
            
            # 如果 OSS_ENDPOINT 存在但其他配置不完整，记录警告
            if not all([access_key_id, access_key_secret, bucket_name]):
                logger.warning(
                    "OSS 配置不完整，无法上传日志文件。"
                    "需要设置环境变量: OSS_ACCESS_KEY_ID_FOR_LOG, OSS_ACCESS_KEY_SECRET_FOR_LOG, OSS_BUCKET_NAME_FOR_LOG"
                )
                self._initialized = True
                return
            
            # 创建 OSS 认证对象
            auth = oss2.Auth(access_key_id, access_key_secret)
            
            # 创建 Bucket 对象
            self._bucket = oss2.Bucket(auth, endpoint, bucket_name)
            self._client = auth
            self._initialized = True
            logger.info(f"OSS 客户端初始化成功，Bucket: {bucket_name}")
            
        except ImportError:
            logger.warning(
                "未安装阿里云 OSS SDK，无法上传日志文件。"
                "请安装: pip install oss2"
            )
            self._initialized = True
        except Exception as e:
            logger.error(f"初始化 OSS 客户端失败: {e}")
            self._initialized = True
    
    def upload_file(
        self, 
        local_file_path: str, 
        oss_object_key: Optional[str] = None
    ) -> bool:
        """
        上传文件到 OSS
        
        Args:
            local_file_path: 本地文件路径
            oss_object_key: OSS 对象键（路径），如果为 None 则使用文件名
            
        Returns:
            是否上传成功
        """
        self._init_client()
        
        # 如果未配置 OSS，静默跳过（向下兼容）
        if not self._bucket:
            return False
        
        # 检查文件是否存在
        file_path = Path(local_file_path)
        if not file_path.exists():
            logger.warning(f"日志文件不存在: {local_file_path}")
            return False
        
        try:
            # 如果没有指定 OSS 对象键，使用文件名
            if oss_object_key is None:
                oss_object_key = file_path.name
            
            # 从环境变量获取 OSS 路径前缀（可选）
            oss_path_prefix = os.environ.get('OSS_LOG_PATH_PREFIX', '')
            if oss_path_prefix:
                # 确保路径前缀以 / 结尾（如果没有）
                if not oss_path_prefix.endswith('/'):
                    oss_path_prefix += '/'
                oss_object_key = oss_path_prefix + oss_object_key
            
            # 上传文件
            with open(local_file_path, 'rb') as f:
                self._bucket.put_object(oss_object_key, f)
            
            logger.info(f"日志文件已上传到 OSS: {oss_object_key}")
            return True
            
        except Exception as e:
            logger.error(f"上传日志文件到 OSS 失败: {e}", exc_info=True)
            return False
    
    def upload_log_file(self, log_file_path: str) -> bool:
        """
        上传日志文件到 OSS（便捷方法）
        
        Args:
            log_file_path: 日志文件路径
            
        Returns:
            是否上传成功
        """
        return self.upload_file(log_file_path)


def get_oss_client() -> Optional[OSSClient]:
    """
    获取 OSS 客户端实例
    
    Returns:
        OSSClient 实例，如果配置不完整则返回 None
    """
    # 如果环境变量中没有 OSS_ENDPOINT 配置，则不使用 OSS，直接返回 None（向下兼容）
    if not os.environ.get('OSS_ENDPOINT_FOR_LOG'):
        return None
    
    client = OSSClient()
    client._init_client()
    
    # 如果客户端未正确初始化，返回 None
    if not client._bucket:
        return None
    
    return client
