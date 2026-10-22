"""Tu dong cap nhat code game tu GitHub.

Y tuong: exe chi chua Python runtime + pygame + code ban dau.
Code moi (chi ~200 KB zip) duoc tai ve APPDATA/NeonClash/app va duoc
uu tien hon code dong trong exe khi import. Nguoi chi cai exe 1 lan.

Hoat dong:
  - prepare(): goi dau main.py — neu co code da tai ve thi them vao sys.path.
  - check_async(): background — kiem tra version.json tren GitHub, neu co
    ban moi thi tai ve, lan mo game sau se dung ban moi.
Offline / loi mang -> bo qua yen lang, game van chay voi code co san.
"""
import base64
import hashlib
import io
import json
import os
import shutil
import sys
import threading
import urllib.request
import zipfile

REPO = "buithaisang321/NeonClash"   # tools/release.py khong doi dong nay
BRANCH = "main"
BASE = os.environ.get("NC_UPDATE_BASE") or \
    ("https://raw.githubusercontent.com/%s/%s" % (REPO, BRANCH))

# phien ban code dong trong exe — tools/release.py cap nhat khi build
BUNDLED_VERSION = "1.5.0"


def _app_dir():
    base = os.environ.get("NC_DATA_DIR")
    if not base:
        base = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "NeonClash")
    return os.path.join(base, "app")


def _read_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _fetch(url, timeout=4.0):
    req = urllib.request.Request(url, headers={"User-Agent": "NeonClash-Updater"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def _ver_tuple(v):
    try:
        return tuple(int(x) for x in str(v).split("."))
    except Exception:
        return (0, 0, 0)


def prepare():
    """Uu tien code da tai ve (neu khong han hon code trong exe).

    Goi TRUOC khi import game. Tra ve thu muc code dang dung, hoac None.
    """
    app = _app_dir()
    meta = _read_json(os.path.join(app, "version.json"))
    if meta and os.path.isdir(os.path.join(app, "game")):
        if _ver_tuple(meta.get("version", "0")) >= _ver_tuple(BUNDLED_VERSION):
            if app not in sys.path:
                sys.path.insert(0, app)
            return app
    return None


def _download_update(app, meta):
    zip_name = meta.get("zip", "game.zip.b64")
    data = _fetch(BASE + "/release/" + zip_name, timeout=30)
    if zip_name.endswith(".b64"):
        data = base64.b64decode(data)
    if meta.get("sha256") and hashlib.sha256(data).hexdigest() != meta["sha256"]:
        raise ValueError("sha256 khong khop — file tai ve loi")
    tmp_new = app + ".new"
    tmp_old = app + ".old"
    if os.path.isdir(tmp_new):
        shutil.rmtree(tmp_new, ignore_errors=True)
    os.makedirs(tmp_new, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        z.extractall(tmp_new)
    with open(os.path.join(tmp_new, "version.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    # swap an toan: doi thu muc cu di cho khac roi doi thu muc moi vao
    if os.path.isdir(tmp_old):
        shutil.rmtree(tmp_old, ignore_errors=True)
    if os.path.isdir(app):
        os.rename(app, tmp_old)
    os.rename(tmp_new, app)
    if os.path.isdir(tmp_old):
        shutil.rmtree(tmp_old, ignore_errors=True)


def check_async(log=None):
    """Background thread: neu co ban moi thi tai ve (dung o lan mo sau)."""
    def run():
        app = _app_dir()
        try:
            meta = json.loads(_fetch(BASE + "/release/version.json").decode("utf-8"))
            cur = _read_json(os.path.join(app, "version.json")) or {"version": BUNDLED_VERSION}
            if _ver_tuple(meta.get("version", "0")) > _ver_tuple(cur.get("version", "0")):
                if log:
                    log("Đang cập nhật lên bản " + str(meta.get("version")) + "...")
                _download_update(app, meta)
                if log:
                    log("Đã tải bản mới — lần mở game sau sẽ chạy bản cập nhật.")
        except Exception:
            pass  # offline hoac chua co ban moi: lam ngo

    t = threading.Thread(target=run, daemon=True)
    t.start()
    return t
