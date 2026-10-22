"""Dong goi game thanh 1 file exe bang PyInstaller."""
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)


def main():
    print("[1/3] Tạo icon...")
    subprocess.run([sys.executable, os.path.join("tools", "make_icon.py"), os.path.join("build", "icon.ico")],
                   check=True)

    print("[2/3] Dọn bản build cũ...")
    for d in ("build/NeonClash", "dist/NeonClash.exe"):
        p = os.path.join(ROOT, d)
        if os.path.isdir(p):
            shutil.rmtree(p, ignore_errors=True)
        elif os.path.exists(p):
            try:
                os.remove(p)
            except Exception:
                pass

    print("[3/3] PyInstaller...")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean", "--onefile", "--windowed",
        "--name", "NeonClash",
        "--icon", os.path.join(ROOT, "build", "icon.ico"),
        "--distpath", "dist",
        "--workpath", "build",
        "--specpath", "build",
        "--exclude-module", "tkinter",
        "--exclude-module", "unittest",
        "--exclude-module", "pydoc",
        os.path.join(ROOT, "main.py"),
    ]
    subprocess.run(cmd, check=True)

    exe = os.path.join(ROOT, "dist", "NeonClash.exe")
    if os.path.exists(exe):
        print("")
        print("XONG:", exe)
        print("Dung luong: %.1f MB" % (os.path.getsize(exe) / 1024 / 1024))
    else:
        print("KHONG THAY FILE EXE")


if __name__ == "__main__":
    main()
