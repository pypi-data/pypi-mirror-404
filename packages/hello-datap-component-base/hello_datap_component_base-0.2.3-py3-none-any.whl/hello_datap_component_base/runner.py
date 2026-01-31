import asyncio
import signal
import sys
import subprocess
from typing import Optional, Dict, Any, Type
from .base import BaseService, ServiceConfig
from .config import ServerConfig
from .discover import get_single_service_class
from .logger import setup_logging


class ServiceRunner:
    """服务运行器"""

    def __init__(self, config_path: str, class_name: Optional[str] = None):
        """
        初始化运行器

        Args:
            config_path: 配置文件路径
            class_name: 指定的服务类名
        """
        self.config_path = config_path
        self.class_name = class_name
        self.config: Optional[ServerConfig] = None
        self.service_class: Optional[Type[BaseService]] = None
        self.service_instance: Optional[BaseService] = None

    def load_config(self):
        """加载配置"""
        self.config = ServerConfig.from_file(self.config_path)

    def discover_service(self):
        """发现服务类"""
        import os
        # 使用当前工作目录作为搜索路径
        search_path = os.getcwd()
        self.service_class = get_single_service_class(
            search_path=search_path,
            class_name=self.class_name
        )

    def setup_environment(self):
        """设置运行环境"""
        # 设置日志
        from .logger import setup_logging, get_log_file_path
        self.log_file_path = setup_logging(
            level=self.config.runtime_env.env_vars.get("LOG_LEVEL", "INFO")
            if self.config.runtime_env and self.config.runtime_env.env_vars
            else "INFO",
            json_format=False,
            service_name=self.config.name,
            version=self.config.version
        )
        
        # 安装pip包（如果配置了）
        self._install_pip_packages()

    def _install_pip_packages(self):
        """安装runtime_env中指定的pip包"""
        if not self.config.runtime_env or not self.config.runtime_env.pip:
            return
        
        pip_packages = self.config.runtime_env.pip
        if not isinstance(pip_packages, list) or len(pip_packages) == 0:
            return
        
        print(f"Installing pip packages: {pip_packages}")
        
        try:
            # 使用 subprocess 调用 pip install
            # 使用 -q 参数减少输出，--disable-pip-version-check 禁用版本检查警告
            cmd = [
                sys.executable, "-m", "pip", "install", 
                "-q", "--disable-pip-version-check"
            ] + pip_packages
            
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            )
            
            print(f"✅ Successfully installed packages: {', '.join(pip_packages)}")
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to install pip packages: {pip_packages}\n"
            if e.stdout:
                error_msg += f"stdout: {e.stdout}\n"
            if e.stderr:
                error_msg += f"stderr: {e.stderr}\n"
            print(f"❌ {error_msg}", file=sys.stderr)
            raise RuntimeError(f"Failed to install required pip packages: {error_msg}")
        except Exception as e:
            print(f"❌ Error installing pip packages: {e}", file=sys.stderr)
            raise RuntimeError(f"Failed to install required pip packages: {e}")

    def create_service_instance(self):
        """创建服务实例"""
        # 创建 ServiceConfig
        runtime_env_dict = None
        if self.config.runtime_env:
            runtime_env_dict = self.config.runtime_env.model_dump(exclude_none=True)
            # 如果转换后的字典为空，设置为None
            if not runtime_env_dict:
                runtime_env_dict = None
        
        service_config = ServiceConfig(
            name=self.config.name,
            version=self.config.version,
            params=self.config.params,
            runtime_env=runtime_env_dict,
            work_flow_id=self.config.work_flow_id,
            work_flow_instance_id=self.config.work_flow_instance_id,
            task_id=self.config.task_id
        )

        # 创建服务实例
        self.service_instance = self.service_class(service_config)

    async def run_async(self):
        """异步运行服务并执行一次处理"""
        print(f"Starting service: {self.config.name}")
        if self.config.version:
            print(f"Version: {self.config.version}")
        import json
        params_to_print = self.config.params if self.config.params is not None else {}
        print(f"Param: {json.dumps(params_to_print, indent=2, ensure_ascii=False)}")
        print("\n" + "=" * 60)
        print("Processing request...")
        print("=" * 60 + "\n")

        try:
            # 准备输入数据
            # 从配置文件的 params 中获取，如果不存在则使用默认值
            params = self.config.params
            if params is None:
                params = {}

            # 执行一次处理（handle_request 会封装结果，包括异常情况）
            result = await self.service_instance.handle_request(params)
            
            # 输出结果
            import json
            print("=" * 60)
            print("Processing Result:")
            print("=" * 60)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            print("=" * 60)
            
            # 发送结果到 MNS 队列
            self._send_result_to_mns(result)
            
            # 上传日志文件到 OSS（如果配置了）
            self._upload_log_to_oss()
            
            print("Service completed successfully.")
            print("=" * 60)

        except Exception as e:
            print(f"\nError processing request: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            
            # 即使发生异常，也要尝试发送错误结果到队列
            try:
                error_result = {
                    "code": -1,
                    "message": str(e),
                    "data": {
                        "work_flow_id": self.config.work_flow_id,
                        "work_flow_instance_id": self.config.work_flow_instance_id,
                        "task_id": self.config.task_id,
                        "out_put": None
                    }
                }
                self._send_result_to_mns(error_result)
            except Exception as mns_error:
                print(f"Failed to send error result to MNS: {mns_error}", file=sys.stderr)
            
            # 即使发生异常，也要尝试上传日志文件到 OSS
            try:
                self._upload_log_to_oss()
            except Exception as oss_error:
                print(f"Failed to upload log to OSS: {oss_error}", file=sys.stderr)
            
            raise

    def run(self):
        """运行服务（主入口）"""
        try:
            # 加载配置
            self.load_config()

            # 发现服务类
            self.discover_service()

            # 设置环境
            self.setup_environment()

            # 创建服务实例
            self.create_service_instance()

            # 运行服务
            asyncio.run(self.run_async())

        except KeyboardInterrupt:
            print("\nService stopped by user")
        except Exception as e:
            print(f"Error running service: {e}", file=sys.stderr)
            sys.exit(1)

    def _send_result_to_mns(self, result: Dict[str, Any]):
        """
        发送结果到 MNS 队列
        
        Args:
            result: 封装后的结果字典
        """
        try:
            from .mns_client import get_mns_client
            import os
            
            # 如果环境变量中没有 MNS_ENDPOINT 配置，则不发送 MNS，静默跳过
            if not os.environ.get('MNS_ENDPOINT'):
                return
            
            client = get_mns_client()
            if client:
                # result 已经是封装好的格式，直接发送
                success = client.send_message(result)
                if success:
                    print("✅ Result sent to MNS queue successfully")
                else:
                    print("⚠️  Failed to send result to MNS queue")
            # 如果 client 为 None（配置不完整），静默跳过，不打印警告
        except Exception as e:
            print(f"⚠️  Error sending result to MNS queue: {e}", file=sys.stderr)
    
    def _upload_log_to_oss(self):
        """
        上传日志文件到 OSS
        
        如果未配置 OSS 环境变量，则静默跳过（向下兼容）
        """
        try:
            from .oss_client import get_oss_client
            from .logger import get_log_file_path
            import os
            
            # 如果环境变量中没有 OSS_ENDPOINT 配置，则不上传，静默跳过（向下兼容）
            if not os.environ.get('OSS_ENDPOINT'):
                return
            
            # 获取日志文件路径
            log_file_path = getattr(self, 'log_file_path', None)
            if not log_file_path:
                # 如果 runner 中没有保存路径，尝试从 logger 获取
                log_file_path = get_log_file_path()
            
            if not log_file_path:
                # 没有日志文件，静默跳过
                return
            
            client = get_oss_client()
            if client:
                # 生成 OSS 对象键（可选：包含时间戳和服务信息）
                from datetime import datetime
                import os
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                service_name = self.config.name
                task_id = self.config.task_id or 'unknown'
                
                # 生成 OSS 对象键：logs/{service_name}/{task_id}_{timestamp}.log
                oss_object_key = f"logs/{service_name}/{task_id}.log"
                
                success = client.upload_file(log_file_path, oss_object_key)
                if success:
                    print(f"✅ Log file uploaded to OSS: {oss_object_key}")
                    # 上传成功后删除本地日志文件
                    try:
                        if os.path.exists(log_file_path):
                            os.remove(log_file_path)
                            print(f"✅ Local log file deleted: {log_file_path}")
                    except Exception as delete_error:
                        print(f"⚠️  Failed to delete local log file: {delete_error}", file=sys.stderr)
                else:
                    print("⚠️  Failed to upload log file to OSS")
            # 如果 client 为 None（配置不完整），静默跳过，不打印警告
        except Exception as e:
            print(f"⚠️  Error uploading log to OSS: {e}", file=sys.stderr)

    async def process_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理请求（供外部调用）

        Args:
            data: 输入数据

        Returns:
            处理结果
        """
        if not self.service_instance:
            raise RuntimeError("Service not started")

        result = await self.service_instance.handle_request(data)
        
        # 发送结果到 MNS 队列
        self._send_result_to_mns(result)
        
        return result
