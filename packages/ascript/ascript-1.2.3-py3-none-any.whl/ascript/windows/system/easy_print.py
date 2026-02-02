# sub_print_capture.py
from multiprocessing import Queue, current_process
import sys
import threading
import os

# 全局队列，用于进程间传递打印内容
_print_queue = None
# 标记是否为主进程
_is_main = False

class QueueStream:
    """重定向stdout/stderr的流对象，将内容写入队列"""
    def __init__(self, queue, stream_type="stdout"):
        self.queue = queue
        self.stream_type = stream_type
        self.origin_stream = sys.stdout if stream_type == "stdout" else sys.stderr

    def write(self, msg):
        if msg.strip():  # 过滤空行
            # 传递：进程ID+进程名+输出类型+内容
            self.queue.put({
                "pid": os.getpid(),
                "pname": current_process().name,
                "type": self.stream_type,
                "msg": msg
            })

    def flush(self):
        # 兼容print的flush=True，无实际操作
        pass

    def isatty(self):
        # 兼容终端判断，避免部分库报错
        return self.origin_stream.isatty()

def init_main(listen_callback=None):
    """主进程初始化：创建队列+启动监听线程"""
    global _print_queue, _is_main
    if _is_main:
        return
    _print_queue = Queue()
    _is_main = True

    # 自定义监听回调，默认打印到主进程终端
    def default_listen():
        while True:
            try:
                data = _print_queue.get()
                if data is None:  # 结束标记
                    break
                # 格式化输出，可自定义
                prefix = f"[子进程{data['pid']}-{data['pname']}][{data['type']}]"
                print(f"{prefix} {data['msg']}", end="")
            except Exception:
                break

    # 启动监听线程
    listen_fun = listen_callback or default_listen
    t = threading.Thread(target=listen_fun, daemon=True)
    t.start()

def init_sub():
    """子进程初始化：重定向stdout/stderr到队列，引入时自动执行"""
    global _print_queue
    if _print_queue is None:
        return  # 主进程未初始化，不处理
    if current_process().name == "MainProcess":
        return  # 跳过主进程

    # 重定向标准输出/错误
    sys.stdout = QueueStream(_print_queue, "stdout")
    sys.stderr = QueueStream(_print_queue, "stderr")

# 子进程引入模块时，自动执行重定向
init_sub()