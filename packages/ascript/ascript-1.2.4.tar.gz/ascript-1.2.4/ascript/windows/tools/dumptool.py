import eel
import os
import sys
from ..window import  Window
from ..system import R

def start_vtree(hwnd: str = None, window_title: str = None):
    # --- 核心修改：动态路径处理 ---
    web_folder =  R.internal("windows","tools","web") #paths.get_path("ascript/windows/tools/web/")

    if not os.path.exists(web_folder):
        print(f"错误：找不到 web 文件夹: {web_folder}")
        # 打印一下当前目录结构，方便在打包后的控制台排查
        # print(f"DEBUG: sys._MEIPASS = {getattr(sys, '_MEIPASS', 'N/A')}")
        # print(f"DEBUG: __file__ = {__file__}")
        return

    # --- 后续逻辑不变 ---
    if window_title:
        temp_window = Window.find(window_title)
        if temp_window:
            hwnd = temp_window.hwnd

    eel.init(web_folder)

    eel_kwargs = {
        'mode': 'chrome',
        'port': 0,
        'cmdline_args': ['--start-maximized', '--incognito']
    }

    try:
        url = f"vtree.html?hwnd={hwnd}" if hwnd else "vtree.html"
        eel.start(url, **eel_kwargs)
    except (SystemExit, MemoryError, KeyboardInterrupt):
        pass