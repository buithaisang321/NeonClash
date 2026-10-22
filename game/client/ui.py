"""Widget giao dien kieu immediate-mode — style lay 1-1 tu style.css ban Edge."""
import math
import time

import pygame

from . import theme as T


class UI:
    def __init__(self):
        self.mouse = (0, 0)
        self.click = None          # (x, y) neu vua bam chuot trai
        self.wheel = 0
        self.keys = []             # danh sach KEYDOWN trong frame
        self.focus = None          # key cua o nhap dang focus
        self.anim = {}
        self.scroll = {}
        self.t = 0.0
        self.caret_t = 0.0
        self.blocked = False

    # ---------------- vong frame ----------------
    def begin(self, events, dt):
        self.click = None
        self.wheel = 0
        self.keys = []
        self.t += dt
        self.caret_t += dt
        for e in events:
            if e.type == pygame.MOUSEMOTION:
                self.mouse = e.pos
            elif e.type == pygame.MOUSEBUTTONDOWN:
                if e.button == 1:
                    self.mouse = e.pos
                    self.click = e.pos
                elif e.button == 4:
                    self.wheel = 1
                elif e.button == 5:
                    self.wheel = -1
            elif e.type == pygame.KEYDOWN:
                self.keys.append(e)

    def end(self):
        # click khong roi vao o nhap nao -> bo focus
        if self.click is not None:
            self.focus = None

    def _hover(self, r):
        if self.blocked:
            return False
        x, y = self.mouse
        return r[0] <= x < r[0] + r[2] and r[1] <= y < r[1] + r[3]

    def _anim(self, key, target, speed=12.0, dt=1 / 60):
        v = self.anim.get(key, 0.0)
        v += (target - v) * min(1.0, speed * dt)
        self.anim[key] = v
        return v

    def _take_click(self, r):
        if self.blocked:
            return False
        if self.click and self._hover(r):
            self.click = None
            return True
        return False

    def hovered(self, r):
        return self._hover(r)

    # ---------------- nut (.btn cua CSS) ----------------
    def button(self, key, r, label, kind="normal", enabled=True, size=14, icon=None, radius=10):
        r = pygame.Rect(r)
        hov = self._hover(r) and enabled
        press = hov and pygame.mouse.get_pressed()[0]
        clicked = enabled and self._take_click(r)
        h = self._anim(key, 1.0 if hov else 0.0)
        dst = pygame.display.get_surface()

        # .btn: padding 12 18, radius 10, bg rgba(255,255,255,.055), border line
        # CSS .btn:hover{transform:translateY(-1px)} — ap dung cho moi loai
        y_off = 1 if press else (-1 if hov else 0)
        fill_a = int(14 + h * 12)          # .055 -> .1
        border = T.mix(T.LINE, T.LINE_HI, h)
        txt_col = T.TXT
        grad = None

        if kind == "primary":
            # linear-gradient(120deg,#6c5ce7,#8b5cf6), hover brightness 1.12
            g1 = T.mix(T.PURPLE, T.WHITE, h * 0.12)
            g2 = T.mix(T.PURPLE_HI, T.WHITE, h * 0.12)
            grad = T.rounded_hgrad(r.w, r.h, g1, g2, radius)
            border = None
            txt_col = T.WHITE
        elif kind == "accent":
            # linear-gradient(120deg,#ff2d6f,#ff7a3d)
            g1 = T.mix(T.ACCENT, T.WHITE, h * 0.10)
            g2 = T.mix(T.ORANGE, T.WHITE, h * 0.10)
            grad = T.rounded_hgrad(r.w, r.h, g1, g2, radius)
            border = None
            txt_col = T.WHITE
        elif kind == "danger":
            # .btn.danger: chu #ff8ba7, vien line; hover nen do nhat + vien do
            txt_col = T.mix(T.PINK, T.WHITE, h * 0.4)
            fill_a = int(14 * (1 - h)) + int(h * 40)   # hover bg rgba(255,45,111,.16)
            border = T.mix(T.LINE, (255, 45, 111), h * 0.8)
        elif kind == "ghost":
            # .btn.ghost: trong suot, chu muted -> hover chu sang
            txt_col = T.mix(T.MUTED, T.TXT, h)
            fill_a = int(10 * h)

        rr = pygame.Rect(r.x, r.y + y_off, r.w, r.h)

        if not enabled:
            if grad is not None:
                grad = grad.copy()
                grad.set_alpha(115)
            fill_a = int(fill_a * 0.45)
            txt_col = T.DIM

        if grad is not None:
            dst.blit(grad, rr.topleft)
        elif fill_a > 0:
            s = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
            if kind == "danger" and h > 0.05:
                pygame.draw.rect(s, (255, 45, 111, fill_a), s.get_rect(), border_radius=radius)
            else:
                pygame.draw.rect(s, (255, 255, 255, fill_a), s.get_rect(), border_radius=radius)
            dst.blit(s, rr.topleft)
        if border is not None:
            if len(border) == 4:
                T.rect(dst, rr, border, radius, width=1)
            else:
                pygame.draw.rect(dst, border, rr, width=1, border_radius=radius)

        # box-shadow cho primary/accent
        if kind == "primary" and enabled:
            T.glow(dst, (r.centerx, r.bottom + 2), max(18, r.w // 2), T.PURPLE, 40)
        elif kind == "accent" and enabled:
            T.glow(dst, (r.centerx, r.bottom + 2), max(18, r.w // 2), T.ACCENT, 36)

        tw, th = T.text_size(label, size, kind in ("primary", "accent"))
        tx = rr.centerx - tw // 2
        if icon:
            iw, _ = T.text_size(icon, size + 2, False)
            total = iw + 6 + tw
            tx = rr.centerx - total // 2 + iw + 6
            T.text(dst, icon, (rr.centerx - total // 2, rr.centery - th // 2 - 1), size + 2, txt_col)
        T.text(dst, label, (tx, rr.centery - th // 2 - 1), size, txt_col,
               bold=kind in ("primary", "accent"))
        return clicked

    def icon_button(self, key, r, glyph, kind="ghost", size=17, color=None, radius=8):
        r = pygame.Rect(r)
        hov = self._hover(r)
        clicked = self._take_click(r)
        h = self._anim(key, 1.0 if hov else 0.0)
        dst = pygame.display.get_surface()
        if hov:
            s = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
            pygame.draw.rect(s, (255, 255, 255, 14), s.get_rect(), border_radius=radius)
            dst.blit(s, r.topleft)
        col = color or T.mix(T.MUTED, T.WHITE, h)
        T.text(dst, glyph, (r.centerx, r.centery - size // 2 - 1), size, col, align="center")
        return clicked

    # ---------------- o nhap (.field input) ----------------
    def text_input(self, key, r, value, placeholder="", maxlen=24, size=14,
                   numeric=False, password=False, icon=None, mono=False):
        r = pygame.Rect(r)
        hov = self._hover(r)
        clicked = self._take_click(r)
        if clicked:
            self.focus = key
        focused = self.focus == key
        val = str(value)
        submitted = False

        if focused:
            for e in self.keys:
                if e.key == pygame.K_BACKSPACE:
                    val = val[:-1]
                elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    submitted = True
                elif e.key == pygame.K_ESCAPE:
                    self.focus = None
                elif e.unicode and e.unicode.isprintable():
                    ch = e.unicode
                    if numeric and not (ch.isdigit() or ch in ".:"):
                        continue
                    if len(val) < maxlen:
                        val += ch
            self.keys = []

        dst = pygame.display.get_surface()
        # .field input: bg rgba(255,255,255,.04), border line, radius 10
        s = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
        pygame.draw.rect(s, (255, 255, 255, 10), s.get_rect(), border_radius=10)
        if focused:
            # focus: bg rgba(0,229,255,.05)
            pygame.draw.rect(s, (0, 229, 255, 13), s.get_rect(), border_radius=10)
        dst.blit(s, r.topleft)
        if focused:
            # box-shadow: 0 0 0 3px rgba(0,229,255,.12)
            ring_s = pygame.Surface((r.w + 6, r.h + 6), pygame.SRCALPHA)
            pygame.draw.rect(ring_s, (0, 229, 255, 30), ring_s.get_rect(), width=3, border_radius=12)
            dst.blit(ring_s, (r.x - 3, r.y - 3))
            border = T.CYAN
        elif hov:
            border = T.LINE_HI
        else:
            border = T.LINE
        pygame.draw.rect(dst, border, r, width=1, border_radius=10)

        pad = 14
        tx = r.x + pad
        if icon:
            T.text(dst, icon, (tx, r.centery - size // 2 - 1), size, T.DIM)
            tx += T.text_size(icon, size)[0] + 8

        shown = ("•" * len(val)) if password else val
        if shown:
            tw, th = T.text_size(shown, size, mono=mono)
            clip = dst.get_clip()
            dst.set_clip(pygame.Rect(tx, r.y, r.w - (tx - r.x) - 8, r.h))
            T.text(dst, shown, (tx, r.centery - th // 2 - 1), size, T.TXT, mono=mono)
            dst.set_clip(clip)
            cx = tx + min(tw, r.w - (tx - r.x) - 12)
        else:
            T.text(dst, placeholder, (tx, r.centery - size // 2 - 1), size, T.DIM)
            cx = tx
        if focused and int(self.caret_t * 2) % 2 == 0:
            pygame.draw.line(dst, T.CYAN, (cx + 1, r.centery - size // 2), (cx + 1, r.centery + size // 2), 2)

        return val, submitted

    # ---------------- slider (dung cho host chinh luat) ----------------
    def slider(self, key, r, value, lo, hi, step=1, fmt=None, label=None):
        r = pygame.Rect(r)
        hov = self._hover(r)
        dragging = hov and pygame.mouse.get_pressed()[0]
        if dragging:
            t = T.clamp((self.mouse[0] - r.x) / max(1, r.w), 0, 1)
            raw = lo + (hi - lo) * t
            value = round(raw / step) * step if step else raw
            value = T.clamp(value, lo, hi)
        dst = pygame.display.get_surface()
        track_y = r.y + r.h - 12
        T.rect(dst, (r.x, track_y, r.w, 5), (30, 36, 56), 3)
        t = (value - lo) / max(1e-6, (hi - lo))
        T.rect(dst, (r.x, track_y, int(r.w * t), 5), T.CYAN if hov or dragging else (0, 170, 195), 3)
        kx = r.x + int(r.w * t)
        T.glow(dst, (kx, track_y + 2), 14, T.CYAN, 60 if (hov or dragging) else 30)
        pygame.draw.circle(dst, T.WHITE, (kx, track_y + 2), 6)
        if label:
            T.text(dst, label, (r.x, r.y - 2), 11, T.MUTED)
        shown = fmt(value) if fmt else str(value)
        T.text(dst, shown, (r.right, r.y - 2), 12, T.TXT, align="right", bold=True, mono=True)
        return value

    # ---------------- cong tac (.switch cua CSS) ----------------
    def toggle(self, key, r, value):
        r = pygame.Rect(r)
        clicked = self._take_click(r)
        dst = pygame.display.get_surface()
        h = self._anim("sw" + key, 1.0 if value else 0.0)
        # off: bg rgba(255,255,255,.12) border line; on: gradient cyan->purple
        s = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
        if h < 0.02:
            pygame.draw.rect(s, (255, 255, 255, 30), s.get_rect(), border_radius=r.h // 2)
            pygame.draw.rect(s, T.LINE, s.get_rect(), 1, border_radius=r.h // 2)
        else:
            grad = T.rounded_hgrad(r.w, r.h, T.CYAN, T.PURPLE, r.h // 2)
            dst.blit(grad, r.topleft)
            T.glow(dst, (r.centerx, r.centery), r.w // 2, T.CYAN, int(40 * h))
        dst.blit(s, r.topleft)
        kx = r.x + 3 + int((r.w - r.h) * h) + r.h // 2 - 3
        pygame.draw.circle(dst, T.WHITE if h > 0.5 else T.MUTED, (kx, r.centery), r.h // 2 - 4)
        return (not value) if clicked else value

    # ---------------- tab (.tab cua CSS) ----------------
    def tabs(self, key, r, items, active, size=13):
        """items: list (id, label). Tra ve id duoc bam hoac None."""
        r = pygame.Rect(r)
        dst = pygame.display.get_surface()
        x = r.x
        picked = None
        for i, (tid, label) in enumerate(items):
            tw, _ = T.text_size(label, size, False)
            w = tw + 28
            rr = pygame.Rect(x, r.y, w, r.h)
            hov = self._hover(rr)
            if self._take_click(rr):
                picked = tid
            is_active = tid == active
            if is_active:
                # .tab.active: bg rgba(108,92,231,.22), border rgba(108,92,231,.5)
                s = pygame.Surface((rr.w, rr.h), pygame.SRCALPHA)
                pygame.draw.rect(s, (108, 92, 231, 56), s.get_rect(), border_radius=8)
                dst.blit(s, rr.topleft)
                T.rect(dst, rr, (108, 92, 231, 128), 8, width=1)
            elif hov:
                s = pygame.Surface((rr.w, rr.h), pygame.SRCALPHA)
                pygame.draw.rect(s, (255, 255, 255, 9), s.get_rect(), border_radius=8)
                dst.blit(s, rr.topleft)
            else:
                s = pygame.Surface((rr.w, rr.h), pygame.SRCALPHA)
                pygame.draw.rect(s, (255, 255, 255, 9), s.get_rect(), border_radius=8)
                dst.blit(s, rr.topleft)
            col = T.WHITE if is_active else (T.TXT if hov else T.MUTED)
            T.text(dst, label, (rr.centerx, rr.centery - size // 2 - 1), size, col,
                   align="center", bold=False)
            x += w + 6
        return picked

    # ---------------- chip (.chip pill) ----------------
    def chip(self, key, r, label, active=False, color=T.CYAN, size=12):
        r = pygame.Rect(r)
        hov = self._hover(r)
        clicked = self._take_click(r)
        dst = pygame.display.get_surface()
        if active:
            # .chip.active: bg rgba(108,92,231,.25), border rgba(108,92,231,.6)
            s = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
            pygame.draw.rect(s, (108, 92, 231, 64), s.get_rect(), border_radius=r.h // 2)
            dst.blit(s, r.topleft)
            T.rect(dst, r, (108, 92, 231, 153), r.h // 2, width=1)
            col = T.WHITE
        else:
            s = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
            pygame.draw.rect(s, (255, 255, 255, 10 if hov else 10), s.get_rect(), border_radius=r.h // 2)
            dst.blit(s, r.topleft)
            pygame.draw.rect(dst, T.LINE_HI if hov else T.LINE, r, width=1, border_radius=r.h // 2)
            col = T.TXT if hov else T.MUTED
        T.text(dst, label, (r.centerx, r.centery - size // 2 - 1), size, col, align="center")
        return clicked

    # ---------------- vung cuon ----------------
    def scroll_area(self, key, r, content_h):
        r = pygame.Rect(r)
        off = self.scroll.get(key, 0)
        max_off = max(0, content_h - r.h)
        if self._hover(r) and self.wheel:
            off -= self.wheel * 64
            self.wheel = 0
        off = T.clamp(off, 0, max_off)
        self.scroll[key] = off
        if max_off > 0:
            bar_h = max(28, int(r.h * r.h / max(1, content_h)))
            bar_y = r.y + int((r.h - bar_h) * (off / max_off))
            # scrollbar thumb rgba(120,140,255,.22)
            T.rect(pygame.display.get_surface(), (r.right - 5, bar_y, 3, bar_h), (52, 62, 100), 2)
        return off, max_off

    def wheel_in(self, r):
        return self._hover(r) and self.wheel

    # ---------------- thanh tien trinh ----------------
    def bar(self, r, t, color=T.CYAN, bg=(28, 35, 54), h=None):
        r = pygame.Rect(r)
        T.rect(pygame.display.get_surface(), r, bg, r.h // 2)
        w = int(r.w * T.clamp(t, 0, 1))
        if w > 0:
            T.rect(pygame.display.get_surface(), (r.x, r.y, w, r.h), color, r.h // 2)
