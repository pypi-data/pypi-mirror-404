import time
from ctypes import windll

import pyautogui
from typing import Optional

# 常量定义
LEFT = "left"
MIDDLE = "middle"
RIGHT = "right"
PRIMARY = "primary"
SECONDARY = "secondary"

# 启用 DPI 感知
try:
    windll.shcore.SetProcessDpiAwareness(1)
except:
    windll.user32.SetProcessDPIAware()


class Mouse:
    # 全局配置
    pyautogui.FAILSAFE = True
    # 默认鼠标移动耗时
    DEFAULT_MOVE_DURATION = 0.1

    @classmethod
    def mouse_move(cls, x: int, y: int, move_duration: float = DEFAULT_MOVE_DURATION, tween=pyautogui.linear):
        """移动鼠标到指定位置"""
        pyautogui.moveTo(x=x, y=y, duration=move_duration, tween=tween)
        return cls

    @classmethod
    def mouse_down(cls, x: int = None, y: int = None, button: str = PRIMARY, move_duration: float = 0.0):
        """按下鼠标按键"""
        pyautogui.mouseDown(x=x, y=y, button=button, duration=move_duration)
        return cls

    @classmethod
    def mouse_up(cls, x: int = None, y: int = None, button: str = PRIMARY, move_duration: float = 0.0):
        """松开鼠标按键"""
        pyautogui.mouseUp(x=x, y=y, button=button, duration=move_duration)
        return cls

    @classmethod
    def click(cls,
              x: Optional[int] = None,
              y: Optional[int] = None,
              clicks: int = 1,
              interval: float = 0.1,
              button: str = PRIMARY,
              move_duration: float = 0.00,
              duration: float = 0.0,
              offset: int = 0):
        """
        模拟鼠标点击。支持移动耗时控制、多重点击、长按逻辑路由及随机偏移。

        :param x:             目标位置横坐标。若为 None，则在当前位置点击。
        :param y:             目标位置纵坐标。若为 None，则在当前位置点击。
        :param clicks:        点击次数。默认为 1 次。
        :param interval:      多次点击之间的间隔时间（秒）。仅在 clicks > 1 时有效。
        :param button:        触发的鼠标按键。可选: 'left', 'middle', 'right', 'primary', 'secondary'。
        :param move_duration: 鼠标移动到目标坐标 (x, y) 所需的时间（秒）。
        :param duration:      按键按下的物理持续时间（秒）。若 > 0，会自动调用 long_press 逻辑。
        :param offset:        随机偏移半径（像素）。在以 (x, y) 为中心的区域内随机点击。
        :return:              Mouse 类对象，支持链式调用。
        """
        target_x, target_y = x, y

        # 1. 逻辑核心：计算随机偏移后的最终目标坐标
        if offset > 0 and x is not None and y is not None:
            import random
            target_x = max(0, x + random.randint(-offset, offset))
            target_y = max(0, y + random.randint(-offset, offset))

        # 2. 逻辑核心：显式处理移动耗时 (move_duration)
        # 如果指定了坐标，先平滑移动到目标点（含偏移量）
        if target_x is not None and target_y is not None:
            cls.mouse_move(target_x, target_y, move_duration=move_duration)

        # 3. 逻辑核心：处理长按路由
        # 如果设置了 duration > 0，则跳转到长按逻辑，并返回
        if duration > 0:
            cls.mouse_down(x=target_x, y=target_y, button=button)
            time.sleep(duration)
            cls.mouse_up(button=button)

        # 4. 执行最终点击
        # 注意：此处 x, y 传 None 是因为已经在上面移动到了 target_x, target_y
        pyautogui.click(x=None, y=None, clicks=clicks, interval=interval,
                        button=button, duration=0.0)

        return cls

    @classmethod
    def long_press(cls, x: int = None, y: int = None, press_duration: float = 2.0, button: str = PRIMARY):
        """
        模拟长按逻辑
        :param press_duration: 鼠标按下的物理持续时间
        """
        cls.mouse_down(x=x, y=y, button=button)
        time.sleep(press_duration)
        cls.mouse_up(button=button)
        return cls

    @classmethod
    def scroll(cls, lines: int, x: int = None, y: int = None, direction: str = "v"):
        """模拟滚动"""
        if x is not None and y is not None:
            cls.mouse_move(x, y, move_duration=0.0)

        if direction == "h":
            pyautogui.hscroll(lines)
        else:
            pyautogui.scroll(lines)
        return cls

    @classmethod
    def drag(cls, to_x: int, to_y: int, from_x: int = None, from_y: int = None, move_duration: float = 0.5):
        """从指定位置拖拽到目标位置"""
        if from_x is not None and from_y is not None:
            pyautogui.moveTo(from_x, from_y)
        pyautogui.dragTo(to_x, to_y, duration=move_duration)
        return cls

    @classmethod
    def wait(cls, seconds: float):
        """链式调用中的逻辑等待"""
        time.sleep(seconds)
        return cls