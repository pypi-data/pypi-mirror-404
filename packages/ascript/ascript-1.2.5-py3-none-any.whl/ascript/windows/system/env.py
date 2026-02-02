import os
import shutil
import threading
import subprocess
import sys
import ctypes
import psutil
import time
from pkginfo import Wheel  # 确保主环境已安装 pkginfo


class EnvManager:
    def __init__(self, root_path=None):
        self.root_path = root_path or os.path.abspath(os.path.join(os.getcwd(), "user_envs"))
        self.module_dir = os.path.join(self.root_path, "module")
        if not os.path.exists(self.root_path):
            os.makedirs(self.root_path)

        if not os.path.exists(self.module_dir):
            os.makedirs(self.module_dir)

    def _get_pkg_name(self, wheel_path):
        """新增：利用 pkginfo 自动从 whl 提取包名"""
        try:
            return Wheel(wheel_path).name
        except Exception as e:
            print(f"提取包名失败: {e}")
            return None

    def get_env_dir(self, user_id):
        return os.path.join(self.root_path, str(user_id))

    def get_model_dir(self, user_id):
        return os.path.join(self.module_dir, str(user_id))

    def get_python_exe(self, user_id):
        base = self.get_env_dir(user_id)
        suffix = "Scripts\\python.exe" if sys.platform == "win32" else "bin/python"
        return os.path.join(base, suffix)

    def get_pip_exe(self, user_id):
        base = self.get_env_dir(user_id)
        suffix = "Scripts\\pip.exe" if sys.platform == "win32" else "bin/pip"
        return os.path.join(base, suffix)

    def get_create_cmd(self, env_dir):
        return f'"{sys.executable}" -m virtualenv "{env_dir}"'

    def smart_deploy(self, user_id, wheel_path, file_md5, show_console=True):
        env_dir = self.get_env_dir(user_id)
        md5_file = os.path.join(env_dir, "env_identity.md5")
        name_info_file = os.path.join(env_dir, "pkg_name.info")  # 记录包名的文件
        python_exe = self.get_python_exe(user_id)

        # wheel_path = r"D:\workspace\python\ascript-windows\apps\module\1085\8bb2a42175a3d4f473f58333020aebda\ascriptproject2-0.1.0-py3-none-any.whl"

        is_ready = False
        # 增加对 pkg_name.info 的存在性检查
        if os.path.exists(md5_file) and os.path.exists(python_exe) and os.path.exists(name_info_file):
            try:
                with open(md5_file, "r", encoding="utf-8") as f:
                    saved_md5 = f.read().strip()
                if saved_md5 == file_md5:
                    is_ready = True
            except Exception:
                is_ready = False

        if is_ready:
            print(f"[{user_id}] 环境匹配且完整。")
            return True

        print(f"[{user_id}] 环境重建中...")

        # 提前提取包名
        current_pkg_name = self._get_pkg_name(wheel_path)
        if not current_pkg_name:
            self._show_error_box(f"无法从文件解析包名: {wheel_path}", "部署异常")
            return False

        try:
            if os.path.exists(env_dir):
                self.stop_app(user_id)
                time.sleep(0.8)

            if os.path.exists(env_dir):
                shutil.rmtree(env_dir, ignore_errors=True)

            os.makedirs(self.root_path, exist_ok=True)

            # 执行安装
            self._execute_combined_install(user_id, wheel_path, env_dir, show_console)

            # 写入校验信息
            with open(md5_file, "w", encoding="utf-8") as f:
                f.write(file_md5)
            # 关键修改：持久化包名，供 run_app 使用
            with open(name_info_file, "w", encoding="utf-8") as f:
                f.write(current_pkg_name)

            return True

        except RuntimeError as re:
            print(f"[{user_id}] 部署中断: {re}")
            if os.path.exists(env_dir):
                shutil.rmtree(env_dir, ignore_errors=True)
            return False
        except Exception as e:
            self._show_error_box(f"用户 {user_id} 部署失败！\n原因: {str(e)}", "环境部署中断")
            if os.path.exists(env_dir):
                shutil.rmtree(env_dir, ignore_errors=True)
            return False

    def _execute_combined_install(self, user_id, wheel_path, env_dir, show_console):
        abs_env_dir = os.path.abspath(env_dir)
        abs_wheel_path = os.path.abspath(wheel_path)
        pip_path = self.get_pip_exe(user_id)

        combined_payload = (
            f'title 正在初始化运行环境 - {user_id} && '
            f'"{sys.executable}" -m virtualenv "{abs_env_dir}" && '
            f'title 正在安装插件依赖 - {user_id} && '
            f'"{pip_path}" install --no-cache-dir "{abs_wheel_path}" '
            f'|| (echo. && echo ------------------------------------------------ && '
            f'echo [错误] 部署失败！请查看上方红字报错原因。 && '
            f'echo 解决后关闭此窗口，重新启动程序即可。 && '
            f'echo ------------------------------------------------ && pause && exit 1)'
        )

        full_cmd = f'cmd /s /c "{combined_payload}"'
        res = subprocess.run(full_cmd, creationflags=0x00000010, check=False)

        if res.returncode != 0:
            raise RuntimeError("Installation command failed.")

    def run_app(self, user_id, entry_module="main", cwd=None, show_console=False):
        """修改：移除 package_name 参数，实现自动读取"""
        python_exe = self.get_python_exe(user_id)
        env_dir = self.get_env_dir(user_id)
        name_info_file = os.path.join(env_dir, "pkg_name.info")

        # 自动获取包名
        if not os.path.exists(name_info_file):
            self._show_error_box("找不到环境包名配置，请重新部署环境。", "启动失败")
            return None

        with open(name_info_file, "r", encoding="utf-8") as f:
            package_name = f.read().strip()

        work_dir = cwd or env_dir
        last_error_log = os.path.join(env_dir, "last_error.log")

        if os.path.exists(last_error_log):
            try:
                os.remove(last_error_log)
            except:
                pass

        target_module = f"{package_name}.{entry_module}"
        cmd = [python_exe, "-u", "-m", target_module]
        pid_file = os.path.join(env_dir, "app.pid")

        try:
            flags = 0 if show_console else 0x08000000
            with open(last_error_log, "w", encoding="utf-8") as f_err:
                process = subprocess.Popen(
                    cmd,
                    cwd=work_dir,
                    creationflags=flags,
                    stdout=subprocess.DEVNULL,
                    stderr=f_err,
                    text=True,
                    encoding='utf-8'
                )

            with open(pid_file, "w") as f:
                f.write(str(process.pid))

            monitor_thread = threading.Thread(
                target=self._wait_and_handle_error,
                args=(process, user_id, package_name, pid_file, show_console, last_error_log),
                daemon=True
            )
            monitor_thread.start()
            return process.pid
        except Exception as e:
            self._show_error_box(f"启动失败: {str(e)}", "致命错误")
            return None

    def _wait_and_handle_error(self, process, user_id, name, pid_file, show_console, log_path):
        try:
            process.wait()
            is_manual_stop = not os.path.exists(pid_file)
            if process.returncode != 0 and not show_console and not is_manual_stop:
                stderr_content = ""
                if os.path.exists(log_path):
                    with open(log_path, "r", encoding="utf-8") as f:
                        stderr_content = f.read()
                self._handle_runtime_error(name, stderr_content, process.returncode)
        finally:
            if os.path.exists(pid_file):
                try:
                    os.remove(pid_file)
                except:
                    pass

    def _handle_runtime_error(self, name, stderr, code):
        if not stderr: stderr = f"进程异常退出，退出码: {code}"
        lines = [line.strip() for line in stderr.splitlines() if line.strip()]
        error_summary = "\n".join(lines[-10:])
        try:
            log_path = os.path.join(os.getcwd(), f"crash_{int(time.time())}.log")
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(f"Time: {time.ctime()}\nModule: {name}\nCode: {code}\n{stderr}")
        except:
            pass
        self._show_error_box(f"【代码崩溃】核心摘要:\n{error_summary}", f"运行异常 - {name}")

    def _show_error_box(self, content, title):
        if sys.platform == "win32":
            ctypes.windll.user32.MessageBoxW(0, content, title, 16)

    def is_running(self, user_id):
        env_dir = self.get_env_dir(user_id)
        pid_file = os.path.join(env_dir, "app.pid")
        if not os.path.exists(pid_file): return False
        try:
            with open(pid_file, "r") as f:
                saved_pid = int(f.read().strip())
            if not psutil.pid_exists(saved_pid):
                if os.path.exists(pid_file): os.remove(pid_file)
                return False
            proc = psutil.Process(saved_pid)
            expected_python = os.path.normcase(os.path.normpath(self.get_python_exe(user_id)))
            actual_python = os.path.normcase(os.path.normpath(proc.exe()))
            return expected_python == actual_python
        except Exception:
            return False

    def stop_app(self, user_id):
        pid_file = os.path.join(self.get_env_dir(user_id), "app.pid")
        if not os.path.exists(pid_file): return
        try:
            with open(pid_file, "r") as f:
                pid = int(f.read().strip())
            if os.path.exists(pid_file):
                try:
                    os.remove(pid_file)
                except:
                    pass
            if psutil.pid_exists(pid):
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], creationflags=0x08000000,
                               capture_output=True)
        except:
            pass