"""Cac man hinh menu — tai tao 1-1 giao dien ban Edge (public/index.html + style.css)."""
import math
import random

import pygame

from ..gamedata import (
    CHARS, CHAR_MAP, SLOTS, GEAR, GEAR_MAP, gear_by_slot, SKILLS, SKILL_MAP,
    SKILL_GROUPS, GROUP_MAP, SKILL_RANGES, RANGE_MAP, STATS, STAT_POINTS, STAT_MAX,
    MODES, MODE_MAP, compute_build, build_summary, hex_rgb, sanitize_loadout,
)
from . import theme as T


# ============================================================
#  helper dung chung
# ============================================================
def avatar(surf, shape, color, cx, cy, r, glow=True, accent=None):
    """Avatar tron (dung boi HUD trong tran)."""
    col = hex_rgb(color) if isinstance(color, str) else color
    acc = hex_rgb(accent) if accent else T.mix(col, (255, 255, 255), 0.5)
    if glow:
        T.glow(surf, (cx, cy), r * 1.5, col, 70)
    pygame.draw.circle(surf, (14, 18, 30), (int(cx), int(cy)), int(r))
    pts = T.shape_points(shape, cx, cy, r * 0.72)
    pygame.draw.polygon(surf, col, pts)
    pygame.draw.polygon(surf, acc, pts, 2)


def h3(surf, x, y, title, extra=None, extra_col=T.MUTED):
    """Tieu de muc .panel h3: 13px, HOA, mau muted."""
    T.text(surf, title, (x, y), 12, T.MUTED, bold=True)
    if extra:
        T.text(surf, extra, (x + T.text_size(title, 12, True)[0] + 8, y), 12, extra_col)
    return y + 26


def field_label(surf, x, y, label):
    """Label .field label: 12px HOA ls .08em muted."""
    T.text(surf, label, (x, y), 10.5, T.MUTED)
    return y + 22


def avatar_box(surf, shape, color, cx, cy, size, radius=10, icon_ratio=0.55, glow_k=40):
    """O avatar giong .kc-avatar / .profile-avatar: nen tint mau, vien tint, hinh o giua."""
    col = hex_rgb(color) if isinstance(color, str) else color
    r = pygame.Rect(0, 0, size, size)
    r.center = (int(cx), int(cy))
    tint = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.rect(tint, (*col, 30), tint.get_rect(), border_radius=radius)
    surf.blit(tint, r.topleft)
    pygame.draw.rect(surf, (*col, 85), r, 1, border_radius=radius)
    T.shape_icon(surf, shape, col, r.centerx, r.centery, size * icon_ratio / 2, glow_k=glow_k)
    return r


def badge(surf, x, y, label, kind, align="left"):
    """Badge .badge: 10px HOA, nen tint, radius 5."""
    col = {"host": T.YELLOW, "ready": T.GREEN, "wait": T.MUTED}.get(kind, T.MUTED)
    bg_a = {"host": 41, "ready": 41, "wait": 18}.get(kind, 18)
    tw, th = T.text_size(label, 9, True)
    w, hh = tw + 12, 16
    if align == "right":
        x -= w
    T.rect(surf, (x, y, w, hh), (*col, bg_a), 5)
    T.text(surf, label, (x + 6, y + 3), 9, col, bold=True)
    return w


def range_tag(surf, x, y, label, color):
    """The nho .range-tag: vien theo mau."""
    tw = T.text_size(label, 8)[0]
    T.rect(surf, (x, y, tw + 8, 13), (0, 0, 0, 0), 4)
    pygame.draw.rect(surf, color, (x, y, tw + 8, 13), 1, border_radius=4)
    T.text(surf, label, (x + 4, y + 2), 8, color)
    return tw + 8


def mode_card(surf, ui, key, r, mode, active):
    """The chon che độ .mode-card."""
    r = pygame.Rect(r)
    hov = ui.hovered(r)
    T.rect(surf, r, (255, 255, 255, 8), 10)
    if active:
        T.rect(surf, r, (0, 229, 255, 23), 10)
        pygame.draw.rect(surf, T.CYAN, r, 1, border_radius=10)
        T.rect(surf, r.inflate(-4, -4), (0, 229, 255, 38), 9, width=2)
    else:
        pygame.draw.rect(surf, T.LINE_HI if hov else T.LINE, r, 1, border_radius=10)
    T.text(surf, mode["name"], (r.x + 12, r.y + 10), 12.5, T.TXT, bold=True)
    for j, line in enumerate(T.wrap(mode["desc"], 10.5, r.w - 24)[:3]):
        T.text(surf, line, (r.x + 12, r.y + 30 + j * 13), 10.5, T.MUTED)
    return ui.click is not None and hov


def kit_btn(surf, ui, key, x, y, label, active, size=12):
    """Nut kit .kit-btn."""
    tw = T.text_size(label, size)[0]
    w, hh = tw + 22, 24
    r = pygame.Rect(x, y, w, hh)
    if active:
        T.rect(surf, r, (0, 229, 255, 36), 7)
        T.rect(surf, r, (0, 229, 255, 115), 7, width=1)
        col = T.WHITE
    else:
        hov = ui.hovered(r)
        T.rect(surf, r, (255, 255, 255, 26 if hov else 13), 7)
        col = T.TXT if hov else T.MUTED
    T.text(surf, label, (r.centerx, r.centery - size // 2 - 1), size, col, align="center")
    if ui.click and ui.hovered(r):
        ui.click = None
        return True
    return False


def kv_row(surf, x, y, w, label, value):
    """Hang .kv cua settings-view: label trai, gia tri phai, gach dut duoi."""
    T.text(surf, label, (x, y + 3), 11.5, T.MUTED)
    T.text(surf, value, (x + w, y + 3), 11.5, T.TXT, align="right", bold=True)
    T.dashed_hline(surf, x, x + w, y + 22, (255, 255, 255, 15))
    return y + 27


def conn_status(app):
    if app.net.connected:
        return "Đã kết nối server", T.GREEN
    return "Mất kết nối — đang thử lại...", T.ACCENT


def draw_modal_dim(surf, a=199):
    ov = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    ov.fill((3, 4, 8, a))
    surf.blit(ov, (0, 0))


# ============================================================
#  LAUNCHER (public/launcher.html)
# ============================================================
class Launcher:
    def __init__(self, app):
        self.app = app
        self.port = str(app.config.get("port", 3000))
        self.addr = app.config.get("lastAddr", "localhost:3000")
        self.error = ""
        self.busy = False

    def on_msg(self, m):
        if m.get("t") == "err":
            self.error = m.get("msg", "")

    def update(self, dt, events, ui):
        pass

    def _card_bg(self, surf, r, hover=False):
        # .card: gradient 160deg white .06 -> .018, border rgba(120,140,255,.2)
        g = T.rounded_vgrad(r.w, r.h, (24, 27, 43), (18, 21, 35), 14)
        surf.blit(g, r.topleft)
        pygame.draw.rect(surf, (36, 43, 78), r, 1, border_radius=14)

    def draw(self, surf, ui, dt):
        app = self.app
        w, h = surf.get_size()
        # nen rieng cua launcher.html
        T.bg_grid(surf, (w, h))
        T.glow(surf, (w * 0.5, -h * 0.05), int(w * 0.42), T.PURPLE, 82)
        T.glow(surf, (w * 0.92, h * 1.02), int(w * 0.3), T.CYAN, 36)

        colw = min(500, w - 68)
        x0 = (w - colw) // 2
        cy = max(30, (h - 470) // 2)

        # logo: NEON / CLASH 2 dong
        T.logo(surf, (w // 2, cy), 40, inline=False, align="center")
        T.text(surf, "Đấu trường 2D · FFA · chơi qua IP", (w // 2, cy + 78), 12, T.MUTED, align="center")
        cy += 108

        # ---- card tao phong ----
        r1 = pygame.Rect(x0, cy, colw, 152)
        self._card_bg(surf, r1)
        T.text(surf, "◆", (r1.x + 15, r1.y + 14), 11, T.CYAN)
        T.text(surf, "TẠO PHÒNG", (r1.x + 30, r1.y + 14), 11, T.MUTED, bold=True)
        T.text(surf, "Mở server trên máy này rồi vào game. Bạn bè nhập IP của bạn để vào.",
               (r1.x + 15, r1.y + 32), 11, (124, 132, 165))

        if ui.button("lhost", (r1.x + 15, r1.y + 52, colw - 30, 38), "Vào game (tạo phòng)", "primary", size=13):
            self.do_host()
        # server-line
        sl = pygame.Rect(r1.x + 15, r1.y + 98, colw - 30, 30)
        T.rect(surf, sl, (0, 229, 255, 15), 9)
        T.rect(surf, sl, (0, 229, 255, 41), 9, width=1)
        T.text(surf, "Server: ", (sl.x + 10, sl.y + 8), 11.5, T.MUTED)
        T.text(surf, "localhost:%s" % (app.port or self.port or 3000),
               (sl.x + 62, sl.y + 7), 12, T.ICE, bold=True, mono=True)
        if ui.button("lport", (sl.right - 74, sl.y + 4, 64, 22), "Đổi cổng", "normal", size=10, radius=6):
            app.ask_text("Cổng server", self.port, self._set_port, numeric=True)

        st = "Đã mở server ở cổng %s." % (app.port or 3000) if app.server else ""
        if st:
            T.text(surf, st, (r1.x + 15, r1.bottom + 4), 11, T.GREEN)
        cy = r1.bottom + 26

        # ---- card vao phong ----
        r2 = pygame.Rect(x0, cy, colw, 138)
        self._card_bg(surf, r2)
        T.text(surf, "▸", (r2.x + 15, r2.y + 14), 11, T.CYAN)
        T.text(surf, "VÀO PHÒNG", (r2.x + 30, r2.y + 14), 11, T.MUTED, bold=True)
        T.text(surf, "Nhập IP máy chủ của người tạo phòng. Test nhiều client trên 1 máy:",
               (r2.x + 15, r2.y + 32), 11, (124, 132, 165))
        T.text(surf, "mở thêm NeonClash.exe rồi nhập localhost:%s." % (self.port or 3000),
               (r2.x + 15, r2.y + 47), 11, T.ICE)

        inp = pygame.Rect(r2.x + 15, r2.y + 68, colw - 30 - 92, 36)
        self.addr, sub = ui.text_input("laddr", inp, self.addr, "26.12.34.56:3000", 40, mono=True)
        if ui.button("ljoin", (inp.right + 8, inp.y, 84, 36), "Kết nối", "ghost", size=12):
            self.do_join()
        if sub:
            self.do_join()

        if self.busy:
            T.text(surf, "Đang kiểm tra %s..." % self.addr, (r2.x + 15, r2.bottom + 4), 11, T.YELLOW)
        elif self.error:
            T.text(surf, self.error, (r2.x + 15, r2.bottom + 4), 11, T.ACCENT)

        T.text(surf, "v1.4 · NEON CLASH", (w // 2, h - 26), 10, (57, 64, 92), align="center")

    def _set_port(self, v):
        app = self.app
        try:
            port = int(v)
        except ValueError:
            self.error = "Cổng không hợp lệ."
            return
        if not (1 <= port <= 65535):
            self.error = "Cổng phải trong khoảng 1..65535."
            return
        self.port = str(port)
        if app.server:
            self.error = "Server đang chạy — khởi động lại game để đổi cổng."
            return
        app.config["port"] = port
        app.save_config()

    # ---------------- hanh dong ----------------
    def do_host(self):
        app = self.app
        if app.server:
            app.set_screen("hub")
            return
        try:
            port = int(self.port or 3000)
        except ValueError:
            self.error = "Cổng không hợp lệ."
            return
        ok, res = app.host_server(port)
        if not ok:
            self.error = "Không mở được server: %s" % res
            return
        app.config["port"] = res
        app.save_config()
        self.error = ""
        app.connect_to("localhost:%d" % res)
        app.set_screen("hub")

    def do_join(self):
        app = self.app
        addr = self.addr.strip().replace("http://", "").replace("https://", "").split("/")[0]
        if not addr:
            self.error = "Nhập IP máy chủ trước."
            return
        if ":" not in addr:
            addr += ":3000"
        self.error = ""
        self.busy = True
        app.probe_async(addr)


# ============================================================
#  HUB (scr-hub)
# ============================================================
class Hub:
    def __init__(self, app):
        self.app = app

    def on_msg(self, m):
        pass

    def update(self, dt, events, ui):
        app = self.app
        if app.room and app.room.get("state") == "lobby" and app.room.get("players"):
            app.set_screen("lobby")

    def draw(self, surf, ui, dt):
        app = self.app
        w, h = surf.get_size()
        app.renderer.draw_backdrop(surf, app.time, 0.75)

        # ---------- hub-head ----------
        pad_x, pad_t, pad_b = 22, 14, 14
        logo_w = T.logo(surf, (pad_x, pad_t), 36, inline=True)
        msg, col = conn_status(app)
        msg_w = T.text_size(msg, 12)[0]
        T.text(surf, msg, (w - pad_x, pad_t + 26), 12, col, align="right")
        btn_w = 100
        btn_x = w - pad_x - msg_w - 16 - btn_w
        if ui.button("hchg", (btn_x, pad_t + 20, btn_w, 26), "Đổi server", "ghost", size=10, radius=7):
            app.ask_text("Đổi server", app.net.host or "localhost:3000", app.change_server, "IP:cổng")

        # ---------- hub-grid ----------
        top = pad_t + 54 + 14
        left_w, right_w, gap = 290, 270, 14
        left = pygame.Rect(pad_x, top, left_w, h - top - pad_b)
        right = pygame.Rect(w - right_w - pad_x, top, right_w, h - top - pad_b)
        center = pygame.Rect(left.right + gap, top, right.x - left.right - gap, h - top - pad_b)

        self._draw_profile(surf, ui, left)
        self._draw_kits(surf, ui, center)
        self._draw_actions(surf, ui, right)

    # ---------------- panel ho so ----------------
    def _draw_profile(self, surf, ui, r):
        app = self.app
        T.panel(surf, r, 16)
        x = r.x + 16
        y = r.y + 14
        y = h3(surf, x, y, "HỒ SƠ")

        kit = app.profile.active_kit()
        ch = CHAR_MAP.get(kit["char"], CHARS[0])

        # .profile-avatar 96px radius 18
        av_r = pygame.Rect(0, 0, 96, 96)
        av_r.centerx = r.centerx
        av_r.y = y + 4
        av_s = pygame.Surface((96, 96), pygame.SRCALPHA)
        pygame.draw.rect(av_s, (255, 255, 255, 20), av_s.get_rect(), border_radius=18)
        pygame.draw.rect(av_s, (108, 92, 231, 46), av_s.get_rect(), border_radius=18)
        surf.blit(av_s, av_r.topleft)
        T.rect(surf, av_r, (255, 255, 255, 23), 18, width=1)
        T.shape_icon(surf, ch["shape"], hex_rgb(ch["color"]), av_r.centerx, av_r.centery - 2, 26, glow_k=70)

        y = av_r.bottom + 8
        # ten nhan vat (CSS to mau char)
        T.text(surf, ch["name"], (r.centerx, y), 18, hex_rgb(ch["color"]), bold=True, align="center")
        y += 26
        T.text(surf, ch["passiveName"] + " · " + ch["passiveDesc"],
               (r.centerx, y), 11, T.MUTED, align="center")
        y += 28

        # field ten
        y = field_label(surf, x, y, "TÊN HIỂN THỊ")
        nm, _ = ui.text_input("hname", (x, y, r.w - 32, 40), app.profile.display_name, "Nhập tên...", 16)
        if nm != app.profile.name:
            app.profile.name = nm
            app.net.send({"t": "hello", "name": nm})
        y += 52

        # field dia chi server + join row
        y = field_label(surf, x, y, "ĐỊA CHỈ SERVER (IP:PORT)")
        inp = pygame.Rect(x, y, r.w - 32 - 62, 40)
        addr, sub = ui.text_input("haddr", inp, app.config.get("lastAddr", "localhost:3000"),
                                  "26.12.34.56:3000", 64, mono=True)
        if ui.button("hjoin", (inp.right + 6, y, 56, 40), "Nối", "normal", size=12):
            app.join_by_addr(addr)
        if sub:
            app.join_by_addr(addr)
        y += 48
        hint = ("Đang dùng server: " + (app.net.host or "?")) if app.net.connected \
            else "Nhập IP:port của chủ phòng rồi bấm Nối."
        T.text(surf, hint, (x, y), 10.5, T.GREEN if app.net.connected else T.MUTED)
        y += 24

        # .profile-stats: 2 cot, gach dut tren
        T.dashed_hline(surf, x, r.right - 16, r.bottom - 128, (255, 255, 255, 20))
        sm = build_summary(kit, 100)
        stats = [
            ("Máu", str(sm["hp"])),
            ("Sát thương", "×%.2f" % sm["dmgMul"]),
            ("Tốc chạy", "%.0f" % sm["speed"]),
            ("Giáp", "%d%%" % round(sm["armor"] * 100)),
            ("Hồi chiêu", "×%.2f" % sm["cdr"]),
            ("Hồi máu", "%.1f/s" % sm["regen"]),
        ]
        cw = (r.w - 32 - 6) // 2
        for i, (lab, val) in enumerate(stats):
            cxx = x + (i % 2) * (cw + 6)
            cyy = r.bottom - 122 + (i // 2) * 34
            T.rect(surf, (cxx, cyy, cw, 28), (255, 255, 255, 9), 7)
            T.text(surf, lab, (cxx + 8, cyy + 8), 10, T.MUTED)
            T.text(surf, val, (cxx + cw - 8, cyy + 7), 10.5, T.TXT, align="right", bold=True, mono=True)

    # ---------------- panel kits ----------------
    def _draw_kits(self, surf, ui, r):
        app = self.app
        x = r.x + 16
        y = r.y + 14
        # panel-head: h2 + hint + nut
        T.text(surf, "KIT CỦA BẠN", (x, y), 15, T.TXT, bold=True)
        if ui.button("hknew", (r.right - 16 - 92, y - 2, 92, 28), "+ Kit mới", "primary", size=11, radius=8):
            app.ask_text("Tên kit mới", "Kit %d" % (len(app.profile.kits) + 1),
                         lambda v: (app.profile.new_kit(v), app.sync_loadout()))
        y += 24
        for j, line in enumerate(T.wrap(
                "Mỗi kit là một bộ đồ hoàn chỉnh: nhân vật · 5 trang bị · 5 chiêu · 10 điểm chỉ số. "
                "Chọn kit nào thì vào trận với kit đó.", 11, r.w - 220)[:2]):
            T.text(surf, line, (x, y + j * 14), 10.5, T.MUTED)
        y += 36

        # luoi kit-card
        active = app.profile.active_kit()
        cols = max(1, (r.w + 10) // 296)
        cw = (r.w - 16 - (cols - 1) * 10) // cols
        chh = 172
        n = len(app.profile.kits)
        rows = (n + 1 + cols - 1) // cols
        content_h = rows * (chh + 10) + 10
        off, _ = ui.scroll_area("hubkits", (r.x, y, r.w, r.bottom - y - 6), content_h)
        old = surf.get_clip()
        surf.set_clip(pygame.Rect(r.x, y, r.w, r.bottom - y))
        for i, k in enumerate(app.profile.kits):
            rr = pygame.Rect(r.x + 16 + (i % cols) * (cw + 10),
                             y + (i // cols) * (chh + 10) - off, cw, chh)
            act = self._kit_card(surf, ui, "hk%d" % i, rr, k, k["id"] == active["id"])
            if act == "select":
                app.profile.set_active(k["id"])
                app.sync_loadout()
                app.sfx.ui()
            elif act == "edit":
                app.profile.set_active(k["id"])
                app.open_kit_editor(k["id"])
            elif act == "dup":
                app.profile.duplicate_kit(k["id"])
                app.sync_loadout()
            elif act == "del":
                app.confirm_delete_kit(k["id"])
        # the + tao kit moi (dashed)
        i = n
        rr = pygame.Rect(r.x + 16 + (i % cols) * (cw + 10),
                         y + (i // cols) * (chh + 10) - off, cw, chh)
        hov = ui.hovered(rr)
        if hov:
            T.rect(surf, rr, (0, 229, 255, 15), 12)
        T.dashed_rect(surf, rr, (0, 229, 255, 128) if hov else (255, 255, 255, 46), radius=12)
        T.text(surf, "+", (rr.centerx, rr.centery - 34), 30, T.WHITE if hov else T.MUTED,
               align="center")
        T.text(surf, "Tạo kit mới", (rr.centerx, rr.centery + 16), 11.5,
               T.WHITE if hov else T.MUTED, align="center")
        if ui.click and hov:
            ui.click = None
            app.ask_text("Tên kit mới", "Kit %d" % (n + 1),
                         lambda v: (app.profile.new_kit(v), app.sync_loadout()))
        surf.set_clip(old)

    def _kit_card(self, surf, ui, key, r, kit, active):
        """The kit .kit-card. Tra ve None|select|edit|dup|del."""
        r = pygame.Rect(r)
        hov = ui.hovered(r)
        action = None
        # nen gradient 160deg
        g = T.rounded_vgrad(r.w, r.h, (26, 29, 46), (19, 22, 37), 12)
        surf.blit(g, r.topleft)
        if active:
            T.rect(surf, r, (0, 229, 255, 153), 12, width=1)
            T.rect(surf, r.inflate(-4, -4), (0, 229, 255, 26), 10, width=1)
        else:
            pygame.draw.rect(surf, T.LINE_HI if hov else T.LINE, r, 1, border_radius=12)

        # tag ĐANG DÙNG
        if active:
            tag = "ĐANG DÙNG"
            tw = T.text_size(tag, 8.5, True)[0]
            tg = T.rounded_hgrad(tw + 16, 16, T.CYAN, T.PURPLE, 0)
            surf.blit(tg, (r.right - tw - 16, r.y))
            T.text(surf, tag, (r.right - 8, r.y + 3), 8.5, (4, 18, 26), align="right", bold=True)

        ch = CHAR_MAP.get(kit["char"], CHARS[0])
        wp = GEAR_MAP.get(kit["gear"]["weapon"], {})
        # kc-head
        avatar_box(surf, ch["shape"], ch["color"], r.x + 30, r.y + 30, 38, 10, 0.58, 0)
        T.text(surf, kit["name"], (r.x + 56, r.y + 12), 13, T.TXT, bold=True)
        T.text(surf, "%s · %s" % (ch["name"], wp.get("name", "")), (r.x + 56, r.y + 30), 10, T.MUTED)

        # kc-skills
        for i2, sid in enumerate(kit["skills"][:5]):
            sk = SKILL_MAP.get(sid)
            if not sk:
                continue
            bx = r.x + 11 + i2 * 26
            by = r.y + 56
            T.rect(surf, (bx, by, 22, 22), (0, 229, 255, 20), 6)
            T.rect(surf, (bx, by, 22, 22), (0, 229, 255, 46), 6, width=1)
            T.text(surf, sk["icon"], (bx + 11, by + 4), 11, (191, 243, 255), align="center")

        # kc-gear
        gear_names = " · ".join(GEAR_MAP[kit["gear"][s["id"]]]["name"]
                                for s in SLOTS if kit["gear"].get(s["id"]))
        yy = r.y + 84
        for j, line in enumerate(T.wrap(gear_names, 10, r.w - 22)[:2]):
            T.text(surf, line, (r.x + 11, yy), 10, T.MUTED)
            yy += 13
        # kc-stats
        sm = build_summary(kit, 100)
        chips = [("Máu", "%d" % sm["hp"]), ("Dmg", "×%.2f" % sm["dmgMul"]),
                 ("Tốc", "%.0f" % sm["speed"]), ("Giáp", "%d%%" % round(sm["armor"] * 100))]
        cx = r.x + 11
        cy = r.y + 112
        for lab, val in chips:
            tw = T.text_size(lab + "  " + val, 9)[0]
            T.rect(surf, (cx, cy, tw + 12, 17), (255, 255, 255, 12), 5)
            T.text(surf, lab, (cx + 6, cy + 3), 9, T.MUTED)
            T.text(surf, val, (cx + 6 + T.text_size(lab + "  ", 9)[0], cy + 3), 9.5, T.TXT, mono=True)
            cx += tw + 18
            if cx > r.right - 60 and lab == "Tốc":
                break

        # kc-actions
        ay = r.bottom - 28
        bw = (r.w - 22 - 10) // 3
        if ui.button(key + "e", (r.x + 11, ay, bw, 22), "Chỉnh sửa", "normal", size=9.5, radius=6):
            action = "edit"
        if ui.button(key + "d", (r.x + 11 + bw + 5, ay, bw, 22), "Nhân bản", "normal", size=9.5, radius=6):
            action = "dup"
        if ui.button(key + "x", (r.x + 11 + (bw + 5) * 2, ay, bw, 22), "Xoá", "danger", size=9.5, radius=6):
            action = "del"
        if action is None and ui.click and hov:
            # click vao than the -> chon kit
            body = pygame.Rect(r.x, r.y, r.w, r.h - 30)
            if ui.hovered(body):
                ui.click = None
                action = "select"
        return action

    # ---------------- panel hanh dong ----------------
    def _draw_actions(self, surf, ui, r):
        app = self.app
        T.panel(surf, r, 16)
        x = r.x + 16
        y = r.y + 14
        y = h3(surf, x, y, "VÀO TRẬN")
        if ui.button("hcreate", (x, y, r.w - 32, 44), "Tạo phòng", "primary", size=14):
            app.set_screen("create")
        y += 52
        if ui.button("hrooms", (x, y, r.w - 32, 44), "Danh sách phòng", "normal", size=13):
            app.open_rooms()
        y += 56
        T.rect(surf, (x, y, r.w - 32, 1), (255, 255, 255, 18))
        y += 14
        y = h3(surf, x, y, "KHÁC")
        if ui.button("hset", (x, y, r.w - 32, 36), "Cài đặt", "normal", size=13):
            app.open_settings()
        y += 42
        if ui.button("hhelp", (x, y, r.w - 32, 36), "Hướng dẫn", "normal", size=13):
            app.open_help()
        y += 46
        T.rect(surf, (x, y, r.w - 32, 1), (255, 255, 255, 18))
        y += 12
        # hub-tip
        tip_h = 86
        T.rect(surf, (x, y, r.w - 32, tip_h), (0, 229, 255, 13), 9)
        T.rect(surf, (x, y, r.w - 32, tip_h), (0, 229, 255, 36), 9, width=1)
        T.text(surf, "MẸO", (x + 10, y + 8), 9.5, T.CYAN, bold=True)
        for j, line in enumerate(T.wrap(
                "Giữ chuột trái để bắn liên tục, phím 1–5 để tung chiêu. "
                "Núp trong bụi cỏ để phục kích.", 10.5, r.w - 56)[:3]):
            T.text(surf, line, (x + 10, y + 24 + j * 14), 10.5, T.MUTED)
        T.text(surf, "v1.4 · NEON CLASH", (r.centerx, r.bottom - 24), 9.5,
               (57, 64, 92), align="center")


# ============================================================
#  TẠO PHÒNG (scr-create) — man hinh rieng giong Edge
# ============================================================
class CreateRoom:
    def __init__(self, app):
        self.app = app
        o = app.room_opts()
        self.name = str(o.get("name") or "Phòng của tôi")
        self.password = str(o.get("password") or "")
        self.max_players = str(int(o.get("maxPlayers", 16)))
        self.start_hp = str(int(o.get("startHp", 100)))
        self.mode = o.get("mode", "kills")
        self.kill_target = str(int(o.get("killTarget", 20)))
        self.time_limit = str(int(o.get("timeLimit", 300)))
        self.respawn = str(int(o.get("respawn", 3)))

    def on_msg(self, m):
        pass

    def update(self, dt, events, ui):
        pass

    def _field(self, surf, ui, key, x, y, w, label, value, maxlen, numeric=False, password=False):
        y = field_label(surf, x, y, label)
        val, sub = ui.text_input(key, (x, y, w, 40), value, "", maxlen,
                                 numeric=numeric, password=password)
        return val, y + 54

    def draw(self, surf, ui, dt):
        app = self.app
        w, h = surf.get_size()
        T.bg_grid(surf, (w, h))

        pw = min(720, w - 40)
        ph = min(560, h - 30)
        box = pygame.Rect((w - pw) // 2, (h - ph) // 2, pw, ph)
        T.panel(surf, box, 16)
        x = box.x + 30
        y = box.y + 24
        T.text(surf, "Tạo phòng FFA", (x, y), 20, T.TXT, bold=True)
        y += 44

        colw = (pw - 60 - 16) // 2
        self.name, y = self._field(surf, ui, "cname", x, y, colw, "TÊN PHÒNG", self.name, 28)
        self.password, y = self._field(surf, ui, "cpass", x + colw + 16, y - 54, colw,
                                       "MẬT KHẨU (BỎ TRỐNG = CÔNG KHAI)", self.password, 16, password=True)
        self.max_players, y = self._field(surf, ui, "cmax", x, y, colw,
                                          "SỐ NGƯỜI TỐI ĐA", self.max_players, 3, numeric=True)
        self.start_hp, y = self._field(surf, ui, "chp", x + colw + 16, y - 54, colw,
                                       "MÁU KHỞI ĐẦU", self.start_hp, 3, numeric=True)

        # chedo thang
        y = field_label(surf, x, y, "CHẾ ĐỘ THẮNG")
        mw = (pw - 60 - 20) // 3
        for i, mode in enumerate(MODES):
            r = pygame.Rect(x + i * (mw + 10), y, mw, 74)
            if mode_card(surf, ui, "cm%d" % i, r, mode, self.mode == mode["id"]) and ui.click:
                ui.click = None
                self.mode = mode["id"]
                app.sfx.ui()
        y += 88

        grid3 = [("SỐ MẠNG ĐỂ THẮNG", self.kill_target, "ckills"),
                 ("THỜI GIAN TRẬN (GIÂY)", self.time_limit, "ctime"),
                 ("HỒI SINH SAU (GIÂY)", self.respawn, "cresp")]
        fw = (pw - 60 - 32) // 3
        vals = []
        for i, (lab, val, key) in enumerate(grid3):
            v, dy = self._field(surf, ui, key, x + i * (fw + 16), y, fw, lab, val, 4, numeric=True)
            vals.append(v)
        y += 60
        self.kill_target, self.time_limit, self.respawn = vals

        # form-actions
        if ui.button("cdo", (x, box.bottom - 62, 140, 42), "Tạo phòng", "primary", size=14):
            self._create()
        if ui.button("cback", (x + 152, box.bottom - 62, 110, 42), "Quay lại", "ghost", size=13):
            app.set_screen("hub")

    def _num(self, s, default, lo, hi):
        try:
            v = int(float(s))
        except (ValueError, TypeError):
            return default
        return max(lo, min(hi, v))

    def _create(self):
        app = self.app
        st = {
            "name": self.name.strip() or "Phòng của tôi",
            "password": self.password.strip()[:16],
            "maxPlayers": self._num(self.max_players, 16, 2, 64),
            "startHp": self._num(self.start_hp, 100, 50, 500),
            "mode": self.mode,
            "killTarget": self._num(self.kill_target, 20, 1, 999),
            "timeLimit": self._num(self.time_limit, 300, 30, 3600),
            "respawn": self._num(self.respawn, 3, 0, 30),
        }
        app.config["room"] = st
        app.save_config()
        if not app.server:
            try:
                port = int(app.config.get("port", 3000))
            except (ValueError, TypeError):
                port = 3000
            ok, res = app.host_server(port)
            if not ok:
                app.toast("Không mở được server: %s" % res)
                return
            app.config["port"] = res
            app.save_config()
            app.connect_to("localhost:%d" % res)
        elif not app.net.connected:
            app.connect_to("localhost:%d" % (app.port or 3000))
        app.pending_create = st
        app.set_screen("hub")


# ============================================================
#  DANH SÁCH PHÒNG (scr-rooms) — man hinh rieng giong Edge
# ============================================================
class RoomsScreen:
    def __init__(self, app):
        self.app = app
        self.timer = 0.0

    def on_msg(self, m):
        pass

    def update(self, dt, events, ui):
        self.timer -= dt
        if self.timer <= 0:
            self.timer = 2.5
            self.app.net.send({"t": "list"})

    def draw(self, surf, ui, dt):
        app = self.app
        w, h = surf.get_size()
        T.bg_grid(surf, (w, h))

        pw = min(820, w - 40)
        ph = min(560, h - 30)
        box = pygame.Rect((w - pw) // 2, (h - ph) // 2, pw, ph)
        T.panel(surf, box, 16)
        x = box.x + 26
        y = box.y + 22
        T.text(surf, "Phòng đang mở", (x, y), 20, T.TXT, bold=True)
        if ui.button("rref", (box.right - 26 - 96, y, 96, 32), "Làm mới", "normal", size=12):
            app.net.send({"t": "list"})
            self.timer = 2.5
        y += 44

        list_r = pygame.Rect(x, y, pw - 52, box.bottom - y - 62)
        if not app.rooms:
            T.text(surf, "Chưa có phòng nào. Hãy tạo phòng đầu tiên!",
                   (list_r.centerx, list_r.centery - 8), 13, T.MUTED, align="center")
        else:
            row_h = 64
            content_h = len(app.rooms) * (row_h + 10)
            off, _ = ui.scroll_area("roomslist", list_r, content_h)
            old = surf.get_clip()
            surf.set_clip(list_r)
            for i, room in enumerate(app.rooms[:20]):
                rr = pygame.Rect(x, y + i * (row_h + 10) - off, pw - 56, row_h)
                hov = ui.hovered(rr)
                T.rect(surf, rr, (255, 255, 255, 15 if hov else 9), 12)
                pygame.draw.rect(surf, T.LINE_HI if hov else T.LINE, rr, 1, border_radius=12)
                T.text(surf, room.get("name", "?"), (rr.x + 16, rr.y + 10), 13.5, T.TXT, bold=True)
                T.text(surf, "%s · %d/%d người · mã %s" % (
                    room.get("modeName", ""), room.get("players", 0), room.get("max", 16),
                    room.get("id", "")), (rr.x + 16, rr.y + 32), 11.5, T.MUTED)
                rx = rr.right - 100
                if room.get("hasPass"):
                    tw = T.text_size("Có mật khẩu", 10)[0]
                    T.text(surf, "Có mật khẩu", (rx - tw - 16, rr.y + 12), 10, T.YELLOW)
                    T.rect(surf, (rx - tw - 22, rr.y + 9, tw + 14, 18), (255, 182, 72, 100), 5,
                           width=1)
                in_lobby = room.get("state") == "lobby"
                if ui.button("rj" + str(room.get("id", i)), (rr.right - 88, rr.y + 16, 76, 32),
                             "Vào" if in_lobby else "Đang chơi", "primary" if in_lobby else "normal",
                             size=12, enabled=in_lobby):
                    if room.get("hasPass"):
                        rid = room["id"]
                        app.ask_text("Nhập mật khẩu phòng:", "", lambda v: app.join_room(rid, v),
                                     password=True)
                    else:
                        app.join_room(room["id"], "")
            surf.set_clip(old)

        if ui.button("rback", (x, box.bottom - 54, 110, 40), "Quay lại", "ghost", size=13):
            app.set_screen("hub")


# ============================================================
#  KIT EDITOR (modal-kit)
# ============================================================
class KitEditor:
    def __init__(self, app, kit_id=None):
        self.app = app
        self.kit_id = kit_id or app.profile.active_kit()["id"]
        app.profile.set_active(self.kit_id)
        self.tab = "char"
        self.filter = "all"

    @property
    def kit(self):
        for k in self.app.profile.kits:
            if k["id"] == self.kit_id:
                return k
        return self.app.profile.active_kit()

    def handle(self, events, ui, dt):
        return True

    def draw(self, surf, ui, dt):
        app = self.app
        w, h = surf.get_size()
        draw_modal_dim(surf)

        bw = min(1180, w - 40)
        bh = min(int(h * 0.92), 900, h - 24)
        box = pygame.Rect((w - bw) // 2, (h - bh) // 2, bw, bh)
        T.panel(surf, box, 16)

        kit = self.kit

        # ---------- kit-modal-head ----------
        x = box.x + 20
        y = box.y + 16
        T.text(surf, "Chỉnh kit: " + kit["name"], (x, y), 17, T.TXT, bold=True)
        T.text(surf, "Mọi thay đổi được lưu ngay vào kit đang chọn.", (x, y + 24), 11, T.MUTED)
        if ui.button("kok", (box.right - 20 - 96, y + 4, 96, 36), "Xong", "primary", size=13):
            app.close_modal()
        y += 52

        # ---------- kit-bar ----------
        bar = pygame.Rect(x, y, bw - 40, 40)
        T.rect(surf, bar, (0, 0, 0, 71), 10)
        T.rect(surf, bar, (255, 255, 255, 13), 10, width=1)
        T.text(surf, "KIT", (bar.x + 9, bar.centery - 6), 9.5, T.MUTED, bold=True)
        kx = bar.x + 44
        for k in app.profile.kits:
            if kit_btn(surf, ui, "kb" + k["id"], kx, bar.y + 8, k["name"], k["id"] == kit["id"]):
                self.kit_id = k["id"]
                app.profile.set_active(k["id"])
                app.sync_loadout()
                app.sfx.ui()
                kit = self.kit
            kx += T.text_size(k["name"], 12)[0] + 22
            if kx > bar.right - 240:
                break
        ax = bar.right - 8
        bw2 = 58
        if ui.button("kdel", (ax - bw2, bar.y + 8, bw2, 24), "Xoá", "danger", size=10.5, radius=7):
            app.confirm_delete_kit(self.kit_id)
        ax -= bw2 + 5
        if ui.button("kren", (ax - bw2, bar.y + 8, bw2, 24), "Đổi tên", "normal", size=10.5, radius=7):
            app.ask_text("Đổi tên kit", kit["name"],
                         lambda v: app.profile.rename_kit(self.kit_id, v))
        ax -= bw2 + 5
        if ui.button("kdup", (ax - bw2 + 8, bar.y + 8, bw2, 24), "Nhân bản", "normal", size=10.5, radius=7):
            k = app.profile.duplicate_kit(self.kit_id)
            if k:
                self.kit_id = k["id"]
        ax -= bw2 - 8 + 5
        if ui.button("knew", (ax - 58, bar.y + 8, 58, 24), "+ Mới", "normal", size=10.5, radius=7):
            app.ask_text("Tên kit mới", "Kit %d" % (len(app.profile.kits) + 1),
                         lambda v: self._new_kit(v))
        y += 52

        # ---------- tabs ----------
        tabs = [("char", "Nhân vật"), ("gear", "Trang bị"),
                ("skill", "Chiêu %d/5" % len(kit["skills"])),
                ("stat", "Chỉ số %d/%d" % (sum(kit["stats"].values()), STAT_POINTS))]
        picked = ui.tabs("ktabs", (x, y, bw - 40, 32), tabs, self.tab, size=12.5)
        if picked:
            self.tab = picked
            app.sfx.ui()
        y += 44

        body = pygame.Rect(x, y, bw - 40, box.bottom - y - 16)
        if self.tab == "char":
            self._tab_char(surf, ui, body)
        elif self.tab == "gear":
            self._tab_gear(surf, ui, body)
        elif self.tab == "skill":
            self._tab_skill(surf, ui, body)
        else:
            self._tab_stat(surf, ui, body)

    def _new_kit(self, name):
        k = self.app.profile.new_kit(name)
        self.kit_id = k["id"]
        self.app.sync_loadout()

    # ---------------- tab nhan vat ----------------
    def _tab_char(self, surf, ui, body):
        app = self.app
        kit = self.kit
        cols = max(3, body.w // 180)
        cw = (body.w - (cols - 1) * 10) // cols
        chh = 122
        rows = (len(CHARS) + cols - 1) // cols
        off, _ = ui.scroll_area("kchars", body, rows * (chh + 10) + 10)
        old = surf.get_clip()
        surf.set_clip(body)
        for i, ch in enumerate(CHARS):
            rr = pygame.Rect(body.x + (i % cols) * (cw + 10),
                             body.y + (i // cols) * (chh + 10) - off, cw, chh)
            sel = kit["char"] == ch["id"]
            hov = ui.hovered(rr)
            col = hex_rgb(ch["color"])
            T.rect(surf, rr, (255, 255, 255, 8), 12)
            if sel:
                T.rect(surf, rr, (0, 229, 255, 18), 12)
            pygame.draw.rect(surf, T.CYAN if sel else (T.LINE_HI if hov else T.LINE), rr, 1,
                             border_radius=12)
            if sel:
                T.glow(surf, rr.center, cw // 2, T.CYAN, 18)
            # .avatar 38px nen tint
            avatar_box(surf, ch["shape"], ch["color"], rr.x + 12 + 19, rr.y + 12 + 19, 38, 10, 0.6, 0)
            T.text(surf, ch["name"], (rr.x + 12, rr.y + 58), 13.5, col, bold=True)
            T.text(surf, ch["passiveName"], (rr.x + 12, rr.y + 78), 10.5, T.GREEN, bold=True)
            for j, line in enumerate(T.wrap(ch["passiveDesc"], 10.5, cw - 24)[:2]):
                T.text(surf, line, (rr.x + 12, rr.y + 94 + j * 13), 10.5, T.MUTED)
            if ui.click and hov:
                ui.click = None
                app.set_kit_field("char", ch["id"])
                app.sfx.ui()
        surf.set_clip(old)

    # ---------------- tab trang bi ----------------
    def _tab_gear(self, surf, ui, body):
        app = self.app
        kit = self.kit
        n = len(SLOTS)
        cw = (body.w - (n - 1) * 10) // n
        # tinh chieu cao noi dung that de scroll du het
        max_h = 0
        for slot in SLOTS:
            hh = 22
            for g in gear_by_slot(slot["id"]):
                hh += 30 + max(0, len(T.wrap(g.get("desc", ""), 10, cw - 20)) - 1) * 13 + 7
            max_h = max(max_h, hh)
        off, _ = ui.scroll_area("kgear", body, max_h + 10)
        old = surf.get_clip()
        surf.set_clip(body)
        for si, slot in enumerate(SLOTS):
            cx = body.x + si * (cw + 10)
            T.text(surf, slot["icon"], (cx, body.y + 2 - off), 12, T.PURPLE)
            T.text(surf, slot["name"].upper(), (cx + T.text_size(slot["icon"], 12)[0] + 6,
                                                body.y + 3 - off), 10.5, T.MUTED)
            items = gear_by_slot(slot["id"])
            yy = body.y + 22 - off
            for g in items:
                ih = 30 + max(0, len(T.wrap(g.get("desc", ""), 10, cw - 20)) - 1) * 13
                rr = pygame.Rect(cx, yy - off, cw, ih)
                sel = kit["gear"].get(slot["id"]) == g["id"]
                hov = ui.hovered(rr)
                T.rect(surf, rr, (255, 255, 255, 7), 9)
                if sel:
                    T.rect(surf, rr, (0, 229, 255, 23), 9)
                pygame.draw.rect(surf, T.CYAN if sel else (T.LINE_HI if hov else T.LINE), rr, 1,
                                 border_radius=9)
                T.text(surf, g["name"], (rr.x + 10, rr.y + 7), 11.5, T.TXT, bold=True)
                for j, line in enumerate(T.wrap(g.get("desc", ""), 10, cw - 20)[:2]):
                    T.text(surf, line, (rr.x + 10, rr.y + 24 + j * 13), 9.5, T.MUTED)
                if ui.click and hov:
                    ui.click = None
                    g2 = dict(kit["gear"])
                    g2[slot["id"]] = g["id"]
                    app.set_kit_field("gear", g2)
                    app.sfx.ui()
                yy += ih + 7
        surf.set_clip(old)

    # ---------------- tab chieu ----------------
    def _tab_skill(self, surf, ui, body):
        app = self.app
        kit = self.kit
        # hint
        T.text(surf, "Chọn đúng 5 chiêu — trộn bao nhiêu cận chiến / tầm xa cũng được. Bấm lại để bỏ chọn.",
               (body.x, body.y), 11, T.MUTED)
        fy = body.y + 20
        # range-filter chips
        x = body.x
        for cid, label in [("all", "Tất cả")] + [(r_["id"], r_["name"]) for r_ in SKILL_RANGES]:
            cw2 = T.text_size(label, 11)[0] + 24
            if ui.chip("sf" + cid, (x, fy, cw2, 24), label, self.filter == cid,
                       T.PURPLE, size=11):
                self.filter = cid
                app.sfx.ui()
            x += cw2 + 6
        gy = fy + 34

        grid_r = pygame.Rect(body.x, gy, body.w, body.bottom - gy)
        cols = max(2, body.w // 214)
        cw = (body.w - (cols - 1) * 9) // cols
        chh = 84
        # nhom chieu giong renderSkillPanel: group title + card
        items = []  # (kind, data)
        for grp in SKILL_GROUPS:
            lst = [s for s in SKILLS if s["group"] == grp["id"]
                   and (self.filter == "all" or s["range"] == self.filter)]
            if not lst:
                continue
            items.append(("title", grp))
            for s in lst:
                items.append(("skill", s))
        rows_h = 0
        heights = []
        for kind, data in items:
            if kind == "title":
                heights.append(24)
            else:
                heights.append(chh + 9)
        content_h = sum(heights)
        off, _ = ui.scroll_area("kskills", grid_r, content_h + 10)
        old = surf.get_clip()
        surf.set_clip(grid_r)
        yy = grid_r.y - off
        col_i = 0
        row_y = yy
        for (kind, data), hh in zip(items, heights):
            if kind == "title":
                if col_i:
                    row_y += chh + 9
                    col_i = 0
                T.text(surf, data["name"].upper(), (grid_r.x, row_y + 4), 10.5,
                       hex_rgb(data["color"]), bold=True)
                row_y += 24
                continue
            s = data
            cw_full = cw
            if col_i == cols - 1:
                cw_full = grid_r.right - (grid_r.x + col_i * (cw + 9))
            rr = pygame.Rect(grid_r.x + col_i * (cw + 9), row_y, cw_full, chh)
            idx = kit["skills"].index(s["id"]) if s["id"] in kit["skills"] else -1
            sel = idx >= 0
            hov = ui.hovered(rr)
            grp = GROUP_MAP.get(s["group"], {"color": "#fff"})
            gcol = hex_rgb(grp["color"])
            T.rect(surf, rr, (255, 255, 255, 7), 10)
            if sel:
                T.rect(surf, rr, (0, 229, 255, 25), 10)
            pygame.draw.rect(surf, T.CYAN if sel else (T.LINE_HI if hov else T.LINE), rr, 1,
                             border_radius=10)
            # sicon 24px
            T.rect(surf, (rr.x + 10, rr.y + 9, 24, 24), (255, 255, 255, 18), 7)
            T.text(surf, s["icon"], (rr.x + 22, rr.y + 14), 12.5, gcol, align="center")
            T.text(surf, s["name"], (rr.x + 42, rr.y + 9), 11.5, T.TXT, bold=True)
            T.text(surf, "%ds" % s["cd"], (rr.right - 10, rr.y + 11), 9.5, T.MUTED,
                   align="right", mono=True)
            # sdesc + range-tag
            rng = RANGE_MAP.get(s["range"], {"name": "", "color": "#888"})
            tx = rr.x + 10
            ty = rr.y + 40
            if rng.get("name"):
                tw = range_tag(surf, tx, ty, rng["name"], hex_rgb(rng["color"]))
                tx += tw + 6
            words = T.wrap(s["desc"], 10, rr.w - 20)
            if words:
                T.text(surf, words[0], (tx, ty + 1), 10, T.MUTED)
                for j, line in enumerate(words[1 if tx > rr.x + 12 else 0:][:2]):
                    T.text(surf, line, (rr.x + 10, rr.y + 55 + j * 12), 10, T.MUTED)
            # sel badge
            if sel:
                pygame.draw.circle(surf, T.CYAN, (rr.right - 15, rr.y + 15), 8)
                T.text(surf, str(idx + 1), (rr.right - 15, rr.y + 8), 10, (4, 18, 26),
                       align="center", bold=True)
            if ui.click and hov:
                ui.click = None
                sk = list(kit["skills"])
                if s["id"] in sk:
                    sk.remove(s["id"])
                elif len(sk) < 5:
                    sk.append(s["id"])
                else:
                    app.toast("Chỉ được chọn 5 chiêu — bỏ bớt một chiêu trước.")
                    continue
                app.set_kit_field("skills", sk)
                app.sfx.ui()
            col_i += 1
            if col_i >= cols:
                col_i = 0
                row_y += chh + 9
        surf.set_clip(old)

    # ---------------- tab chi so ----------------
    def _tab_stat(self, surf, ui, body):
        app = self.app
        kit = self.kit
        used = sum(kit["stats"].values())
        left_pts = STAT_POINTS - used
        row_h = 40
        content_h = 22 + len(STATS) * (row_h + 7) + 6 + 62
        off, _ = ui.scroll_area("kstats", body, content_h)
        old = surf.get_clip()
        surf.set_clip(body)
        T.text(surf, "Có 10 điểm, mỗi chỉ số tối đa 3 điểm. Bấm + để tăng, − để giảm.",
               (body.x, body.y - off), 11, T.MUTED)
        ry = body.y + 22 - off
        for st in STATS:
            v = kit["stats"].get(st["id"], 0)
            rr = pygame.Rect(body.x, ry, body.w, row_h)
            if v > 0:
                T.rect(surf, rr, (0, 229, 255, 14), 9)
                T.rect(surf, rr, (0, 229, 255, 71), 9, width=1)
            else:
                T.rect(surf, rr, (255, 255, 255, 8), 9)
            T.text(surf, st["name"], (rr.x + 12, rr.y + 12), 12, T.TXT, bold=True)
            T.text(surf, st["desc"], (rr.x + 142, rr.y + 14), 10.5, T.MUTED)
            # pips
            px = rr.right - 150
            for j in range(STAT_MAX):
                pxx = px + j * 18
                if j < v:
                    g = T.rounded_vgrad(14, 14, T.CYAN, T.PURPLE, 4)
                    surf.blit(g, (pxx, rr.y + 13))
                    T.glow(surf, (pxx + 7, rr.y + 20), 10, T.CYAN, 42)
                else:
                    T.rect(surf, (pxx, rr.y + 13, 14, 14), (255, 255, 255, 23), 4)
                    T.rect(surf, (pxx, rr.y + 13, 14, 14), (255, 255, 255, 20), 4, width=1)
            # sbtns
            bx = rr.right - 70
            if ui.button("sdec" + st["id"], (bx, rr.y + 7, 26, 26), "−", "normal", size=13,
                         radius=7, enabled=v > 0):
                stt = dict(kit["stats"])
                stt[st["id"]] = v - 1
                app.set_kit_field("stats", stt)
                app.sfx.ui()
            if ui.button("sinc" + st["id"], (bx + 32, rr.y + 7, 26, 26), "+", "normal", size=13,
                         radius=7, enabled=v < STAT_MAX and left_pts > 0):
                stt = dict(kit["stats"])
                stt[st["id"]] = v + 1
                app.set_kit_field("stats", stt)
                app.sfx.ui()
            ry += row_h + 7

        # build-summary
        sy = ry + 6
        sm = build_summary(kit, 100)
        T.rect(surf, (body.x, sy, body.w, 56), (0, 0, 0, 64), 10)
        T.rect(surf, (body.x, sy, body.w, 56), (255, 255, 255, 13), 10, width=1)
        chips = [("Máu tối đa", "%d" % sm["hp"]), ("Sát thương", "×%.2f" % sm["dmgMul"]),
                 ("Tốc chạy", "%.0f" % sm["speed"]), ("Tốc đánh", "×%.2f" % sm["atkspd"]),
                 ("Giáp", "%d%%" % round(sm["armor"] * 100)), ("Hồi chiêu", "×%.2f" % sm["cdr"]),
                 ("Hồi máu", "%.1f/s" % sm["regen"]), ("Tầm bắn", "×%.2f" % sm["range"])]
        cw2 = (body.w - 24) // 4
        for i2, (lab, val) in enumerate(chips):
            cx = body.x + 12 + (i2 % 4) * cw2
            cy2 = sy + 8 + (i2 // 4) * 22
            T.text(surf, lab, (cx, cy2), 10.5, T.MUTED)
            T.text(surf, val, (cx + T.text_size(lab + "  ", 10.5)[0], cy2 - 1), 11, T.TXT,
                   bold=True, mono=True)
        surf.set_clip(old)


# ============================================================
#  LOBBY (scr-lobby)
# ============================================================
class Lobby:
    def __init__(self, app):
        self.app = app
        self.chat_text = ""
        self.chat_log = []

    def on_msg(self, m):
        if m.get("t") == "chat":
            self.chat_log.append((m.get("from", "?"), m.get("text", "")))
            if len(self.chat_log) > 60:
                self.chat_log.pop(0)
            if self.app.game:
                self.app.game.chat_log = self.chat_log

    def update(self, dt, events, ui):
        app = self.app
        room = app.room
        if not room or not room.get("players"):
            app.set_screen("hub")

    def draw(self, surf, ui, dt):
        app = self.app
        w, h = surf.get_size()
        app.renderer.draw_backdrop(surf, app.time, 0.85)
        room = app.room or {"settings": {}, "players": [], "id": "----", "you": 0, "hostId": 0}
        st = room.get("settings", {})
        me = room.get("you")

        # lobby-wrap: padding 14, 3 cot 290 / 1fr / 300
        pad = 14
        lw, rw, gap = 290, 300, 14
        left = pygame.Rect(pad, pad, lw, h - pad * 2)
        right = pygame.Rect(w - rw - pad, pad, rw, h - pad * 2)
        center = pygame.Rect(left.right + gap, pad, right.x - left.right - gap, h - pad * 2)

        self._draw_players(surf, ui, left, room, st, me)
        self._draw_kit(surf, ui, center, st)
        self._draw_roominfo(surf, ui, right, room, st, me)

    # ---------------- panel nguoi choi + chat ----------------
    def _draw_players(self, surf, ui, r, room, st, me):
        app = self.app
        T.panel(surf, r, 16)
        x = r.x + 16
        y = r.y + 14
        cnt = "%d/%d" % (len(room.get("players", [])), st.get("maxPlayers", 16))
        y = h3(surf, x, y, "NGƯỜI CHƠI", cnt, T.DIM)

        # khoang danh cho chat o duoi
        bottom_block = 130 + 8 + 34 + 8 + 34
        list_r = pygame.Rect(x, y, r.w - 32, r.bottom - 14 - bottom_block - y)
        players = room.get("players", [])
        content_h = len(players) * 37
        off, _ = ui.scroll_area("plob", list_r, content_h)
        old = surf.get_clip()
        surf.set_clip(list_r)
        yy = list_r.y - off
        for p in players:
            ch = CHAR_MAP.get((p.get("loadout") or {}).get("char"), CHARS[0])
            col = hex_rgb(ch["color"])
            rr = pygame.Rect(x, yy, r.w - 32, 30)
            T.rect(surf, rr, (255, 255, 255, 10), 9)
            # dot 9px glow
            T.glow(surf, (rr.x + 13, rr.centery), 9, col, 90)
            pygame.draw.circle(surf, col, (rr.x + 13, rr.centery), 4.5)
            is_me = p.get("id") == me
            T.text(surf, T.fit(p.get("name", "?"), 12, rr.w - 130), (rr.x + 26, rr.y + 8), 12,
                   T.ICE if is_me else T.TXT, bold=is_me)
            bx = rr.right - 8
            if p.get("ready"):
                w2 = badge(surf, bx, rr.y + 7, "SẴN SÀNG", "ready", align="right")
                bx -= w2 + 5
            else:
                w2 = badge(surf, bx, rr.y + 7, "CHỜ", "wait", align="right")
                bx -= w2 + 5
            if p.get("id") == room.get("hostId") or p.get("isHost"):
                badge(surf, bx, rr.y + 7, "CHỦ PHÒNG", "host", align="right")
            yy += 37
        surf.set_clip(old)
        y = list_r.bottom + 8

        # room-code
        T.text(surf, "Mã phòng:", (x, y + 3), 11.5, T.MUTED)
        T.text(surf, room.get("id", "----"), (x + 72, y), 15, T.CYAN, bold=True, mono=True)
        if ui.button("lcopy", (x + 72 + T.text_size(room.get("id", "----"), 15, True)[0] + 12,
                               y - 1, 56, 22), "Copy", "normal", size=10, radius=6):
            app.copy_text(str(room.get("id", "")))
        y += 34

        # chat-log 130px
        log_r = pygame.Rect(x, y, r.w - 32, 130)
        T.rect(surf, log_r, (0, 0, 0, 77), 9)
        T.rect(surf, log_r, (255, 255, 255, 13), 9, width=1)
        old = surf.get_clip()
        surf.set_clip(log_r.inflate(-4, -4))
        lines = self.chat_log[-8:]
        ly = log_r.bottom - 8 - len(lines) * 17
        for who, txt in lines:
            T.text(surf, who + ":", (log_r.x + 9, ly), 10.5, T.CYAN, bold=True)
            T.text(surf, txt, (log_r.x + 9 + T.text_size(who + ":", 10.5, True)[0] + 5, ly),
                   10.5, T.TXT)
            ly += 17
        surf.set_clip(old)
        y = log_r.bottom + 8

        # chat input
        self.chat_text, sub = ui.text_input("lchat", (x, y, r.w - 32, 34), self.chat_text,
                                            "Nhắn gì đó...", 140, size=12)
        if sub and self.chat_text.strip():
            app.net.send({"t": "chat", "text": self.chat_text.strip()})
            self.chat_text = ""

    # ---------------- panel kit ----------------
    def _draw_kit(self, surf, ui, r, st):
        app = self.app
        T.panel(surf, r, 16)
        x = r.x + 16
        y = r.y + 14
        T.text(surf, "KIT ĐANG DÙNG", (x, y), 15, T.TXT, bold=True)
        if ui.button("ledit", (r.right - 16 - 110, y - 2, 110, 28), "Chỉnh sửa kit", "primary",
                     size=11, radius=8):
            app.open_kit_editor()
        y += 36

        kit = app.profile.active_kit()
        # lobby-kits: hang nut kit
        kx = x
        for k in app.profile.kits[:8]:
            if kit_btn(surf, ui, "lk" + k["id"], kx, y, k["name"], k["id"] == kit["id"], size=11.5):
                app.profile.set_active(k["id"])
                app.sync_loadout()
                app.sfx.ui()
            kx += T.text_size(k["name"], 11.5)[0] + 30
            if kx > r.right - 60:
                break
        y += 38

        # lks summary
        ch = CHAR_MAP.get(kit["char"], CHARS[0])
        col = hex_rgb(ch["color"])
        # lks-head: avatar 74
        av = pygame.Rect(0, 0, 74, 74)
        av.topleft = (x, y)
        T.rect(surf, av, (*col, 26), 16)
        pygame.draw.rect(surf, (*col, 68), av, 1, border_radius=16)
        T.shape_icon(surf, ch["shape"], col, av.centerx, av.centery, 20, glow_k=60)
        T.text(surf, kit["name"], (x + 88, y + 6), 18, col, bold=True)
        T.text(surf, "%s · %s: %s" % (ch["name"], ch["passiveName"], ch["passiveDesc"]),
               (x + 88, y + 30), 11, T.MUTED)
        y += 88

        sm = build_summary(kit, 100)

        # block 5 chieu
        T.text(surf, "5 CHIÊU", (x, y), 10, T.MUTED, bold=True)
        y += 18
        sx = x
        for i, sid in enumerate(kit["skills"][:5]):
            sk = SKILL_MAP.get(sid)
            if not sk:
                continue
            tw = T.text_size(sk["name"], 11)[0] + 44
            rr = pygame.Rect(sx, y, tw, 26)
            T.rect(surf, rr, (0, 229, 255, 18), 8)
            T.rect(surf, rr, (0, 229, 255, 41), 8, width=1)
            T.text(surf, sk["icon"], (sx + 10, y + 5), 12.5, T.ICE)
            T.text(surf, sk["name"], (sx + 28, y + 6), 11, T.TXT)
            T.text(surf, str(i + 1), (rr.right - 12, y + 7), 9, T.MUTED, align="right")
            sx += tw + 7
            if sx > r.right - 80:
                sx = x
                y += 32
        y += 40

        # block trang bi
        T.text(surf, "TRANG BỊ", (x, y), 10, T.MUTED, bold=True)
        y += 18
        gx = x
        for sl in SLOTS:
            g = GEAR_MAP.get(kit["gear"].get(sl["id"]))
            if not g:
                continue
            tw = T.text_size(sl["name"] + ": " + g["name"], 10.5)[0] + 18
            rr = pygame.Rect(gx, y, tw, 24)
            T.rect(surf, rr, (255, 255, 255, 10), 7)
            T.rect(surf, rr, (255, 255, 255, 15), 7, width=1)
            T.text(surf, sl["name"] + ":", (gx + 9, y + 5), 10.5, T.TXT, bold=True)
            T.text(surf, g["name"], (gx + 9 + T.text_size(sl["name"] + ": ", 10.5, True)[0],
                                     y + 5), 10.5, T.MUTED)
            gx += tw + 7
            if gx > r.right - 80:
                gx = x
                y += 30
        y += 38

        # block chi so: grid 4 cot
        T.text(surf, "CHỈ SỐ", (x, y), 10, T.MUTED, bold=True)
        y += 18
        stats = [("Máu", "%d" % sm["hp"]), ("Sát thương", "×%.2f" % sm["dmgMul"]),
                 ("Tốc chạy", "%.0f" % sm["speed"]), ("Tốc đánh", "×%.2f" % sm["atkspd"]),
                 ("Giáp", "%d%%" % round(sm["armor"] * 100)), ("Hồi chiêu", "×%.2f" % sm["cdr"]),
                 ("Tầm bắn", "×%.2f" % sm["range"]), ("Hồi máu", "%.1f/s" % sm["regen"])]
        cw2 = (r.w - 32 - 21) // 4
        for i, (lab, val) in enumerate(stats):
            cx = x + (i % 4) * (cw2 + 7)
            cy = y + (i // 4) * 44
            T.rect(surf, (cx, cy, cw2, 38), (255, 255, 255, 9), 8)
            T.text(surf, lab, (cx + 9, cy + 6), 9.5, T.MUTED)
            T.text(surf, val, (cx + 9, cy + 19), 12.5, T.TXT, bold=True, mono=True)

        # lobby-tip
        tip_h = 64
        ty = r.bottom - 14 - tip_h
        T.dashed_hline(surf, x, r.right - 16, ty - 10, (255, 255, 255, 18))
        T.text(surf, "ĐIỀU KHIỂN", (x, ty), 9.5, T.CYAN, bold=True)
        T.text(surf, "WASD di chuyển · chuột ngắm · giữ chuột trái bắn ·",
               (x, ty + 18), 10.5, T.MUTED)
        T.text(surf, "1–5 dùng chiêu · Enter chat", (x, ty + 34), 10.5, T.MUTED)

    # ---------------- panel thong tin phong ----------------
    def _draw_roominfo(self, surf, ui, r, room, st, me):
        app = self.app
        T.panel(surf, r, 16)
        x = r.x + 16
        y = r.y + 14
        y = h3(surf, x, y, "THÔNG TIN PHÒNG")

        is_host = me == room.get("hostId")
        mode = MODE_MAP.get(st.get("mode"), MODES[0])
        view_w = r.w - 32

        if not is_host:
            target = ("%d mạng" % st.get("killTarget", 20) if st.get("mode") == "kills"
                      else "%ds" % st.get("timeLimit", 300) if st.get("mode") == "time" else "Sống cuối")
            y = kv_row(surf, x, y, view_w, "Chế độ", mode["name"])
            y = kv_row(surf, x, y, view_w, "Mục tiêu", target)
            y = kv_row(surf, x, y, view_w, "Hồi sinh",
                       "Không" if st.get("mode") == "last" else "%ds" % st.get("respawn", 3))
            y = kv_row(surf, x, y, view_w, "Máu đầu trận", "%d" % st.get("startHp", 100))
            y = kv_row(surf, x, y, view_w, "Tên phòng", str(st.get("name", "?")))
        else:
            # host: chon mode bang chip nho
            T.text(surf, "Chế độ", (x, y + 3), 11.5, T.MUTED)
            mx = x + 70
            for i, m in enumerate(MODES):
                tw = T.text_size(m["name"], 10.5)[0] + 16
                if ui.chip("lmode%d" % i, (mx, y, tw, 22), m["name"], st.get("mode") == m["id"],
                           T.PURPLE, size=10.5):
                    app.admin_settings({"mode": m["id"]})
                mx += tw + 5
                if mx > r.right - 40:
                    mx = x + 70
                    y += 27
            y += 30
            # cac hang input nho
            rows = [("Số mạng", "killTarget", st.get("killTarget", 20), 1, 999),
                    ("Thời gian (s)", "timeLimit", st.get("timeLimit", 300), 30, 3600),
                    ("Hồi sinh (s)", "respawn", st.get("respawn", 3), 0, 30),
                    ("Máu đầu trận", "startHp", st.get("startHp", 100), 50, 500),
                    ("Slot tối đa", "maxPlayers", st.get("maxPlayers", 16), 2, 64)]
            if not hasattr(self, "_vals"):
                self._vals = {}
            for lab, key, val, lo, hi in rows:
                T.text(surf, lab, (x, y + 8), 11.5, T.MUTED)
                iw = 88
                shown = self._vals.get(key)
                if shown is None:
                    shown = str(val)
                v, sub = ui.text_input("lv" + key, (r.right - 16 - iw, y, iw, 26),
                                       shown, "", 4, numeric=True, size=11)
                self._vals[key] = v
                try:
                    nv = int(v)
                except ValueError:
                    nv = val
                if sub and lo <= nv <= hi and nv != st.get(key):
                    app.admin_settings({key: nv})
                T.dashed_hline(surf, x, x + view_w, y + 30, (255, 255, 255, 15))
                y += 35

        # lobby-actions
        ay = r.bottom - 168
        is_ready = next((p.get("ready") for p in room.get("players", []) if p.get("id") == me), False)
        if ui.button("lready", (x, ay, view_w, 38), "Bỏ sẵn sàng" if is_ready else "Sẵn sàng",
                     "normal" if is_ready else "primary", size=13):
            app.net.send({"t": "ready", "ready": not is_ready})
        if is_host:
            if ui.button("lstart", (x, ay + 44, view_w, 40), "Bắt đầu trận", "accent", size=14):
                app.net.send({"t": "start"})
        y2 = ay + (92 if is_host else 46)
        if ui.button("lset", (x, y2, view_w, 34), "Cài đặt", "ghost", size=12):
            app.open_settings()
        if ui.button("lleave", (x, y2 + 40, view_w, 34), "Rời phòng", "ghost", size=12):
            app.ask_confirm("Rời phòng?", "Bạn sẽ trở về Hub và rời khỏi phòng hiện tại.",
                            "Rời phòng", app.leave_room, danger=True)
        T.text(surf, "Chủ phòng có thể sửa luật ở trên trước khi bắt đầu.",
               (x, r.bottom - 26), 10, T.MUTED)


# ============================================================
#  MODAL: settings / help / dialog
# ============================================================
class Modal:
    def __init__(self, app):
        self.app = app

    def handle(self, events, ui, dt):
        return True

    def draw(self, surf, ui, dt):
        pass


class SettingsModal(Modal):
    def draw(self, surf, ui, dt):
        app = self.app
        w, h = surf.get_size()
        draw_modal_dim(surf)
        bw, bh = min(620, w - 40), 420
        box = pygame.Rect((w - bw) // 2, (h - bh) // 2, bw, bh)
        T.panel(surf, box, 16)
        x = box.x + 26
        y = box.y + 22
        T.text(surf, "Cài đặt", (x, y), 19, T.TXT, bold=True)
        if ui.icon_button("stx", (box.right - 48, box.y + 16, 32, 32), "✕", size=15):
            app.close_modal()
        y += 52

        s = app.profile.settings
        vol = ui.slider("stvol", (box.right - 26 - 220, y, 220, 30), s["volume"], 0, 1, 0.05,
                        lambda v2: "%d%%" % round(v2 * 100))
        T.text(surf, "Âm lượng", (x, y + 2), 12.5, T.TXT, bold=True)
        T.text(surf, "Tiếng bắn, nổ, va chạm", (x, y + 20), 11, T.MUTED)
        if abs(vol - s["volume"]) > 0.001:
            s["volume"] = vol
            app.sfx.set_volume(vol)
            app.profile.save()
        y += 48

        for key, label, desc in (
            ("particles", "Hiệu ứng hạt", "Tắt để tăng FPS trên máy yếu"),
            ("glow", "Ánh sáng / glow", "Tắt để nhẹ máy hơn nhiều"),
            ("shake", "Rung màn hình", "Rung khi bị đánh hoặc có vụ nổ gần"),
            ("fps", "Hiện FPS", "Góc trên màn hình"),
        ):
            T.text(surf, label, (x, y + 2), 12.5, T.TXT, bold=True)
            T.text(surf, desc, (x, y + 20), 11, T.MUTED)
            nv = ui.toggle("st" + key, (box.right - 26 - 46, y + 4, 46, 26), bool(s[key]))
            if nv != s[key]:
                s[key] = nv
                app.profile.save()
                app.apply_settings()
            T.dashed_hline(surf, x, box.right - 26, y + 44, (255, 255, 255, 18))
            y += 52

        if ui.button("streset", (x, box.bottom - 58, 150, 34), "Đặt lại", "danger", size=12):
            app.ask_confirm("Đặt lại kit?", "Toàn bộ kit sẽ bị xoá và thay bằng 3 kit mặc định.",
                            "Đặt lại", app.reset_kits, danger=True)
        T.text(surf, "Đưa profile về 3 kit mặc định", (x + 162, box.bottom - 47), 11, T.MUTED)


class HelpModal(Modal):
    def draw(self, surf, ui, dt):
        app = self.app
        w, h = surf.get_size()
        draw_modal_dim(surf)
        bw, bh = min(880, w - 40), min(500, h - 40)
        box = pygame.Rect((w - bw) // 2, (h - bh) // 2, bw, bh)
        T.panel(surf, box, 16)
        x = box.x + 28
        y = box.y + 22
        T.text(surf, "Hướng dẫn", (x, y), 19, T.TXT, bold=True)
        if ui.icon_button("hpx", (box.right - 48, box.y + 16, 32, 32), "✕", size=15):
            app.close_modal()
        y += 54

        colw = (bw - 56 - 44) // 3

        def col_block(cx, cy, title, lines):
            T.text(surf, title, (cx, cy), 11.5, T.CYAN, bold=True)
            cy += 22
            for ln in lines:
                T.text(surf, "▸", (cx, cy), 10.5, T.PURPLE)
                for j, part in enumerate(T.wrap(ln, 10.5, colw - 18)):
                    T.text(surf, part, (cx + 14, cy), 10.5, T.MUTED)
                    cy += 15
                cy += 3
            return cy

        y1 = col_block(x, y, "ĐIỀU KHIỂN", [
            "WASD hoặc phím mũi tên: di chuyển",
            "Chuột: ngắm, giữ chuột trái: đánh thường",
            "1 2 3 4 5: dùng 5 chiêu đã chọn",
            "Enter: chat · ESC: đóng chat / rời trận",
        ])
        y1 = col_block(x, y1 + 8, "KIT & LUẬT CHƠI", [
            "Ở Hub, mỗi người tự tạo và chọn kit của mình.",
            "Mỗi kit: nhân vật + 5 trang bị + 5 chiêu + 10 điểm chỉ số.",
            "35 chiêu, trộn cận chiến và tầm xa tuỳ thích.",
            "Núp trong bụi cỏ thì người ở xa không thấy bạn.",
        ])

        x2 = x + colw + 22
        y2 = col_block(x2, y, "CHƠI QUA IP", [
            "Cách 1: chủ phòng bấm Vào game (tạo phòng), bạn bè nhập IP:port rồi bấm Nối.",
            "Cách 2: tạo phòng ở màn Tạo phòng.",
            "Dùng Radmin VPN / Hamachi nếu không mở port được.",
        ])
        y2 = col_block(x2, y2 + 8, "TRONG TRẬN", [
            "Chủ phòng chọn luật: số mạng / thời gian / sống sót cuối.",
            "Bị hạ vẫn xem được trận (spectator) ở chế độ thường.",
            "Q/E đổi người xem khi đang spectate.",
        ])

        x3 = x2 + colw + 22
        y3 = col_block(x3, y, "MẸO", [
            "Mở thêm NeonClash.exe để test nhiều client trên 1 máy.",
            "Giữ chuột trái để bắn liên tục.",
            "Đổi kit bất cứ lúc nào ở Hub hoặc phòng chờ.",
        ])
        if ui.button("hpok", (box.right - 130, box.bottom - 54, 104, 34), "Đã hiểu", "primary", size=12):
            app.close_modal()


class RoomsModal(Modal):
    """Tuong thich: dung RoomsScreen thay the — nhung giu lop nay de app cu khong lo."""

    def draw(self, surf, ui, dt):
        app = self.app
        app.set_screen("rooms")
        app.close_modal()


class RoomOptions(Modal):
    """Tuy chon phong — da thay bang man hinh CreateRoom; giu de tuong thich."""

    def draw(self, surf, ui, dt):
        app = self.app
        app.set_screen("create")
        app.close_modal()


class RoomInfo(Modal):
    """Chu phong sua ten / mat khau / so nguoi khi dang trong phong cho."""

    def __init__(self, app):
        super().__init__(app)
        st = (app.room or {}).get("settings", {})
        self.name = str(st.get("name") or "Phòng")
        self.password = str(st.get("password") or "")

    def draw(self, surf, ui, dt):
        app = self.app
        w, h = surf.get_size()
        draw_modal_dim(surf)
        box = pygame.Rect((w - 460) // 2, (h - 330) // 2, 460, 330)
        T.panel(surf, box, 16)
        x = box.x + 26
        y = box.y + 22
        T.text(surf, "Thông tin phòng", (x, y), 17, T.TXT, bold=True)
        if ui.icon_button("rix", (box.right - 46, box.y + 14, 30, 30), "✕", size=14):
            app.close_modal()
        y += 50
        y2 = y + 22
        T.text(surf, "TÊN PHÒNG", (x, y + 6), 10.5, T.MUTED)
        self.name, _ = ui.text_input("riname", (x, y2, box.w - 52, 38), self.name, "Phòng", 28)
        y += 66
        y2 = y + 22
        T.text(surf, "MẬT KHẨU (ĐỂ TRỐNG = AI CŨNG VÀO ĐƯỢC)", (x, y + 6), 10.5, T.MUTED)
        self.password, _ = ui.text_input("ripass", (x, y2, box.w - 52, 38), self.password,
                                         "không có", 16, password=True)
        if ui.button("riok", (box.right - 244, box.bottom - 58, 104, 38), "Lưu", "primary", size=12):
            app.admin_settings({"name": self.name.strip() or "Phòng",
                                "password": self.password[:16]})
            app.close_modal()
            app.toast("Đã cập nhật phòng.")
        if ui.button("ricancel", (box.right - 130, box.bottom - 58, 104, 38), "Đóng", "ghost", size=12):
            app.close_modal()


class Dialog(Modal):
    def __init__(self, app, title, message="", value="", on_ok=None, on_cancel=None,
                 ok_label="OK", cancel_label="Huỷ", numeric=False, password=False, confirm_only=False):
        super().__init__(app)
        self.title = title
        self.message = message
        self.value = value
        self.on_ok = on_ok
        self.on_cancel = on_cancel
        self.ok_label = ok_label
        self.cancel_label = cancel_label
        self.numeric = numeric
        self.password = password
        self.confirm_only = confirm_only
        self.done = False
        self.focused_once = False

    def handle(self, events, ui, dt):
        for e in events:
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                self._cancel()
                return False
        return True

    def _cancel(self):
        if self.done:
            return
        self.done = True
        if self.on_cancel:
            self.on_cancel()
        self.app.close_modal()

    def _ok(self):
        if self.done:
            return
        self.done = True
        cb = self.on_ok
        val = self.value
        self.app.close_modal()
        if cb:
            cb(val)

    def draw(self, surf, ui, dt):
        w, h = surf.get_size()
        draw_modal_dim(surf, 190)
        bh = 224 if not self.confirm_only else 196
        box = pygame.Rect((w - 430) // 2, (h - bh) // 2, 430, bh)
        T.panel(surf, box, 16)
        x = box.x + 22
        y = box.y + 20
        T.text(surf, self.title, (x, y), 15, T.TXT, bold=True)
        if self.message:
            for j, line in enumerate(T.wrap(self.message, 11, box.w - 44)[:3]):
                T.text(surf, line, (x, y + 26 + j * 16), 11, T.MUTED)
        if not self.confirm_only:
            if not self.focused_once:
                ui.focus = "dlgin"
                self.focused_once = True
            self.value, sub = ui.text_input("dlgin", (x, box.y + 96, box.w - 44, 40),
                                            self.value, "", 60, numeric=self.numeric,
                                            password=self.password)
            if sub:
                self._ok()
        if ui.button("dlgok", (box.right - 216, box.bottom - 58, 98, 38), self.ok_label, "primary", size=12):
            self._ok()
        if ui.button("dlgcancel", (box.right - 110, box.bottom - 58, 88, 38), self.cancel_label,
                     "ghost", size=12):
            self._cancel()
