import json
import inspect
import sys
import os
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional


def get_function_info(func) -> Dict[str, Any]:
    """获取函数的完整信息"""
    try:
        info = {
            "name": func.__name__,
            "module": func.__module__,
            "doc": inspect.getdoc(func) or "",
        }

        # 获取函数签名
        try:
            signature = inspect.signature(func)
            info["signature"] = str(signature)

            # 提取参数信息
            info["params"] = {}
            for name, param in signature.parameters.items():
                param_info = {
                    "name": name,
                    "type": str(param.annotation) if param.annotation != param.empty else "any",
                    "default": str(param.default) if param.default != param.empty else None,
                    "kind": str(param.kind)
                }
                info["params"][name] = param_info
        except (ValueError, TypeError):
            info["signature"] = f"{func.__name__}(...)"
            info["params"] = {}

        # 获取返回类型
        if hasattr(func, "__annotations__") and "return" in func.__annotations__:
            info["returns"] = str(func.__annotations__["return"])
        else:
            info["returns"] = None

        # 获取源码位置
        try:
            info["file"] = str(Path(inspect.getfile(func)).resolve())
            info["line"] = inspect.getsourcelines(func)[1]
        except (TypeError, OSError):
            info["file"] = "unknown"
            info["line"] = 0

        return info
    except Exception as e:
        print(f"提取函数信息失败: {str(e)}")
        return None


def find_functions_in_module(module) -> List[Dict[str, Any]]:
    """在模块中查找所有函数"""
    functions = []

    for name in dir(module):
        # 跳过私有成员
        if name.startswith("_"):
            continue

        obj = getattr(module, name)

        # 只处理函数
        if inspect.isfunction(obj):
            # 确保函数是在这个模块中定义的
            if getattr(obj, "__module__", None) == module.__name__:
                func_info = get_function_info(obj)
                if func_info:
                    functions.append(func_info)

    return functions


def main():
    # 确保正确导入目标模块
    try:
        # 替换为您的包名
        import ascript.android as target_module
        print(f"成功导入模块: {target_module.__name__}")
    except ImportError:
        print("错误: 无法导入 your_package，请确保:")
        print("1. 包已安装 (pip install -e .)")
        print("2. 当前目录在 PYTHONPATH 中")
        print("3. 包名正确")
        sys.exit(1)

    # 收集函数信息
    functions = find_functions_in_module(target_module)

    # 如果主模块中没有函数，尝试查找子模块
    if not functions:
        print("主模块中没有找到函数，尝试查找子模块...")
        for name in dir(target_module):
            obj = getattr(target_module, name)
            if inspect.ismodule(obj):
                print(f"检查子模块: {obj.__name__}")
                functions.extend(find_functions_in_module(obj))

    # 保存数据
    output_path = "api_data.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(functions, f, indent=2, ensure_ascii=False)

    print(f"\n成功! 共提取 {len(functions)} 个函数")
    print(f"数据已保存到: {output_path}")

    # 打印一些示例
    if functions:
        print("\n示例函数:")
        for func in functions[:3]:
            print(f"\n函数名: {func['name']}")
            print(f"模块: {func['module']}")
            print(f"签名: {func.get('signature', '')}")
            print(f"文件: {func.get('file', 'unknown')}:{func.get('line', 0)}")
            if func.get('doc'):
                print(f"文档摘要: {func['doc'][:100]}...")
    else:
        print("\n警告: 没有找到任何函数! 可能的原因:")
        print("1. 您的函数可能定义在类中（作为方法）")
        print("2. 函数可能是私有的（以 _ 开头）")
        print("3. 模块结构可能需要特殊处理")


if __name__ == "__main__":
    main()