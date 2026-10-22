"""Dung goi cai dat Windows: dist/NeonClash-Setup-<version>.exe

Can Inno Setup (tu dong tai bang tools/install_inno.py hoac cai tai
https://jrsoftware.org/isdl.php). Chay sau khi tools/build.py da xong.
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ISCC_CANDIDATES = [
    r"C:\Program Files\Inno Setup 7\ISCC.exe",
    r"C:\Program Files (x86)\Inno Setup 7\ISCC.exe",
    r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    r"C:\Program Files\Inno Setup 6\ISCC.exe",
]


def find_iscc():
    for p in ISCC_CANDIDATES:
        if os.path.exists(p):
            return p
    found = subprocess.run(["where", "ISCC"], capture_output=True, text=True)
    if found.returncode == 0 and found.stdout.strip():
        return found.stdout.strip().splitlines()[0]
    return None


def main():
    # doc version tu game/version.py
    with open(os.path.join(ROOT, "game", "version.py"), "r", encoding="utf-8") as f:
        src = f.read()
    m = re.search(r'VERSION\s*=\s*"([^"]+)"', src)
    version = m.group(1) if m else "0.0.0"

    if not os.path.exists(os.path.join(ROOT, "dist", "NeonClash.exe")):
        print("Chua co dist/NeonClash.exe — chay python tools/build.py truoc.")
        return 1

    iscc = find_iscc()
    if not iscc:
        print("Khong tim thay Inno Setup. Chay: python tools/install_inno.py")
        return 1

    iss = os.path.join(ROOT, "installer", "neonclash.iss")
    out = os.path.join(ROOT, "dist", "NeonClash-Setup-%s.exe" % version)
    print("Bien dich installer (version %s) ..." % version)
    r = subprocess.run([iscc, "/DAPP_VERSION=%s" % version, "/Qp", iss], cwd=ROOT)
    if r.returncode != 0:
        print("ISCC that bai (exit %d)" % r.returncode)
        return 1
    if os.path.exists(out):
        print("")
        print("XONG:", out)
        print("Dung luong: %.1f MB" % (os.path.getsize(out) / 1024 / 1024))
    return 0


if __name__ == "__main__":
    sys.exit(main())
