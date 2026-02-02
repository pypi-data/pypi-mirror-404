import psutil
import platform
import socket
import uuid
import ctypes
import os
import sys
import time
from datetime import datetime
from typing import Dict, Any, List


# --- 工具类：实现类属性的静态访问 ---
class classproperty(object):
    def __init__(self, fget):
        self.fget = fget

    def __get__(self, owner_self, owner_cls):
        return self.fget(owner_cls)


class Device:
    """AScript 设备环境全感知中心"""

    # ================= 1. 身份识别 (ID) =================
    @classproperty
    def id(cls) -> str:
        """设备唯一标识符 (基于硬件指纹，重装系统不变)"""
        raw = f"{uuid.getnode()}-{platform.processor()}-{platform.node()}"
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, raw)).upper()

    # ================= 2. 操作系统 (OS) =================
    class os:
        type = platform.system()  # Windows
        release = platform.release()  # 10 / 11
        version = platform.version()  # 内核版本
        hostname = socket.gethostname()  # 计算机名

        @classproperty
        def boot_time(cls) -> str:
            """系统启动时间"""
            return datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")

        @classproperty
        def uptime_seconds(cls) -> int:
            """系统已运行秒数"""
            return int(time.time() - psutil.boot_time())

    # ================= 3. 运行环境 (Env) =================
    class env:
        @classproperty
        def is_admin(cls) -> bool:
            """当前进程是否拥有管理员权限"""
            try:
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            except:
                return False

        @classproperty
        def python_ver(cls) -> str:
            return platform.python_version()

        @classproperty
        def cwd(cls) -> str:
            return os.getcwd()

    # ================= 4. 屏幕与缩放 (Screen) =================
    class screen:
        @classproperty
        def scale(cls) -> float:
            """缩放倍数 (如 1.25)"""
            try:
                hdc = ctypes.windll.user32.GetDC(0)
                dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)
                ctypes.windll.user32.ReleaseDC(0, hdc)
                return round(dpi / 96.0, 2)
            except:
                return 1.0

        @classproperty
        def percent(cls) -> str:
            return f"{int(cls.scale * 100)}%"

        @classproperty
        def logical(cls) -> str:
            """逻辑分辨率 (受缩放影响)"""
            u32 = ctypes.windll.user32
            return f"{u32.GetSystemMetrics(0)}x{u32.GetSystemMetrics(1)}"

        @classproperty
        def physical(cls) -> str:
            """物理真实分辨率"""
            u32 = ctypes.windll.user32
            w = int(u32.GetSystemMetrics(0) * cls.scale)
            h = int(u32.GetSystemMetrics(1) * cls.scale)
            return f"{w}x{h}"

    # ================= 5. 核心硬件 (CPU/Mem/GPU) =================
    class cpu:
        brand = platform.processor()
        cores = psutil.cpu_count(logical=False)
        threads = psutil.cpu_count(logical=True)

        @classproperty
        def usage(cls): return psutil.cpu_percent(interval=0.1)

    class memory:
        total_gb = round(psutil.virtual_memory().total / (1024 ** 3), 2)

        @classproperty
        def free_gb(cls): return round(psutil.virtual_memory().available / (1024 ** 3), 2)

        @classproperty
        def percent(cls): return psutil.virtual_memory().percent

    class gpu:
        @classproperty
        def list(cls) -> List[str]:
            """显卡型号列表"""
            names = []
            try:
                import wmi
                for v in wmi.WMI().Win32_VideoController():
                    names.append(v.Name)
            except:
                names = ["Standard Display Adapter"]
            return names

    # ================= 6. 磁盘管理 (Disks) =================
    class disks:
        @classproperty
        def list(cls) -> List[str]:
            """所有有效盘符 (['C', 'D'])"""
            d = []
            for p in psutil.disk_partitions():
                if 'cdrom' in p.opts or p.fstype == '': continue
                d.append(p.mountpoint.split(":")[0].upper())
            return sorted(list(set(d)))

        @classproperty
        def count(cls) -> int:
            return len(cls.list)

        @staticmethod
        def get_detail(drive: str) -> Dict[str, Any]:
            """指定盘符详情 (Device.disks.get_detail('C'))"""
            try:
                u = psutil.disk_usage(f"{drive.upper()}:\\")
                return {
                    "total": f"{u.total / (1024 ** 3):.1f}GB",
                    "free": f"{u.free / (1024 ** 3):.1f}GB",
                    "percent": f"{u.percent}%"
                }
            except:
                return {"error": "Access Denied"}

    # ================= 7. 电源与外设 (Power/Audio) =================
    class power:
        @classproperty
        def is_plugged(cls) -> bool:
            """是否接通电源"""
            batt = psutil.sensors_battery()
            return batt.power_plugged if batt else True

        @classproperty
        def percent(cls) -> int:
            """电池电量"""
            batt = psutil.sensors_battery()
            return batt.percent if batt else 100

    class audio:
        @classproperty
        def list(cls) -> List[str]:
            """音频输出设备"""
            try:
                import wmi
                return [s.Name for s in wmi.WMI().Win32_SoundDevice()]
            except:
                return []

    # ================= 8. 网络信息 (Network) =================
    class network:
        @classproperty
        def ip(cls): return socket.gethostbyname(socket.gethostname())

        @classproperty
        def mac(cls):
            return ':'.join(['{:02x}'.format((uuid.getnode() >> e) & 0xff) for e in range(0, 48, 8)][::-1])