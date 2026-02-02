import os
import tempfile

# 1. 定义路径
file_root_path = os.path.join(tempfile.gettempdir(), "ascript")
file_capture_dir = os.path.join(file_root_path, "capture")
file_data_temp = os.path.join(file_root_path, "temp")

# 2. 判断并创建文件夹
# 创建根目录及其子目录
# os.makedirs 会自动创建中间路径（递归创建）
os.makedirs(file_capture_dir, exist_ok=True)
os.makedirs(file_data_temp, exist_ok=True)

# print(f"路径已就绪: {file_capture_dir}")