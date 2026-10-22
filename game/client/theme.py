"""Theme: bang mau + font + helper ve — lay 1-1 tu style.css ban Edge."""
import os
import pygame
import pygame.freetype

# ---------------- bang mau (chinh xac tu CSS) ----------------
BG      = (6, 7, 12)        # --bg #06070c
BG2     = (10, 12, 20)      # --bg2 #0a0c14
PANEL   = (15, 18, 32)      # --panel-solid #0f1220
PANEL_A = 224               # alpha .88 cua --panel
PANEL_HI = (24, 30, 50)
PANEL_LO = (11, 14, 24)
LINE    = (34, 40, 72)      # rgba(120,140,255,.18) tren panel
LINE_HI = (56, 65, 118)     # rgba(120,140,255,.38)
TXT     = (232, 236, 255)   # --txt #e8ecff
MUTED   = (139, 147, 181)   # --muted #8b93b5
DIM     = (110, 118, 152)
CYAN    = (0, 229, 255)     # --p2 #00e5ff
PURPLE  = (108, 92, 231)    # --p1 #6c5ce7
PURPLE_HI = (139, 92, 246)  # #8b5cf6
LAVENDER = (159, 139, 255)  # #9f8bff
GREEN   = (61, 220, 151)    # --ok #3ddc97
RED     = (255, 92, 122)
ACCENT  = (255, 45, 111)    # --accent #ff2d6f
ORANGE  = (255, 122, 61)    # #ff7a3d
YELLOW  = (255, 182, 72)    # --warn #ffb648
PINK    = (255, 139, 167)   # #ff8ba7
ICE     = (142, 240, 255)   # #8ef0ff
WHITE   = (255, 255, 255)
P1_TINT = (20, 24, 42)      # nen chan cho tint mau nhat

_FONT_DIRS = [
    os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts"),
    "/usr/share/fonts/truetype/dejavu",
    "/Library/Fonts",
]
_REG = ["segoeui.ttf", "SegoeUI.ttf", "arial.ttf", "DejaVuSans.ttf", "Helvetica.ttc"]
_BOLD = ["segoeuib.ttf", "SegoeUIBold.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf", "Helvetica.ttc"]
_MONO = ["consola.ttf", "Consolas.ttf", "DejaVuSansMono.ttf"]
_MONO_B = ["consolab.ttf", "ConsolasBold.ttf", "DejaVuSansMono-Bold.ttf"]


def _find(names):
    for d in _FONT_DIRS:
        for n in names:
            p = os.path.join(d, n)
            if os.path.exists(p):
                return p
    return None


class Fonts:
    def __init__(self):
        self.reg_path = _find(_REG)
        self.bold_path = _find(_BOLD) or self.reg_path
        self.sym_path = _find(["seguisym.ttf", "SegoeUISymbol.ttf", "DejaVuSans.ttf"]) or self.reg_path
        self.mono_path = _find(_MONO)
        self.monob_path = _find(_MONO_B) or self.mono_path
        self.cache = {}
        self.sym_cache = {}
        self.mono_cache = {}

    def get(self, size, bold=False):
        key = (int(size), bool(bold))
        f = self.cache.get(key)
        if f is None:
            path = self.bold_path if bold else self.reg_path
            try:
                f = pygame.freetype.Font(path, int(size)) if path else pygame.freetype.SysFont(None, int(size))
            except Exception:
                f = pygame.freetype.SysFont(None, int(size))
            f.antialiased = True
            f.kerning = True
            self.cache[key] = f
        return f

    def sym(self, size):
        key = int(size)
        f = self.sym_cache.get(key)
        if f is None:
            try:
                f = pygame.freetype.Font(self.sym_path, key) if self.sym_path else pygame.freetype.SysFont(None, key)
            except Exception:
                f = pygame.freetype.SysFont(None, key)
            f.antialiased = True
            self.sym_cache[key] = f
        return f

    def mono(self, size, bold=False):
        key = (int(size), bool(bold))
        f = self.mono_cache.get(key)
        if f is None:
            path = self.monob_path if bold else self.mono_path
            try:
                f = pygame.freetype.Font(path, int(size)) if path else pygame.freetype.SysFont(None, int(size))
            except Exception:
                f = pygame.freetype.SysFont(None, int(size))
            f.antialiased = True
            self.mono_cache[key] = f
        return f


fonts = None
_text_cache = {}
_TEXT_CAP = 3000
_glyph_cache = {}


def init():
    global fonts
    if fonts is None:
        fonts = Fonts()


def font(size, bold=False):
    return fonts.get(size, bold)


def symbol_font(size):
    return fonts.sym(size)


def mono_font(size, bold=False):
    return fonts.mono(size, bold)


def _glyph_ok(f, ch):
    """Kiem tra font co that su ve duoc ky tu nay (khong phai o vuong)."""
    key = (id(f), ch)
    v = _glyph_cache.get(key)
    if v is None:
        if ch in " \t\n":
            v = True
        else:
            try:
                nf, _ = f.render("\ue123", (255, 255, 255))
                cf, _ = f.render(ch, (255, 255, 255))
                if nf.get_width() == cf.get_width() and nf.get_height() == cf.get_height():
                    v = pygame.image.tostring(cf, "RGBA") != pygame.image.tostring(nf, "RGBA")
                else:
                    v = True
            except Exception:
                v = True
        _glyph_cache[key] = v
    return v


def _runs(s, size, bold, mono=False):
    """Tach chuoi thanh cac doan cung mot font (co fallback cho icon)."""
    f = mono_font(size, bold) if mono else font(size, bold)
    sym = symbol_font(size)
    runs = []
    cur_f = None
    cur = ""
    for ch in s:
        use = f if _glyph_ok(f, ch) else sym
        if cur_f is None or use is cur_f:
            cur += ch
            cur_f = use
        else:
            runs.append((cur_f, cur))
            cur = ch
            cur_f = use
    if cur:
        runs.append((cur_f, cur))
    return runs


def _run_width(f, s):
    try:
        return f.get_rect(s).width
    except Exception:
        return len(s) * 7


def text_size(s, size, bold=False, mono=False):
    s = str(s or " ")
    key = ("sz", s, int(size), bool(bold), bool(mono))
    v = _text_cache.get(key)
    if v is not None:
        return v
    w = 0
    h = int(size * 1.25)
    for f, run in _runs(s, size, bold, mono):
        w += _run_width(f, run)
        try:
            h = max(h, f.get_rect(run).height)
        except Exception:
            pass
    v = (w, h)
    if len(_text_cache) > _TEXT_CAP:
        _text_cache.clear()
    _text_cache[key] = v
    return v


def _render(s, size, color, bold, mono=False):
    key = (s, int(size), color, bool(bold), bool(mono))
    surf = _text_cache.get(key)
    if surf is None:
        runs = _runs(s, size, bold, mono)
        if len(runs) == 1:
            f, run = runs[0]
            surf, _ = f.render(run, color)
        else:
            widths = []
            h = 1
            for f, run in runs:
                r = f.get_rect(run)
                widths.append(r.width)
                h = max(h, r.height)
            surf = pygame.Surface((max(1, sum(widths)), h), pygame.SRCALPHA)
            x = 0
            for (f, run), w in zip(runs, widths):
                s2, _ = f.render(run, color)
                surf.blit(s2, (x, 0))
                x += w
        if len(_text_cache) > _TEXT_CAP:
            _text_cache.clear()
        _text_cache[key] = surf
    return surf


def text(dst, s, pos, size=15, color=TXT, bold=False, align="left", alpha=255,
         shadow=False, mono=False):
    if s is None:
        return 0
    s = str(s)
    surf = _render(s, size, color, bold, mono)
    x, y = pos
    w, h = surf.get_size()
    if align == "center":
        x -= w // 2
    elif align == "right":
        x -= w
    if shadow:
        sh = _render(s, size, (0, 0, 0), bold, mono).copy()
        sh.set_alpha(120)
        dst.blit(sh, (x + 1, y + 2))
    if alpha < 255:
        surf = surf.copy()
        surf.set_alpha(alpha)
    dst.blit(surf, (x, y))
    return w


def text_glow(dst, s, pos, size=15, color=CYAN, bold=True, align="left", strength=90):
    """Tieu de co quang sang."""
    w, h = text_size(s, size, bold)
    x, y = pos
    if align == "center":
        x -= w // 2
    elif align == "right":
        x -= w
    glow = _render(s, size, color, bold).copy()
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (-2, 0), (2, 0)):
        glow.set_alpha(strength)
        dst.blit(glow, (x + dx, y + dy))
    dst.blit(_render(s, size, color, bold), (x, y))
    return w


# ---------------- chu gradient (logo) ----------------
_gt_cache = {}


def _stops_gradient(w, stops):
    """stops: [(t, (r,g,b)), ...] tang dan theo t."""
    surf = pygame.Surface((max(1, w), 1))
    seg = 0
    for x in range(w):
        t = x / max(1, w - 1)
        while seg < len(stops) - 2 and t > stops[seg + 1][0]:
            seg += 1
        t0, c0 = stops[seg]
        t1, c1 = stops[seg + 1]
        k = 0 if t1 <= t0 else T_clamp((t - t0) / (t1 - t0), 0, 1)
        surf.set_at((x, 0), lerp_color(c0, c1, k))
    return surf


def T_clamp(v, a, b):
    return a if v < a else (b if v > b else v)


def grad_text(dst, s, pos, size, stops, bold=True, ls=0, align="left", alpha=255):
    """Chu voi doGradient ngang (nhu -webkit-background-clip:text)."""
    s = str(s)
    stops = tuple((float(t), tuple(c)) for t, c in stops)
    key = (s, int(size), stops, bool(bold), int(ls))
    surf = _gt_cache.get(key)
    if surf is None:
        f = font(size, bold)
        widths = []
        for ch in s:
            if _glyph_ok(f, ch):
                widths.append(_run_width(f, ch))
            else:
                widths.append(_run_width(symbol_font(size), ch))
        tw = sum(widths) + max(0, len(s) - 1) * ls
        mask = pygame.Surface((max(1, tw), int(size * 1.5)), pygame.SRCALPHA)
        x = 0
        for ch, w in zip(s, widths):
            fo = f if _glyph_ok(f, ch) else symbol_font(size)
            cs, _ = fo.render(ch, (255, 255, 255))
            mask.blit(cs, (x, 0))
            x += w + ls
        # gradient keo dai full chieu cao, roi nhan voi alpha cua chu
        grad = pygame.transform.smoothscale(_stops_gradient(max(1, tw), stops),
                                            (max(1, tw), mask.get_height())).convert_alpha()
        out = grad.copy()
        out.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        if len(_gt_cache) > 200:
            _gt_cache.clear()
        _gt_cache[key] = out
    surf = _gt_cache[key]
    x, y = pos
    w, h = surf.get_size()
    if align == "center":
        x -= w // 2
    elif align == "right":
        x -= w
    if alpha < 255:
        surf = surf.copy()
        surf.set_alpha(alpha)
    dst.blit(surf, (x, y))
    return w


def logo(dst, pos, size=38, inline=True, align="left", alpha=255):
    """Logo NEON CLASH giong CSS .logo (gradient + letter-spacing)."""
    ls = int(size * 0.14)
    stops = [(0.0, WHITE), (0.4, LAVENDER), (0.7, CYAN), (1.0, WHITE)]
    w = grad_text(dst, "NEON", pos, size, stops, bold=True, ls=ls, align=align, alpha=alpha)
    x = pos[0]
    if align == "center":
        x -= w // 2
    elif align == "right":
        x -= w
    sub = int(size * 0.55)
    sub_ls = int(sub * 0.3)
    if inline:
        # "CLASH" cung hang, chu trang co letter-spacing nhu .logo span
        w2 = grad_text(dst, "CLASH", (x + w + int(size * 0.26), pos[1] + int(size * 0.18)),
                       sub, [(0.0, WHITE), (1.0, WHITE)], bold=True, ls=sub_ls,
                       align="left", alpha=int(alpha * 0.9))
        return w + int(size * 0.26) + w2
    # xuong dong
    grad_text(dst, "CLASH", (x + w // 2, pos[1] + int(size * 1.02)), sub,
              [(0.0, WHITE), (1.0, WHITE)], bold=True, ls=sub_ls,
              align="center", alpha=int(alpha * 0.9))
    return w


# ---------------- helpers co ban ----------------
def fit(s, size, max_w, bold=False):
    """Cat chuoi cho vua max_w voi dau ..."""
    s = str(s)
    if text_size(s, size, bold)[0] <= max_w:
        return s
    while s and text_size(s + "…", size, bold)[0] > max_w:
        s = s[:-1]
    return s + "…"


def wrap(s, size, max_w, bold=False):
    """Ngat dong don gian theo tu."""
    words = str(s).split(" ")
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if text_size(test, size, bold)[0] <= max_w or not cur:
            cur = test
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_color(c1, c2, t):
    return (int(lerp(c1[0], c2[0], t)), int(lerp(c1[1], c2[1], t)), int(lerp(c1[2], c2[2], t)))


def mix(c1, c2, t):
    return lerp_color(c1, c2, t)


def alpha(c, a):
    return (c[0], c[1], c[2], max(0, min(255, int(a))))


def clamp(v, a, b):
    return a if v < a else (b if v > b else v)


# ---------------- gradient ----------------
_grad_cache = {}


def vgrad(size, top, bottom):
    key = (size, top, bottom)
    surf = _grad_cache.get(key)
    if surf is None:
        w, h = int(size[0]), max(1, int(size[1]))
        surf = pygame.Surface((w, h))
        for y in range(h):
            t = y / max(1, h - 1)
            pygame.draw.line(surf, lerp_color(top, bottom, t), (0, y), (w, y))
        _grad_cache[key] = surf
    return surf


def hgrad(size, left, right):
    """Gradient ngang; ho tro mau RGBA (giu nguyen kenh alpha)."""
    key = ("h", size, tuple(left), tuple(right))
    surf = _grad_cache.get(key)
    if surf is None:
        w, h = max(1, int(size[0])), max(1, int(size[1]))
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        a1 = left[3] if len(left) > 3 else 255
        a2 = right[3] if len(right) > 3 else 255
        for x in range(w):
            t = x / max(1, w - 1)
            c = lerp_color(left, right, t)
            if len(left) > 3 or len(right) > 3:
                c = (*c, int(lerp(a1, a2, t)))
            pygame.draw.line(surf, c, (x, 0), (x, h))
        _grad_cache[key] = surf
    return surf


_rgrad_cache = {}


def rounded_hgrad(w, h, left, right, radius):
    """Hinh chu nhat bo goc voi gradient ngang (dung cho nut primary/accent)."""
    key = (int(w), int(h), tuple(left), tuple(right), int(radius))
    surf = _rgrad_cache.get(key)
    if surf is None:
        if len(_rgrad_cache) > 600:
            _rgrad_cache.clear()
        base = hgrad((w, h), left, right).copy()
        mask = pygame.Surface((int(w), int(h)), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=int(radius))
        base.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        _rgrad_cache[key] = base
    return _rgrad_cache[key]


def rounded_vgrad(w, h, top, bottom, radius):
    key = ("v", int(w), int(h), top, bottom, int(radius))
    surf = _rgrad_cache.get(key)
    if surf is None:
        base = pygame.Surface((max(1, int(w)), max(1, int(h))), pygame.SRCALPHA)
        g = vgrad((int(w), int(h)), top, bottom).convert_alpha()
        base.blit(g, (0, 0))
        mask = pygame.Surface(base.get_size(), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=int(radius))
        base.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        _rgrad_cache[key] = base
    return _rgrad_cache[key]


def draw_vgrad(dst, rect, top, bottom):
    dst.blit(vgrad((max(1, rect[2]), max(1, rect[3])), top, bottom), (rect[0], rect[1]))


# ---------------- glow ----------------
_glow_cache = {}


def glow_sprite(radius, color, strength=120):
    """Sprite glow da nhan san do sang (de dung voi BLEND_ADD)."""
    radius = max(2, int(radius))
    key = (radius, color, int(strength))
    surf = _glow_cache.get(key)
    if surf is None:
        size = radius * 2 + 2
        surf = pygame.Surface((size, size))
        surf.fill((0, 0, 0))
        cx = cy = size // 2
        step = max(1, radius // 30)
        r = radius
        k0 = max(0.0, min(1.0, strength / 255.0))
        while r > 0:
            t = r / radius
            k = ((1 - t) ** 2.2) * k0
            c = (int(color[0] * k), int(color[1] * k), int(color[2] * k))
            if c[0] or c[1] or c[2]:
                pygame.draw.circle(surf, c, (cx, cy), int(r))
            r -= step
        _glow_cache[key] = surf
    return surf


def glow(dst, center, radius, color, strength=120, scale=1.0):
    spr = glow_sprite(radius * scale, color, strength)
    dst.blit(spr, (int(center[0] - spr.get_width() / 2), int(center[1] - spr.get_height() / 2)),
             special_flags=pygame.BLEND_ADD)


# ---------------- hinh ----------------
def rect(dst, r, color, radius=0, width=0):
    if r[2] <= 0 or r[3] <= 0:
        return
    if len(color) == 4 and color[3] < 255:
        tmp = pygame.Surface((max(1, int(r[2])), max(1, int(r[3]))), pygame.SRCALPHA)
        pygame.draw.rect(tmp, color, tmp.get_rect(), width=width, border_radius=int(radius))
        dst.blit(tmp, (r[0], r[1]))
        return
    pygame.draw.rect(dst, color, pygame.Rect(r), width=width, border_radius=int(radius))


def panel(dst, r, radius=16, fill=None, border=LINE, shadow=True, top_hi=False, alpha_=PANEL_A):
    """Panel giong CSS .panel: nen rgba(15,18,32,.88), border line, bo goc 16."""
    r = pygame.Rect(r)
    if shadow:
        sh = pygame.Surface((r.w + 44, r.h + 56), pygame.SRCALPHA)
        pygame.draw.rect(sh, (0, 0, 0, 70), pygame.Rect(22, 24, r.w, r.h), border_radius=radius + 10)
        dst.blit(sh, (r.x - 22, r.y - 18))
    if fill is not None:
        pygame.draw.rect(dst, fill, r, border_radius=radius)
    else:
        tmp = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
        pygame.draw.rect(tmp, (*PANEL, alpha_), tmp.get_rect(), border_radius=radius)
        dst.blit(tmp, r.topleft)
    if top_hi:
        hi = pygame.Surface((max(1, r.w - 2), max(1, r.h - 2)), pygame.SRCALPHA)
        pygame.draw.rect(hi, (255, 255, 255, 9), hi.get_rect(), border_radius=max(1, radius - 1))
        dst.blit(hi, (r.x + 1, r.y + 1))
    if border:
        pygame.draw.rect(dst, border, r, width=1, border_radius=radius)


def hline(dst, x1, x2, y, color=LINE, w=1):
    pygame.draw.line(dst, color, (x1, y), (x2, y), w)


def dashed_hline(dst, x1, x2, y, color=(255, 255, 255, 18), dash=5, gap=4):
    x = x1
    while x < x2:
        pygame.draw.line(dst, color, (x, y), (min(x + dash, x2), y))
        x += dash + gap


def dashed_rect(dst, r, color=(255, 255, 255, 40), radius=12, dash=6, gap=5):
    """Vien duties dut (cho the + Kit moi)."""
    r = pygame.Rect(r)
    surf = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
    # canh tren
    x = radius
    while x < r.w - radius:
        pygame.draw.line(surf, color, (x, 0), (min(x + dash, r.w - radius), 0))
        x += dash + gap
    x = radius
    while x < r.w - radius:
        pygame.draw.line(surf, color, (x, r.h - 1), (min(x + dash, r.w - radius), r.h - 1))
        x += dash + gap
    y = radius
    while y < r.h - radius:
        pygame.draw.line(surf, color, (0, y), (0, min(y + dash, r.h - radius)))
        y += dash + gap
    y = radius
    while y < r.h - radius:
        pygame.draw.line(surf, color, (r.w - 1, y), (r.w - 1, min(y + dash, r.h - radius)))
        y += dash + gap
    dst.blit(surf, r.topleft)


def circle(dst, center, r, color, width=0):
    pygame.draw.circle(dst, color, (int(center[0]), int(center[1])), int(r), width)


def ring(dst, center, r, color, w=2, alpha_=255):
    if alpha_ < 255:
        surf = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(surf, alpha(color, alpha_), (r + 2, r + 2), int(r), int(w))
        dst.blit(surf, (center[0] - r - 2, center[1] - r - 2))
    else:
        pygame.draw.circle(dst, color, (int(center[0]), int(center[1])), int(r), int(w))


def poly(dst, points, color, width=0):
    pygame.draw.polygon(dst, color, points, width)


def shape_points(shape, cx, cy, r, rot=0.0):
    """Diem cua cac hinh nhan vat."""
    import math
    pts = []
    if shape == "square":
        for i in range(4):
            a = rot + math.pi / 4 + i * math.pi / 2
            pts.append((cx + math.cos(a) * r * 0.92, cy + math.sin(a) * r * 0.92))
    elif shape == "triangle":
        for i in range(3):
            a = rot - math.pi / 2 + i * (2 * math.pi / 3)
            pts.append((cx + math.cos(a) * r * 1.12, cy + math.sin(a) * r * 1.12))
    elif shape == "diamond":
        for i in range(4):
            a = rot - math.pi / 2 + i * (math.pi / 2)
            pts.append((cx + math.cos(a) * r * 1.2, cy + math.sin(a) * r * 1.2))
    elif shape == "hex":
        for i in range(6):
            a = rot + i * (math.pi / 3)
            pts.append((cx + math.cos(a) * r * 1.05, cy + math.sin(a) * r * 1.05))
    elif shape == "star":
        for i in range(10):
            a = rot - math.pi / 2 + i * (math.pi / 5)
            rr = r * (1.25 if i % 2 == 0 else 0.55)
            pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    else:  # circle
        for i in range(16):
            a = rot + i * (math.pi / 8)
            pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return pts


def draw_shape(dst, shape, cx, cy, r, color, rot=0.0, glow_size=0, glow_color=None, outline=None):
    if glow_size:
        glow(dst, (cx, cy), glow_size, glow_color or color, 90)
    pts = shape_points(shape, cx, cy, r, rot)
    pygame.draw.polygon(dst, color, pts)
    if outline:
        pygame.draw.polygon(dst, outline, pts, 2)
    return pts


def shape_icon(dst, shape, color, cx, cy, r, glow_k=0):
    """Icon hinh don sac giong shapeSvg trong ban Edge (khong vien, khong lop trong)."""
    if glow_k:
        glow(dst, (cx, cy), r * 1.6, color, glow_k)
    pts = shape_points(shape, cx, cy, r)
    pygame.draw.polygon(dst, color, pts)


def clip_push(dst, r):
    old = dst.get_clip()
    dst.set_clip(pygame.Rect(r))
    return old


def clip_pop(dst, old):
    dst.set_clip(old)


def hex_rgb(c):
    c = c.lstrip("#")
    return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16))


def ease_out(t):
    return 1 - (1 - t) ** 3


def ease_in_out(t):
    return t * t * (3 - 2 * t)


# ---------------- nen menu (bg-grid cua CSS) ----------------
_bg_cache = {}


def bg_grid(dst, size):
    """Nen .bg-grid: gradient doc + 3 vung sang radial + luoi 56px mo dan."""
    w, h = int(size[0]), int(size[1])
    key = (w, h)
    surf = _bg_cache.get(key)
    if surf is None:
        surf = pygame.Surface((w, h))
        # linear-gradient(180deg,#080a12,#05060a 70%)
        base = vgrad((w, h), (8, 10, 18), (5, 6, 10))
        surf.blit(base, (0, 0))
        # radial glows
        glow(surf, (w * 0.5, h * 0.08), int(w * 0.34), PURPLE, 58)
        glow(surf, (w * 0.85, h * 0.9), int(w * 0.26), CYAN, 32)
        glow(surf, (w * 0.10, h * 0.85), int(w * 0.26), ACCENT, 26)
        # luoi 56px voi mask radial
        grid = pygame.Surface((w, h), pygame.SRCALPHA)
        gc = (120, 150, 255, 14)
        for x in range(0, w, 56):
            pygame.draw.line(grid, gc, (x, 0), (x, h))
        for y in range(0, h, 56):
            pygame.draw.line(grid, gc, (0, y), (w, y))
        # mask radial (trang giua -> den ria)
        mask = pygame.Surface((w, h))
        mask.fill((0, 0, 0))
        cx, cy = w * 0.5, h * 0.4
        maxr = max(w, h) * 0.55
        step = 10
        r = int(maxr)
        while r > 0:
            t = r / maxr
            v = int(255 * (1 - t) ** 1.5)
            pygame.draw.circle(mask, (v, v, v), (int(cx), int(cy)), r)
            r -= step
        grid.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        surf.blit(grid, (0, 0))
        _bg_cache[key] = surf
    dst.blit(surf, (0, 0))
