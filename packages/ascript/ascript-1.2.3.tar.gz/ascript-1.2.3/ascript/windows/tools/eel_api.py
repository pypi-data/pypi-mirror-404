# 1. 暴露函数建议放在函数外（或者确保在函数内时，函数被调用）
import os
import platform
import shutil
import stat
import subprocess

import eel,io,base64
from ..window import Window,Selector
import uiautomation as auto
import time


@eel.expose
def get_online_windows():
    """获取所有可见窗口并返回给前端"""
    try:
        # 调用你的类方法
        windows = Window.find_all(visible_only=True)

        # 转换为前端易读的格式：名称 [句柄]
        # 同时保留 hwnd 以便后续探测指定窗口
        output = []
        for win in windows:
            if win.title:  # 过滤掉无标题的背景窗口
                output.append({
                    "display": f"{win.title} [{win.hwnd}]",
                    "hwnd": win.hwnd,
                    "title": win.title
                })
        return {"status": "success", "data": output}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@eel.expose
def get_ui_tree_data(hwnd, max_depth=0):
    """
    JS 调用：传入句柄和深度，返回全量 UI 树字典
    :param hwnd: 窗口句柄 (int)
    :param max_depth: 探测深度 (int), 0 为不限
    """
    try:
        # 1. 确保 hwnd 是整数类型
        hwnd = int(hwnd)
        max_depth = int(max_depth)

        if max_depth==0:
            max_depth = 0xFFFFFFFF

        # 2. 构造 Window 对象
        target_win = Window(hwnd)
        if not target_win.title:
            return {"status": "error", "message": "无效的窗口句柄或窗口已关闭"}

        target_win.activate()

        # 3. 初始化 Selector (假设你的 Selector 接收 window 和 max_depth)
        # 这里演示你的 get_uielement_tree 逻辑
        # 注意：如果你的 Selector 类还没写好，这里直接调用你提供的函数逻辑
        selector = Selector(target_win, depth=max_depth)

        print(f"开始探测窗口 [{target_win.title}]，深度: {max_depth}...")

        # 4. 获取树状结构（调用你写的那个逻辑）
        root_element = selector.get_uielement_tree()

        if not root_element:
            return {"status": "empty", "message": "未能获取到任何 UI 元素"}

        # 5. 转换为字典（递归调用 UIElement.to_dict）
        tree_dict = root_element.to_dict()

        return {
            "status": "success",
            "data": tree_dict
        }

    except Exception as e:
        import traceback
        print(f"探测失败: {e}")
        traceback.print_exc()
        return {"status": "error", "message": str(e)}


@eel.expose
def test_selector(selector_str: str):
    print(f"\n[Python Receive] 收到指令: {selector_str}")
    try:
        # 1. 准备环境
        safe_vars = {'Selector': Selector, 'auto': auto}

        # 2. 执行 eval
        print("[Python Debug] 开始执行 eval...")
        results = eval(selector_str, {"__builtins__": None}, safe_vars)

        # 3. 核心修复逻辑：自动补全与类型统一
        # 情况 A: 如果返回的是 Selector 实例（用户忘了写 .find()）
        if hasattr(results, 'find'):
            print("[Python Debug] 检测到未执行 find，自动调用 .find()")
            results = results.find()

        # 情况 B: 统一转换为列表 (处理 find_first 返回单个对象的情况)
        if results is None:
            final_list = []
        elif isinstance(results, list):
            final_list = results
        else:
            # 说明是单个 UIElement 对象
            final_list = [results]

        print(f"[Python Debug] 最终待处理结果数量: {len(final_list)}")

        # 4. 序列化
        tree_dict = [el.to_dict() for el in final_list]

        return {
            "status": "success",
            "data": tree_dict
        }

    except Exception as e:
        import traceback
        error_stack = traceback.format_exc()
        print(f"[Python Error] 详细报错如下:\n{error_stack}")
        return {
            "status": "error",
            "message": str(e),
            "data": []
        }




@eel.expose
def get_screenshot(hwnd, save_path=None):
    # 初始化返回结构
    result = {
        "status": "error",
        "data": None,
        "save_info": {"status": "none", "path": None},
        "message": ""
    }

    try:
        # --- 阶段 1: 参数校验 ---
        try:
            hwnd_int = int(hwnd)
        except (ValueError, TypeError):
            result["message"] = f"无效的句柄: {hwnd}"
            return result

        # --- 阶段 2: 捕获窗口 (最易崩溃点) ---
        try:
            # 假设你的 Window 类在捕获失败时会抛错
            img = Window(hwnd_int).capture()
            if img is None:
                raise Exception("捕获返回对象为空")
        except Exception as capture_err:
            result["message"] = f"窗口捕获失败: {str(capture_err)}"
            return result

        # --- 阶段 3: 保存逻辑 (独立异常处理) ---
        if save_path:
            try:
                # 规范化路径
                clean_save_path = os.path.abspath(save_path)

                # 如果是目录，则生成文件名
                if os.path.isdir(clean_save_path):
                    filename = f"{int(time.time() * 1000)}.jpg"
                    clean_save_path = os.path.join(clean_save_path, filename)

                # 确保后缀正确
                if not clean_save_path.lower().endswith(('.jpg', '.jpeg')):
                    clean_save_path += ".jpg"

                # 确保父目录存在
                os.makedirs(os.path.dirname(clean_save_path), exist_ok=True)

                # 保存图片 (转换模式防止 PNG 包含透明通道导致转 JPG 失败)
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")

                img.save(clean_save_path, format="JPEG", quality=100)
                result["save_info"] = {"status": "success", "path": clean_save_path}
            except Exception as save_err:
                result["save_info"] = {"status": "failed", "message": str(save_err)}
                print(f"磁盘保存跳过 (非致命错误): {save_err}")

        # --- 阶段 4: 转换 Base64 返回前端 ---
        try:
            buffer = io.BytesIO()
            # 同样转换模式确保转码成功
            preview_img = img if img.mode == "RGB" else img.convert("RGB")
            preview_img.save(buffer, format="JPEG", quality=80)  # 预览质量可以略低，提高传输速度
            img_str = base64.b64encode(buffer.getvalue()).decode()

            result["status"] = "success"
            result["data"] = f"data:image/jpeg;base64,{img_str}"
        except Exception as encode_err:
            result["message"] = f"预览图生成失败: {str(encode_err)}"

    except Exception as global_err:
        # 最后的兜底，确保 Python 不会闪退
        result["status"] = "error"
        result["message"] = f"系统级异常: {str(global_err)}"

    return result





@eel.expose
def open_folder(path):
    """
    使用系统默认文件浏览器打开指定路径
    """
    # 转换路径为当前系统的标准路径（处理斜杠方向）
    path = os.path.abspath(path)

    if not os.path.exists(path):
        print(f"路径不存在: {path}")
        return False

    current_os = platform.system()

    try:
        if current_os == "Windows":
            # Windows: 使用 explorer
            # os.startfile(path) 是另一种简便方法，但 subprocess 更可控
            subprocess.run(['explorer', path])

        elif current_os == "Darwin":
            # macOS: 使用 open
            subprocess.run(['open', path])

        else:
            # Linux: 通常使用 xdg-open
            subprocess.run(['xdg-open', path])

        return True
    except Exception as e:
        print(f"打开文件夹失败: {e}")
        return False


@eel.expose
def file_delete(path):
    try:
        abs_path = os.path.abspath(path)
        if not os.path.exists(abs_path):
            return False

        # 定义一个内部函数处理只读文件
        def on_rm_error(func, path, exc_info):
            # 修改权限后重试
            os.chmod(path, stat.S_IWRITE)
            func(path)

        if os.path.isdir(abs_path):
            # 方案：不删除文件夹，只删除内容，防止程序崩溃
            for item in os.listdir(abs_path):
                item_path = os.path.join(abs_path, item)
                try:
                    if os.path.isfile(item_path) or os.path.islink(item_path):
                        os.unlink(item_path)  # 删除文件或链接
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path, onerror=on_rm_error)
                except Exception as e:
                    print(f"无法删除项 {item_path}: {e}")
            print(f"文件夹内容已清空: {abs_path}")
        else:
            os.remove(abs_path)

        return True
    except Exception as e:
        print(f"删除操作引发崩溃风险，已拦截: {e}")
        return False


import sys
import os
import traceback
import json
import types
import numpy as np

# 自动将当前脚本目录加入 sys.path，确保 JS 里 `import 你的私有库` 能成功
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)


@eel.expose
def python_executor(python_code):
    """
    强大的通用 Python 执行器
    支持 JS 端自主 import，全量捕获异常
    """
    # 结果容器
    response = {
        "success": False,
        "data": None,
        "error": {
            "type": None,
            "message": None,
            "traceback": None
        }
    }


    try:
        # 1. 编译代码 (这一步能捕获 SyntaxError)
        byte_code = compile(python_code, '<js_executed_code>', 'exec')

        # 2. 执行代码
        # 不预设 globals，让 JS 自己 import。但传入常见的内置模块作为兜底
        exec_env = {"__builtins__": __builtins__}
        exec(byte_code, exec_env, exec_env)

        # 3. 提取结果
        if "_result" in exec_env:
            response["data"] = make_json_serializable(exec_env["_result"])

        response["success"] = True
        response["error"] = None  # 显式清空错误信息

    except Exception as e:
        # 4. 全量异常捕捉
        response["success"] = False
        response["error"] = {
            "type": e.__class__.__name__,
            "message": str(e),
            "traceback": traceback.format_exc()  # 返回完整的错误堆栈，方便 JS 端调试
        }
    except SyntaxError as e:
        # 特殊处理语法错误
        response["success"] = False
        response["error"] = {
            "type": "SyntaxError",
            "message": f"行 {e.lineno}: {e.msg}",
            "traceback": traceback.format_exc()
        }

    return response


def make_json_serializable(obj):
    """
    工业级序列化：确保任何结果都能平安传回 JS
    """
    if obj is None: return None
    if isinstance(obj, (int, float, str, bool)): return obj

    # 优先使用对象自带的转换方法
    if hasattr(obj, 'to_dict') and callable(obj.to_dict):
        return make_json_serializable(obj.to_dict())

    # 处理容器
    if isinstance(obj, (list, tuple, set)):
        return [make_json_serializable(i) for i in obj]
    if isinstance(obj, dict):
        return {str(k): make_json_serializable(v) for k, v in obj.items()}

    # 处理 Numpy/OpenCV 数据
    if hasattr(obj, 'tolist'):
        return obj.tolist()

    # 处理类实例
    if hasattr(obj, '__dict__'):
        return {k: make_json_serializable(v) for k, v in obj.__dict__.items() if not k.startswith('_')}

    # 最终兜底：转为字符串，防止 JSON 失败导致崩溃
    return str(obj)

import eel
import tkinter as tk
from tkinter import filedialog

# 初始化一个隐藏的 tkinter 窗口，用于弹出对话框
root = tk.Tk()
root.withdraw()
root.wm_attributes('-topmost', 1) # 确保对话框在最前面
@eel.expose
def select_folder():
    """弹出文件夹选择对话框并返回路径"""
    folder_path = filedialog.askdirectory()
    return folder_path if folder_path else ""