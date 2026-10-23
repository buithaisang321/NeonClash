"""Dong goi + dang ban phien ban moi NEON CLASH len GitHub.

Cach dung (trong thu muc du an):
  python tools/release.py                 # dong goi lai theo version hien tai
  python tools/release.py 1.4.2           # tang version (sua game/version.py) roi dong goi
  python tools/release.py 1.4.2 --push    # dong goi + day thang len GitHub

Day len GitHub can GITHUB_TOKEN (personal access token, quyen repo):
  set GITHUB_TOKEN=ghp_xxx          (Windows cmd)
  $env:GITHUB_TOKEN="ghp_xxx"       (PowerShell)

Khong co token: script chi tao 2 file trong release/ — ban co the bao
WorkBuddy (da ket noi GitHub connector) day 2 file nay len repo.
"""
import base64
import hashlib
import io
import json
import os
import re
import sys
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

RELEASE_DIR = os.path.join(ROOT, "release")
VERSION_FILE = os.path.join(ROOT, "game", "version.py")
UPDATER_FILE = os.path.join(ROOT, "updater.py")


def read_current():
    ns = {"VERSION": "", "PROTOCOL": 0}
    with open(VERSION_FILE, "r", encoding="utf-8") as f:
        src = f.read()
    m = re.search(r'VERSION\s*=\s*"([^"]+)"', src)
    if m:
        ns["VERSION"] = m.group(1)
    m = re.search(r"PROTOCOL\s*=\s*(\d+)", src)
    if m:
        ns["PROTOCOL"] = int(m.group(1))
    return ns


def write_version(version, protocol):
    with open(VERSION_FILE, "r", encoding="utf-8") as f:
        src = f.read()
    src = re.sub(r'VERSION\s*=\s*"[^"]+"', 'VERSION = "%s"' % version, src)
    with open(VERSION_FILE, "w", encoding="utf-8") as f:
        f.write(src)
    # dong bo BUNDLED_VERSION trong updater.py
    with open(UPDATER_FILE, "r", encoding="utf-8") as f:
        usrc = f.read()
    usrc = re.sub(r'BUNDLED_VERSION\s*=\s*"[^"]+"', 'BUNDLED_VERSION = "%s"' % version, usrc)
    with open(UPDATER_FILE, "w", encoding="utf-8") as f:
        f.write(usrc)


def make_zip():
    import game  # noqa: F401  (kiem tra import truoc khi dong goi)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for dirpath, dirnames, filenames in os.walk(os.path.join(ROOT, "game")):
            dirnames[:] = [d for d in dirnames if d != "__pycache__"]
            for fn in filenames:
                if fn.endswith(".pyc"):
                    continue
                full = os.path.join(dirpath, fn)
                rel = os.path.relpath(full, ROOT)
                z.write(full, rel.replace("\\", "/"))
    return buf.getvalue()


def github_put(owner_repo, branch, path, content_bytes, token, message):
    url = "https://api.github.com/repos/%s/contents/%s" % (owner_repo, path)
    # lay sha neu file da ton tai
    sha = None
    try:
        req = urllib.request.Request(url + "?ref=" + branch,
                                     headers={"Authorization": "Bearer " + token,
                                              "User-Agent": "NeonClash-Release"})
        with urllib.request.urlopen(req, timeout=15) as r:
            sha = json.loads(r.read().decode("utf-8")).get("sha")
    except Exception:
        sha = None
    body = {
        "message": message,
        "content": base64.b64encode(content_bytes).decode("ascii"),
        "branch": branch,
    }
    if sha:
        body["sha"] = sha
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"),
                                 headers={"Authorization": "Bearer " + token,
                                          "User-Agent": "NeonClash-Release",
                                          "Content-Type": "application/json"},
                                 method="PUT")
    with urllib.request.urlopen(req, timeout=30) as r:
        r.read()


def purge_jsdelivr():
    """Xoa cache jsDelivr cho release/ de nguoi choi nhan ban moi ngay.

    jsDelivr cache file theo branch ~12h; purge de dam bao CDN tra dung ban vua push.
    """
    from updater import REPO, BRANCH
    ok = 0
    for f in ("version.json", "game.zip.b64"):
        try:
            req = urllib.request.Request(
                "https://purge.jsdelivr.net/gh/%s@%s/release/%s" % (REPO, BRANCH, f),
                method="POST",
                headers={"User-Agent": "NeonClash-Release"})
            urllib.request.urlopen(req, timeout=15).read()
            print("Da purge jsDelivr: release/" + f)
            ok += 1
        except Exception as ex:
            print("Purge jsDelivr release/%s loi (bo qua): %s" % (f, ex))
    return ok


def main():
    if "--purge" in sys.argv:
        purge_jsdelivr()
        return
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    do_push = "--push" in sys.argv
    cur = read_current()
    version = args[0] if args else cur["VERSION"]
    protocol = cur["PROTOCOL"]

    if version != cur["VERSION"]:
        write_version(version, protocol)
        print("Da cap nhat game/version.py -> %s (protocol %d)" % (version, protocol))
    else:
        print("Version giu nguyen: %s (protocol %d)" % (version, protocol))

    print("Dong goi game.zip ...")
    zip_bytes = make_zip()
    os.makedirs(RELEASE_DIR, exist_ok=True)
    with open(os.path.join(RELEASE_DIR, "game.zip.b64"), "wb") as f:
        f.write(base64.b64encode(zip_bytes))
    meta = {
        "version": version,
        "protocol": protocol,
        "zip": "game.zip.b64",
        "zip_b64": True,
        "sha256": hashlib.sha256(zip_bytes).hexdigest(),
        "size": len(zip_bytes),
    }
    meta_path = os.path.join(RELEASE_DIR, "version.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    print("Da tao release/version.json + release/game.zip.b64 (%.0f KB zip)" %
          (len(zip_bytes) / 1024))

    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if do_push and token:
        from updater import REPO
        print("Day len GitHub: %s (branch main) ..." % REPO)
        github_put(REPO, "main", "release/version.json",
                   json.dumps(meta, ensure_ascii=False, indent=1).encode("utf-8"),
                   token, "release " + version)
        github_put(REPO, "main", "release/game.zip.b64",
                   open(os.path.join(RELEASE_DIR, "game.zip.b64"), "rb").read(),
                   token, "release " + version)
        print("XONG! Nguoi choi mo game se tu cap nhat len %s." % version)
    elif do_push:
        print("Chua co GITHUB_TOKEN — chua day len GitHub.")
        print("2 file trong release/ san sang de WorkBuddy day len repo cho ban.")
    else:
        print("Mẹo: dung --push (kem GITHUB_TOKEN) de day thang, hoac bao WorkBuddy day giup.")


if __name__ == "__main__":
    main()
