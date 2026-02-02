
from .web_window import  WebWindow
from .. import  license
from ..system import KeyValue,R


class LicenseWindow(WebWindow):
    def __init__(self, app_id: str):
        self.app_id = app_id
        self.license_data = None
        self.app_info = None
        # 默认返回 False，确保任何非正常退出都视为失败
        self._return_value = False

        _root =  R.internal("windows","tools","web") #paths.get_path("ascript/windows/tools/web/")
        _filepath = R.internal("windows","tools","web","license_window.html") #paths.get_path("ascript/windows/tools/web/license_window.html")
        print(_filepath)
        super().__init__(_filepath, project_root=_root)

        self.expose(self.get_app_info)
        self.expose(self.get_cached_key)
        self.expose(self.activate_key)
        self.expose(self.start_app)

    def get_app_info(self):
        res = license.achttp.get_apps(self.app_id)
        if res and len(res) > 0:
            self.app_info = res[0]
            return self.app_info
        return {'name': '没有找到该程序'}

    def activate_key(self, key: str):
        # 这里的 res 结构需包含 {code: 1, data: {status: 1...}}
        res = license.achttp.get_card(self.app_id, key)
        if res and res.get('code') == 1:
            self.license_data = res.get('data')
            KeyValue.save("license_cache_no", key)
        else:
            self.license_data = None  # 验证失败必须清空旧数据
        return res

    def start_app(self):
        """最终的逻辑守门员"""
        # print("Final security check before launch...")

        # 1. 验证 app_info
        if not self.app_info:
            print("Error: App info not loaded.")
            return {"error": "初始化未完成"}

        # 2. 免费版直接放行
        if self.app_info.get('is_free') == 1:
            # print("Mode: Free version. Access granted.")
            self._return_value = True
            self.close()
            return True

        # 3. 授权版严格校验
        # 核心：必须 status 存在且明确等于 1
        if self.license_data and self.license_data.get('status') == 1:
            # print("Mode: Professional. License verified.")
            self._return_value = True
            self.close()
            return True
        else:
            # 如果 status 是 2 (过期) 或其他，拦截并告知前端
            current_status = self.license_data.get('status') if self.license_data else "None"
            print(f"Access Denied: License status is {current_status}")
            self._return_value = False
            return {"error": "授权已过期或无效，请重新激活"}

    def get_cached_key(self):
        return KeyValue.get("license_cache_no", "")