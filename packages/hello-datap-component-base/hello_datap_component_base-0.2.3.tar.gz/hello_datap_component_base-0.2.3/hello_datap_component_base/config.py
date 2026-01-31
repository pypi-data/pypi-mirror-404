import json
import os
import ssl
import base64
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, ValidationError, ConfigDict
import yaml
import urllib.request
import urllib.parse


class RuntimeEnv(BaseModel):
    """运行时环境配置"""
    pip: Optional[list] = None
    conda: Optional[dict] = None
    env_vars: Optional[Dict[str, str]] = None

    model_config = ConfigDict(extra="ignore")


class ServerConfig(BaseModel):
    """服务器配置"""
    name: str = Field(..., description="服务名称")
    version: Optional[str] = Field(None, description="服务版本")
    runtime_env: Optional[RuntimeEnv] = None
    params: Dict[str, Any] = Field(default_factory=dict)
    work_flow_id: Optional[int] = Field(None, description="工作流ID")
    work_flow_instance_id: Optional[int] = Field(None, description="工作流实例ID")
    task_id: Optional[str] = Field(None, description="任务ID")

    model_config = ConfigDict(extra="ignore")

    @classmethod
    def from_file(cls, config_path: str) -> "ServerConfig":
        """
        从文件或HTTP URL加载配置
        
        Args:
            config_path: 配置文件路径（本地文件路径、HTTP URL 或 base64 编码的 URL）
            
        Returns:
            ServerConfig实例
        """
        # 检查是否是 base64 编码的 URL
        decoded_path = cls._decode_base64_url(config_path)
        if decoded_path:
            config_path = decoded_path
        
        # 判断是否为HTTP URL
        parsed = urllib.parse.urlparse(config_path)
        is_http = parsed.scheme in ('http', 'https')
        
        if is_http:
            # 从HTTP URL加载配置
            try:
                # 检查是否跳过 SSL 验证（通过环境变量控制）
                skip_ssl_verify = os.environ.get('SKIP_SSL_VERIFY', 'false').lower() in ('true', '1', 'yes')
                
                if parsed.scheme == 'https' and skip_ssl_verify:
                    # 创建不验证 SSL 证书的上下文（仅用于内部服务）
                    ssl_context = ssl.create_default_context()
                    ssl_context.check_hostname = False
                    ssl_context.verify_mode = ssl.CERT_NONE
                    
                    # 创建请求
                    request = urllib.request.Request(config_path)
                    with urllib.request.urlopen(request, timeout=30, context=ssl_context) as response:
                        content = response.read().decode('utf-8')
                        data = json.loads(content)
                else:
                    # 正常请求（验证 SSL 证书）
                    with urllib.request.urlopen(config_path, timeout=30) as response:
                        content = response.read().decode('utf-8')
                        data = json.loads(content)
            except ssl.SSLError as e:
                error_msg = (
                    f"SSL certificate verification failed for URL {config_path}.\n"
                    f"Error: {e}\n\n"
                    f"Solutions:\n"
                    f"1. For internal services, set environment variable: export SKIP_SSL_VERIFY=true\n"
                    f"2. Install the CA certificate bundle\n"
                    f"3. Use HTTP instead of HTTPS if security is not required"
                )
                raise ValueError(error_msg)
            except urllib.error.URLError as e:
                raise ValueError(f"Failed to load config from URL {config_path}: {e}")
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in config from URL {config_path}: {e}")
        else:
            # 从本地文件加载配置
            path = Path(config_path)
            
            if not path.exists():
                raise FileNotFoundError(f"Config file not found: {config_path}")

            # 根据扩展名解析
            if path.suffix.lower() in ['.json']:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            elif path.suffix.lower() in ['.yaml', '.yml']:
                with open(path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
            else:
                raise ValueError(f"Unsupported config file format: {path.suffix}")

        # 如果 runtime_env 是字典且不为空，转换为 RuntimeEnv 对象
        runtime_env = data.get("runtime_env")
        if runtime_env is not None:
            if isinstance(runtime_env, dict) and runtime_env:
                data["runtime_env"] = RuntimeEnv(**runtime_env)
            elif isinstance(runtime_env, dict) and not runtime_env:
                # 空字典，设置为None
                data["runtime_env"] = None
            # 如果runtime_env是None，保持None不变

        return cls(**data)

    @staticmethod
    def _decode_base64_url(config_path: str) -> Optional[str]:
        """
        尝试解码 base64 编码的 URL
        
        Args:
            config_path: 可能是 base64 编码的字符串
            
        Returns:
            解码后的 URL，如果不是 base64 编码则返回 None
        """
        # 检查是否是 base64 编码（base64 字符串通常只包含 A-Z, a-z, 0-9, +, /, =）
        # 并且长度合理（至少 10 个字符）
        if len(config_path) < 10:
            return None
        
        # 检查是否看起来像 base64（不包含常见的路径分隔符和协议前缀）
        if config_path.startswith(('http://', 'https://', '/', './', '../')):
            return None
        
        # 检查是否包含 base64 字符集
        base64_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=')
        if not all(c in base64_chars or c.isspace() for c in config_path):
            return None
        
        try:
            # 移除可能的空白字符
            clean_path = config_path.strip()
            # 尝试解码
            decoded_bytes = base64.b64decode(clean_path, validate=True)
            decoded_str = decoded_bytes.decode('utf-8')
            
            # 验证解码后的字符串是否是有效的 URL
            parsed = urllib.parse.urlparse(decoded_str)
            if parsed.scheme in ('http', 'https'):
                return decoded_str
            # 如果不是 URL，可能是误判，返回 None
            return None
        except Exception:
            # 解码失败，不是 base64 编码
            return None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = self.model_dump(exclude_none=True)
        if self.runtime_env:
            runtime_env_dict = self.runtime_env.model_dump(exclude_none=True)
            # 如果转换后的字典不为空，才添加到结果中
            if runtime_env_dict:
                data["runtime_env"] = runtime_env_dict
        return data