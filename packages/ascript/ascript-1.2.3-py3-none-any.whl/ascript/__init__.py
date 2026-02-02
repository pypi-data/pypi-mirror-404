import sys

# 1. 操作系统检查
if sys.platform != "win32":
    raise ImportError(f"Package 'your_package' is Windows-only. Current: {sys.platform}")

# 2. 导出版本号（方便用户查看）
__version__ = "0.1.0"