import numpy as np
from .as_cv import AsCv


class FindColors:
    @staticmethod
    def _hex_to_bgr(hex_str):
        """
        将十六进制颜色转换为 OpenCV 使用的 BGR 格式
        """
        hex_str = hex_str.lstrip('#')
        r, g, b = tuple(int(hex_str[i:i + 2], 16) for i in (0, 2, 4))
        return (b, g, r)

    @staticmethod
    def _parse_colors(colors_str):
        """
        解析颜色字符串，例如 "x,y,color|dx,dy,color"
        返回：(基础点BGR, 偏移列表)
        """
        parts = colors_str.split('|')
        points = []
        for p in parts:
            x, y, color = p.split(',')
            points.append((int(x), int(y), FindColors._hex_to_bgr(color)))

        base_x, base_y, base_bgr = points[0]
        offsets = []
        for i in range(1, len(points)):
            curr_x, curr_y, curr_bgr = points[i]
            # 计算相对于第一个点的偏移和对应的颜色数组
            offsets.append((curr_y - base_y, curr_x - base_x, np.array(curr_bgr, dtype=np.int16)))

        return np.array(base_bgr, dtype=np.int16), offsets

    @staticmethod
    def find(colors: str, rect=None, threshold: float = 0.95, ori: int = 2, exclusion_radius: int = 5, im_source=None,
             max_res: int = 1):
        """
        查找单个目标
        """
        res = FindColors.find_all(colors, rect, threshold, ori, exclusion_radius, im_source, max_res=max_res)
        return res[0] if res else None

    @staticmethod
    def find_all(colors: str, rect=None, threshold: float = 0.95, ori: int = 2, exclusion_radius: int = 5,
                 im_source=None, max_res: int = 0):
        """
        全量查找目标。采用向量化位移过滤算法，防止主色点过多导致的性能卡死。
        """

        # 获取图像源
        if im_source is None:
            from .screen_core import Screen
            im_source = Screen.capture()

        img = AsCv.to_numpy(im_source)

        # 处理范围（ROI）
        if rect:
            l, t, r, b = rect
            img = img[t:b, l:r]
            offset_l, offset_t = l, t
        else:
            offset_l, offset_t = 0, 0

        h, w, _ = img.shape
        base_bgr, offsets = FindColors._parse_colors(colors)
        tol = int(255 * (1.0 - threshold))

        # 预转换图像类型，避免在循环中重复计算
        img_int16 = img.astype(np.int16)

        # --- 步骤 1: 生成主色掩码 ---
        diff = np.abs(img_int16 - base_bgr)
        final_mask = np.all(diff <= tol, axis=-1)

        # 如果没有匹配到主色，直接返回
        if not np.any(final_mask):
            return []

        # --- 步骤 2: 向量化位移过滤 (核心防卡死逻辑) ---
        for dy, dx, target_bgr in offsets:
            # 计算有效区域（防止偏移后越界）
            y_start, y_end = max(0, dy), min(h, h + dy)
            x_start, x_end = max(0, dx), min(w, w + dx)
            oy_start, oy_end = max(0, -dy), min(h, h - dy)
            ox_start, ox_end = max(0, -dx), min(w, w - dx)

            if oy_start >= oy_end or ox_start >= ox_end:
                continue

            # 核心：直接对整张掩码进行位移比对
            # 这一步在 NumPy 内部完成，比 Python 循环快几个量级
            shifted_pixels = img_int16[y_start:y_end, x_start:x_end]
            match_offset = np.all(np.abs(shifted_pixels - target_bgr) <= tol, axis=-1)

            # 对齐掩码并做逻辑“与”操作
            aligned_mask = np.zeros((h, w), dtype=bool)
            aligned_mask[oy_start:oy_end, ox_start:ox_end] = match_offset

            final_mask &= aligned_mask

            # 如果中间过程掩码已空，提前终止
            if not np.any(final_mask):
                return []

        # --- 步骤 3: 提取剩下的合格点 ---
        candidates = np.argwhere(final_mask)

        # 防护性熔断：即使过滤后还有海量点（如全屏纯色），限制处理上限
        if len(candidates) > 10000:
            candidates = candidates[:10000]

        # --- 步骤 4: 排序 (根据 ori 参数) ---
        if len(candidates) > 1:
            # 按照你原代码的 1-8 方向逻辑
            # lexsort 是从后往前作为优先级排序的
            order_map = {
                1: (candidates[:, 1], candidates[:, 0]),  # 从左到右, 从上到下
                2: (candidates[:, 0], candidates[:, 1]),  # 从上到下, 从左到右
                3: (candidates[:, 0], -candidates[:, 1]),  # 从上到下, 从右到左
                4: (-candidates[:, 1], candidates[:, 0]),  # 从右到左, 从上到下
                5: (-candidates[:, 1], -candidates[:, 0]),  # 从右到左, 从下到上
                6: (-candidates[:, 0], -candidates[:, 1]),  # 从下到上, 从右到左
                7: (-candidates[:, 0], candidates[:, 1]),  # 从下到上, 从左到右
                8: (candidates[:, 1], -candidates[:, 0]),  # 从左到右, 从下到上
            }
            candidates = candidates[np.lexsort(order_map.get(ori, order_map[2]))]

        # --- 步骤 5: 结果构建与排除半径处理 ---
        results = []
        if exclusion_radius > 0:
            excluded = np.zeros((h, w), dtype=bool)
            for y, x in candidates:
                if excluded[y, x]:
                    continue
                results.append((int(x + offset_l), int(y + offset_t)))
                if max_res > 0 and len(results) >= max_res:
                    break
                # 标记半径内的点为已排除
                y1, y2 = max(0, y - exclusion_radius), min(h, y + exclusion_radius + 1)
                x1, x2 = max(0, x - exclusion_radius), min(w, x + exclusion_radius + 1)
                excluded[y1:y2, x1:x2] = True
        else:
            for y, x in candidates:
                results.append((int(x + offset_l), int(y + offset_t)))
                if max_res > 0 and len(results) >= max_res:
                    break

        return results