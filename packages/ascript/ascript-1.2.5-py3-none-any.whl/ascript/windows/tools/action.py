import webview
import os
import threading
import ctypes
import time
import sys
import win32gui
import win32con
import win32clipboard
from ctypes import windll, byref, sizeof
from ctypes.wintypes import RECT, MSG

# 设置 AppID 以便在任务栏独立显示（虽然在 .py 环境下图标可能仍是 Python）
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(u'ascript.coordinate.picker.v6')
except:
    pass

# DPI 高清适配
try:
    windll.shcore.SetProcessDpiAwareness(1)
except:
    windll.user32.SetProcessDPIAware()

HTML_CODE = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { margin: 0; padding: 12px; font-family: 'Segoe UI', sans-serif; background: #000; color: #eee; overflow: hidden; user-select: none; }
        .box { border: 1px solid #333; border-radius: 8px; background: #111; padding: 12px; margin-top: 5px; }
        .row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
        .coord-val { font-size: 18px; font-weight: bold; font-family: 'Consolas'; color: #00bcd4; }
        #history { height: 280px; overflow-y: auto; margin-top: 10px; border-top: 1px solid #222; padding-top: 5px; }
        .item { background: #1a1a1a; padding: 8px; border-radius: 4px; margin-bottom: 5px; font-size: 12px; cursor: pointer; border-left: 2px solid #00bcd4; }
        .item:hover { background: #222; }
    </style>
</head>
<body>
    <div style="font-size:11px; color:#555; margin-bottom:5px;">Shift + A 记录坐标</div>
    <div class="box">
        <div class="row">
            <label><input type="radio" name="m" value="abs" checked> 屏幕</label>
            <span id="a-v" class="coord-val">0, 0</span>
        </div>
        <div class="row">
            <label><input type="radio" name="m" value="rel"> 窗口</label>
            <span id="r-v" class="coord-val" style="color:#4caf50;">0, 0</span>
        </div>
        <div id="w-t" style="font-size:11px; color:#666; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">窗口: -</div>
    </div>
    <div id="history"></div>
    <script>
        function updateUI(a, r, w) {
            document.getElementById('a-v').innerText = a;
            document.getElementById('r-v').innerText = r;
            document.getElementById('w-t').innerText = "窗口: " + w;
        }
        function getMode() { return document.querySelector('input[name="m"]:checked').value; }
        function addHistory(v) {
            const l = document.getElementById('history');
            const d = document.createElement('div');
            d.className = 'item'; d.innerText = "复制: " + v;
            d.onclick = () => window.pywebview.api.copy(v);
            l.insertBefore(d, l.firstChild);
        }
    </script>
</body>
</html>
"""


class ProApi:
    def copy(self, text):
        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(str(text))
            win32clipboard.CloseClipboard()
        except:
            pass


class AScriptApp:
    def __init__(self):
        # 路径逻辑 [cite: 2026-01-20]
        base = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        self.icon_path = os.path.normpath(os.path.join(base, "web", "img", "ico", "favicon.png"))
        self.title = "AScript 坐标捕获工具"
        self.window = None
        self.running = True

    def _worker(self):
        hotkey_id = 1
        # --- 修改处：将 MOD_ALT 改为 MOD_SHIFT ---
        windll.user32.RegisterHotKey(None, hotkey_id, win32con.MOD_SHIFT, ord('A'))

        while self.running:
            try:
                x, y = win32gui.GetCursorPos()
                raw_hwnd = win32gui.WindowFromPoint((x, y))
                root_hwnd = win32gui.GetAncestor(raw_hwnd, win32con.GA_ROOT)
                title = win32gui.GetWindowText(root_hwnd) or "Unknown"
                rect = RECT()
                windll.dwmapi.DwmGetWindowAttribute(root_hwnd, 9, byref(rect), sizeof(rect))
                rx, ry = x - rect.left, y - rect.top

                if self.window:
                    try:
                        self.window.evaluate_js(f"updateUI('{x}, {y}', '{rx}, {ry}', `{title}`)")
                    except:
                        pass

                # 监听热键消息
                msg = MSG()
                if windll.user32.PeekMessageW(byref(msg), 0, 0x0312, 0x0312, 1):
                    mode = self.window.evaluate_js("getMode()")
                    res = f"{x}, {y}" if mode == "abs" else f"{rx}, {ry}"
                    ProApi().copy(res)
                    self.window.evaluate_js(f"addHistory('{res}')")
            except:
                pass
            time.sleep(0.05)

    def run(self):
        self.window = webview.create_window(
            self.title, html=HTML_CODE, js_api=ProApi(),
            width=340, height=520, on_top=True
        )

        threading.Thread(target=self._worker, daemon=True).start()

        # 启动。注意：此时左上角可能会变，但任务栏在 .py 环境下极难改变
        webview.start(icon=self.icon_path, gui='edgechromium')
        self.running = False


if __name__ == "__main__":
    AScriptApp().run()