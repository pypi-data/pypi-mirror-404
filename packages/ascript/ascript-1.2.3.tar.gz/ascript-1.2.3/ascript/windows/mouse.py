import pyautogui
import pyperclip
import time
from typing import Union, List, Optional

# 常量定义
LEFT = "left"
MIDDLE = "middle"
RIGHT = "right"
PRIMARY = "primary"
SECONDARY = "secondary"

# 全局配置：增加安全保护
pyautogui.FAILSAFE = True  # 鼠标移动到屏幕四角可强制停止脚本

def click(x: int = None, y: int = None, clicks: int = 1, interval: float = 0.0,
          button: str = PRIMARY, duration: float = 0.02, tween=pyautogui.linear):
    """模拟鼠标点击"""
    pyautogui.click(x=x, y=y, clicks=clicks, interval=interval,
                    button=button, duration=duration, tween=tween)

def scroll(lines: int, x: int = None, y: int = None, h: bool = False, v: bool = True):
    """模拟滚动：lines 为正向上，为负向下"""
    if x is not None and y is not None:
        pyautogui.moveTo(x, y)

    if h:
        pyautogui.hscroll(lines)
    elif v:
        pyautogui.vscroll(lines)
    else:
        pyautogui.scroll(lines)

def drag(start_x: int, start_y: int, to_x: int, to_y: int, duration: float = 0.5):
    """从指定位置拖拽到目标位置"""
    pyautogui.moveTo(start_x, start_y)
    pyautogui.dragTo(to_x, to_y, duration=duration)

def mouse_down(x: int = None, y: int = None, button: str = PRIMARY, duration: float = 0.0, tween=pyautogui.linear):
    """按下鼠标按键"""
    pyautogui.mouseDown(x=x, y=y, button=button, duration=duration, tween=tween)

def mouse_move(x: int, y: int, duration: float = 0.5, tween=pyautogui.linear):
    """移动鼠标"""
    pyautogui.moveTo(x, y, duration=duration, tween=tween)

def mouse_up(x: int = None, y: int = None, button: str = PRIMARY, duration: float = 0.0, tween=pyautogui.linear):
    """松开鼠标按键"""
    pyautogui.mouseUp(x=x, y=y, button=button, duration=duration, tween=tween)

def input(msg: str, interval: float = 0.0):
    """自动识别中英文并输入"""
    # 检查是否包含非 ASCII 字符（如中文）
    if any(ord(c) > 127 for c in msg):
        pyperclip.copy(msg)
        time.sleep(0.1)  # 给剪贴板一点缓冲时间，防止粘贴失败
        pyautogui.hotkey('ctrl', 'v')
    else:
        # typewrite 已逐步被 write 取代，推荐使用 write
        pyautogui.write(msg, interval=interval)

def key(keys: Union[str, List[str]], presses: int = 1, interval: float = 0.0):
    """按下指定按键"""
    pyautogui.press(keys, presses=presses, interval=interval)

def key_hot(*args):
    """
    组合键操作，例如: key_hot('ctrl', 'c')
    修正了原先参数传递的错误
    """
    pyautogui.hotkey(*args)

def key_down(key_str: str):
    """按下按键不松开"""
    pyautogui.keyDown(key_str)

def key_up(key_str: str):
    """松开按键"""
    pyautogui.keyUp(key_str)