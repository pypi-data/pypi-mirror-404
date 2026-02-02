import ctypes
from ctypes import wintypes
import threading
import time
import struct

# --- 系统环境检查 ---
IS_64BIT = struct.calcsize("P") == 8
PTR_TYPE = ctypes.c_int64 if IS_64BIT else ctypes.c_int32


class DrawWindow:
    _hwnd = None
    _thread = None
    _shapes = []  # 存储任务: {'type': 'rect', 'data': (x, y, w, h, color, thickness)}
    _lock = threading.Lock()
    _wnd_proc_ptr = None

    # 窗口过程回调定义
    WNDPROC = ctypes.WINFUNCTYPE(PTR_TYPE, wintypes.HWND, ctypes.c_uint, wintypes.WPARAM, wintypes.LPARAM)

    @staticmethod
    def _create_window():
        user32 = ctypes.windll.user32
        gdi32 = ctypes.windll.gdi32
        kernel32 = ctypes.windll.kernel32

        # 1. 开启 DPI 感知 (防止 Win10/Win11 缩放导致坐标偏移)
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            user32.SetProcessDPIAware()

        clsname = f"DrawWindow_{int(time.time())}"
        hinst = kernel32.GetModuleHandleW(None)

        def wnd_proc(hwnd, msg, wparam, lparam):
            if msg == 0x000F:  # WM_PAINT
                ps = ctypes.create_string_buffer(64)
                hdc = user32.BeginPaint(hwnd, ps)

                with DrawWindow._lock:
                    for item in DrawWindow._shapes:
                        t, d = item['type'], item['data']

                        if t in ('rect', 'line'):
                            color, thick = d[4], d[5]
                            pen = gdi32.CreatePen(0, thick, color)
                            old_pen = gdi32.SelectObject(hdc, pen)
                            if t == 'rect':
                                brush = gdi32.GetStockObject(5)  # NULL_BRUSH
                                old_brush = gdi32.SelectObject(hdc, brush)
                                gdi32.Rectangle(hdc, d[0], d[1], d[0] + d[2], d[1] + d[3])
                                gdi32.SelectObject(hdc, old_brush)
                            else:  # line
                                gdi32.MoveToEx(hdc, d[0], d[1], None)
                                gdi32.LineTo(hdc, d[2], d[3])
                            gdi32.SelectObject(hdc, old_pen)
                            gdi32.DeleteObject(pen)

                        elif t == 'text':
                            x, y, text, color, size = d
                            font = gdi32.CreateFontW(size, 0, 0, 0, 400, 0, 0, 0, 1, 0, 0, 0, 0, "Microsoft YaHei")
                            old_font = gdi32.SelectObject(hdc, font)
                            gdi32.SetTextColor(hdc, color)
                            gdi32.SetBkMode(hdc, 1)  # TRANSPARENT
                            gdi32.TextOutW(hdc, x, y, text, len(text))
                            gdi32.SelectObject(hdc, old_font)
                            gdi32.DeleteObject(font)

                user32.EndPaint(hwnd, ps)
                return 0

            if msg == 0x0002:  # WM_DESTROY
                user32.PostQuitMessage(0)
                return 0

            # 安全调用默认窗口过程
            user32.DefWindowProcW.argtypes = [wintypes.HWND, ctypes.c_uint, wintypes.WPARAM, wintypes.LPARAM]
            user32.DefWindowProcW.restype = PTR_TYPE
            return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

        DrawWindow._wnd_proc_ptr = DrawWindow.WNDPROC(wnd_proc)

        from ctypes import Structure, c_uint, c_int
        class WNDCLASS(Structure):
            _fields_ = [("style", c_uint), ("lpfnWndProc", DrawWindow.WNDPROC), ("cbClsExtra", c_int),
                        ("cbWndExtra", c_int), ("hInstance", wintypes.HINSTANCE), ("hIcon", wintypes.HICON),
                        ("hCursor", wintypes.HANDLE), ("hbrBackground", wintypes.HANDLE),
                        ("lpszMenuName", wintypes.LPCWSTR), ("lpszClassName", wintypes.LPCWSTR)]

        wc = WNDCLASS()
        wc.lpfnWndProc = DrawWindow._wnd_proc_ptr
        wc.hInstance = hinst
        wc.lpszClassName = clsname
        wc.hbrBackground = gdi32.GetStockObject(4)  # BLACK_BRUSH
        wc.hCursor = user32.LoadCursorW(0, 32512)  # IDC_ARROW
        user32.RegisterClassW(ctypes.byref(wc))

        # 获取当前屏幕物理分辨率
        sw = user32.GetSystemMetrics(0)
        sh = user32.GetSystemMetrics(1)

        # 创建全屏透明置顶窗口
        # WS_EX_LAYERED(0x80000) | WS_EX_TRANSPARENT(0x20) | WS_EX_TOPMOST(0x08)
        DrawWindow._hwnd = user32.CreateWindowExW(
            0x00080000 | 0x00000020 | 0x00000008,
            clsname, "DrawOverlay", 0x80000000,
            0, 0, sw, sh, 0, 0, hinst, 0
        )

        # 防截图核心 API
        user32.SetWindowDisplayAffinity(DrawWindow._hwnd, 0x11)  # WDA_EXCLUDEFROMCAPTURE
        # 黑色透明
        user32.SetLayeredWindowAttributes(DrawWindow._hwnd, 0, 255, 0x1)
        user32.ShowWindow(DrawWindow._hwnd, 5)

        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), 0, 0, 0) != 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

    @staticmethod
    def _init():
        if DrawWindow._thread is None:
            DrawWindow._thread = threading.Thread(target=DrawWindow._create_window, daemon=True)
            DrawWindow._thread.start()
            while DrawWindow._hwnd is None: time.sleep(0.05)

    @staticmethod
    def draw_rect(x, y, w, h, color=0x0000FF, thickness=2):
        """BGR 颜色格式"""
        DrawWindow._init()
        with DrawWindow._lock:
            DrawWindow._shapes.append({'type': 'rect', 'data': (x, y, w, h, color, thickness)})
        ctypes.windll.user32.InvalidateRect(DrawWindow._hwnd, None, True)

    @staticmethod
    def draw_line(x1, y1, x2, y2, color=0x0000FF, thickness=2):
        DrawWindow._init()
        with DrawWindow._lock:
            DrawWindow._shapes.append({'type': 'line', 'data': (x1, y1, x2, y2, color, thickness)})
        ctypes.windll.user32.InvalidateRect(DrawWindow._hwnd, None, True)

    @staticmethod
    def draw_text(x, y, text, color=0x0000FF, font_size=20):
        DrawWindow._init()
        with DrawWindow._lock:
            DrawWindow._shapes.append({'type': 'text', 'data': (x, y, text, color, font_size)})
        ctypes.windll.user32.InvalidateRect(DrawWindow._hwnd, None, True)

    @staticmethod
    def clear():
        if DrawWindow._hwnd:
            with DrawWindow._lock: DrawWindow._shapes.clear()
            ctypes.windll.user32.InvalidateRect(DrawWindow._hwnd, None, True)


# --- 辅助工具：RGB 转 BGR ---
def RGB(r, g, b):
    return (b << 16) | (g << 8) | r


# --- 示例使用 ---
if __name__ == "__main__":
    # 画一个三角形（三条线）
    DrawWindow.draw_line(500, 200, 300, 500, thickness=3)  # 蓝色
    DrawWindow.draw_line(300, 500, 700, 500, color=0xFF0000, thickness=3)
    DrawWindow.draw_line(700, 500, 500, 200, color=0xFF0000, thickness=3)

    DrawWindow.draw_text(450, 520, "Triangle Base", color=0xFFFFFF, font_size=25)

    time.sleep(10)
    DrawWindow.clear()