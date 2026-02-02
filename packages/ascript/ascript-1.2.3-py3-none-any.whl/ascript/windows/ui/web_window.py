import time

import webview
import os
import json
from typing import Optional, Callable, Dict

class WebWindow:
    def __init__(self, html_path: str, project_root: Optional[str] = None):
        self.project_root = os.path.abspath(project_root) if project_root else os.getcwd()
        self.abs_path = os.path.abspath(html_path)
        self._exposed_functions: Dict[str, Callable] = {}
        self.webview_instance = None
        self._return_value = None  # 新增：用于存储返回结果

    def expose(self, func: Callable):
        self._exposed_functions[func.__name__] = func
        return func

    def show(self, title: str = "AScript Window", debug=False, **kwargs):
        class ApiBridge:
            def __init__(self, funcs): self._funcs = funcs
            def call_internal(self, func_name, args):
                f = self._funcs.get(func_name)
                # 包装一下执行，防止 Python 报错导致 JS 卡死
                try:
                    return f(*args) if f else None
                except Exception as e:
                    print(f"Error calling {func_name}: {e}")
                    return None

        # 核心改动 1：使用 file:// 协议，这是最稳定且毫秒级响应的
        file_url = 'file://' + self.abs_path

        self.webview_instance = webview.create_window(
            title=title,
            url=file_url,
            js_api=ApiBridge(self._exposed_functions),
            **kwargs
        )

        # 核心改动 2：监听窗口创建，通过 evaluate_js 动态注入 callPython
        # 这样就不需要去改 HTML 文件内容了，更干净
        def on_loaded():
            # print("ready",time.time())
            injection_code = """
            window.callPython = async function(fnName, ...args) {
                return await window.pywebview.api.call_internal(fnName, args);
            };
            window.dispatchEvent(new CustomEvent('onPythonReady'));
            """
            self.webview_instance.evaluate_js(injection_code)
            # print("end", time.time())

        # 启动并绑定加载完成事件
        webview.start(on_loaded, debug=debug)
        # 窗口关闭后，返回存储的结果
        return self._return_value

    def close(self):
        if self.webview_instance:
            self.webview_instance.destroy()