import json
import time
import os
from .web_window import WebWindow
from .. import license
from ..system import KeyValue, R, EnvManager


class AppStoreWindow(WebWindow):
    def __init__(self, default_id: str = None, on_start=None,env_path:str=None):  # 增加默认 ID 参数
        self.default_id = default_id
        self.on_start = on_start  # 存储回调
        self.app_info = None
        self.license_data = None
        self.target_path = None
        self.env_manager = EnvManager(root_path=env_path)

        _root = R.internal("windows", "tools", "web")
        _filepath = R.internal("windows", "tools", "web", "app_store_window.html")

        super().__init__(_filepath, project_root=_root)

        self.expose(self.get_app_info)
        self.expose(self.activate_key)
        self.expose(self.start_app)
        self.expose(self.get_history)
        self.expose(self.get_cached_key)
        # 暴露一个获取初始 ID 的方法
        self.expose(self.get_init_config)
        self.expose(self.check_status)
        self.expose(self.stop_app)
        self.expose(self.clear_env)
        self.expose(self.download_app)

    def get_init_config(self):
        return {"default_id": self.default_id}

    def get_app_info(self, app_id):
        """搜索应用信息"""
        app_id = str(app_id).strip()  # 强制转字符串，解决类型报错
        res = license.achttp.get_apps(app_id)
        if res and len(res) > 0:
            self.app_info = res[0]
            return {"code": 1, "data": self.app_info}
        return {"code": 0, "msg": f"未能找到 ID 为 '{app_id}' 的应用，请检查输入是否正确。"}

    def get_cached_key(self, app_id):
        """按 ID 获取缓存的激活码"""
        return KeyValue.get(f"lic_cache_{str(app_id)}", "")

    def activate_key(self, app_id, key: str):
        """激活逻辑"""
        app_id = str(app_id)
        res = license.achttp.get_card(app_id, key)
        if res and res.get('code') == 1:
            self.license_data = res.get('data')
            # 区分 ID 存储
            KeyValue.save(f"lic_cache_{app_id}", key)
        else:
            self.license_data = None
        return res

    def get_history(self):
        """获取运行记录列表"""
        try:
            history_str = KeyValue.get("app_run_history", "[]")
            return json.loads(history_str)
        except:
            return []

    # 在 AppStoreWindow 类中新增/修改以下方法
    def download_app(self, app_info):
        """前端点击运行后，首先调用的下载逻辑"""
        url = app_info['filePath']
        file_md5 = app_info['fileMd5']
        user_id = str(app_info["id"])

        # 从 URL 中提取原始文件名（例如: myapp-1.0.whl）
        # 如果 URL 后面带参数，可以用 url.split('?')[0]
        remote_filename = os.path.basename(url.split('?')[0])
        # if not remote_filename.endswith('.whl'):
        #     remote_filename = f"{file_md5}.whl"

        # 1. 获取目标文件夹路径：module/user_id/file_md5/
        # 这里的 get_module_storage_path 会返回完整的：.../module/1085/md5_string/xxx.whl
        self.target_path = os.path.join(self.env_manager.get_model_dir(user_id), file_md5, remote_filename)

        # 确保文件夹存在（即 module/user_id/file_md5/ 这一层）
        storage_dir = os.path.dirname(self.target_path)
        if not os.path.exists(storage_dir):
            os.makedirs(storage_dir, exist_ok=True)

        # 2. 如果文件已存在，直接返回
        if os.path.exists(self.target_path):
            return {"code": 1, "msg": "已存在", "path": self.target_path}

        # 3. 开始执行下载
        try:
            import requests
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, stream=True, timeout=30, headers=headers)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(self.target_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024 * 64):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = int(downloaded * 100 / total_size)
                            # 确保 webview_instance 存在
                            if hasattr(self, 'webview_instance'):
                                self.webview_instance.evaluate_js(f"updateDownloadProgress({percent})")

            return {"code": 1, "msg": "下载完成", "path": self.target_path}
        except Exception as e:
            if os.path.exists(self.target_path):
                try:
                    os.remove(self.target_path)
                except:
                    pass
            return {"code": 0, "msg": f"下载失败: {str(e)}"}

    def start_app(self, app_info: dict):
        """点击启动按钮"""
        # 1. 保存/更新运行记录
        history = self.get_history()
        new_item = {"id": str(app_info['id']), "name": app_info['name']}

        # 去重：如果已存在则先删除旧记录
        history = [i for i in history if str(i.get('id')) != new_item['id']]
        # 插入到开头
        history.insert(0, new_item)
        # 限制数量为 10 条
        KeyValue.save("app_run_history", json.dumps(history[:10]))

        # 2. 执行回调逻辑
        if self.on_start:
            # 将 app_info 和当前激活的 license_data 一并传出
            # 这样外部调用者就能拿到所有必要信息去启动引擎
            self.on_start(app_info, self.license_data)

        # 2. 这里的逻辑可以根据您的业务决定是否关闭窗口
        self._return_value = True
        # self.close() # 如果需要启动后关闭商城窗口，请取消注释
        return {"code": 1, "msg": "启动成功"}

    def check_status(self, app_id):
        """前端轮询：检查程序是否在运行"""
        # 调用之前我们完善的 EnvManager.is_running
        # 假设实例名为 self.env_manager
        is_run = self.env_manager.is_running(str(app_id))
        return {"running": is_run}

    def stop_app(self, app_id):
        """前端点击：强行停止程序"""
        self.env_manager.stop_app(str(app_id))
        return {"code": 1, "msg": "已发送停止指令"}

    def clear_env(self, app_id):
        """前端点击：清理虚拟环境"""
        # 只有在未运行的情况下才允许清理
        if self.env_manager.is_running(str(app_id)):
            return {"code": 0, "msg": "程序运行中，无法清理环境"}

        env_dir = self.env_manager.get_env_dir(str(app_id))
        import shutil
        try:
            shutil.rmtree(env_dir, ignore_errors=True)
            return {"code": 1, "msg": "环境已重置"}
        except Exception as e:
            return {"code": 0, "msg": str(e)}