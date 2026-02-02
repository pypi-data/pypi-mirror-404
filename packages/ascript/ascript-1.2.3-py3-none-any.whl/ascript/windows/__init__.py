import os
import sys

# 获取当前 windows 目录的路径
_current_dir = os.path.dirname(os.path.abspath(__file__))

# 关键：将 windows 目录加入搜索路径
# 这样其下的子模块 license 就能直接 import 旁边的 pyarmor_runtime_000000
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)