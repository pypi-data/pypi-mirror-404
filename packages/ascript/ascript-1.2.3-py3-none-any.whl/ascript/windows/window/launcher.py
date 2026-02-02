import os
import pathlib
import re
import subprocess
import winreg
from typing import Optional, Tuple
import win32com.client


class Launcher:
    @staticmethod
    def get_info(name: Optional[str] = None, path: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
        """获取物理路径和进程名"""
        if path and os.path.exists(path):
            return str(path), os.path.basename(path)

        if name:
            # 1. 尝试从注册表获取 (App Paths & Uninstall)
            reg_path, proc_name = Launcher._get_path_from_registry(name)
            if reg_path:
                return reg_path, proc_name

            # 2. 尝试搜索并解析快捷方式
            lnk_path = Launcher._find_shortcut(name)
            if lnk_path:
                real_path = Launcher._resolve_lnk(lnk_path)
                if real_path:
                    return real_path, os.path.basename(real_path)

        return None, (f"{name}.exe" if name and ".exe" not in name.lower() else name)

    @staticmethod
    def run(name: Optional[str] = None, path: Optional[str] = None) -> bool:
        """
        全兼容启动：支持物理路径、系统应用、以及 Shell 协议
        """
        final_path, _ = Launcher.get_info(name, path)

        # 场景 1：有明确的物理路径（你自己安装的软件）
        if final_path and os.path.exists(final_path):
            try:
                # 这种方式最接近鼠标双击，能处理系统重定向和 UAC 权限
                os.startfile(final_path)
                return True
            except Exception as e:
                # 备选：强制使用 shell 执行
                subprocess.Popen(f'start "" "{final_path}"', shell=True)
                return True

        # 场景 2：系统应用保底（比如：电脑管家、计算器、记事本）
        # 如果通过路径找不到，我们直接尝试通过 Windows Shell 搜索启动
        if name:
            try:
                # 尝试通过 Windows 命令行 start 指令启动
                # 这种方式会自动处理环境变量中的程序（如 notepad, calc, cmd）
                # 也能尝试唤起已经注册在 Shell 里的名字
                subprocess.Popen(f'start {name}', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True
            except:
                pass

        return False

    @staticmethod
    def _get_path_from_registry(name_regex: str) -> Tuple[Optional[str], Optional[str]]:
        """
        深度扫描注册表：App Paths + Uninstall (32位与64位全覆盖)
        """
        reg_keys = [
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths",
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths",
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
        ]
        regex = re.compile(name_regex, re.IGNORECASE)

        # 遍历 HKLM 和 HKCU
        for root_key in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
            for key_path in reg_keys:
                try:
                    with winreg.OpenKey(root_key, key_path) as key:
                        for i in range(winreg.QueryInfoKey(key)[0]):
                            try:
                                sub_key_name = winreg.EnumKey(key, i)
                                # 1. 先匹配键名（例如：QQPCMgr）
                                # 2. 如果键名没匹配上，进去看 DisplayName（例如：腾讯电脑管家）
                                match_found = False
                                if regex.search(sub_key_name):
                                    match_found = True

                                with winreg.OpenKey(key, sub_key_name) as sub_key:
                                    display_name = ""
                                    try:
                                        display_name, _ = winreg.QueryValueEx(sub_key, "DisplayName")
                                    except:
                                        pass

                                    if not match_found and display_name and regex.search(display_name):
                                        match_found = True

                                    if match_found:
                                        # 提取路径的优先级：Default > DisplayIcon > InstallLocation
                                        path = ""
                                        for val_name in ["", "DisplayIcon", "InstallLocation", "UninstallString"]:
                                            try:
                                                path, _ = winreg.QueryValueEx(sub_key, val_name)
                                                if path: break
                                            except:
                                                continue

                                        if path:
                                            # 清理路径：去掉引号，去掉末尾的参数（如 ,0 或 /uninstall）
                                            clean_path = path.split(',')[0].split(' /')[0].strip('"')
                                            # 如果是目录，尝试补全 exe (针对只有 InstallLocation 的情况)
                                            if os.path.isdir(clean_path):
                                                # 尝试在目录下找包含关键字的 exe
                                                for f in os.listdir(clean_path):
                                                    if f.lower().endswith(".exe") and regex.search(f):
                                                        full_exe = os.path.join(clean_path, f)
                                                        return full_exe, f

                                            if os.path.exists(clean_path) and clean_path.lower().endswith(".exe"):
                                                return clean_path, os.path.basename(clean_path)
                            except:
                                continue
                except:
                    continue
        return None, None

    @staticmethod
    def _find_shortcut(name_regex: str) -> Optional[pathlib.Path]:
        """全域扫描快捷方式"""
        search_paths = [
            pathlib.Path(os.environ.get("ProgramData", "")) / "Microsoft/Windows/Start Menu/Programs",
            pathlib.Path(os.environ.get("AppData", "")) / "Microsoft/Windows/Start Menu/Programs",
            pathlib.Path(os.environ.get("Public", r"C:\Users\Public")) / "Desktop",
            pathlib.Path(os.path.expanduser("~")) / "Desktop"
        ]
        regex = re.compile(name_regex, re.IGNORECASE)
        for p in search_paths:
            if not p.exists(): continue
            try:
                for link in p.rglob("*.lnk"):
                    if regex.search(link.stem): return link
            except:
                continue
        return None

    @staticmethod
    def _resolve_lnk(lnk_path: pathlib.Path) -> Optional[str]:
        """解析 LNK 真实路径"""
        try:
            shell = win32com.client.Dispatch("WScript.Shell")
            return shell.CreateShortcut(str(lnk_path)).TargetPath
        except:
            return None

