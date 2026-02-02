import sys

from ascript.windows.ui.app_store_window import AppStoreWindow
import os
import sys
import json


def get_app_id_from_env():
    """
    从 python_env/config.json 中读取 app_id
    确保：文件缺失、格式错误、字段缺失、字段为空字符串均返回 None
    """
    try:
        # 1. 定位路径
        env_dir = os.path.dirname(os.path.abspath(sys.executable))
        config_path = os.path.join(env_dir, "config.json")

        if not os.path.exists(config_path):
            return None

        # 2. 读取 JSON
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 3. 核心逻辑修改：提取值并去除首尾空格
        # .get() 确保 key 不存在时不报错；strip() 处理 "  " 这种情况
        val = data.get("app_id")

        if isinstance(val, str):
            val = val.strip()

        # 只有当 val 不是空值（None, "", " ", [], {} 等）时才返回它
        return val if val else None

    except Exception:
        return None

def main():
    launcher_dir = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
    root_path = os.path.join(launcher_dir, "apps")
    def on_start(app_info, license_data):
        print(app_info)
        print(license_data)
        package_name = "AScriptProject2"

        user_id = str(app_info["id"])
        file_md5 = app_info['fileMd5']

        is_ready = app_store.env_manager.smart_deploy(user_id, app_store.target_path, file_md5)
        if is_ready:
            app_store.env_manager.run_app(user_id, package_name)

    app_store = AppStoreWindow(default_id=get_app_id_from_env(),on_start=on_start, env_path=root_path)
    app_store.show()