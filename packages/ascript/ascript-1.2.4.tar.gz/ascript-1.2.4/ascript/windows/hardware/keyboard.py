import pyautogui
import pyperclip
import time
from typing import Union, List, Optional

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