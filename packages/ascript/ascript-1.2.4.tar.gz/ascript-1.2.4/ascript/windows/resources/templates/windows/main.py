import multiprocessing
import time
import sys
from ascript.windows.system import R  # 程序上下文与资源路由
from ascript.windows.ui import LicenseWindow  # 安全验证组件
from ascript.windows.ui import FloatScriptWindow  # 脚本控制台组件

# 初始化控制台：支持自启动 (auto_start) 与 多进程隔离 (use_process)
app = FloatScriptWindow(R.img("logo.ico"), title="我的程序", auto_start=True)

@app.on('start')
def task_start():
    # ---------------------------------------------------------
    # 入口程序 (Entry Point)
    # ---------------------------------------------------------
    """
    [业务逻辑入口]
    当用户点击启动按钮或触发自启动时，此函数将在独立的子进程中运行。
    """
    print(">>> [系统] 业务进程已建立，开始执行自动化任务...")
    i= 0

    # 模拟耗时逻辑操作
    while True:
        print(i)
        time.sleep(0.5)
        i += 1


@app.on('stop')
def task_stop():
    """
    [善后处理回调]
    当用户手动停止或任务结束时触发。
    注意：您有约 3 秒的时间进行资源释放（如关闭文件、数据库断开等）。
    即使此处存在死循环，系统也会在超时后强制回收进程资源。
    """
    print(">>> [系统] 接收到停止信号，正在释放系统资源...")
    # 模拟保存数据逻辑
    time.sleep(1)
    print(">>> [系统] 资源释放完毕，安全退出。")




if __name__ == '__main__':
    # 解决打包后子进程重复启动问题
    app.show()