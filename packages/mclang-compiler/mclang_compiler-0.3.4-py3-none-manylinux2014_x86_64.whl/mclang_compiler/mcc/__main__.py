import os
import sys
from pathlib import Path

def get_executable_path():
    """获取可执行文件路径（适配不同平台的 Nuitka 输出）"""
    current_file = Path(__file__).resolve()
    bin_dir = current_file.parent / "bin"

    # Linux Nuitka 生成 mcc.bin，macOS 可能直接生成 mcc
    # 优先尝试 mcc.bin，如果不存在则使用 mcc
    exe_file = bin_dir / "mcc.bin"
    if not exe_file.exists():
        exe_file = bin_dir / "mcc"
    return exe_file

def main():
    bin_path = get_executable_path()
    if not bin_path.exists():
        print(f"Error: mcc executable not found at {bin_path}", file=sys.stderr)
        sys.exit(1)

    # 启动可执行文件
    os.execv(str(bin_path), [str(bin_path)] + sys.argv[1:])

if __name__ == "__main__":
    main()
