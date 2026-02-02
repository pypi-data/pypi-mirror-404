from __future__ import annotations

import json
from typing import Tuple
from .Window import Window
from PIL import Image

class UIElement:
    def __init__(self, node: auto.Control, window: Any, depth: int):
        """
        UI 元素封装类
        """
        self.node = node
        self.window = window
        self.depth = depth
        self.children: List['UIElement'] = []

        # --- 1. 基础标识属性 (原生映射，不拼凑) ---
        self.name: str = node.Name or ""
        self.type: str = node.ControlTypeName or ""
        self.class_name: str = node.ClassName or ""
        self.handle: int = node.NativeWindowHandle or 0

        # 资源 ID: 仅存储原生的 AutomationId
        self.res_id: str = node.AutomationId or ""

        # 内存 ID: 仅存储对象在内存中的物理唯一地址 (Python Object ID)
        self.memory_id: int = id(self.node)

        # --- 2. 交互状态属性 ---
        self.is_enabled: bool = node.IsEnabled
        self.is_visible: bool = not node.IsOffscreen
        self.is_clickable: bool = self._check_clickable(node)
        self.is_password: bool = node.IsPassword

        # 内容获取
        self.value: str = self._get_node_value(node)
        self.description: str = node.HelpText or ""

        # --- 3. 坐标转换 (窗口相对坐标) ---
        rect = node.BoundingRectangle
        w_rect = self.window.rect
        win_l = w_rect.left if hasattr(w_rect, 'left') else w_rect[0]
        win_t = w_rect.top if hasattr(w_rect, 'top') else w_rect[1]

        self.relative_rect = (
            rect.left - win_l,
            rect.top - win_t,
            rect.right - win_l,
            rect.bottom - win_t
        )

    def _check_clickable(self, node: auto.Control) -> bool:
        """检查节点是否支持点击模式"""
        try:
            return any([
                hasattr(node, 'GetInvokePattern') and node.GetInvokePattern(),
                hasattr(node, 'GetTogglePattern') and node.GetTogglePattern(),
                hasattr(node, 'GetSelectionItemPattern') and node.GetSelectionItemPattern()
            ])
        except:
            return False

    def _get_node_value(self, node: auto.Control) -> str:
        """获取控件内容值"""
        try:
            if hasattr(node, 'GetValuePattern'):
                val = node.GetValuePattern().Value
                if val and val != self.name:
                    return val
            if self.type == "EditControl":
                return node.Name or ""
        except:
            pass
        return ""

    def to_dict(self) -> Dict[str, Any]:
        """将对象转换为扁平化的字典结构"""
        return {
            "name": self.name,
            "type": self.type,
            "res_id": self.res_id,  # 有就有，没有就是 ""
            "memory_id": self.memory_id,  # 纯数字内存地址
            "class_name": self.class_name,
            "handle": self.handle,
            "rect": {
                "left": self.relative_rect[0],
                "top": self.relative_rect[1],
                "right": self.relative_rect[2],
                "bottom": self.relative_rect[3]
            },
            "enabled": self.is_enabled,
            "visible": self.is_visible,
            "clickable": self.is_clickable,
            "value": self.value,
            "description": self.description,
            "password": self.is_password,
            "depth": self.depth,
            "child_count": len(self.children),
            "children": [child.to_dict() for child in self.children]
        }

    @property
    def child_count(self) -> int:
        """获取子节点数量"""
        return len(self.children)

    @property
    def center(self) -> Tuple[int, int]:
        l, t, r, b = self.relative_rect
        return (l + r) // 2, (t + b) // 2

    def click(self, simulate: bool = False):
        """
        :param simulate:
            True:  强制移动鼠标并进行物理点击 (Input Simulation)
            False: 尝试底层指令点击 (Action/Invoke)，如果不支持则自动降级为物理点击
        """
        if not simulate:
            # 1. 尝试使用 InvokePattern (最通用的底层点击)
            try:
                pattern = self.node.GetInvokePattern()
                if pattern:
                    pattern.Invoke()
                    return self
            except:
                pass

            # 2. 尝试使用 TogglePattern (适用于复选框、某些开关按钮)
            try:
                pattern = self.node.GetTogglePattern()
                if pattern:
                    pattern.Toggle()
                    return self
            except:
                pass

        # 3. 降级方案：如果上述底层接口不支持，或者明确要求 simulate=True
        # 使用物理模拟点击。
        # 注意：uiautomation 的 Click 默认就是移动鼠标。
        # 如果不想移动鼠标但还要发物理点击，基本不可能，除非用 PostMessage。
        cx, cy = self.center
        if simulate:
            self.node.Click()  # 这里的 Click 会移动鼠标
        else:
            # 使用你 Window 封装的底层坐标点击逻辑
            self.window.click(cx, cy)

        return self

    def input(self, text: str, simulate: bool = False):
        """
        输入文本
        :param text: 要输入的字符串
        :param simulate:
            False: 尝试使用 ValuePattern 直接设置值 (静默且快)
            True:  使用 SendKeys 模拟键盘敲击 (适合需要触发监听事件的输入框)
        """
        if not simulate:
            try:
                # 1. 尝试 ValuePattern (最通用的设置文本方式)
                pattern = self.node.GetValuePattern()
                if pattern:
                    pattern.SetValue(text)
                    return self
            except:
                pass

        # 2. 降级方案 或 强制模拟：先点击聚焦，再发送按键
        # 注意：这里调用的是你已有的 click()
        self.click(simulate=simulate)
        self.node.SendKeys(text)
        return self

    def capture(self, save_path: str = None) -> Image:
        """
        捕获当前元素的截图
        :param save_path: 如果提供，则保存到该路径
        :return: Pillow Image 对象
        """
        # uiautomation 的 CaptureToImage 返回的是 Pillow 的 Image 对象
        img = self.node.CaptureToImage()

        if save_path:
            img.save(save_path)

        return img

    def __repr__(self):
        return f"<UIElement: [{self.type}] res_id: {self.res_id} memory_id: {self.memory_id}>"



import uiautomation as auto
import re
import os
import sys
from typing import List, Optional, Any, Dict, Union

import re
import json
from typing import Any, List, Dict, Optional, Union
import uiautomation as auto


# 假设你的 UIElement 类定义如下（根据你提供的代码推断）
# class UIElement:
#     def __init__(self, node, window, depth):
#         self.node = node
#         self.window = window
#         self.depth = depth
#         self.children = []
#     ...

class Selector:
    def __init__(self, window: Any = None, title: str = None, depth: int = 0xFFFFFFFF):
        """
        :param window: 已经存在的 Window 对象实例
        :param title: 如果 window 为 None，则通过 title 查找并初始化 Window
        :param depth: 搜索深度
        """
        self.window = window

        if self.window is None and title:
            try:
                # 尝试通过 Window 类查找，这里保留你的逻辑
                # from your_module import Window
                self.window = Window.find(title)
            except:
                pass

        self._steps: List[Dict] = []
        self._current_filters: Dict[str, Any] = {}
        self._max_depth = depth

        self._attr_map = {
            'name': 'Name',
            'type': 'ControlTypeName',
            'class_name': 'ClassName',
            'handle': 'NativeWindowHandle',
            'res_id': 'AutomationId',
            'description': 'HelpText',
            'is_enabled': 'IsEnabled',
            'is_password': 'IsPassword'
        }

    def _add_filter(self, key: str, value: Any):
        if self._steps and self._steps[-1]['method'] in ['child', 'parent', 'brother']:
            self._steps[-1]['filters'][key] = value
        else:
            self._current_filters[key] = value

    def _flush_to_step(self):
        if self._current_filters or self._max_depth != 0xFFFFFFFF:
            self._steps.append({
                'method': 'find',
                'param': None,
                'filters': self._current_filters.copy(),
                'max_depth': self._max_depth
            })
            self._current_filters = {}
            self._max_depth = 0xFFFFFFFF

    def _add_relation(self, method: str, param: Any):
        self._flush_to_step()
        self._steps.append({
            'method': method,
            'param': param,
            'filters': {},
            'max_depth': 0xFFFFFFFF
        })

    # --- 属性链式调用 (保持原样) ---
    def name(self, val: str) -> 'Selector':
        self._add_filter('name', val); return self

    def type(self, val: str) -> 'Selector':
        self._add_filter('type', val); return self

    def class_name(self, val: str) -> 'Selector':
        self._add_filter('class_name', val); return self

    def res_id(self, val: str) -> 'Selector':
        self._add_filter('res_id', val); return self

    def value(self, val: str) -> 'Selector':
        self._add_filter('value', val); return self

    def description(self, val: str) -> 'Selector':
        self._add_filter('description', val); return self

    def handle(self, val: int) -> 'Selector':
        self._add_filter('handle', val); return self

    def enabled(self, val: bool = True) -> 'Selector':
        self._add_filter('is_enabled', val); return self

    def visible(self, val: bool = True) -> 'Selector':
        self._add_filter('is_visible', val); return self

    def clickable(self, val: bool = True) -> 'Selector':
        self._add_filter('is_clickable', val); return self

    def password(self, val: bool = True) -> 'Selector':
        self._add_filter('is_password', val); return self

    def child_count(self, count: int) -> 'Selector':
        self._add_filter('child_count', count); return self

    # --- 关系链式调用 ---
    def depth(self, d: int) -> 'Selector':
        self._max_depth = d; return self

    def child(self, index: Any = None) -> 'Selector':
        self._add_relation('child', index); return self

    def parent(self, index: Any = None) -> 'Selector':
        self._add_relation('parent', index); return self

    def brother(self, index: Any = None) -> 'Selector':
        self._add_relation('brother', index); return self

    # --- 动作插值 (保持原样) ---
    def click(self, simulate: bool = False) -> 'Selector':
        self._flush_to_step()
        self._steps.append({'method': 'action', 'action_type': 'click', 'param': simulate, 'filters': {}})
        return self

    def input(self, msg: str) -> 'Selector':
        self._flush_to_step()
        self._steps.append({'method': 'action', 'action_type': 'input', 'param': msg, 'filters': {}})
        return self

    # --- 匹配内核 (保持原样) ---
    def _match_node(self, node: auto.Control, filters: Dict) -> bool:
        if not filters: return True
        for key, target in filters.items():
            actual = None
            if key == 'value':
                try:
                    p = node.GetValuePattern()
                    v = p.Value if p else ""
                    actual = v if (v and v != node.Name) else (
                        "" if node.ControlTypeName != "EditControl" else node.Name)
                except:
                    actual = ""
            elif key == 'is_clickable':
                try:
                    actual = any([hasattr(node, f'Get{p}Pattern') and getattr(node, f'Get{p}Pattern')()
                                  for p in ['Invoke', 'Toggle', 'SelectionItem']])
                except:
                    actual = False
            elif key == 'child_count':
                try:
                    actual = len(node.GetChildren())
                except:
                    actual = 0
            elif key == 'is_visible':
                try:
                    actual = not node.IsOffscreen
                except:
                    actual = False
            else:
                native_key = self._attr_map.get(key, key)
                actual = getattr(node, native_key, None)

            if isinstance(target, bool):
                if bool(actual) != target: return False
            elif isinstance(target, int):
                if actual != target: return False
            else:
                try:
                    if not re.search(str(target), str(actual or ""), re.IGNORECASE): return False
                except:
                    if str(target).lower() not in str(actual or "").lower(): return False
        return True

    # --- 执行引擎 (修改了 parent 部分) ---
    def find_all(self) -> List[Any]:
        self._flush_to_step()

        if self.window and hasattr(self.window, 'hwnd') and self.window.hwnd:
            root = auto.ControlFromHandle(self.window.hwnd)
            try:
                root.GetRuntimeId()
            except:
                pass
            current_pool = [(root, 0)]
        else:
            current_pool = [(auto.GetRootControl(), 0)]

        for step in self._steps:
            next_pool = []
            method, param, filters = step['method'], step['param'], step['filters']

            if method == 'action':
                action_type = step.get('action_type')
                for node, d in current_pool:
                    try:
                        temp_el = UIElement(node, self.window, d)
                        if action_type == 'click':
                            temp_el.click(simulate=param)
                        elif action_type == 'input':
                            val_pat = node.GetValuePattern()
                            if val_pat:
                                val_pat.SetValue(param)
                            else:
                                node.SendKeys(param)
                    except Exception as e:
                        print(f"执行插值动作 {action_type} 失败: {e}")
                continue

            max_d = step.get('max_depth', 0xFFFFFFFF)

            for node, d in current_pool:
                if method == 'find':
                    for c, rel_d in auto.WalkControl(node, maxDepth=max_d):
                        if rel_d == 0: continue
                        if self._match_node(c, filters):
                            next_pool.append((c, d + rel_d))
                else:
                    # --- 轴跳转逻辑 ---
                    if method == 'child':
                        candidates = node.GetChildren()
                        new_d = d + 1
                        if isinstance(param, float):
                            picked = self._pick_by_float(candidates, node, param)
                            next_pool.extend([(p, new_d) for p in picked if self._match_node(p, filters)])
                        else:
                            matched = [c for c in candidates if self._match_node(c, filters)]
                            picked = self._pick_by_int(matched, param)
                            next_pool.extend([(p, new_d) for p in picked])

                    elif method == 'parent':
                        # 修改后的 parent 逻辑：支持向上跳 n 层
                        # param 为调用 .parent(n) 时传入的值
                        up_level = param if (isinstance(param, int) and param > 0) else 1
                        curr_p = node
                        for _ in range(up_level):
                            curr_p = curr_p.GetParentControl()
                            if not curr_p: break

                        # 跳转完成后进行属性匹配，并计算新的深度
                        if curr_p and self._match_node(curr_p, filters):
                            next_pool.append((curr_p, max(0, d - up_level)))

                    elif method == 'brother':
                        p = node.GetParentControl()
                        candidates = p.GetChildren() if p else []
                        new_d = d
                        if isinstance(param, float):
                            picked = self._pick_by_float(candidates, node, param)
                            next_pool.extend([(p, new_d) for p in picked if self._match_node(p, filters)])
                        else:
                            matched = [c for c in candidates if self._match_node(c, filters)]
                            picked = self._pick_by_int(matched, param)
                            next_pool.extend([(p, new_d) for p in picked])

            current_pool = next_pool
            if not current_pool: break

        final_list = []
        seen_ids = set()
        for node, depth in current_pool:
            try:
                rid = tuple(node.GetRuntimeId())
                if rid in seen_ids: continue
                seen_ids.add(rid)
            except:
                pass
            final_list.append(UIElement(node, self.window, depth))

        return final_list

    def _pick_by_float(self, candidates, current, param) -> List[auto.Control]:
        try:
            curr_idx = -1
            for i, c in enumerate(candidates):
                if auto.CompareControl(c, current):
                    curr_idx = i;
                    break
            if curr_idx == -1: return []
            target_idx = curr_idx + int(round(param * 10))
            return [candidates[target_idx]] if 0 <= target_idx < len(candidates) else []
        except:
            return []

    def _pick_by_int(self, matched, param) -> List[auto.Control]:
        if param is None: return matched
        try:
            idx = int(param)
            if idx > 0: return [matched[idx - 1]] if idx <= len(matched) else []
            if idx < 0: return [matched[idx]] if abs(idx) <= len(matched) else []
        except:
            pass
        return []

    def find(self) -> Optional[Any]:
        res = self.find_all()
        return res[0] if res else None

    def get_uielement_tree(self, as_json: bool = False) -> Union[Any, str]:
        if not self.window.hwnd: return "" if as_json else None
        root = auto.ControlFromHandle(self.window.hwnd)
        if not root.Exists(0): return "" if as_json else None

        root_element = UIElement(root, self.window, 0)
        stack = {0: root_element}
        try:
            for control, depth in auto.WalkControl(root, maxDepth=self._max_depth):
                if depth == 0: continue
                new_el = UIElement(control, self.window, depth)
                parent = stack.get(depth - 1)
                if parent: parent.children.append(new_el)
                stack[depth] = new_el
        except Exception as e:
            print(f"构建 UI 树失败: {e}")

        if as_json: return json.dumps(root_element.to_dict(), ensure_ascii=False, indent=2)
        return root_element