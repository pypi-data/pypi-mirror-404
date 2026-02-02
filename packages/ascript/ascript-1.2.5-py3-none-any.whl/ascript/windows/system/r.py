import sys
import os
from pathlib import Path
import ascript  # 必须导入你的包以定位其物理位置

class R:
    _BASE_DIR = None
    # 静态定位 ascript 包的物理根目录 (site-packages/ascript)
    _PKG_ROOT = Path(os.path.dirname(os.path.abspath(ascript.__file__))).resolve()

    @classmethod
    def get_root(cls) -> Path:
        """获取【开发者工程】或【解压临时目录】的根目录"""
        if cls._BASE_DIR is not None:
            return cls._BASE_DIR

        if getattr(sys, 'frozen', False):
            # Nuitka 优先环境变量
            nuitka_tmp = os.environ.get('NUITKA_ONEFILE_PARENT')
            if nuitka_tmp:
                cls._BASE_DIR = Path(nuitka_tmp).resolve()
            elif hasattr(sys, '_MEIPASS'):
                cls._BASE_DIR = Path(sys._MEIPASS).resolve()
            else:
                cls._BASE_DIR = Path(sys.executable).resolve().parent
        else:
            # 开发环境：锚定 main.py 所在目录
            main_file = sys.argv[0]
            if main_file:
                cls._BASE_DIR = Path(main_file).resolve().parent
            else:
                cls._BASE_DIR = Path.cwd().resolve()
        return cls._BASE_DIR

    @classmethod
    def _build_path(cls, base: Path, *sub_paths) -> str:
        """通用路径构建，增加 base 参数以区分锚点"""
        full_path = base.joinpath(*sub_paths)
        if not full_path.exists():
            # 这里的警告非常有意义，能帮开发者快速定位是缺文件还是路走错了
            print(f"⚠️ [R] 找不到路径: {full_path}")
            print(f"ℹ️ [R] 当前基准目录为: {base}")
        return str(full_path)

    # --- 1. 开发者使用的接口 (锚定工程根目录/res) ---

    @classmethod
    def ui(cls, path: str) -> str:
        """开发者调用：获取工程 res/ui/ 下的文件"""
        return cls._build_path(cls.get_root(), "res", "ui", path)

    @classmethod
    def img(cls, path: str) -> str:
        """开发者调用：获取工程 res/img/ 下的文件"""
        return cls._build_path(cls.get_root(), "res", "img", path)

    @classmethod
    def res(cls, path: str) -> str:
        """开发者调用：获取工程 res/ 下的通用文件"""
        return cls._build_path(cls.get_root(), "res", path)

    # --- 2. ascript 内部使用的接口 (双重查找逻辑) ---

    @classmethod
    def internal(cls, *sub_paths) -> str:
        """
        ascript 包内部资源专用查找。
        逻辑：如果是打包环境，先去临时目录找；如果没找到或在开发环境，去包安装目录找。
        """
        # A. 打包环境下的尝试 (寻找临时目录/ascript/xxx)
        if getattr(sys, 'frozen', False):
            # 注意：这里 sub_paths 前面通常要带上 "ascript"
            # 因为 Nuitka 会把整个包结构解压出来
            bundle_path = cls.get_root().joinpath("ascript", *sub_paths)
            if bundle_path.exists():
                return str(bundle_path)

        # B. 开发环境或兜底 (寻找 site-packages/ascript/xxx)
        return cls._build_path(cls._PKG_ROOT, *sub_paths)