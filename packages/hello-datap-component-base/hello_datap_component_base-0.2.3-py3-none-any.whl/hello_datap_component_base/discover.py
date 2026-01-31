import importlib
import inspect
import pkgutil
from pathlib import Path
from typing import List, Type, Optional, Tuple
from .base import BaseService


def find_service_classes(
        search_path: str = ".",
        exclude_dirs: List[str] = None
) -> List[Tuple[str, Type[BaseService]]]:
    """
    查找所有继承自 BaseService 的类

    Args:
        search_path: 搜索路径
        exclude_dirs: 排除的目录

    Returns:
        列表，每个元素是 (模块名, 类) 的元组
    """
    if exclude_dirs is None:
        exclude_dirs = ["__pycache__", ".git", ".pytest_cache", "venv", "env", ".venv", 
                        "hello_datap_component_base.egg-info", "build", "dist"]

    import sys
    import os
    
    # 确保搜索路径在 Python 路径中，以便能够导入模块
    search_path_obj = Path(search_path).resolve()
    search_path_str = str(search_path_obj)
    
    # 确保当前工作目录和搜索路径都在 sys.path 中
    current_dir = os.getcwd()
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    if search_path_str not in sys.path:
        sys.path.insert(0, search_path_str)
    # 确保 '.' 也在路径中（相对导入）
    if '.' not in sys.path:
        sys.path.insert(0, '.')

    service_classes = []

    # 遍历目录查找 Python 文件
    for py_file in search_path_obj.rglob("*.py"):
        # 跳过排除的目录
        py_file_str = str(py_file)
        py_file_parts = py_file.parts
        
        # 检查是否在排除的目录中
        if any(exclude in py_file_parts for exclude in exclude_dirs):
            continue
        
        # 跳过包目录（hello_datap_component_base）下的文件
        # 但允许根目录下的其他文件（如 example_service.py）
        if "hello_datap_component_base" in py_file_parts:
            # 如果文件在包目录内（不是包目录本身作为文件名），跳过
            idx = py_file_parts.index("hello_datap_component_base")
            if idx < len(py_file_parts) - 1:  # 包目录下还有子路径
                continue

        # 计算模块路径
        relative_path = py_file.relative_to(search_path_obj)
        module_path = str(relative_path.with_suffix('')).replace('/', '.')

        try:
            # 动态导入模块
            module = importlib.import_module(module_path)

            # 查找模块中继承自 BaseService 的类
            for name, obj in inspect.getmembers(module, inspect.isclass):
                try:
                    # 检查是否是 BaseService 的子类
                    if (inspect.isclass(obj) and 
                        issubclass(obj, BaseService) and
                        obj is not BaseService and
                        not inspect.isabstract(obj)):

                        # 检查是否实现了 process 方法
                        if hasattr(obj, 'process'):
                            service_classes.append((module_path, obj))
                except (TypeError, AttributeError) as e:
                    # 跳过不是类的对象或无法检查的对象
                    continue

        except (ImportError, ValueError, AttributeError) as e:
            # 对于根目录下的用户文件，输出错误信息以便调试
            # 检查是否是搜索路径下的直接文件（不是包内的文件）
            relative_to_search = py_file.relative_to(search_path_obj)
            is_root_file = len(relative_to_search.parts) == 1 and py_file.name not in ["__init__.py"]
            
            if is_root_file:
                # 输出到stderr以便用户看到
                import sys
                error_msg = str(e)
                # 检查是否是缺少模块的错误
                if "No module named" in error_msg or "ModuleNotFoundError" in error_msg:
                    print(f"⚠️  警告: 导入 {module_path} 失败，缺少依赖: {error_msg}", file=sys.stderr)
                    print(f"   提示: 请检查配置文件的 runtime_env.pip 是否包含所需的包", file=sys.stderr)
                else:
                    print(f"⚠️  警告: 导入 {module_path} 失败: {error_msg}", file=sys.stderr)
            continue
        except Exception as e:
            # 对于根目录下的用户文件，输出错误信息以便调试
            relative_to_search = py_file.relative_to(search_path_obj)
            is_root_file = len(relative_to_search.parts) == 1 and py_file.name not in ["__init__.py"]
            
            if is_root_file:
                import sys
                error_msg = str(e)
                if "No module named" in error_msg or "ModuleNotFoundError" in error_msg:
                    print(f"⚠️  警告: 导入 {module_path} 失败，缺少依赖: {error_msg}", file=sys.stderr)
                    print(f"   提示: 请检查配置文件的 runtime_env.pip 是否包含所需的包", file=sys.stderr)
                else:
                    print(f"⚠️  警告: 导入 {module_path} 时出错: {error_msg}", file=sys.stderr)
                    import traceback
                    traceback.print_exc(file=sys.stderr)
            continue

    return service_classes


def get_single_service_class(
        search_path: str = ".",
        class_name: Optional[str] = None
) -> Type[BaseService]:
    """
    获取单个服务类

    Args:
        search_path: 搜索路径
        class_name: 指定的类名（可选）

    Returns:
        服务类

    Raises:
        ValueError: 如果找到0个或多个服务类
    """
    service_classes = find_service_classes(search_path)

    if not service_classes:
        import os
        current_dir = os.getcwd()
        search_abs = os.path.abspath(search_path)
        
        # 尝试列出一些可能的服务文件
        possible_files = []
        for py_file in Path(search_abs).rglob("*.py"):
            if "example" in str(py_file).lower() and "service" in str(py_file).lower():
                possible_files.append(str(py_file.relative_to(search_abs)))
            if len(possible_files) >= 3:
                break
        
        error_msg = (
            f"No service class found in '{search_abs}' (current directory: {current_dir}).\n"
            f"Please ensure:\n"
            f"  1. You are in the project root directory\n"
            f"  2. There is a Python file containing a class that inherits from BaseService\n"
            f"  3. The service class implements the 'process' method\n"
        )
        if possible_files:
            error_msg += f"\nPossible service files found:\n"
            for f in possible_files:
                error_msg += f"  - {f}\n"
            error_msg += f"\nTry using --class-name to specify the service class name."
        
        raise ValueError(error_msg)

    if class_name:
        # 查找指定类名的服务
        for module_path, cls in service_classes:
            if cls.__name__ == class_name:
                return cls
        raise ValueError(f"Service class '{class_name}' not found")

    # 检查是否只有一个服务类
    if len(service_classes) > 1:
        class_list = [f"{module}.{cls.__name__}" for module, cls in service_classes]
        raise ValueError(
            f"Multiple service classes found: {class_list}. "
            f"Please specify which one to use with --class-name."
        )

    return service_classes[0][1]