import subprocess
import sys
import re
from importlib.metadata import version, PackageNotFoundError


class Pip:
    """
    Python 包管理工具类，提供检测、安装和卸载功能。
    """

    @staticmethod
    def is_installed(package_spec: str) -> bool:
        """
        检测包是否已安装。
        :param package_spec: 包名或带版本的描述 (例如 'requests' 或 'requests==2.28.1')
        """
        # 提取纯包名（处理 requests>=2.0 这种情况）
        package_name = re.split(r'[<>=!]', package_spec)[0].strip()
        try:
            version(package_name)
            return True
        except PackageNotFoundError:
            return False

    @staticmethod
    def install(package_spec: str, upgrade: bool = False) -> bool:
        """
        安装指定的包（阻塞执行）。
        :param package_spec: 包名及其版本要求
        :param upgrade: 是否强制升级
        :return: 安装成功返回 True
        """
        command = [sys.executable, "-m", "pip", "install", package_spec]
        if upgrade:
            command.append("--upgrade")

        try:
            # check_call 会等待子进程结束
            subprocess.check_call(command)
            return True
        except subprocess.CalledProcessError:
            return False

    @staticmethod
    def ensure(package_spec: str) -> bool:
        """
        确保包已安装：如果未安装则进行安装。
        """
        if Pip.is_installed(package_spec):
            return True
        return Pip.install(package_spec)

    @staticmethod
    def remove(package_name: str) -> bool:
        """
        卸载指定的包。
        """
        try:
            # -y 自动确认，避免阻塞时需要人工输入
            subprocess.check_call([sys.executable, "-m", "pip", "uninstall", package_name, "-y"])
            return True
        except subprocess.CalledProcessError:
            return False