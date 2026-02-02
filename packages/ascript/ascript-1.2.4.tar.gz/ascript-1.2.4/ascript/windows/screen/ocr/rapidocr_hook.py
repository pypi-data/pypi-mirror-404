import sys
import re
import importlib.abc
import importlib.util
import importlib
from dataclasses import dataclass, asdict
from typing import List, Optional, Tuple, Union, TYPE_CHECKING

# 假设你的硬件操作模块路径如下
from ...hardware import mouse

# --- 1. 类型存根 (仅用于 PyCharm 等 IDE 的代码补全提示) ---
if TYPE_CHECKING:
    try:
        from rapidocr.utils.output import RapidOCROutput as BaseOutput
    except ImportError:
        class BaseOutput:
            pass


    class RapidOCROutput(BaseOutput):
        """IDE 提示：使 RapidOCR 的返回结果具备 find 和 find_all 方法"""

        def find(self, text_re: str = None, score: float = 0.85) -> 'OCRItem': ...

        def find_all(self, text_re: str = None, score: float = 0.85) -> List['OCRItem']: ...


# --- 2. 核心结果对象定义 ---

@dataclass
class OCRItem:
    """真实的识别结果对象"""
    txt: str
    box: List[List[float]]
    score: float
    center: Tuple[int, int]  # 截图内的相对坐标
    rect: List[int]  # [l, t, r, b]

    def click(self, window=None):
        """
        点击目标
        :param window: 可选，传入 ascript 的 Window 对象。
                       如果传入，则调用 window.click(x, y) 进行窗口内相对点击；
                       如果不传，则调用全局 mouse.click(x, y) 进行全屏点击。
        """
        x, y = self.center
        if window:
            # 让窗口对象处理相对坐标点击
            print("窗口点击")
            window.click(x, y)
        else:
            # 全屏绝对点击
            mouse.click(x, y)
        return self

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return asdict(self)

    def __bool__(self):
        """支持 if item: 语法"""
        return True

    def __repr__(self):
        return f"<OCRItem txt='{self.txt}' score={self.score:.2f} center={self.center}>"


class NullOCRItem:
    """空对象：当 find 找不到结果时返回，防止链式调用报错"""

    def __init__(self):
        self.txt, self.box, self.score = "", [], 0.0
        self.center, self.rect = (0, 0), [0, 0, 0, 0]

    def click(self, window=None):
        """静默处理，什么都不做"""
        return self

    def to_dict(self) -> dict:
        return {}

    def __bool__(self):
        """支持 if not item: 语法"""
        return False

    def __repr__(self):
        return "<NullOCRItem (Not Found)>"


# --- 3. 运行时 Hook 逻辑 ---

class RapidOCRHook(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        # 监听 RapidOCR 的核心输出模块
        if fullname == "rapidocr.utils.output":
            importlib.invalidate_caches()  # 动态感知新安装的包
            try:
                spec = importlib.util.find_spec(fullname)
                if spec is None: return None

                if self in sys.meta_path:
                    sys.meta_path.remove(self)

                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self._patch(module)
                sys.modules[fullname] = module
                return spec
            except Exception:
                return None
        return None

    def _patch(self, module):
        """执行动态植入方法"""

        def _build_item(txt, box, score) -> OCRItem:
            """构建结果对象"""
            l, t = float(box[0][0]), float(box[0][1])
            r, b = float(box[2][0]), float(box[2][1])
            center = (int((l + r) / 2), int((t + b) / 2))
            rect = [int(l), int(t), int(r), int(b)]
            return OCRItem(
                txt=str(txt),
                box=box.tolist() if hasattr(box, 'tolist') else box,
                score=float(score),
                center=center,
                rect=rect
            )

        def find(self, text_re: str = None, score: float = 0.85) -> Union[OCRItem, NullOCRItem]:
            """查找单个结果"""
            txts, boxes, scores = getattr(self, 'txts', None), getattr(self, 'boxes', None), getattr(self, 'scores',
                                                                                                     None)
            if txts is not None and boxes is not None:
                for i in range(len(txts)):
                    if scores[i] >= score:
                        if text_re is None or re.search(text_re, str(txts[i])):
                            return _build_item(txts[i], boxes[i], scores[i])
            return NullOCRItem()

        def find_all(self, text_re: str = None, score: float = 0.85) -> List[OCRItem]:
            """查找所有结果并按坐标排序"""
            results = []
            txts, boxes, scores = getattr(self, 'txts', None), getattr(self, 'boxes', None), getattr(self, 'scores',
                                                                                                     None)
            if txts is not None and boxes is not None:
                for i in range(len(txts)):
                    if scores[i] >= score:
                        if text_re is None or re.search(text_re, str(txts[i])):
                            results.append(_build_item(txts[i], boxes[i], scores[i]))

            # 按从上到下、从左到右排序
            results.sort(key=lambda x: (x.center[1], x.center[0]))
            return results

        # 将方法绑定到目标类
        target_class = "RapidOCROutput"
        if hasattr(module, target_class):
            cls = getattr(module, target_class)
            if not hasattr(cls, "find"):
                cls.find = find
                cls.find_all = find_all
                print(f"✅ [RapidOCR-Hook] 成功注入 find/find_all 扩展")


def install():
    """入口函数：确保 Hook 被注册"""
    target_mod = "rapidocr.utils.output"
    if target_mod in sys.modules:
        RapidOCRHook()._patch(sys.modules[target_mod])
        return
    if not any(isinstance(h, RapidOCRHook) for h in sys.meta_path):
        sys.meta_path.insert(0, RapidOCRHook())