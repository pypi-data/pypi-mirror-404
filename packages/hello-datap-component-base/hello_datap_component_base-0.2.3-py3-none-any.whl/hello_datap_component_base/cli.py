import click
import json
import sys
from pathlib import Path
from typing import Optional

from .base import ServiceConfig
from .runner import ServiceRunner
from .discover import find_service_classes, get_single_service_class
from .config import ServerConfig


@click.group()
@click.version_option(version="0.2.3")
def cli():
    """数据处理平台组件基类 - 统一的服务管理框架"""
    pass


@cli.command()
@click.argument("config_path")
@click.option("--class-name", "-c", help="指定要使用的服务类名")
def start(config_path: str, class_name: Optional[str] = None):
    """
    启动服务并执行一次处理（支持本地文件路径或HTTP URL）
    
    输入数据从配置文件的 params.input_data 中获取。
    如果 params.input_data 不存在，将使用默认测试数据。
    """
    runner = ServiceRunner(config_path, class_name)
    runner.run()


@cli.command()
def init():
    """初始化示例项目"""
    # 创建示例目录结构
    example_dir = Path("example_service")
    example_dir.mkdir(exist_ok=True)

    # 创建示例配置文件
    config = {
        "name": "example-service",
        "version": "1.0.0",
        "runtime_env": {
            "pip": ["requests>=2.25.0"],
            "env_vars": {
                "LOG_LEVEL": "INFO",
                "ENV": "development"
            }
        },
        "params": {
            "example_param": "value"
        }
    }

    config_file = example_dir / "config.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    # 创建示例服务代码
    example_code = '''#!/usr/bin/env python3
"""
示例服务
"""
import asyncio
from hello_datap_component_base import BaseService


class ExampleService(BaseService):
    """示例服务实现"""

    async def process(self, data: dict) -> dict:
        """处理请求的业务逻辑"""
        self.logger.info(f"收到请求数据: {data}")

        # 模拟处理逻辑
        await asyncio.sleep(0.1)

        # 返回结果
        result = {
            "status": "success",
            "message": f"Hello, {data.get('name', 'World')}!",
            "processed_data": {
                    "original": data,
                "extra_info": self.params
            },
            "timestamp": asyncio.get_event_loop().time()
        }

        return result


if __name__ == "__main__":
    # 本地测试
    import json
    from hello_datap_component_base import ServiceConfig

    async def test():
        config = ServiceConfig(
            name="test-example",
            params={"test": "value"}
        )
        service = ExampleService(config)

        # 测试请求
        result = await service.process({"name": "Test User"})
        print(json.dumps(result, indent=2, ensure_ascii=False))

    asyncio.run(test())
'''

    code_file = example_dir / "service.py"
    with open(code_file, "w", encoding="utf-8") as f:
        f.write(example_code)

    # 创建 README
    readme = f"""# 示例服务

    这是一个通过 component_manager 创建的服务示例。
    
    ## 文件结构
    - `config.json` - 服务配置文件
    - `service.py` - 服务实现代码
    
    ## 启动服务
    ```bash
    component_manager start config.json
    ```
    
    ## 本地测试
    ```bash
    cd {example_dir}
    python service.py
    ```
    
    ## 配置说明
    配置文件包含以下主要部分：
    
    1. **name**: 服务名称
    2. **version**: 服务版本（可选）
    3. **runtime_env**: 运行时环境
       - pip: Python 依赖包
       - env_vars: 环境变量
    4. **params**: 服务参数
    """

    readme_file = example_dir / "README.md"
    with open(readme_file, "w", encoding="utf-8") as f:
        f.write(readme)

    click.echo(f"✅ 示例项目已创建在: {example_dir}")
    click.echo(f"📁 配置文件: {config_file}")
    click.echo(f"🐍 示例代码: {code_file}")
    click.echo("\n启动服务:")
    click.echo(f"  cd {example_dir}")
    click.echo(f"  component_manager start config.json")


@cli.command()
@click.option("--json", "-j", "json_format", is_flag=True, help="JSON 格式输出")
def list(json_format: bool = False):
    """列出可用的服务类"""
    try:
        import os
        # 确保使用当前工作目录
        search_path = os.getcwd()
        services = find_service_classes(search_path)

        if json_format:
            output = [
                {
                    "module": module,
                    "class": cls.__name__,
                    "file": getattr(cls, "__module__", "unknown"),
                }
                for module, cls in services
            ]
            click.echo(json.dumps(output, indent=2, ensure_ascii=False))
        else:
            if not services:
                click.echo("❌ 未找到服务类")
                click.echo("\n可能的原因：")
                click.echo("  1. 当前目录下没有继承自 BaseService 的服务类")
                click.echo("  2. 服务类文件导入失败（可能是缺少依赖包）")
                click.echo("  3. 服务类未实现 process 方法")
                click.echo("\n提示：")
                click.echo("  - 检查是否有 example_service.py 等文件")
                click.echo("  - 如果服务类需要额外的包，请在配置文件的 runtime_env.pip 中指定")
                click.echo("  - 运行命令时查看上方的警告信息")
                return

            click.echo("📋 发现的服务类:")
            for i, (module, cls) in enumerate(services, 1):
                click.echo(f"{i}. {cls.__name__} (来自 {module})")

    except Exception as e:
        click.echo(f"❌ 错误: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("config_path")
def validate(config_path: str):
    """验证配置文件（支持本地文件路径或HTTP URL）"""
    try:
        config = ServerConfig.from_file(config_path)
        click.echo("✅ 配置文件有效")
        click.echo(json.dumps(config.to_dict(), indent=2, ensure_ascii=False))
    except Exception as e:
        click.echo(f"❌ 配置文件无效: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("config_path")
@click.argument("data", required=False)
@click.option("--file", "-f", type=click.File("r"), help="从文件读取请求数据")
def test(config_path: str, data: Optional[str] = None, file: Optional[click.File] = None):
    """测试服务（发送测试请求，支持本地文件路径或HTTP URL）"""
    try:
        # 加载配置
        config = ServerConfig.from_file(config_path)

        # 发现服务
        import os
        search_path = os.getcwd()
        service_class = get_single_service_class(search_path=search_path)

        # 准备请求数据
        if file:
            request_data = json.load(file)
        elif data:
            try:
                request_data = json.loads(data)
            except json.JSONDecodeError:
                request_data = {"data": data}
        else:
            request_data = {"test": "default"}

        # 创建服务实例
        runtime_env_dict = None
        if config.runtime_env:
            runtime_env_dict = config.runtime_env.model_dump(exclude_none=True)
            # 如果转换后的字典为空，设置为None
            if not runtime_env_dict:
                runtime_env_dict = None
        
        service_config = ServiceConfig(
            name=config.name + "-test",
            version=config.version,
            params=config.params,
            runtime_env=runtime_env_dict
        )

        service = service_class(service_config)

        # 发送测试请求
        import asyncio
        result = asyncio.run(service.process(request_data))

        click.echo("✅ 测试结果:")
        click.echo(json.dumps(result, indent=2, ensure_ascii=False))

    except Exception as e:
        click.echo(f"❌ 测试失败: {e}", err=True)
        sys.exit(1)


def main():
    """主入口点"""
    cli()


if __name__ == "__main__":
    main()