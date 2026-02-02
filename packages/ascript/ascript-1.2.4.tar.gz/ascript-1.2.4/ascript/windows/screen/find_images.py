
from .screen_core import Screen
from .as_cv import AsCv
from ..window import Window

class FindImages:

    @staticmethod
    def _get_source_image(im_source):
        """ 处理 im_source 的多种来源，转换为 NumPy """
        # 1. 如果为空，全屏截图
        if im_source is None:
            return AsCv.to_numpy(Screen.capture())

        # 2. 如果是 Window 对象 (包含 hwnd)
        if hasattr(im_source, 'hwnd'):
            img = im_source.capture()
            if img is not None: return img
            return AsCv.to_numpy(img)

        # 3. 如果是 int (视为句柄)
        if isinstance(im_source, int):
            img = Window(hwnd=im_source).capture()
            if img is not None: return img
            return AsCv.to_numpy(img)

        # 4. 其余情况（路径、PIL、NumPy）交给 AirCV 处理
        return AsCv.to_numpy(im_source)

    @staticmethod
    def find_all_template(im_search, im_source=None, threshold=0.8, max_res=0, rgb=False):
        """
        统一找图入口
        :param im_search: 模板图 (路径/PIL/NumPy)
        :param im_source: 来源 (路径/PIL/NumPy/Window对象/HWND句柄/None)
        :param threshold: 阈值
        :param max_res: 最大结果数
        :param rgb: 是否开启色彩权重匹配
        """
        # 自动转换背景源
        source_img = FindImages._get_source_image(im_source)
        # 自动转换搜索图
        search_img = AsCv.to_numpy(im_search)

        # 调用 AirCV 的逻辑
        return AsCv.find_all_template(
            im_source=source_img,
            im_search=search_img,
            threshold=threshold,
            maxcnt=max_res,
            rgb=rgb
        )

    @staticmethod
    def find_template(self):
        pass

    @staticmethod
    def find_akaze(im_search,im_source = None, threshold=0.5, min_match=10):
        # 自动转换背景源
        source_img = FindImages._get_source_image(im_source)
        # 自动转换搜索图
        search_img = AsCv.to_numpy(im_search)

        # 调用 AirCV 的逻辑
        return AsCv.find_akaze(
            im_source=source_img,
            im_search=search_img,
            threshold=threshold,
            min_match=min_match
        )
