import cv2
import numpy as np
import os
from PIL import Image
from dataclasses import dataclass, asdict
from typing import Tuple, List, Optional


@dataclass
class MatchResult:
    """ 找图结果对象封装 """
    center: Tuple[int, int]  # 中心点坐标 (x, y)
    rectangle: List[Tuple[int, int]]  # 原始角坐标 (多边形，四个顶点)
    rect: List[int]  # 增加：[left, top, right, bottom] 格式，方便 UI 绘图
    confidence: float  # 置信度 (0.0~1.0)
    method: str  # 识别方法
    scale: float = 1.0  # 匹配时的缩放比例

    @property
    def x(self) -> int:
        return self.center[0]

    @property
    def y(self) -> int:
        return self.center[1]

    def to_dict(self):
        """ 转换为 JSON 兼容的字典，增加 x, y 方便 JS 直接调用 """
        d = asdict(self)
        d.update({
            "x": self.x,
            "y": self.y
        })
        return d

    def __getitem__(self, key):
        if key == 'result': return self.center
        if key == 'rectangle': return self.rectangle
        if key == 'rect': return self.rect
        if key == 'confidence': return self.confidence
        return getattr(self, key)

    def __str__(self):
        return f"<MatchResult '{self.method}' conf={self.confidence} center={self.center}>"


class AsCv:
    @staticmethod
    def to_numpy(im):
        """ 统一图像格式为 NumPy (OpenCV BGR 格式) """
        if im is None:
            return None

        # 1. 处理文件路径 (支持中文)
        if isinstance(im, str):
            im_data = np.fromfile(im, dtype=np.uint8)
            im = cv2.imdecode(im_data, cv2.IMREAD_COLOR)
            if im is None:
                raise FileNotFoundError(f"图像解析失败，请检查路径或格式: {im}")
            return im

        # 2. 处理 PIL Image 对象
        if isinstance(im, Image.Image):
            # PIL 是 RGB，OpenCV 是 BGR
            # 使用 np.ascontiguousarray 确保内存连续，提升后续 mask 运算速度
            return cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR)

        # 3. 如果已经是 NumPy 数组，直接返回 (确保是 uint8)
        if isinstance(im, np.ndarray):
            return im

        return np.array(im, dtype=np.uint8)

    @classmethod
    def find_all_template(cls, im_source, im_search, threshold=0.8, maxcnt=0, rgb=False) -> List[MatchResult]:
        """ 基础模板匹配 """
        im_source, im_search = cls.to_numpy(im_source), cls.to_numpy(im_search)
        w, h = im_search.shape[1], im_search.shape[0]
        method = cv2.TM_CCOEFF_NORMED

        if rgb:
            s_bgr, i_bgr = cv2.split(im_search), cv2.split(im_source)
            res = (cv2.matchTemplate(i_bgr[0], s_bgr[0], method) * 0.3 +
                   cv2.matchTemplate(i_bgr[1], s_bgr[1], method) * 0.3 +
                   cv2.matchTemplate(i_bgr[2], s_bgr[2], method) * 0.4)
        else:
            res = cv2.matchTemplate(cv2.cvtColor(im_source, cv2.COLOR_BGR2GRAY),
                                    cv2.cvtColor(im_search, cv2.COLOR_BGR2GRAY), method)

        results = []

        # 封装结果辅助函数
        def wrap(val, loc, mth):
            l, t = int(loc[0]), int(loc[1])
            r, b = l + w, t + h
            return MatchResult(
                center=(l + w // 2, t + h // 2),
                rectangle=[(l, t), (l, b), (r, b), (r, t)],
                rect=[l, t, r, b],  # 注入 LTRB
                confidence=round(float(val), 3),
                method=mth
            )

        if maxcnt == 1:
            _, max_val, _, max_loc = cv2.minMaxLoc(res)
            return [wrap(max_val, max_loc, "template_fast")] if max_val >= threshold else []

        while True:
            _, max_val, _, max_loc = cv2.minMaxLoc(res)
            if max_val < threshold:
                break

            results.append(wrap(max_val, max_loc, "template_multi"))
            if 0 < maxcnt <= len(results):
                break

            # --- 修改部分：手动覆盖屏蔽区域 ---
            # 计算屏蔽半径，通常取模板宽高的 1/4 或 1/2
            # 这样可以确保同一个目标不会被重复计算
            margin_w, margin_h = w // 2, h // 2

            # 计算在 res 矩阵中的屏蔽范围（注意边界检查）
            t = max(0, max_loc[1] - margin_h)
            b = min(res.shape[0], max_loc[1] + margin_h)
            l = max(0, max_loc[0] - margin_w)
            r = min(res.shape[1], max_loc[0] + margin_w)

            # 将该区域全部置为 -1.0 (最小匹配度)
            res[t:b, l:r] = -1.0

        return results

    @classmethod
    def find_all_multi_scale(cls, im_source, im_search, threshold=0.8, maxcnt=0, scale_range=(0.5, 1.5),
                             steps=10) -> List[MatchResult]:
        """ 多尺度模板匹配 """
        im_source, im_search = cls.to_numpy(im_source), cls.to_numpy(im_search)
        all_candidates = []

        for scale in np.linspace(scale_range[0], scale_range[1], steps):
            tw, th = int(im_search.shape[1] * scale), int(im_search.shape[0] * scale)
            if tw > im_source.shape[1] or th > im_source.shape[0] or tw < 10 or th < 10: continue

            resized_sch = cv2.resize(im_search, (tw, th), interpolation=cv2.INTER_AREA)
            step_res = cls.find_all_template(im_source, resized_sch, threshold=threshold, maxcnt=maxcnt)
            for r in step_res:
                r.scale = round(scale, 2)
                r.method = "multi_scale"
                all_candidates.append(r)

        if not all_candidates: return []
        # 按置信度排序
        all_candidates.sort(key=lambda x: x.confidence, reverse=True)

        # 非极大值抑制 (简易版)：过滤重叠过近的结果
        final = []
        for cand in all_candidates:
            if not any(np.linalg.norm(np.array(cand.center) - np.array(f.center)) < (min(im_search.shape[:2]) * 0.3)
                       for f in final):
                final.append(cand)
                if 0 < maxcnt <= len(final): break
        return final

    @classmethod
    def find_akaze(cls, im_source, im_search, threshold=0.5, min_match=10) -> List[MatchResult]:
        """ 特征匹配 (AKAZE) """
        im_source, im_search = cls.to_numpy(im_source), cls.to_numpy(im_search)
        akaze = cv2.AKAZE_create()
        kp_sch, des_sch = akaze.detectAndCompute(im_search, None)
        kp_src, des_src = akaze.detectAndCompute(im_source, None)

        if des_sch is None or des_src is None or len(kp_sch) < min_match: return []

        matches = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True).match(des_sch, des_src)
        if len(matches) < min_match: return []

        src_pts = np.float32([kp_sch[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp_src[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)
        M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

        if M is not None:
            conf = mask.sum() / len(matches)
            if conf >= threshold:
                h, w = im_search.shape[:2]
                pts = np.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(-1, 1, 2)
                dst = cv2.perspectiveTransform(pts, M)

                # 1. 原始多边形坐标
                poly_pts = [tuple(npt[0].astype(int)) for npt in dst]

                # 2. 计算外接矩形 LTRB (rect)
                all_pts = dst.reshape(-1, 2)
                l, t = int(all_pts[:, 0].min()), int(all_pts[:, 1].min())
                r, b = int(all_pts[:, 0].max()), int(all_pts[:, 1].max())

                rect_ltrb = [l, t, r, b]
                center = ((l + r) // 2, (t + b) // 2)

                return [MatchResult(center, poly_pts, rect_ltrb, round(float(conf), 3), "akaze")]
        return []

    @classmethod
    def find(cls, im_source, im_search, threshold=0.8, maxcnt=1, use_scale=True) -> List[MatchResult]:
        """ 综合查找入口 """
        res = cls.find_all_template(im_source, im_search, threshold=threshold, maxcnt=maxcnt)

        # 如果模板匹配没找够，尝试多尺度
        if (len(res) < maxcnt or maxcnt == 0) and use_scale:
            needed = maxcnt - len(res) if maxcnt > 0 else 0
            res.extend(cls.find_all_multi_scale(im_source, im_search, threshold=threshold, maxcnt=needed))

        # 如果还是没找到，尝试特征匹配
        if not res:
            res = cls.find_akaze(im_source, im_search)

        return res[:maxcnt] if maxcnt > 0 else res