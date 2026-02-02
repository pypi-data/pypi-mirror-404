import threading
import signal
import sys


class Runtime:
    # 静态变量，用于控制生命周期
    _stop_event = threading.Event()

    @staticmethod
    def wait():
        """
        [专业写法] 启动全局事件循环，主线程会停留在此。
        直到调用 Runtime.stop() 或 窗口关闭，程序才会继续向下运行。
        """

        # 优雅处理 Ctrl+C 信号
        def _handle_signal(signum, frame):
            Runtime.stop()

        try:
            signal.signal(signal.SIGINT, _handle_signal)
            signal.signal(signal.SIGTERM, _handle_signal)
        except (ValueError, AttributeError):
            # 某些环境（如非主线程）不支持信号注册
            pass

        print("[System] Runtime 正在等待信号，程序不会退出...")

        # 核心逻辑：无限等待。
        # wait(timeout) 可以让主线程有机会处理系统中断，比 wait() 更推荐
        try:
            while not Runtime._stop_event.is_set():
                Runtime._stop_event.wait(timeout=0.1)
        except KeyboardInterrupt:
            pass

        print("[System] Runtime 已停止。")

    @staticmethod
    def stop():
        """
        手动解除 Runtime.wait() 的阻塞状态，导致主线程继续运行直到退出
        """
        Runtime._stop_event.set()

# --- 调用示范 ---
# win = WebWindow("a.html")
# win.show(block=False)  # 窗口弹出，主线程不被 block
# ... 执行其他初始化 ...
# Runtime.wait()         # 这里才是真正的驻留逻辑