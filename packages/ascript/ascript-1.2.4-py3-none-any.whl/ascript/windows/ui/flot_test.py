import webview
import os
import threading
import pystray
import base64
import ctypes
import time
from PIL import Image
from typing import Optional, Callable

# --- 1. 环境补丁：拦截 AccessibilityObject 导致的递归报错 ---
os.environ['WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS'] = '--disable-features=AccessibilityObjectModel --disable-gpu'

# --- 2. Windows 窗口样式常量 ---
GWL_EXSTYLE = -20
WS_EX_TOOLWINDOW = 0x00000080  # 工具窗口样式（不在任务栏显示）
WS_EX_APPWINDOW = 0x00040000  # 应用程序窗口样式（我们要移除它）

# ---------------- HTML & CSS (满铺直角 + 悬浮交互) ----------------
HTML_CONTENT = """
<!DOCTYPE html>
<html>
<head>
    <style>
        * { box-sizing: border-box; }
        html, body {
            margin: 0; padding: 0; width: 100%; height: 100%;
            overflow: hidden; background-color: #1a1a1a;
            display: flex; align-items: center; user-select: none;
        }
        .full-bar {
            width: 100%; height: 100%;
            display: flex; align-items: center;
            padding: 0 8px; border: 1px solid #333;
            cursor: move; position: relative;
        }
        /* 唱片容器 */
        .disk-box {
            width: 36px; height: 36px;
            flex-shrink: 0; position: relative;
            background: #000; border-radius: 50%;
            overflow: hidden; border: 1px solid #444;
        }
        #disk { width: 100%; height: 100%; object-fit: cover; transition: transform 0.6s ease-out; }
        /* 悬浮覆盖层：播放/停止按钮 */
        .disk-overlay {
            position: absolute; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.6); display: flex; align-items: center; justify-content: center;
            opacity: 0; transition: opacity 0.2s; cursor: pointer;
            -webkit-app-region: no-drag;
        }
        .disk-box:hover .disk-overlay { opacity: 1; }
        .btn-icon { width: 20px; height: 20px; fill: white; }
        /* 状态文本 */
        .info {
            color: #eeeeee; font-size: 12px; font-family: "微软雅黑", sans-serif;
            margin-left: 10px; font-weight: bold; flex-grow: 1;
        }
        /* 隐藏按钮 */
        .hide-btn {
            width: 24px; height: 24px; display: flex; align-items: center; justify-content: center;
            border-radius: 4px; color: #666; cursor: pointer;
            transition: all 0.2s; -webkit-app-region: no-drag;
            opacity: 0;
        }
        .full-bar:hover .hide-btn { opacity: 1; }
        .hide-btn:hover { background: #444; color: white; }
        /* 指示灯 */
        .led { width: 4px; height: 20px; background: #333; margin-left: 8px; }
        .is-active .led { background: #00ff88; box-shadow: -2px 0 8px rgba(0, 255, 136, 0.4); }
    </style>
</head>
<body onmousedown="handleMouseDown(event)">
    <div class="full-bar" id="mainBar">
        <div class="disk-box">
            <img id="disk" src="data:image/png;base64,{base64_data}">
            <div class="disk-overlay" onclick="toggleStatus(event)">
                <svg id="playIcon" class="btn-icon" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                <svg id="stopIcon" class="btn-icon" viewBox="0 0 24 24" style="display:none;"><path d="M6 6h12v12H6z"/></svg>
            </div>
        </div>
        <div class="info" id="statusText">READY</div>
        <div class="hide-btn" onclick="hideToTray(event)" title="隐藏到托盘">
            <svg class="btn-icon" style="width:16px; height:16px;" viewBox="0 0 24 24"><path d="M19 13H5v-2h14v2z"/></svg>
        </div>
        <div class="led" id="ledIndicator"></div>
    </div>
    <script>
        let running = false;
        let currentAngle = 0;
        let animationId = null;
        const disk = document.getElementById('disk');
        const mainBar = document.getElementById('mainBar');
        const statusText = document.getElementById('statusText');

        function rotateStep() {
            if (!running) return;
            currentAngle = (currentAngle + 4) % 360;
            disk.style.transform = `rotate(${currentAngle}deg)`;
            animationId = requestAnimationFrame(rotateStep);
        }

        function toggleStatus(e) {
            e.stopPropagation();
            running = !running;
            const play = document.getElementById('playIcon');
            const stop = document.getElementById('stopIcon');
            if (running) {
                mainBar.classList.add('is-active');
                statusText.innerText = 'RUNNING';
                statusText.style.color = '#00ff88';
                play.style.display = 'none';
                stop.style.display = 'block';
                disk.style.transition = 'none';
                rotateStep();
            } else {
                mainBar.classList.remove('is-active');
                statusText.innerText = 'STOPPED';
                statusText.style.color = '#eeeeee';
                play.style.display = 'block';
                stop.style.display = 'none';
                cancelAnimationFrame(animationId);
                disk.style.transition = 'transform 0.6s ease-out';
                disk.style.transform = 'rotate(0deg)';
                currentAngle = 0;
            }
            window.pywebview.api.on_toggle(running);
        }

        function hideToTray(e) {
            e.stopPropagation();
            window.pywebview.api.hide_window();
        }

        function handleMouseDown(e) {
            if (e.target.id === 'mainBar' || e.target.id === 'statusText') {
                window.pywebview.api.start_drag();
            }
        }
    </script>
</body>
</html>
"""


class Api:
    def __init__(self):
        self.status_callback = None
        self.window = None

    def on_toggle(self, status):
        if self.status_callback:
            self.status_callback(status)

    def start_drag(self):
        if self.window: self.window.move_window()

    def hide_window(self):
        if self.window: self.window.hide()


class RecordPlayer:
    def __init__(self, icon_path: str):
        # 支持根目录初始化 [cite: 2026-01-20]
        self.icon_path = os.path.abspath(icon_path)
        self.api = Api()
        self.tray = None

    def listen(self, callback: Callable[[bool], None]):
        self.api.status_callback = callback

    def _get_base64(self):
        with open(self.icon_path, "rb") as f:
            return base64.b64encode(f.read()).decode('utf-8')

    def _fix_taskbar(self):
        """核心补丁：通过 Win32 API 强制从任务栏抹除图标"""
        while True:
            # 循环查找直到窗口句柄被创建
            hwnd = ctypes.windll.user32.FindWindowW(None, 'ControlPanel')
            if hwnd:
                style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                # 关键：设置为工具窗口并移除 AppWindow 属性
                new_style = (style | WS_EX_TOOLWINDOW) & ~WS_EX_APPWINDOW
                ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)
                # 刷新窗口，SWP_FRAMECHANGED = 0x0020
                ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x0020 | 0x0002 | 0x0001 | 0x0004)
                break
            time.sleep(0.1)

    def _show_window(self, icon=None, item=None):
        if self.api.window:
            self.api.window.show()

    def _quit_app(self, icon, item):
        icon.stop()
        os._exit(0)

    def _setup_tray(self):
        image = Image.open(self.icon_path)
        menu = pystray.Menu(
            pystray.MenuItem("显示控制栏", self._show_window, default=True),
            pystray.MenuItem("彻底退出", self._quit_app)
        )
        self.tray = pystray.Icon("ControlWidget", image, "脚本控制中心", menu)
        self.tray.on_activate = self._show_window
        self.tray.run()

    def run(self):
        b64_data = self._get_base64()
        full_html = HTML_CONTENT.replace("{base64_data}", b64_data)

        self.api.window = webview.create_window(
            'ControlPanel',  # 标题需与 _fix_taskbar 一致
            html=full_html,
            js_api=self.api,
            width=180, height=52,
            frameless=True,
            on_top=True,
            resizable=False,
            background_color='#1a1a1a'
        )

        # 启动托盘
        threading.Thread(target=self._setup_tray, daemon=True).start()
        # 启动任务栏消除补丁线程
        threading.Thread(target=self._fix_taskbar, daemon=True).start()

        webview.start(gui='edgechromium', debug=False)


if __name__ == "__main__":
    # 确保你的根目录有 logo.png
    player = RecordPlayer("logo.png")
    player.listen(lambda s: print(f"【外部监听到状态】: {s}"))
    player.run()