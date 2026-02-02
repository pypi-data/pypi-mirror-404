import subprocess
import sys
import os
import shutil


def auto_build(entry_file, project_name):
    # 1. 确保入口文件存在
    if not os.path.exists(entry_file):
        print(f"❌ 错误: 找不到入口文件 {entry_file}")
        return

    # 2. 构造 Nuitka 命令
    build_cmd = [
        sys.executable, "-m", "nuitka",
        "--standalone",
        "--onefile",
        "--enable-plugin=tk-inter",
        "--include-package=Crypto",  # 强制包含 Crypto 模块
        # "--windows-disable-console", # 先注掉，我们要看控制台报错
        "--include-package=ascript",
        "--output-dir=out",
        f"--output-filename={project_name}",
        entry_file
    ]

    # 3. 针对 Windows 下可能存在的路径空格问题进行处理
    # Popen 传入 list 格式在 Windows 下通常能很好处理空格

    print(f"🚀 Nuitka 开始编译 [{project_name}]，这可能需要几分钟...")

    # 执行打包
    process = subprocess.Popen(
        build_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        bufsize=1  # 行缓冲，实时获取输出
    )

    # 4. 实时输出给 IDE 的控制台
    try:
        for line in process.stdout:
            # 过滤掉一些极其冗长的编译信息，只留关键进度
            clean_line = line.strip()
            if clean_line:
                print(f"[Nuitka]: {clean_line}")
    except Exception as e:
        print(f"读取日志异常: {e}")

    process.wait()

    if process.returncode == 0:
        print(f"✨ 打包成功！文件位于: out/{project_name}.exe")
    else:
        print(f"💥 打包失败，退出码: {process.returncode}")


if __name__ == "__main__":
    # 假设开发者的主程序是 main.py
    auto_build("windows/main.py", "AScriptApp")