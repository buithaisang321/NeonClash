"""E2E test nut "Cap nhat" o Hub (auto-update thu cong).

Chay tu thu muc goc:
    SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python tests/test_update.py

Kich ban:
  A) Mang ON khi mo game: background check tu tai ban gia 9.9.9 ->
     Hub hien nut "Khoi dong lai game", update_ready=True, local_version=9.9.9.
  B) Mang OFF khi mo game (check that bai): nut "Cap nhat ban moi" ->
     nguoi choi bam -> tai ve -> "Khoi dong lai game", local_version=9.9.9.

Test dung HTTP server gia lap raw.githubusercontent (NC_UPDATE_BASE) va
NC_DATA_DIR rieng -> khong dinh vao may that, khong can Internet.
"""
import functools
import http.server
import json
import os
import shutil
import sys
import tempfile
import threading
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# --- cau hinh headless + data dir tam TRUOC khi import pygame/game ---
TMP = tempfile.mkdtemp(prefix="nc_upd_")
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["NC_HEADLESS"] = "1"

FAKE_VER = "9.9.9"
DEAD_BASE = "http://127.0.0.1:9"   # cong khong ai listen -> check that bai

RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok)))
    print("  [%s] %s%s" % ("PASS" if ok else "FAIL", name,
                           (" — " + str(detail)) if detail else ""))


def start_fake_server():
    """Phuc vu /release/version.json + game.zip.b64 (ban gia FAKE_VER)."""
    sdir = os.path.join(TMP, "fake")
    rdir = os.path.join(sdir, "release")
    os.makedirs(rdir, exist_ok=True)
    with open(os.path.join(ROOT, "release", "version.json"), encoding="utf-8") as f:
        meta = json.load(f)
    meta["version"] = FAKE_VER
    with open(os.path.join(rdir, "version.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    shutil.copy(os.path.join(ROOT, "release", "game.zip.b64"),
                os.path.join(rdir, "game.zip.b64"))
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=sdir)
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, "http://127.0.0.1:%d" % srv.server_address[1]


def make_app(live_base, data_sub):
    """Tao App voi data dir rieng; tra ve (app, frame_fn)."""
    os.environ["NC_DATA_DIR"] = os.path.join(TMP, data_sub)
    os.environ["NC_UPDATE_BASE"] = live_base
    import pygame
    from game.client.app import App
    from game.client.ui import UI

    rects = {}
    orig_button = UI.button

    def button(self, key, r, label, *a, **k):
        rects[key] = pygame.Rect(r)
        return orig_button(self, key, r, label, *a, **k)

    UI.button = button

    app = App("main")
    app.net.send = lambda m: None
    app.net.connected = True
    app.set_screen("hub")

    def frame(ev=None):
        events = [ev] if ev else []
        app.ui.begin(events, 0.016)
        app.screen.update(0.016, events, app.ui)
        app.ui.end()
        app.ui.blocked = False
        app.screen.draw(app.window, app.ui, 0.016)

    frame()
    return app, frame, rects


def click_btn(frame, rects, key):
    r = rects[key]
    frame(pygame_event(r.center))


def pygame_event(pos):
    import pygame
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": pos, "button": 1})


def wait_until(fn, timeout=30.0):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if fn():
            return True
        time.sleep(0.1)
    return fn()


def toasts_text(app):
    return " ".join(str(t.get("msg", t)) if isinstance(t, dict) else str(t)
                    for t in app.toasts)


def main():
    # quan trong: set NC_UPDATE_BASE TRUOC khi import updater lan dau
    srv, live = start_fake_server()
    os.environ["NC_UPDATE_BASE"] = live
    import updater
    assert updater.BASE == live, "updater.BASE phai tro vao server gia (dung %s)" % updater.BASE
    print("Fake GitHub: %s (ban gia %s)" % (live, FAKE_VER))
    ok_all = True

    # ---------- A: mang ON -> background tu tai ----------
    print("\nA) Mo game khi mang ON (background check tu tai):")
    try:
        app, frame, rects = make_app(live, "data_a")
        got = wait_until(lambda: app.update_ready, timeout=30)
        check("background tu tai ban moi", got)
        check("update_remote = %s" % FAKE_VER,
              app.update_remote and app.update_remote.get("version") == FAKE_VER,
              app.update_remote)
        label, kind = app.update_label()
        check("nhan nut = 'Khoi dong lai game' (primary)",
              label == "Khởi động lại game" and kind == "primary",
              (label, kind))
        check("local_version = %s" % FAKE_VER,
              updater.local_version() == FAKE_VER, updater.local_version())
        toasts = toasts_text(app)
        check("toast bao da tai ban moi", "Đã tải bản mới" in toasts, toasts[-120:])
        # bam nut -> restart (dev mode: restart_app no-op) -> khong crash
        click_btn(frame, rects, "hupd")
        time.sleep(0.3)
        frame()
        check("bam nut khong crash", True)
        app.shutdown()
    except Exception as ex:
        check("A khong loi ngoai le", False, repr(ex))
        ok_all = False

    # ---------- B: mang OFF khi mo -> nguoi choi bam thu cong ----------
    print("\nB) Mo game khi mang OFF (check that bai) -> bam Cap nhat thu cong:")
    try:
        # reset module state cho App moi
        updater.BASE = DEAD_BASE
        app, frame, rects = make_app(DEAD_BASE, "data_b")
        time.sleep(2.0)   # cho background check that bai xong
        check("update_remote = None (check that bai)", app.update_remote is None,
              app.update_remote)
        label, kind = app.update_label()
        check("nhan luc chua co ban moi = 'Cap nhat ban moi' (normal)",
              label == "Cập nhật bản mới" and kind == "normal", (label, kind))

        # gia su mang ve lai: co meta 9.9.9 -> nhan phai doi thanh accent
        app.update_remote = {"version": FAKE_VER}
        label, kind = app.update_label()
        check("co ban moi -> 'Cap nhat -> V9.9' (accent)",
              label == "Cập nhật → V9.9" and kind == "accent", (label, kind))
        app.update_remote = None

        # bam nut that: check_remote (mang da ve) -> tai ve
        updater.BASE = live
        click_btn(frame, rects, "hupd")
        got = wait_until(lambda: app.update_ready and not app.update_busy, timeout=30)
        check("bam nut -> tai ve xong", got)
        check("local_version = %s" % FAKE_VER,
              updater.local_version() == FAKE_VER, updater.local_version())
        label, kind = app.update_label()
        check("nhan sau update = 'Khoi dong lai game' (primary)",
              label == "Khởi động lại game" and kind == "primary", (label, kind))
        toasts = toasts_text(app)
        check("toast 'Da cap nhat len %s'" % FAKE_VER,
              ("Đã cập nhật lên %s" % FAKE_VER) in toasts, toasts[-160:])
        # bam lan nua -> update_ready -> restart (no-op dev) -> khong crash
        click_btn(frame, rects, "hupd")
        time.sleep(0.3)
        frame()
        check("bam lai khong crash", True)
        app.shutdown()
    except Exception as ex:
        import traceback
        traceback.print_exc()
        check("B khong loi ngoai le", False, repr(ex))
        ok_all = False

    srv.shutdown()
    shutil.rmtree(TMP, ignore_errors=True)

    passed = sum(1 for _, ok in RESULTS if ok)
    print("\n===== KET QUA: %d/%d PASS =====" % (passed, len(RESULTS)))
    if passed != len(RESULTS):
        for name, ok in RESULTS:
            if not ok:
                print("  FAIL:", name)
        return 1
    print("MANUAL UPDATE E2E: TAT CA PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
