import os
import sys
import threading
import base64
import ctypes
import time
import multiprocessing
from typing import Optional, Callable, Dict
from PIL import Image
import pystray
from .web_window import WebWindow
from ..system import R


class QueueWriter:
    def __init__(self, queue):
        self.queue = queue

    def write(self, message):
        if message.strip():
            self.queue.put(message)

    def flush(self):
        pass


class FloatScriptWindow(WebWindow):
    def __init__(self, icon_path: str, title: str = "AScript", use_process: bool = True, auto_start: bool = False):
        self.icon_path = os.path.abspath(icon_path)
        self.ui_title = title
        self._is_hidden = False
        self._callback = None

        self.use_process = use_process
        self.auto_start = auto_start
        self.active_worker = None
        self.events = {}
        self._is_ready = False
        self._is_switching = False

        self.stop_event = multiprocessing.Event()
        self.msg_queue = multiprocessing.Queue()

        # _root = paths.get_path("ascript/windows/tools/web/")
        # _filepath = paths.get_path("ascript/windows/tools/web/flot_control.html")

        _root = R.internal("windows", "tools", "web")  # paths.get_path("ascript/windows/tools/web/")
        _filepath = R.internal("windows", "tools", "web",
                               "flot_control.html")  # paths.get_path("ascript/windows/tools/web/license_window.html")
        super().__init__(_filepath, project_root=_root)

        self.expose(self.get_init_data)
        self.expose(self.on_toggle_click)
        self.expose(self.drag_window)
        self.expose(self.hide_window)
        self.expose(self.resize_ui)

        self._setup_logging()
        threading.Thread(target=self._queue_listener, daemon=True).start()

    def on(self, event_name: str):
        def wrapper(func: Callable):
            self.events[event_name] = func
            return func

        return wrapper

    def _setup_logging(self):
        self._original_stdout = sys.stdout
        sys.stdout = self

    def _queue_listener(self):
        while True:
            try:
                msg = self.msg_queue.get()
                print(msg)
            except:
                pass

    def write(self, message):
        # 1. 尝试写回原始控制台，增加出错捕获
        try:
            self._original_stdout.write(message)
        except:
            # 出错时不进行任何处理，直接跳过，防止程序崩溃
            pass

        # 2. 推送到 WebView UI
        if self._is_ready and message.strip() and self.webview_instance:
            try:
                # 保持你原始的字符替换逻辑
                safe_msg = message.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"').replace("\n",
                                                                                                         "").replace(
                    "\r", "")
                self.webview_instance.evaluate_js(f"if(window.addLog){{window.addLog('{safe_msg}');}}")
            except:
                pass

    def flush(self):
        try:
            self._original_stdout.flush()
        except:
            pass

    @staticmethod
    def _worker_wrapper(start_func, stop_func, queue, stop_event):
        sys.stdout = QueueWriter(queue)
        sys.stderr = QueueWriter(queue)

        worker_thread = threading.Thread(target=start_func, daemon=True)
        worker_thread.start()

        def safe_cleanup():
            if stop_func:
                t = threading.Thread(target=stop_func, daemon=True)
                t.start()
                t.join(timeout=2.5)
                if t.is_alive():
                    pass

        while True:
            if stop_event.is_set():
                safe_cleanup()
                break

            if not worker_thread.is_alive():
                safe_cleanup()
                break

            time.sleep(0.1)

    def _monitor_worker(self, worker):
        worker.join()
        if self.active_worker == worker:
            self.active_worker = None
            self.stop_event.clear()
            if self.webview_instance:
                self.webview_instance.evaluate_js("if(window.syncStatus){window.syncStatus(false);}")

    def on_toggle_click(self, status):
        if self._is_switching:
            return {"status": "error", "msg": "BUSY"}
        self._is_switching = True
        try:
            if status:
                if 'start' in self.events:
                    start_func = self.events['start']
                    stop_func = self.events.get('stop')
                    if self.use_process:
                        if self.active_worker and self.active_worker.is_alive():
                            self._force_stop_worker()
                        self.stop_event.clear()
                        self.active_worker = multiprocessing.Process(
                            target=self._worker_wrapper,
                            args=(start_func, stop_func, self.msg_queue, self.stop_event),
                            daemon=True
                        )
                        self.active_worker.start()
                        threading.Thread(target=self._monitor_worker, args=(self.active_worker,), daemon=True).start()
            else:
                self._force_stop_worker()
            return {"status": "success"}
        finally:
            self._is_switching = False

    def _force_stop_worker(self):
        if self.active_worker:
            worker_to_stop = self.active_worker
            self.active_worker = None
            if self.use_process:
                if worker_to_stop.is_alive():
                    self.stop_event.set()
                    worker_to_stop.join(timeout=3.0)

                    if worker_to_stop.is_alive():
                        worker_to_stop.terminate()
                        worker_to_stop.join(timeout=1.0)
                        if worker_to_stop.is_alive():
                            worker_to_stop.kill()
                            worker_to_stop.join()
            self.stop_event.clear()

    def drag_window(self):
        if self.webview_instance:
            try:
                self.webview_instance.start_drag()
            except:
                try:
                    self.webview_instance.move_window()
                except:
                    pass

    def hide_window(self):
        self.toggle_visible()

    def resize_ui(self, expand):
        if self.webview_instance:
            self.webview_instance.resize(300 if expand else 240, 450 if expand else 76)

    def get_init_data(self):
        self._is_ready = True
        try:
            if not os.path.exists(self.icon_path):
                return {"title": self.ui_title, "icon_b64": ""}
            with open(self.icon_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode('utf-8')
            return {"title": self.ui_title, "icon_b64": b64}
        except:
            return {"title": self.ui_title, "icon_b64": ""}

    def _fix_window_once(self):
        GWL_STYLE, GWL_EXSTYLE = -16, -20
        WS_CAPTION, WS_THICKFRAME, WS_SYSMENU = 0x00C00000, 0x00040000, 0x00080000
        WS_EX_TOOLWINDOW, WS_EX_APPWINDOW = 0x00000080, 0x00040000
        hwnd = ctypes.windll.user32.FindWindowW(None, 'AScriptControlPanel')
        if hwnd:
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_STYLE)
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_STYLE, style & ~WS_CAPTION & ~WS_THICKFRAME & ~WS_SYSMENU)
            ex_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, (ex_style | WS_EX_TOOLWINDOW) & ~WS_EX_APPWINDOW)
            ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x0020 | 0x0002 | 0x0001 | 0x0004)

    def toggle_visible(self, icon=None, item=None):
        if self.webview_instance:
            if self._is_hidden:
                self.webview_instance.show()
                self._is_hidden = False
            else:
                self.webview_instance.hide()
                self._is_hidden = True

    def _setup_tray(self):
        try:
            img = Image.open(self.icon_path)
            menu = pystray.Menu(pystray.MenuItem("显示/隐藏", self.toggle_visible, default=True),
                                pystray.MenuItem("彻底退出", lambda: os._exit(0)))
            tray = pystray.Icon("AScriptTray", img, self.ui_title, menu)
            tray.run()
        except:
            pass

    def _auto_start_logic(self):
        while not self._is_ready:
            time.sleep(0.1)
        if self.webview_instance:
            self.webview_instance.evaluate_js("if(window.syncStatus){window.syncStatus(true);}")
        self.on_toggle_click(True)

    def show(self, title: str = "AScriptControlPanel", debug=False, width: int = 240, height: int = 76, **kwargs):
        if multiprocessing.current_process().name != 'MainProcess':
            return
        threading.Thread(target=self._setup_tray, daemon=True).start()
        threading.Timer(1.5, self._fix_window_once).start()
        if self.auto_start:
            threading.Thread(target=self._auto_start_logic, daemon=True).start()
        kwargs.update({'frameless': True, 'on_top': True, 'resizable': False, 'background_color': '#1a1a1a'})
        super().show(title=title, debug=debug, width=width, height=height, **kwargs)