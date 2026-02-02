import sys
import eel

from ..system import R
from . import eel_api, config,plug_manager
from ..window import Window
from ..screen import Screen
import  time
import ctypes
import threading
import bottle


@eel.expose
def colors_tool_screenshot(hwnd):
    # 建议在临时目录下为你的库创建一个专属子文件夹
    my_file_temp = os.path.join(config.file_capture_dir, str(int(time.time() * 1000)) + ".jpeg")

    if hwnd:
        return eel_api.get_screenshot(hwnd, my_file_temp)
    else:
        tool_window = Window.find("图形处理 AScript")

        if not tool_window.is_minimized:
            tool_window.minimize()
            time.sleep(0.5)
        base64_img = Screen.capture(save_path=my_file_temp,format="base64")
        result = {
            "status": "success",
            "data": base64_img,
            "save_info": {"status": "none", "path": my_file_temp},
            "message": ""
        }
        tool_window.activate()
        return result


import os
import base64
import io
from PIL import Image


@eel.expose
def ascript_get_image(file_path: str, max_side_size: int = 0):
    """
    读取图片。
    :param file_path: 图片完整路径或文件名
    :param max_side_size: 缩放限制。0 表示不缩放；大于 0 则表示长边限制在该像素内。
    """
    try:
        # 1. 路径兼容性处理
        if not os.path.isabs(file_path):
            file_path = os.path.join(config.file_capture_dir, os.path.basename(file_path))

        # 2. 检查文件是否存在
        if not os.path.exists(file_path):
            return {"status": "error", "message": f"找不到文件: {file_path}", "data": ""}

        # 3. 处理图片
        with Image.open(file_path) as img:
            # 统一转为 RGB 模式以兼容 JPEG 格式
            if img.mode != 'RGB':
                img = img.convert('RGB')

            img_byte_arr = io.BytesIO()

            # 判断是否需要缩放
            if max_side_size > 0:
                # 使用 thumbnail 会保持宽高比，且仅在原图大于目标尺寸时缩小
                img.thumbnail((max_side_size, max_side_size), Image.Resampling.LANCZOS)
                # 缩略图可以使用较低的质量来节省空间
                img.save(img_byte_arr, format='JPEG', quality=70, optimize=True)
            else:
                # 不缩放时，尽可能保持高质量输出
                img.save(img_byte_arr, format='JPEG', quality=95)

            img_data = img_byte_arr.getvalue()
            img_base64 = base64.b64encode(img_data).decode()

        return {
            "status": "success",
            "message": "读取成功" + ("并缩放" if max_side_size > 0 else ""),
            "data": f"data:image/jpeg;base64,{img_base64}"
        }

    except Exception as e:
        print(f"读取图片异常: {e}")
        return {"status": "error", "message": str(e), "data": ""}







@eel.expose
def colors_tool_screenshot_files():
    try:
        # 1. 获取配置中的目录路径
        target_dir = config.file_capture_dir

        # 2. 检查目录是否存在
        if not os.path.exists(target_dir):
            return {
                "status": "success",
                "message": "目录不存在",
                "data": []
            }

        # 3. 定义支持的图片后缀名
        valid_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif')

        # 4. 获取目录下所有符合条件的文件，并转换为绝对路径
        file_paths = []
        for f in os.listdir(target_dir):
            if f.lower().endswith(valid_extensions):
                # 拼接成绝对路径
                full_path = os.path.abspath(os.path.join(target_dir, f))
                file_paths.append(full_path)

        # 5. 排序：按文件修改时间从新到旧排列
        # 注意：这里使用 os.path.getmtime 直接对绝对路径进行操作
        file_paths.sort(key=lambda x: os.path.getmtime(x), reverse=True)

        return {
            "status": "success",
            "message": f"成功获取 {len(file_paths)} 个文件路径",
            "data": file_paths,  # 现在的 data 里面是完整的绝对路径列表
            "path": target_dir
        }

    except Exception as e:
        print(f"获取图片路径列表失败: {e}")
        return {
            "status": "error",
            "message": str(e),
            "data": []
        }

@eel.expose
def save_dropped_image(base64_str, filename):
    try:
        # 提取 base64 数据部分
        # 格式通常为: "data:image/png;base64,iVBOR..."
        if "," in base64_str:
            base64_str = base64_str.split(",")[1]

        img_data = base64.b64decode(base64_str)

        # 为了防止文件名重复，加上时间戳
        name, ext = os.path.splitext(filename)
        save_name = f"{name}_{int(time.time())}{ext}"
        save_path = os.path.abspath(os.path.join(config.file_capture_dir, save_name))

        with open(save_path, "wb") as f:
            f.write(img_data)

        return {"status": "success", "path": save_path}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# 1. 定义一个触发函数
def listen_win32_hotkey():
    user32 = ctypes.windll.user32

    HOTKEY_ID = 101

    # 修改这里：使用 MOD_SHIFT (0x0004)
    MOD_SHIFT = 0x0004
    # 如果你想用 Ctrl + Shift + S，就写：MOD_CTRL_SHIFT = 0x0002 | 0x0004

    VK_S = 0x53  # 'S' 键的虚拟键码

    # 注册热键
    if not user32.RegisterHotKey(None, HOTKEY_ID, MOD_SHIFT, VK_S):
        print("❌ 无法注册 Shift + S，可能被占用")
        return

    # print("✅ 成功注册热键: Shift + S")

    try:
        msg = ctypes.wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
            if msg.message == 0x0312:  # WM_HOTKEY
                # 触发 JS 截图逻辑
                eel.triggerScreenshotUI()
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
    finally:
        user32.UnregisterHotKey(None, HOTKEY_ID)


# 启动线程
from urllib.parse import unquote # 必须导入这个
@eel.btl.route('/external/<base64_path>/<filename:path>')
def server_external(base64_path, filename):
    try:
        # 1. 先把 URL 里的 %2F 等符号转回正常字符
        clean_base64 = unquote(base64_path)

        # 2. Base64 解码并处理可能的中文编码
        # 注意：这里增加 try-except 或直接解码
        raw_path = base64.b64decode(clean_base64).decode('utf-8')

        # 3. 再次 unquote 物理路径（因为 JS 端用了 encodeURIComponent）
        actual_root = unquote(raw_path)

        print(f"请求文件: {filename} | 物理根目录: {actual_root}")  # 调试用

        return bottle.static_file(filename, root=actual_root)
    except Exception as e:
        print(f"路径解析失败: {e}")
        return bottle.HTTPError(500, f"Path Error: {str(e)}")

def start_colors(hwnd:str = None,window_title:str = None):

    # --- 核心修改：动态路径处理 ---
    web_folder =  R.internal("windows","tools","web") #paths.get_path("ascript/windows/tools/web/")

    if not os.path.exists(web_folder):
        print(f"错误：找不到 web 文件夹: {web_folder}")
        # 打印一下当前目录结构，方便在打包后的控制台排查
        # print(f"DEBUG: sys._MEIPASS = {getattr(sys, '_MEIPASS', 'N/A')}")
        # print(f"DEBUG: __file__ = {__file__}")
        return

    if window_title:
        temp_window = Window.find(window_title)
        if temp_window:
            hwnd = temp_window.hwnd

    # print(temp_window.hwnd)

    # 初始化 Eel
    eel.init(web_folder)

    # 3. 启动应用
    # cmdline_args 可以添加一些浏览器优化参数
    # 获取一个临时的绝对路径作为用户数据目录
    data_dir = os.path.join(os.getcwd(), 'chrome_debug_profile')

    eel_kwargs = {
        'mode': 'chrome',
        'port': 0,
        'cmdline_args': [
            '--start-maximized',
            '--incognito',
            # '--disable-web-security',  # 核心：禁用安全策略
            # '--disable-site-isolation-trials',  # 核心：禁用站点隔离
            # f'--user-data-dir={data_dir}',  # 核心：必须是独立的绝对路径
            # '--allow-running-insecure-content'  # 允许在 HTTPS 中加载 HTTP
        ]
    }

    print("正在启动 图形处理 工具...")
    try:
        # 这一行搞定：如果有 hwnd 则拼接参数，否则为空字符串
        url = f"colors.html?hwnd={hwnd}" if hwnd else "colors.html"
        # 启动线程
        threading.Thread(target=listen_win32_hotkey, daemon=True).start()
        eel.start(url, **eel_kwargs)

        # eel.start('index.html', mode='chrome', cmdline_args=['--disable-web-security', '--user-data-dir=remote-debug'])

    except (SystemExit, MemoryError, KeyboardInterrupt):
        # 正常退出
        pass

