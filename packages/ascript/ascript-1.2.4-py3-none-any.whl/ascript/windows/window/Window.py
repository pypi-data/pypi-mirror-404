
from typing import List, NamedTuple
import win32gui
import win32con
import win32ui
import win32process
import psutil
import time
from ctypes import windll, byref, sizeof, c_int
from ctypes.wintypes import RECT
from PIL import Image
# import uiautomation as auto
import re
from enum import Enum, auto
from typing import Optional, Union,TYPE_CHECKING
import numpy as np
import cv2
import ctypes

# 启用 DPI 感知
try:
    windll.shcore.SetProcessDpiAwareness(1)
except:
    windll.user32.SetProcessDPIAware()


# 1. 定义独立的结构类
class WindowRect(NamedTuple):
    """窗口空间位置信息 (不占内存，支持补全)"""
    left: int
    top: int
    right: int
    bottom: int
    width: int
    height: int

class WindowCaptureFormat(Enum):
    """窗口截图输出格式枚举"""
    PIL = auto()      # 返回 PIL.Image (默认，最常用)
    NUMPY = auto()    # 返回 numpy.ndarray (RGB)
    OPENCV = auto()   # 返回 numpy.ndarray (BGR，适合 cv2 使用)

    def convert(self, pil_image: Image.Image) -> Union[Image.Image, np.ndarray]:
        """
        将 PIL.Image 转换为当前枚举指定的格式
        """
        if self is WindowCaptureFormat.PIL:
            return pil_image

        array = np.array(pil_image)  # RGB

        if self is WindowCaptureFormat.NUMPY:
            return array

        if self is WindowCaptureFormat.OPENCV:
            return cv2.cvtColor(array, cv2.COLOR_RGB2BGR)

        # 理论上不会走到这里，但为了安全
        raise ValueError(f"Unsupported format: {self}")

class Window:
    def __init__(self, hwnd):
        self.hwnd = hwnd
        self._pid = None  # 延迟加载缓存

    def __repr__(self):
        return f"<Window: {self.title[:15]} [{self.process_name[:15]}] (HWND:{self.hwnd})>"

    @classmethod
    def find_all(
            cls,
            title_re: str = None,
            process_name: str = None,
            class_name: str = None,
            visible_only: bool = True
    ) -> List["Window"]:
        """
        [批量检索] 返回所有满足条件的窗口列表
        """
        results = []
        pattern = re.compile(title_re) if title_re else None

        def callback(hwnd, _):
            if visible_only and not win32gui.IsWindowVisible(hwnd):
                return True

            win = cls(hwnd)
            if class_name and class_name != win.class_name:
                return True
            if process_name and process_name.lower() not in win.process_name.lower():
                return True
            if pattern and not pattern.search(win.title):
                return True

            if win.title:
                results.append(win)
            return True

        win32gui.EnumWindows(callback, None)
        return results

    @classmethod
    def find(
            cls,
            title_re: str = None,
            process_name: str = None,
            class_name: str = None,
            visible_only: bool = True,
            timeout: int = 0
    ) -> Optional["Window"]:
        """
        [快速检索] 返回满足条件的第一个窗口
        :param timeout: 等待超时时间(秒)，默认为 0 (立即返回)
        """
        start_time = time.time()

        while True:
            # 直接调用 find_all 获取当前所有匹配项
            results = cls.find_all(
                title_re=title_re,
                process_name=process_name,
                class_name=class_name,
                visible_only=visible_only
            )

            if results:
                return results[0]

            # 如果没有设置超时，或者已超时，则退出循环
            if timeout <= 0 or (time.time() - start_time) > timeout:
                break

            time.sleep(0.5)  # 轮询间隔，避免过度占用 CPU

        return None

    @classmethod
    def launch(
            cls,
            name: str = None,
            path: str = None,
            allow_multiple: bool = False,
            timeout: int = 15
    ) -> Optional["Window"]:
        from .launcher import Launcher

        # 1. 修正方法名：使用 get_info 自动关联进程名
        auto_path, proc_name = Launcher.get_info(name, path)
        final_path = path or auto_path

        # 2. 修正逻辑：使用 find_all 获取列表，确保判断多开时的基数准确
        pre_wins = cls.find_all(title_re=name, process_name=proc_name, visible_only=False)

        if not allow_multiple and pre_wins:
            win = pre_wins[0]
            # 唤醒逻辑：处理最小化和托盘
            win32gui.ShowWindow(win.hwnd, 9)  # SW_RESTORE
            win.activate()
            return win

        # 3. 启动
        Launcher.run(name=name, path=final_path)

        # 4. 轮询
        start_time = time.time()
        pre_hwnds = {w.hwnd for w in pre_wins}
        while time.time() - start_time < timeout:
            # 持续用 find_all 刷新当前窗口状态
            current_wins = cls.find_all(title_re=name, process_name=proc_name, visible_only=False)

            if allow_multiple:
                new_wins = [w for w in current_wins if w.hwnd not in pre_hwnds]
                if new_wins:
                    new_wins[0].activate()
                    return new_wins[0]
            else:
                if current_wins:
                    current_wins[0].activate()
                    return current_wins[0]

            time.sleep(0.5)

        return pre_wins[0] if pre_wins else None

    # --- 基础标识属性 ---
    @property
    def title(self):
        """窗口标题"""
        return win32gui.GetWindowText(self.hwnd)

    @property
    def class_name(self):
        """窗口类名 (用于区分应用类型)"""
        return win32gui.GetClassName(self.hwnd)

    # --- 进程相关属性 ---
    @property
    def pid(self):
        """进程 ID"""
        if self._pid is None:
            _, self._pid = win32process.GetWindowThreadProcessId(self.hwnd)
        return self._pid

    @property
    def process_path(self):
        """可执行文件完整路径"""
        try:
            return psutil.Process(self.pid).exe()
        except:
            return "Unknown"

    @property
    def process_name(self):
        """进程名 (如 chrome.exe)"""
        try:
            return psutil.Process(self.pid).name()
        except:
            return "Unknown"

    # --- 状态属性 ---
    @property
    def is_visible(self):
        """窗口是否可见"""
        return win32gui.IsWindowVisible(self.hwnd)

    @property
    def is_minimized(self):
        """是否最小化"""
        return win32gui.IsIconic(self.hwnd) != 0

    @property
    def is_maximized(self):
        """是否最大化"""
        return win32gui.IsZoomed(self.hwnd) != 0

    @property
    def is_responding(self):
        """窗口是否响应（未卡死）"""
        return windll.user32.IsHungAppWindow(self.hwnd) == 0

    @property
    def is_always_on_top(self):
        """是否处于“总在最前”置顶状态"""
        style = win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE)
        return (style & win32con.WS_EX_TOPMOST) != 0

    @property
    def rect(self) -> WindowRect:
        """
        [属性] 获取窗口精准的视觉坐标和大小 (DPI感知)
        用法: win.rect.width, win.rect.top
        """
        r = RECT()
        # 底层 DWM 逻辑：获取真实的视觉边界
        windll.dwmapi.DwmGetWindowAttribute(self.hwnd, 9, byref(r), sizeof(r))

        w = r.right - r.left
        h = r.bottom - r.top

        return WindowRect(r.left, r.top, r.right, r.bottom, w, h)

    def set_rect(self, x: int = None, y: int = None, width: int = None, height: int = None):
        """
        [全能设置] 统一调整窗口的位置和大小
        :param x: 目标 X 坐标 (None 则保持现状)
        :param y: 目标 Y 坐标 (None 则保持现状)
        :param width: 目标宽度 (None 则保持现状)
        :param height: 目标高度 (None 则保持现状)
        """
        # 1. 拿当前的 rect (利用我们定义好的 WindowRect 结构)
        curr = self.rect

        # 2. 确定最终参数：如果有传入则用传入值，否则用当前值
        new_x = x if x is not None else curr.left
        new_y = y if y is not None else curr.top
        new_w = width if width is not None else curr.width
        new_h = height if height is not None else curr.height

        # 3. 调用底层 API
        # SWP_NOZORDER: 保证窗口在移动时不会改变它在所有窗口中的层级顺序
        win32gui.SetWindowPos(
            self.hwnd,
            win32con.HWND_TOP,
            new_x, new_y, new_w, new_h,
            win32con.SWP_NOZORDER | win32con.SWP_SHOWWINDOW
        )

    def move(self, x: int, y: int):
        """[白话快捷] 仅移动位置，不改变大小"""
        self.set_rect(x=x, y=y)

    def resize(self, width: int, height: int):
        """[白话快捷] 仅改变大小，不改变位置"""
        self.set_rect(width=width, height=height)

    # --- 核心操作方法 ---
    def activate(self):
        """激活并带到前台"""
        if self.is_minimized:
            win32gui.ShowWindow(self.hwnd, win32con.SW_RESTORE)
        windll.user32.SetForegroundWindow(self.hwnd)

    def set_always_on_top(self, toggle=True):
        """设置或取消置顶"""
        z_order = win32con.HWND_TOPMOST if toggle else win32con.HWND_NOTOPMOST
        win32gui.SetWindowPos(self.hwnd, z_order, 0, 0, 0, 0,
                              win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)

    def minimize(self):
        win32gui.ShowWindow(self.hwnd, win32con.SW_MINIMIZE)

    def close(self):
        """标准关闭"""
        win32gui.PostMessage(self.hwnd, win32con.WM_CLOSE, 0, 0)

    def kill(self):
        """强行杀死所属进程"""
        try:
            psutil.Process(self.pid).kill()
            return True
        except:
            return False

    # --- 增强版截图 (解决黑屏+尺寸不对) ---
    def capture(
            self,
            save_path: Optional[str] = None,
            format: WindowCaptureFormat = WindowCaptureFormat.PIL,
            rect: Optional[WindowRect] = None,
            force_activate: bool = True
    ) -> Union[Image.Image, np.ndarray, None]:
        """
        窗口截图 - 支持指定区域 + 多种输出格式
        （已改为使用客户端坐标系，只截取窗口内容区，不含标题栏/边框/阴影/状态栏）
        """
        prev_hwnd = None
        if force_activate:
            prev_hwnd = windll.user32.GetForegroundWindow()
            self.activate()
            # time.sleep(0.15)  # 给渲染一点缓冲   ← 保持原样，未动

        try:
            # ──────────────── 关键修改：使用客户端矩形 ────────────────
            client_rect = win32gui.GetClientRect(self.hwnd)  # 返回 (left, top, right, bottom) 相对坐标
            client_width = client_rect[2] - client_rect[0]
            client_height = client_rect[3] - client_rect[1]

            if client_width <= 0 or client_height <= 0:
                return None

            # 获取客户端区域在屏幕上的实际位置（用于和 rect 对齐）
            client_top_left = win32gui.ClientToScreen(self.hwnd, (client_rect[0], client_rect[1]))
            f_left, f_top = client_top_left
            f_right = f_left + client_width
            f_bot = f_top + client_height

            # 2. 确定实际要截取的区域（用户指定 or 整窗）
            target = rect if rect else self.rect

            # 计算偏移：现在基于客户端区域左上角
            offset_x = target.left - f_left
            offset_y = target.top - f_top
            w, h = target.width, target.height

            if w <= 0 or h <= 0:
                return None

            # 3. PrintWindow 核心截图流程（完全不变）
            hwndDC = win32gui.GetWindowDC(self.hwnd)
            mfcDC = win32ui.CreateDCFromHandle(hwndDC)
            saveDC = mfcDC.CreateCompatibleDC()
            saveBitMap = win32ui.CreateBitmap()

            # ★ 关键：bitmap 大小改为客户端区域大小（不包含阴影/边框）
            saveBitMap.CreateCompatibleBitmap(mfcDC, client_width, client_height)
            saveDC.SelectObject(saveBitMap)

            # PW_RENDERFULLCONTENT = 3 （保持不变）
            windll.user32.PrintWindow(self.hwnd, saveDC.GetSafeHdc(), 3)

            bmpinfo = saveBitMap.GetInfo()
            bmpstr = saveBitMap.GetBitmapBits(True)

            # 4. 转成 PIL.Image 并裁剪（坐标系已对齐到客户端）
            img = Image.frombuffer(
                'RGB',
                (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                bmpstr,
                'raw',
                'BGRX',
                0,
                1
            )
            img = img.crop((offset_x, offset_y, offset_x + w, offset_y + h))

            # 5. 格式转换（不变）
            result = format.convert(img)

            # 6. 保存（不变）
            if save_path:
                if format is WindowCaptureFormat.OPENCV:
                    cv2.imwrite(save_path, result)
                elif format is WindowCaptureFormat.PIL:
                    img.save(save_path)
                else:  # NUMPY
                    Image.fromarray(result).save(save_path)

            return result

        except Exception as e:
            print(f"窗口截图失败: {e}")
            return None

        finally:
            # 清理资源（不变）
            try:
                win32gui.DeleteObject(saveBitMap.GetHandle())
                saveDC.DeleteDC()
                mfcDC.DeleteDC()
                win32gui.ReleaseDC(self.hwnd, hwndDC)
            except:
                pass

            # 恢复前台窗口（不变）
            if force_activate and prev_hwnd and prev_hwnd != self.hwnd:
                try:
                    windll.user32.SetForegroundWindow(prev_hwnd)
                except:
                    pass

    # --- 交互操作方法 ---

    def _get_lparam(self, x: int, y: int, is_relative: bool):
        """内部工具：将坐标转换为 Windows 消息参数"""
        if not is_relative:
            r = self.rect
            x, y = x - r.left, y - r.top
        # MAKELONG 的逻辑：高16位是Y，低16位是X
        return (y << 16) | (x & 0xFFFF)

    def click(self, x: int, y: int, is_relative: bool = True, button: str = "left"):
        """
        [白话：点击] 支持后台点击
        :param x, y: 坐标
        :param is_relative: 是否为相对于窗口左上角的坐标
        :param button: "left" 或 "right"
        """
        lparam = self._get_lparam(x, y, is_relative)
        btn_down = win32con.WM_LBUTTONDOWN if button == "left" else win32con.WM_RBUTTONDOWN
        btn_up = win32con.WM_LBUTTONUP if button == "left" else win32con.WM_RBUTTONUP
        mk_btn = win32con.MK_LBUTTON if button == "left" else win32con.MK_RBUTTON

        win32gui.PostMessage(self.hwnd, btn_down, mk_btn, lparam)
        time.sleep(0.05)  # 模拟物理间隔
        win32gui.PostMessage(self.hwnd, btn_up, 0, lparam)

    def long_click(self, x: int, y: int, duration: float = 1.0, is_relative: bool = True):
        """[白话：长按]"""
        lparam = self._get_lparam(x, y, is_relative)
        win32gui.PostMessage(self.hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, lparam)
        time.sleep(duration)
        win32gui.PostMessage(self.hwnd, win32con.WM_LBUTTONUP, 0, lparam)

    def drag(self, x1: int, y1: int, x2: int, y2: int, duration: float = 0.5, is_relative: bool = True):
        """
        [白话：拖拽/滑动] 从 (x1,y1) 滑动到 (x2,y2)
        """
        p1 = self._get_lparam(x1, y1, is_relative)
        p2 = self._get_lparam(x2, y2, is_relative)

        # 1. 按下
        win32gui.PostMessage(self.hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, p1)

        # 2. 模拟滑动过程 (平滑移动)
        steps = 10
        for i in range(steps + 1):
            curr_x = int(x1 + (x2 - x1) * (i / steps))
            curr_y = int(y1 + (y2 - y1) * (i / steps))
            curr_p = self._get_lparam(curr_x, curr_y, is_relative)
            win32gui.PostMessage(self.hwnd, win32con.WM_MOUSEMOVE, win32con.MK_LBUTTON, curr_p)
            time.sleep(duration / steps)

        # 3. 抬起
        win32gui.PostMessage(self.hwnd, win32con.WM_LBUTTONUP, 0, p2)

    def type_text(self, text: str):
        """
        [白话：输入文本] 向窗口发送字符消息 (无需激活窗口)
        """
        for char in text:
            # WM_CHAR 消息直接发送字符编码
            win32gui.PostMessage(self.hwnd, win32con.WM_CHAR, ord(char), 0)
            time.sleep(0.01)


