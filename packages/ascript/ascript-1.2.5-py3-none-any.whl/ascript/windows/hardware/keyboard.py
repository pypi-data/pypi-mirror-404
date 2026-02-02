import time
import pyautogui
import pyperclip
from typing import Union, List

class Keyboard:
    """
    基于 PyAutoGUI 封装的键盘自动化操作类。
    支持中英文智能输入、组合键及链式调用。
    """

    @classmethod
    def input(cls, msg: str, interval: float = 0.0):
        """
        自动识别中英文并输入。
        如果是中文或特殊字符，通过剪贴板粘贴实现；如果是纯英文，通过模拟敲击实现。

        :param msg:      要输入的字符串内容。
        :param interval: 仅对纯英文输入有效，每个字符之间敲击的间隔时间（秒）。
        :return:         Keyboard 类对象，支持链式调用。
        """
        # 检查是否包含非 ASCII 字符（如中文、全角符号等）
        if any(ord(c) > 127 for c in msg):
            # 备份当前剪贴板（可选，如果需要更严谨可以记录后还原）
            pyperclip.copy(msg)
            time.sleep(0.1)  # 缓冲，确保系统剪贴板已更新
            pyautogui.hotkey('ctrl', 'v')
        else:
            # 纯英文使用 write，比 typewrite 更现代
            pyautogui.write(msg, interval=interval)
        return cls

    @classmethod
    def key(cls, keys: Union[str, List[str]], presses: int = 1, interval: float = 0.1):
        """
        按下并释放指定按键。

        :param keys:     按键名称（如 'enter', 'esc'）或按键列表。
        :param presses:  连续按下的次数。
        :param interval: 连续按下之间的间隔时间（秒）。
        :return:         Keyboard 类对象。
        """
        pyautogui.press(keys, presses=presses, interval=interval)
        return cls

    @classmethod
    def key_hot(cls, *args, interval: float = 0.1):
        """
        执行组合键操作，如 key_hot('ctrl', 'c')。

        :param args:     按键序列，例如 'ctrl', 'alt', 'delete'。
        :param interval: 按键按下之间的间隔。
        :return:         Keyboard 类对象。
        """
        pyautogui.hotkey(*args, interval=interval)
        return cls

    @classmethod
    def key_down(cls, key_str: str):
        """
        按下按键不松开。

        :param key_str: 按键名称。
        :return:        Keyboard 类对象。
        """
        pyautogui.keyDown(key_str)
        return cls

    @classmethod
    def key_up(cls, key_str: str):
        """
        松开已按下的按键。

        :param key_str: 按键名称。
        :return:        Keyboard 类对象。
        """
        pyautogui.keyUp(key_str)
        return cls

    @classmethod
    def wait(cls, seconds: float):
        """
        键盘操作流中的逻辑等待。

        :param seconds: 等待的时长（秒）。
        :return:        Keyboard 类对象。
        """
        time.sleep(seconds)
        return cls