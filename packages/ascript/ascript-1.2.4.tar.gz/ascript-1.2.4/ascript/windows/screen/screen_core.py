import os
import base64
import ctypes
from io import BytesIO
from typing import Literal, Union, Optional, List
import numpy as np
from PIL import Image
from mss import mss

# 解决 Windows 高分屏缩放导致的截图坐标偏差
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

class Screen:
    @staticmethod
    def size() -> List[int]:
        """获取主显示器尺寸"""
        with mss() as sct:
            monitor = sct.monitors[1]
            return [monitor["width"], monitor["height"]]



    @staticmethod
    def capture(
            rect: Optional[List[int]] = None,
            format: str = "pillow",
            save_path: Optional[str] = None
    ) -> Union[Image.Image, np.ndarray, str, None]:
        """
        截取屏幕（支持 DPI 自适应与区域校验）
        :param rect: [left, top, right, bottom]
        :param format: 'pillow', 'numpy', 'opencv', 'base64' (default jpeg), 'base64:png'
        :param save_path: 自动识别后缀存储
        """
        with mss() as sct:
            try:
                # 1. 区域计算与合法性校验
                if rect and len(rect) == 4:
                    left, top, right, bottom = rect
                    # 确保 width 和 height 为正数
                    width, height = max(0, right - left), max(0, bottom - top)
                    if width == 0 or height == 0:
                        return None
                    monitor = {"left": left, "top": top, "width": width, "height": height}
                else:
                    monitor = sct.monitors[1]

                # 2. 执行截图
                sct_img = sct.grab(monitor)

                # 3. 构造 PIL 对象 (核心中转)
                img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

                # 4. 磁盘保存逻辑
                if save_path:
                    directory = os.path.dirname(save_path)
                    if directory and not os.path.exists(directory):
                        os.makedirs(directory, exist_ok=True)

                    _, ext = os.path.splitext(save_path)
                    ext = ext.lower().strip('.')
                    # 自动匹配存储格式
                    save_fmt = "JPEG" if ext in ["jpg", "jpeg"] else ("PNG" if ext == "png" else "PNG")

                    # 针对不同格式设置最优参数
                    save_args = {"format": save_fmt}
                    if save_fmt == "JPEG":
                        save_args["quality"] = 95
                        save_args["subsampling"] = 0  # 提升色彩保持度

                    img.save(save_path, **save_args)

                # 5. 返回格式化处理
                if format.startswith("base64"):
                    # 默认 jpeg，除非明确指定 base64:png
                    sub_format = "PNG" if (":" in format and format.split(":")[1].lower() == "png") else "JPEG"

                    buffered = BytesIO()
                    img.save(buffered, format=sub_format, quality=80 if sub_format == "JPEG" else None)
                    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
                    return f"data:image/{sub_format.lower()};base64,{img_str}"

                elif format == "pillow":
                    return img

                elif format == "numpy":
                    return np.array(img)

                elif format == "opencv":
                    return np.array(img)[:, :, ::-1]

                return img

            except Exception as e:
                print(f"Screenshot Error: {e}")
                return None