"""App: cua so game, vong lap, dieu huong man hinh, ket noi server."""
import math
import os
import subprocess
import sys
import threading
import time

import pygame

from ..gamedata import DEFAULT_SETTINGS, MODES
from ..server import GameServer, probe_server, local_ips
from . import theme as T
from . import screens as S
from .audio import Sfx
from .net import Net
from .play import Play
from .profile import Profile, load_config, save_config, pick_profile
from .render import Renderer
from .ui import UI

GAME_TITLE = "NEON CLASH"


class App:
    def __init__(self, profile_name="main", width=1280, height=800):
        pygame.init()
        T.init()
        self.profile_name = pick_profile(profile_name)
        self.profile = Profile(self.profile_name)
        self.config = load_config()
        self.settings = self.profile.settings

        os.environ.setdefault("SDL_VIDEO_CENTERED", "1")
        flags = pygame.RESIZABLE | pygame.DOUBLEBUF
        self.window = pygame.display.set_mode((width, height), flags)
        pygame.display.set_caption(GAME_TITLE)
        self._set_icon()
        pygame.key.set_repeat(320, 32)

        self.clock = pygame.time.Clock()
        self.fps = 60
        self.time = 0.0
        self.running = True
        self.fullscreen = False
        self.windowed_size = (width, height)

        self.sfx = Sfx(self.settings.get("volume", 0.6))
        self.renderer = Renderer(width, height)
        self.ui = UI()
        self.net = Net()
        self.net.on_open = self._on_open

        self.modal = None
        self.toasts = []
        self.rooms = []
        self.room = None
        self.game = None
        self.local_ips = local_ips()
        self.server = None
        self.port = 0
        self.probe_result = None
        self.pending_create = None
        self._probe_thread = None
        self.headless = bool(os.environ.get("NC_HEADLESS"))
        self._vig = {}
        # auto-update: ket qua kiem tra ban moi (dung cho nut Cap nhat o Hub)
        self.update_remote = None      # meta cua ban moi nhat tren GitHub (hoac None)
        self.update_busy = False
        self.update_ready = False      # da tai xong, cho restart
        # phien ban code DANG CHAY (frozen: prepare() uu tien code da tai ve
        # qua sys.path nen VERSION o day = code that su dang chay)
        from ..version import VERSION as _RUN_VER
        self.update_running = _RUN_VER

        self.launcher = S.Launcher(self)
        self.hub = S.Hub(self)
        self.lobby = S.Lobby(self)
        self.create = S.CreateRoom(self)
        self.rooms_scr = S.RoomsScreen(self)
        self.screen = self.launcher

        self.apply_settings()
        if self.profile_name != "main":
            self.toast("Client riêng · profile %s" % self.profile_name)
        # kiem tra ban moi trong background (on_meta luu lai cho nut Cap nhat)
        try:
            import updater
            updater.check_async(log=self.toast, on_meta=self._on_update_meta)
        except Exception:
            pass

    def _on_update_meta(self, meta):
        """Background check xong: luu meta ban moi.

        Neu ban moi da duoc tai tu dong (check_async tai ngam) thi bat
        update_ready de Hub hien nut "Khoi dong lai game".
        """
        self.update_remote = meta
        if meta:
            try:
                import updater
                rv = tuple(int(x) for x in str(meta.get("version", "0")).split("."))
                cv = tuple(int(x) for x in self.update_running.split("."))
                if rv > cv and updater.local_version() == meta.get("version"):
                    self.update_ready = True   # da tai xong — chi can khoi dong lai
            except Exception:
                pass

    # ---------------- cap nhat thu cong (nut o Hub) ----------------
    def update_click(self):
        """Nguoi choi bam nut Cap nhat: kiem tra + tai ban moi (neu co)."""
        if self.update_busy:
            return
        if self.update_ready:
            # ban moi da tai xong (tu dong hoac bang tay) — chi can khoi dong lai
            import updater
            updater.restart_app()
            return
        self.update_busy = True

        def run():
            import updater
            try:
                meta = updater.check_remote()
                self.update_remote = meta
                if not meta:
                    self.toast("Không kiểm tra được bản cập nhật (mạng yếu?)")
                    return
                rv = meta.get("version", "0")
                cv = self.update_running   # so voi ban DANG CHAY, khong phai ban da tai
                if tuple(int(x) for x in rv.split(".")) <= tuple(int(x) for x in cv.split(".")):
                    self.toast("Bạn đang dùng bản mới nhất (V%s.%s)" % tuple(cv.split(".")[:2]))
                    return
                self.toast("Đang tải bản %s ..." % rv)
                updater.download_update(self._app_dir_pub(), meta)
                self.update_remote = meta
                self.update_ready = True
                self.toast("Đã cập nhật lên %s! Đang khởi động lại game..." % rv)
                time.sleep(1.0)
                updater.restart_app()
            except Exception as ex:
                self.toast("Cập nhật thất bại: %s" % ex)
            finally:
                self.update_busy = False

        threading.Thread(target=run, daemon=True).start()

    def update_label(self):
        """Nhan + loai nut Cap nhat o Hub."""
        cv = tuple(int(x) for x in self.update_running.split("."))
        rv = self.update_remote.get("version", "0") if self.update_remote else None
        if self.update_busy:
            return "Đang kiểm tra...", "normal"
        if self.update_ready:
            return "Khởi động lại game", "primary"
        if rv and tuple(int(x) for x in rv.split(".")) > cv:
            return "Cập nhật → V%s.%s" % tuple(rv.split(".")[:2]), "accent"
        return "Cập nhật bản mới", "normal"

    @staticmethod
    def _app_dir_pub():
        import updater
        return updater._app_dir()

    def vignette(self, key):
        vg = self._vig.get(key)
        if vg is None:
            w, h = key
            vg = pygame.Surface((w, h), pygame.SRCALPHA)
            steps = 26
            for i in range(steps):
                a = int(52 * (1 - i / steps) ** 1.6)
                inset = int(i * 4)
                pygame.draw.rect(vg, (0, 0, 0, a), (inset, inset, w - inset * 2, h - inset * 2),
                                 border_radius=60)
            self._vig[key] = vg
        return vg

    # ---------------- icon ----------------
    def _set_icon(self):
        try:
            ico = pygame.Surface((64, 64), pygame.SRCALPHA)
            pygame.draw.rect(ico, (8, 11, 20), ico.get_rect(), border_radius=14)
            pts = T.shape_points("triangle", 32, 34, 20)
            pygame.draw.polygon(ico, (0, 229, 255), pts)
            pygame.draw.polygon(ico, (255, 255, 255), pts, 2)
            pygame.draw.circle(ico, (124, 92, 255), (32, 34), 6)
            pygame.display.set_icon(ico)
        except Exception:
            pass

    # ---------------- settings ----------------
    def save_config(self):
        save_config(port=int(self.config.get("port", 3000)),
                    lastAddr=str(self.config.get("lastAddr", "localhost:3000")),
                    room=dict(self.config.get("room") or {}))

    def room_opts(self):
        return self.config.setdefault("room", {})

    def apply_settings(self):
        s = self.settings
        self.renderer.set_quality(s.get("particles", True), s.get("glow", True))
        self.sfx.set_volume(s.get("volume", 0.6))
        if self.game:
            self.game.fps_on = bool(s.get("fps"))

    # ---------------- vong lap ----------------
    def run(self):
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            if dt > 0.05:
                dt = 0.05
            self.fps = int(self.clock.get_fps()) or 60
            self.time += dt

            events = pygame.event.get()
            for e in events:
                if e.type == pygame.QUIT:
                    self.running = False
                elif e.type == pygame.VIDEORESIZE:
                    self._resize(e.w, e.h)
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_F11:
                    self._toggle_fullscreen()

            self.ui.begin(events, dt)
            events = self.handle_esc(events)
            self.poll_net()

            if self.modal:
                alive = self.modal.handle(events, self.ui, dt)
                if not alive and self.modal:
                    self.modal = None

            try:
                self.screen.update(dt, events, self.ui)
            except Exception as ex:
                self.toast("Lỗi: %s" % ex)
                print("update error:", ex)

            self.ui.end()

            surf = self.screen_surface()
            self.ui.blocked = self.modal is not None
            try:
                self.screen.draw(surf, self.ui, dt)
                self.ui.blocked = False
                if self.modal:
                    self.modal.draw(surf, self.ui, dt)
            except Exception as ex:
                self.ui.blocked = False
                self.draw_errors = getattr(self, "draw_errors", 0) + 1
                if self.draw_errors == 1:
                    self.toast("Lỗi hiển thị: %s" % ex)
                    print("draw error:", ex)
            self.draw_toasts(surf, dt)
            pygame.display.flip()

        self.shutdown()

    def screen_surface(self):
        return self.window

    def _resize(self, w, h):
        w, h = max(960, int(w)), max(600, int(h))
        if not self.fullscreen:
            self.windowed_size = (w, h)
        self.window = pygame.display.set_mode((w, h), pygame.RESIZABLE | pygame.DOUBLEBUF)
        self.renderer.resize(w, h)

    def _toggle_fullscreen(self):
        if self.fullscreen:
            self.fullscreen = False
            self.window = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE | pygame.DOUBLEBUF)
        else:
            self.fullscreen = True
            self.window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        w, h = self.window.get_size()
        self.renderer.resize(w, h)

    def draw_toasts(self, surf, dt):
        w, h = surf.get_size()
        y = 26
        for t in self.toasts[:3]:
            t["ttl"] -= dt
        self.toasts = [t for t in self.toasts if t["ttl"] > 0]
        for t in self.toasts[:3]:
            a = int(255 * min(1.0, t["ttl"] / 0.4))
            tw = T.text_size(t["msg"], 12.5, True)[0]
            bx = w / 2 - tw / 2 - 18
            s = pygame.Surface((tw + 36, 34), pygame.SRCALPHA)
            # toast cua ban Edge: nen do rgba(255,45,111,.92), radius 10
            pygame.draw.rect(s, (255, 45, 111, int(235 * a / 255)), s.get_rect(), border_radius=10)
            surf.blit(s, (bx, y))
            T.text(surf, t["msg"], (w / 2, y + 9), 12.5, T.WHITE, align="center",
                   bold=True, alpha=a)
            y += 42

    # ---------------- ESC ----------------
    def handle_esc(self, events):
        esc = [e for e in events if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE]
        if not esc or self.ui.focus is not None:
            return events
        if self.modal:
            if isinstance(self.modal, S.Dialog):
                self.modal._cancel()
            else:
                self.close_modal()
            return [e for e in events if not (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE)]
        if self.screen is self.lobby and not self.game:
            self.ask_confirm("Rời phòng?", "Bạn sẽ trở về Hub và rời khỏi phòng hiện tại.",
                             "Rời phòng", self.leave_room, danger=True)
            return [e for e in events if not (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE)]
        return events

    # ---------------- mang ----------------
    def poll_net(self):
        # ket qua kiem tra server (join bang IP) - xu ly o day de dung duoc tu moi man hinh
        if self.probe_result is not None:
            ok, info = self.probe_result
            self.probe_result = None
            self.launcher.busy = False
            if ok:
                # canh bao neu protocol khac (game cu - server moi hoac nguoc lai)
                from ..version import PROTOCOL as MY_P
                if info.get("protocol") is not None and info.get("protocol") != MY_P:
                    self.toast("⚠ Máy chủ khác phiên bản (protocol %s ≠ %s) — nên cập nhật game!" %
                               (info.get("protocol"), MY_P))
                self.connect_to(info["addr"])
                if self.screen is self.launcher:
                    self.set_screen("hub")
            else:
                msg = "Không tìm thấy server NEON CLASH ở " + (self.launcher.addr or "?")
                self.launcher.error = msg
                self.toast(msg)

        if self.pending_create and self.net.connected:
            s = dict(DEFAULT_SETTINGS)
            s.update(self.pending_create)
            self.pending_create = None
            self.net.send({"t": "create", "settings": s})

        for m in self.net.poll():
            t = m.get("t")
            if t == "welcome":
                self.local_ips = m.get("ips") or self.local_ips
                self.rooms = m.get("rooms") or []
                if m.get("map"):
                    self.renderer.set_map(m["map"])
                # canh bao phien ban khac voi server
                from ..version import VERSION as MY_V, PROTOCOL as MY_P
                sv_p = m.get("protocol")
                sv_v = m.get("version", "?")
                if sv_p is not None and sv_p != MY_P:
                    self.toast("⚠ Server khác phiên bản (protocol %s ≠ %s) — có thể lỗi khi chơi!" %
                               (sv_p, MY_P))
                elif m.get("version") and m.get("version") != MY_V:
                    self.toast("Server đang chạy bản %s, bạn đang dùng %s." % (sv_v, MY_V))
            elif t == "rooms":
                self.rooms = m.get("rooms") or []
            elif t == "joined":
                pass
            elif t == "room":
                self.room = m.get("room")
                st = (self.room or {}).get("state")
                if st == "lobby":
                    if self.game:
                        self.game = None
                    # gui loadout cua kit dang chon 1 lan cho moi phong
                    rid = self.room.get("id")
                    if rid != getattr(self, "_loadout_room", None):
                        self._loadout_room = rid
                        self.sync_loadout()
                    self.set_screen("lobby")
                elif st == "playing":
                    pass
            elif t == "start":
                self.game = Play(self, m)
                self.screen = self.game
                self.room = None
            elif t == "snap":
                if self.game:
                    self.game.on_msg(m)
            elif t == "end":
                if self.game:
                    self.game.on_msg(m)
            elif t == "chat":
                if self.game:
                    self.game.on_msg(m)
                else:
                    self.lobby.on_msg(m)
            elif t == "err":
                self.toast(m.get("msg", "Lỗi"))
                self.launcher.on_msg(m)
            elif t == "kicked":
                self.toast("Bạn đã bị chủ phòng mời ra.")
                self.back_to_hub()
            elif t == "left":
                self.room = None
                self.game = None
                if self.screen is not self.launcher:
                    self.set_screen("hub")
            else:
                if self.screen is not self.game:
                    try:
                        self.screen.on_msg(m)
                    except Exception:
                        pass

    def _on_open(self):
        self.net.send({"t": "hello", "name": self.profile.display_name})

    def connect_to(self, addr):
        addr = str(addr or "").strip()
        if not addr:
            return
        if ":" not in addr:
            addr += ":3000"
        self.config["lastAddr"] = addr
        save_config(lastAddr=addr)
        self.net.connect(addr)
        self.toast("Đang kết nối tới " + addr)

    def change_server(self, addr):
        if not addr:
            return
        if self.room:
            self.net.send({"t": "leave"})
        self.room = None
        self.game = None
        self.connect_to(addr)
        self.set_screen("hub")

    def join_by_addr(self, addr):
        if not addr:
            return
        if ":" not in addr:
            addr += ":3000"
        self.launcher.addr = addr
        self.launcher.busy = True
        self.toast("Đang kiểm tra " + addr + "...")
        self.probe_async(addr)

    def probe_async(self, addr):
        if self._probe_thread and self._probe_thread.is_alive():
            return
        self.probe_result = None

        def run():
            info = probe_server(addr, 3.0)
            self.probe_result = (bool(info), info)

        self._probe_thread = threading.Thread(target=run, daemon=True)
        self._probe_thread.start()

    # ---------------- host ----------------
    def host_server(self, port):
        if self.server:
            return True, self.port
        srv = GameServer(port=port, log=lambda *a: None)
        ok, res = srv.start_thread()
        if not ok:
            return False, res
        self.server = srv
        self.port = res
        self.local_ips = local_ips()
        return True, res

    def go_launcher_host(self):
        self.set_screen("create")

    def join_room(self, room_id, password=""):
        if not self.net.connected:
            self.toast("Chưa kết nối server.")
            return
        self.net.send({"t": "join", "id": room_id, "password": password})

    def leave_room(self):
        self.net.send({"t": "leave"})
        self.back_to_hub()

    def back_to_hub(self):
        self.game = None
        self.room = None
        self.close_modal()
        self.set_screen("hub")
        self.net.send({"t": "list"})

    # ---------------- man hinh ----------------
    def set_screen(self, name):
        if name == "launcher":
            self.screen = self.launcher
        elif name == "hub":
            self.screen = self.hub
        elif name == "lobby":
            self.screen = self.lobby
        elif name == "create":
            self.screen = self.create
        elif name == "rooms":
            self.net.send({"t": "list"})
            self.screen = self.rooms_scr
        elif name == "game" and self.game:
            self.screen = self.game

    # ---------------- kit ----------------
    def sync_loadout(self):
        if self.room and self.room.get("state") == "lobby":
            self.net.send({"t": "loadout", "loadout": self.profile.loadout()})

    def set_kit_field(self, field, value):
        kit = self.profile.active_kit()
        lo = {"char": kit["char"], "stats": dict(kit["stats"]),
              "gear": dict(kit["gear"]), "skills": list(kit["skills"])}
        lo[field] = value
        self.profile.update_kit(kit["id"], lo)
        self.sync_loadout()

    def admin_settings(self, d):
        self.net.send({"t": "admin", "cmd": "settings", "settings": d})

    def reset_kits(self):
        from .profile import default_kits
        self.profile.data["kits"] = default_kits()
        self.profile.data["activeKit"] = self.profile.data["kits"][0]["id"]
        self.profile.save()
        self.sync_loadout()
        self.toast("Đã đặt lại 3 kit mặc định.")

    def confirm_delete_kit(self, kid, close_editor=False):
        def do():
            if self.profile.delete_kit(kid):
                self.toast("Đã xoá kit.")
                if close_editor:
                    self.close_modal()
            else:
                self.toast("Phải còn ít nhất 1 kit.")

        self.ask_confirm("Xoá kit?", "Kit này sẽ bị xoá khỏi profile.", "Xoá", do, danger=True)

    # ---------------- modal ----------------
    def open_kit_editor(self, kit_id=None):
        self.modal = S.KitEditor(self, kit_id)

    def open_room_options(self):
        self.modal = S.RoomOptions(self)

    def open_room_info(self):
        self.modal = S.RoomInfo(self)

    def open_settings(self):
        self.modal = S.SettingsModal(self)

    def open_help(self):
        self.modal = S.HelpModal(self)

    def open_rooms(self):
        self.net.send({"t": "list"})
        self.set_screen("rooms")

    def close_modal(self):
        self.modal = None
        self.ui.focus = None

    def ask_text(self, title, default, on_ok, placeholder="", password=False, numeric=False):
        self.modal = S.Dialog(self, title, "", str(default or ""), on_ok,
                              ok_label="OK", password=password, numeric=numeric)

    def ask_confirm(self, title, message, ok_label, on_ok, danger=False):
        self.modal = S.Dialog(self, title, message, "", lambda _v: on_ok(),
                              ok_label=ok_label, confirm_only=True)

    def toast(self, msg):
        self.toasts.append({"msg": str(msg), "ttl": 2.6})

    def copy_text(self, s):
        ok = False
        try:
            pygame.scrap.init()
            pygame.scrap.put(pygame.SCRAP_TEXT, str(s).encode("utf-8"))
            ok = True
        except Exception:
            try:
                p = subprocess.Popen(["clip"], stdin=subprocess.PIPE, shell=True)
                p.communicate(str(s).encode("utf-16le"))
                ok = True
            except Exception:
                ok = False
        self.toast("Đã copy: " + s if ok else "Không copy được: " + s)

    # ---------------- thoat ----------------
    def shutdown(self):
        try:
            if self.server:
                self.server.stop_thread()
        except Exception:
            pass
        try:
            self.net.close()
        except Exception:
            pass
        try:
            self.profile.save()
        except Exception:
            pass
        pygame.quit()
