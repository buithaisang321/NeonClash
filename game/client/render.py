"""Renderer arena: map, tuong, bui co, nhan vat, dan, hieu ung, minimap."""
import math
import random

import pygame

from ..gamedata import CHAR_MAP, MAP_SIZE, WALL_THICK, hex_rgb
from ..room import make_map
from . import theme as T

TAU = math.pi * 2


def clamp(v, a, b):
    return a if v < a else (b if v > b else v)


class Renderer:
    def __init__(self, w=1280, h=800):
        self.w = w
        self.h = h
        self.zoom = 1.0
        self.map = make_map(20261021)
        self.particles = []
        self.rings = []
        self.beams = []
        self.slashes = []
        self.texts = []
        self.marks = []
        self.smoke = []
        self.noise = self._make_noise()
        self.bush_cache = {}
        self._ov_cache = {}
        self.use_particles = True
        self.use_glow = True
        self.time = 0.0

    # ---------------- chuan bi ----------------
    def _make_noise(self):
        s = pygame.Surface((128, 128))
        s.fill((0, 0, 0))
        rnd = random.Random(7)
        for _ in range(900):
            x, y = rnd.randrange(128), rnd.randrange(128)
            v = rnd.randrange(4, 14)
            s.set_at((x, y), (v, v + 2, v + 7))
        return s

    def set_map(self, m):
        self.map = m
        self.bush_cache = {}

    def resize(self, w, h):
        self.w, self.h = max(320, int(w)), max(240, int(h))

    def set_quality(self, particles=True, glow=True):
        self.use_particles = particles
        self.use_glow = glow

    def _bush_sprite(self, r):
        key = max(40, int(r / 14) * 14)
        spr = self.bush_cache.get(key)
        if spr is None:
            size = key * 2 + 12
            spr = pygame.Surface((size, size), pygame.SRCALPHA)
            cx = cy = size // 2
            rnd = random.Random(key * 7 + 3)
            # nen mo (nhieu lop alpha thap -> mem)
            for i in range(7):
                rr = key * (1.0 - i * 0.11)
                pygame.draw.circle(spr, (14, 52, 34, 16), (cx, cy), int(rr))
            # la nho, alpha thap
            for i in range(30):
                a = rnd.uniform(0, TAU)
                d = rnd.uniform(0.1, 0.86) * key
                lx = cx + math.cos(a) * d
                ly = cy + math.sin(a) * d
                lr = rnd.uniform(0.1, 0.24) * key
                g = rnd.randint(58, 92)
                pygame.draw.circle(spr, (16 + rnd.randint(0, 10), g, 44 + rnd.randint(0, 16),
                                        rnd.randint(34, 66)), (int(lx), int(ly)), int(lr))
            # vet sang nhe phia tren
            for i in range(10):
                a = rnd.uniform(-math.pi, -0.2)
                d = rnd.uniform(0.1, 0.66) * key
                lx = cx + math.cos(a) * d
                ly = cy + math.sin(a) * d
                pygame.draw.circle(spr, (80, 160, 110, rnd.randint(10, 26)), (int(lx), int(ly)),
                                   int(rnd.uniform(0.08, 0.18) * key))
            self.bush_cache[key] = spr
        return spr

    # ---------------- hieu ung ----------------
    def spawn_fx(self, e):
        k = e.get("k")
        x, y = e.get("x", 0), e.get("y", 0)
        if k == "spark":
            self._burst(x, y, e.get("c", "#fff"), 6, 90, 0.35, 2.0)
        elif k == "hit":
            self._burst(x, y, e.get("c", "#fff"), 10, 170, 0.4, 2.6)
            self.rings.append({"x": x, "y": y, "r": 4, "max": 34, "life": 0.25, "t": 0.25,
                               "c": T.hex_rgb(e.get("c", "#fff")), "w": 2})
        elif k == "boom":
            r = e.get("r", 90)
            c = T.hex_rgb(e.get("c", "#ff9b3d"))
            self.rings.append({"x": x, "y": y, "r": 8, "max": r, "life": 0.42, "t": 0.42, "c": c, "w": 4})
            self.rings.append({"x": x, "y": y, "r": 4, "max": r * 0.6, "life": 0.3, "t": 0.3, "c": (255, 255, 255), "w": 2})
            self._burst(x, y, e.get("c", "#ff9b3d"), 26, 260, 0.55, 3.4)
            self._burst(x, y, "#ffffff", 10, 180, 0.35, 2.2)
            self.smoke.append({"x": x, "y": y, "r": r * 0.55, "life": 0.9, "t": 0.9})
        elif k == "beam":
            self.beams.append({"x1": e["x"], "y1": e["y"], "x2": e["x2"], "y2": e["y2"],
                               "life": 0.22, "t": 0.22, "c": (0, 229, 255), "w": 10})
        elif k == "snipe":
            self.beams.append({"x1": e["x"], "y1": e["y"], "x2": e["x2"], "y2": e["y2"],
                               "life": 0.3, "t": 0.3, "c": (255, 240, 180), "w": 5})
            self._burst(e["x2"], e["y2"], "#fff0b0", 8, 120, 0.3, 2.2)
        elif k == "chain":
            self.beams.append({"x1": e["x"], "y1": e["y"], "x2": e["x2"], "y2": e["y2"],
                               "life": 0.2, "t": 0.2, "c": (192, 123, 255), "w": 6, "zigzag": True})
        elif k == "slash":
            self.slashes.append({"x": x, "y": y, "a": e.get("a", 0), "r": e.get("r", 100),
                                 "life": 0.18, "t": 0.18, "hit": e.get("hit", 0)})
        elif k == "whirl":
            self.rings.append({"x": x, "y": y, "r": 20, "max": e.get("r", 120), "life": 0.35,
                               "t": 0.35, "c": (255, 220, 140), "w": 5})
            self._burst(x, y, "#ffd166", 16, 200, 0.4, 2.4)
        elif k == "nova":
            self.rings.append({"x": x, "y": y, "r": 12, "max": e.get("r", 170), "life": 0.4,
                               "t": 0.4, "c": (140, 240, 255), "w": 4})
        elif k == "execute":
            self.slashes.append({"x": x, "y": y, "a": e.get("a", 0), "r": e.get("r", 125),
                                 "life": 0.26, "t": 0.26, "hit": 1, "big": True})
        elif k == "heal":
            for i in range(10):
                self._part(x + random.uniform(-16, 16), y + random.uniform(-8, 16), "#7dffb0",
                           0, -60, 0.8, 2.4)
        elif k == "spawn":
            self.rings.append({"x": x, "y": y, "r": 6, "max": 48, "life": 0.5, "t": 0.5,
                               "c": T.hex_rgb(e.get("c", "#fff")), "w": 3})
        elif k in ("blinkFrom", "blinkTo"):
            for i in range(12):
                a = i / 12 * TAU
                self._part(x + math.cos(a) * 10, y + math.sin(a) * 10, "#8ef0ff",
                           math.cos(a) * 90, math.sin(a) * 90, 0.4, 2.2)
        elif k == "dash":
            a = e.get("a", 0)
            for i in range(8):
                self._part(x - math.cos(a) * i * 6, y - math.sin(a) * i * 6, "#8ef0ff",
                           -math.cos(a) * 60, -math.sin(a) * 60, 0.3, 2.0)
        elif k == "hook":
            self.beams.append({"x1": e["x"], "y1": e["y"], "x2": e["x2"], "y2": e["y2"],
                               "life": 0.25, "t": 0.25, "c": (255, 200, 120), "w": 4})
        elif k == "wall":
            self.rings.append({"x": x + e.get("w", 40) / 2, "y": y + e.get("h", 40) / 2,
                               "r": 8, "max": 70, "life": 0.35, "t": 0.35, "c": (120, 200, 255), "w": 3})
        elif k == "meteorMark":
            self.marks.append({"x": x, "y": y, "r": e.get("r", 140), "life": e.get("d", 0.8),
                               "t": e.get("d", 0.8)})
        elif k == "dmg":
            self.texts.append({"x": x + random.uniform(-8, 8), "y": y - 22, "s": "-%d" % e.get("v", 0),
                               "life": 0.75, "t": 0.75, "c": (255, 220, 120), "size": 15})
        elif k == "dodge":
            self.texts.append({"x": x, "y": y - 26, "s": "NÉ", "life": 0.6, "t": 0.6,
                               "c": (160, 220, 255), "size": 13})
        elif k == "kill":
            self._burst(x, y, e.get("c", "#fff"), 26, 300, 0.7, 3.0)
            self.rings.append({"x": x, "y": y, "r": 10, "max": 90, "life": 0.5, "t": 0.5,
                               "c": T.hex_rgb(e.get("c", "#fff")), "w": 3})

    def _part(self, x, y, c, vx, vy, life, r, kind="dot"):
        if not self.use_particles:
            return
        if len(self.particles) > 700:
            return
        self.particles.append({"x": x, "y": y, "vx": vx, "vy": vy, "life": life, "t": life,
                               "c": T.hex_rgb(c) if isinstance(c, str) else c, "r": r, "kind": kind})

    def _burst(self, x, y, c, n, speed, life, r):
        if not self.use_particles:
            return
        for _ in range(n):
            a = random.uniform(0, TAU)
            sp = speed * random.uniform(0.3, 1.0)
            self._part(x, y, c, math.cos(a) * sp, math.sin(a) * sp,
                       life * random.uniform(0.6, 1.2), r * random.uniform(0.6, 1.3))

    def update(self, dt):
        self.time += dt
        for p in self.particles:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["vx"] *= 0.93
            p["vy"] *= 0.93
            p["life"] -= dt
        self.particles = [p for p in self.particles if p["life"] > 0]

        for r in self.rings:
            r["life"] -= dt
        self.rings = [r for r in self.rings if r["life"] > 0]

        for b in self.beams:
            b["life"] -= dt
        self.beams = [b for b in self.beams if b["life"] > 0]

        for s in self.slashes:
            s["life"] -= dt
        self.slashes = [s for s in self.slashes if s["life"] > 0]

        for t in self.texts:
            t["y"] -= 34 * dt
            t["life"] -= dt
        self.texts = [t for t in self.texts if t["life"] > 0]

        for m in self.marks:
            m["life"] -= dt
        self.marks = [m for m in self.marks if m["life"] > 0]

        for s in self.smoke:
            s["life"] -= dt
            s["r"] += dt * 30
        self.smoke = [s for s in self.smoke if s["life"] > 0]

    # ---------------- toa do ----------------
    def world_to_screen(self, x, y, cam, zoom=None):
        z = self.zoom if zoom is None else zoom
        return ((x - cam[0]) * z + self.w / 2, (y - cam[1]) * z + self.h / 2)

    def screen_to_world(self, sx, sy, cam, zoom=None):
        z = self.zoom if zoom is None else zoom
        return ((sx - self.w / 2) / z + cam[0], (sy - self.h / 2) / z + cam[1])

    # ---------------- ve the gioi ----------------
    def draw(self, surf, world):
        m = world.get("map") or self.map
        if not m:
            return
        cam = world["cam"]
        self.zoom = world.get("zoom", 1.0)
        z = self.zoom
        l = cam[0] - self.w / 2 / z
        t = cam[1] - self.h / 2 / z
        r = cam[0] + self.w / 2 / z
        b = cam[1] + self.h / 2 / z

        self._floor(surf, l, t, r, b, world)
        self._bushes(surf, m, l, t, r, b, world)
        self._hazards_floor(surf, world, cam, z)
        self._walls(surf, m, l, t, r, b, world)
        self._dyn_walls(surf, world, cam, z)
        self._turrets(surf, world, cam, z)
        self._projectiles(surf, world, cam, z)
        self._players(surf, world, cam, z)
        self._particles(surf, cam, z)
        self._marks(surf, cam, z)
        self._minimap(surf, m, world)
        self._arrows(surf, world, cam, z)

    def _floor(self, surf, l, t, r, b, world):
        surf.fill(world.get("floor", (8, 11, 19)))
        # luoi
        step = 100
        x0 = int(l // step) * step
        col = world.get("grid", (18, 26, 44))
        while x0 <= r:
            sx = (x0 - l) * self.zoom
            pygame.draw.line(surf, col, (sx, 0), (sx, self.h), 1)
            x0 += step
        y0 = int(t // step) * step
        while y0 <= b:
            sy = (y0 - t) * self.zoom
            pygame.draw.line(surf, col, (0, sy), (self.w, sy), 1)
            y0 += step
        # diem giao
        dot = (34, 46, 72)
        yy = int(t // step) * step
        while yy <= b:
            sy = (yy - t) * self.zoom
            xx = int(l // step) * step
            while xx <= r:
                pygame.draw.rect(surf, dot, ((xx - l) * self.zoom - 1, sy - 1, 2, 2))
                xx += step
            yy += step

        # vung toi ngoai bien map
        for (mx, my, mw, mh) in ((0, 0, MAP_SIZE, WALL_THICK),
                                 (0, MAP_SIZE - WALL_THICK, MAP_SIZE, WALL_THICK),
                                 (0, 0, WALL_THICK, MAP_SIZE),
                                 (MAP_SIZE - WALL_THICK, 0, WALL_THICK, MAP_SIZE)):
            sx = (mx - l) * self.zoom
            sy = (my - t) * self.zoom
            pygame.draw.rect(surf, (4, 6, 11), (sx, sy, mw * self.zoom, mh * self.zoom))

        # nhieu hat
        nz = self.noise
        for nx in range(0, self.w, 128):
            for ny in range(0, self.h, 128):
                surf.blit(nz, (nx, ny), special_flags=pygame.BLEND_ADD)

    def _bushes(self, surf, m, l, t, r, b, world):
        for bs in m["bushes"]:
            if bs["x"] + bs["r"] < l or bs["x"] - bs["r"] > r or bs["y"] + bs["r"] < t or bs["y"] - bs["r"] > b:
                continue
            if self.use_glow:
                T.glow(surf, self.world_to_screen(bs["x"], bs["y"], world["cam"]),
                       bs["r"] * self.zoom * 1.15, (20, 90, 58), 26)
            spr = self._bush_sprite(bs["r"])
            z = self.zoom
            size = int(spr.get_width() * z)
            if size < 4:
                continue
            scaled = pygame.transform.smoothscale(spr, (size, size)) if abs(z - 1) > 0.05 else spr
            sx, sy = self.world_to_screen(bs["x"], bs["y"], world["cam"])
            surf.blit(scaled, (sx - size / 2, sy - size / 2))

    def _walls(self, surf, m, l, t, r, b, world):
        z = self.zoom
        cam = world["cam"]
        for w in m["walls"]:
            if w.get("t") == "r":
                if w["x"] + w["w"] < l or w["x"] > r or w["y"] + w["h"] < t or w["y"] > b:
                    continue
                sx, sy = self.world_to_screen(w["x"], w["y"], cam)
                sw, sh = w["w"] * z, w["h"] * z
                if sw < 2 or sh < 2:
                    continue
                rad = max(2, int(7 * z))
                # bong
                shs = pygame.Surface((int(sw) + 10, int(sh) + 10), pygame.SRCALPHA)
                pygame.draw.rect(shs, (0, 0, 0, 105), (5, 6, int(sw), int(sh)), border_radius=rad)
                surf.blit(shs, (sx - 5, sy - 5))
                # than
                T.rect(surf, (sx, sy, sw, sh), (21, 28, 45), rad)
                band = pygame.Surface((max(1, int(sw)), max(2, int(sh * 0.42))), pygame.SRCALPHA)
                band.fill((120, 150, 215, 16))
                surf.blit(band, (sx, sy))
                low = pygame.Surface((max(1, int(sw)), max(2, int(sh * 0.3))), pygame.SRCALPHA)
                low.fill((0, 0, 0, 52))
                surf.blit(low, (sx, sy + sh - low.get_height()))
                # vien + canh tren
                T.rect(surf, (sx, sy, sw, sh), (56, 76, 118), rad, width=1)
                if sh > 8:
                    pygame.draw.line(surf, (122, 152, 222), (sx + 7, sy + 1),
                                     (sx + sw - 7, sy + 1), max(1, int(2 * z)))
            else:
                if w["x"] + w["r"] < l or w["x"] - w["r"] > r or w["y"] + w["r"] < t or w["y"] - w["r"] > b:
                    continue
                sx, sy = self.world_to_screen(w["x"], w["y"], cam)
                rad = w["r"] * z
                if rad < 2:
                    continue
                pygame.draw.circle(surf, (0, 0, 0), (int(sx + 4 * z), int(sy + 5 * z)), int(rad))
                pygame.draw.circle(surf, (22, 29, 47), (int(sx), int(sy)), int(rad))
                pygame.draw.circle(surf, (27, 36, 57), (int(sx), int(sy)), int(rad * 0.74))
                pygame.draw.circle(surf, (33, 44, 69), (int(sx), int(sy)), int(rad * 0.44))
                pygame.draw.circle(surf, (58, 78, 120), (int(sx), int(sy)), int(rad), max(1, int(1.5 * z)))

    def _dyn_walls(self, surf, world, cam, z):
        for w in world.get("dyn_walls", []):
            sx, sy = self.world_to_screen(w["x"], w["y"], cam)
            sw, sh = w["w"] * z, w["h"] * z
            s = pygame.Surface((max(1, int(sw)), max(1, int(sh))), pygame.SRCALPHA)
            pygame.draw.rect(s, (60, 170, 255, 54), s.get_rect(), border_radius=4)
            pygame.draw.rect(s, (120, 210, 255, 210), s.get_rect(), width=2, border_radius=4)
            surf.blit(s, (sx, sy))
            if self.use_glow:
                T.glow(surf, (sx + sw / 2, sy + sh / 2), max(sw, sh) * 0.6, (60, 170, 255), 30)

    def _hazards_floor(self, surf, world, cam, z):
        # khói
        for s in world.get("smokes", []):
            sx, sy = self.world_to_screen(s["x"], s["y"], cam)
            rad = s["r"] * z
            if rad < 4:
                continue
            spr = pygame.Surface((int(rad * 2), int(rad * 2)), pygame.SRCALPHA)
            for i in range(4):
                a = self.time * 0.6 + i * 1.6
                cx = rad + math.cos(a) * rad * 0.22
                cy = rad + math.sin(a * 1.3) * rad * 0.22
                pygame.draw.circle(spr, (150, 150, 185, 26), (int(cx), int(cy)), int(rad * 0.78))
            surf.blit(spr, (sx - rad, sy - rad))
        # min
        for m in world.get("mines", []):
            sx, sy = self.world_to_screen(m["x"], m["y"], cam)
            armed = m.get("armed")
            pygame.draw.circle(surf, (28, 24, 24), (int(sx), int(sy)), int(9 * z))
            pygame.draw.circle(surf, (90, 70, 60), (int(sx), int(sy)), int(9 * z), max(1, int(1.5 * z)))
            if armed:
                blink = (math.sin(self.time * 9) + 1) / 2
                pygame.draw.circle(surf, (255, 70, 70), (int(sx), int(sy)), max(2, int(3 * z * (0.7 + blink * 0.5))))
                if self.use_glow:
                    T.glow(surf, (sx, sy), 18 * z, (255, 60, 60), int(30 + blink * 50))
            else:
                pygame.draw.circle(surf, (120, 120, 130), (int(sx), int(sy)), max(1, int(2.5 * z)))
        # bay
        for s in world.get("snares", []):
            sx, sy = self.world_to_screen(s["x"], s["y"], cam)
            rad = 70 * z
            for i in range(8):
                a1 = i / 8 * TAU + self.time * 0.2
                a2 = a1 + 0.7
                pygame.draw.line(surf, (255, 170, 80),
                                 (sx + math.cos(a1) * rad, sy + math.sin(a1) * rad),
                                 (sx + math.cos(a2) * rad, sy + math.sin(a2) * rad), max(1, int(2 * z)))
            pygame.draw.circle(surf, (255, 170, 80), (int(sx), int(sy)), int(rad), max(1, int(1.5 * z)))

    def _turrets(self, surf, world, cam, z):
        for t in world.get("turrets", []):
            sx, sy = self.world_to_screen(t["x"], t["y"], cam)
            rad = 13 * z
            pygame.draw.circle(surf, (16, 30, 40), (int(sx), int(sy)), int(rad))
            pygame.draw.circle(surf, (110, 220, 255), (int(sx), int(sy)), int(rad), max(1, int(2 * z)))
            a = t.get("a", 0)
            pygame.draw.line(surf, (150, 235, 255), (sx, sy),
                             (sx + math.cos(a) * rad * 1.9, sy + math.sin(a) * rad * 1.9), max(2, int(4 * z)))
            if self.use_glow:
                T.glow(surf, (sx, sy), 24 * z, (80, 210, 255), 60)

    def _projectiles(self, surf, world, cam, z):
        for b in world.get("projs", []):
            sx, sy = self.world_to_screen(b["x"], b["y"], cam)
            rad = max(2.0, b.get("r", 5) * z)
            col = T.hex_rgb(b.get("c", "#ffe066"))
            ang = b.get("a", 0)
            bm = b.get("bm")
            if bm:
                # dao xoay
                pts = []
                spin = b.get("s", 0)
                for i in range(8):
                    a = spin + i * (math.pi / 4)
                    rr = rad * (1.7 if i % 2 == 0 else 0.6)
                    pts.append((sx + math.cos(a) * rr, sy + math.sin(a) * rr))
                pygame.draw.polygon(surf, col, pts)
                if self.use_glow:
                    T.glow(surf, (sx, sy), rad * 4, col, 80)
                continue
            # vet dan
            vx, vy = math.cos(ang), math.sin(ang)
            tail = rad * 5.5
            for i in range(3):
                a = 90 - i * 26
                w = max(1, int(rad * (1.5 - i * 0.35)))
                pygame.draw.line(surf, col,
                                 (sx - vx * tail * (0.3 + i * 0.22), sy - vy * tail * (0.3 + i * 0.22)),
                                 (sx, sy), w)
            if self.use_glow:
                T.glow(surf, (sx, sy), rad * 3.4, col, 90)
            pygame.draw.circle(surf, (255, 255, 255), (int(sx), int(sy)), max(1, int(rad * 0.5)))
            pygame.draw.circle(surf, col, (int(sx), int(sy)), int(rad), max(1, int(rad * 0.55)))

    def _players(self, surf, world, cam, z):
        players = sorted(world.get("players", []), key=lambda p: p["y"])
        me = world.get("self_id")
        for p in players:
            sx, sy = self.world_to_screen(p["x"], p["y"], cam)
            if sx < -120 or sx > self.w + 120 or sy < -120 or sy > self.h + 120:
                continue
            ch = CHAR_MAP.get(p.get("c"), CHAR_MAP["shadow"])
            col = hex_rgb(ch["color"])
            accent = hex_rgb(ch["accent"])
            is_me = p.get("id") == me
            hidden = p.get("bn") and not is_me
            alpha = 130 if hidden else 255
            rad = 17 * z

            # bong
            sh = pygame.Surface((int(rad * 2.6), int(rad * 1.8)), pygame.SRCALPHA)
            pygame.draw.ellipse(sh, (0, 0, 0, 120), sh.get_rect())
            surf.blit(sh, (sx - rad * 1.3, sy + rad * 0.45))

            if self.use_glow and not hidden:
                T.glow(surf, (sx, sy), rad * 5.0, col, 26)
                T.glow(surf, (sx, sy), rad * 2.8, col, 80 if is_me else 55)

            if p.get("ph"):
                s = pygame.Surface((int(rad * 2.8), int(rad * 2.8)), pygame.SRCALPHA)
                pygame.draw.circle(s, (255, 255, 255, 60), (int(rad * 1.4), int(rad * 1.4)), int(rad * 1.2), 2)
                surf.blit(s, (sx - rad * 1.4, sy - rad * 1.4))

            pts = T.shape_points(ch["shape"], sx, sy, rad, p.get("a", 0) * 0.35)
            if alpha < 255:
                layer = pygame.Surface((int(rad * 3), int(rad * 3)), pygame.SRCALPHA)
                cxy = (int(rad * 1.5), int(rad * 1.5))
                lpts = T.shape_points(ch["shape"], cxy[0], cxy[1], rad, p.get("a", 0) * 0.35)
                pygame.draw.polygon(layer, (*col, alpha), lpts)
                pygame.draw.polygon(layer, (*accent, alpha), lpts, max(1, int(2 * z)))
                surf.blit(layer, (sx - rad * 1.5, sy - rad * 1.5))
            else:
                pygame.draw.polygon(surf, col, pts)
                pygame.draw.polygon(surf, accent, pts, max(1, int(2 * z)))
                inner = T.shape_points(ch["shape"], sx, sy, rad * 0.55, p.get("a", 0) * 0.35)
                pygame.draw.polygon(surf, T.mix(col, (255, 255, 255), 0.35), inner)

            # huong sung
            a = p.get("a", 0)
            pygame.draw.line(surf, accent, (sx + math.cos(a) * rad * 0.9, sy + math.sin(a) * rad * 0.9),
                             (sx + math.cos(a) * rad * 1.7, sy + math.sin(a) * rad * 1.7),
                             max(2, int(3 * z)))

            # vong trang thai
            if p.get("hs"):
                pygame.draw.circle(surf, (80, 255, 200), (int(sx), int(sy)), int(rad * 1.5), max(1, int(1.6 * z)))
            if p.get("is"):
                pygame.draw.circle(surf, (120, 190, 255), (int(sx), int(sy)), int(rad * 1.62), max(1, int(1.6 * z)))
            if p.get("rt"):
                pygame.draw.circle(surf, (255, 160, 90), (int(sx), int(sy)), int(rad * 1.35), max(1, int(2 * z)))
            if p.get("sl"):
                s = pygame.Surface((int(rad * 3), int(rad * 3)), pygame.SRCALPHA)
                pygame.draw.circle(s, (120, 200, 255, 70), (int(rad * 1.5), int(rad * 1.5)), int(rad * 1.4), 2)
                surf.blit(s, (sx - rad * 1.5, sy - rad * 1.5))

            if is_me:
                pygame.draw.circle(surf, (255, 255, 255), (int(sx), int(sy)), int(rad * 1.78), max(1, int(1.4 * z)))

            # thanh mau
            bw = max(28, int(46 * z))
            bh = max(3, int(5 * z))
            bx, by = sx - bw / 2, sy - rad * 2.15
            pygame.draw.rect(surf, (0, 0, 0), (bx - 1, by - 1, bw + 2, bh + 2), border_radius=2)
            pygame.draw.rect(surf, (40, 26, 34), (bx, by, bw, bh), border_radius=2)
            hp_t = clamp(p.get("hp", 1) / max(1, p.get("mhp", 1)), 0, 1)
            hp_col = (90, 220, 130) if hp_t > 0.5 else ((255, 200, 90) if hp_t > 0.25 else (255, 80, 100))
            pygame.draw.rect(surf, hp_col, (bx, by, bw * hp_t, bh), border_radius=2)
            if p.get("sh", 0) > 0:
                sh_t = clamp(p["sh"] / max(1, p.get("mhp", 1)), 0, 1)
                pygame.draw.rect(surf, (120, 200, 255), (bx, by - bh - 1, bw * sh_t, max(2, bh - 1)),
                                 border_radius=2)
            # ten
            if z > 0.55:
                T.text(surf, p.get("n", ""), (sx, by - 16), max(9, int(11 * z)),
                       (255, 255, 255) if is_me else (210, 220, 240), align="center", shadow=True)

        # tam ngam cua minh
        if world.get("show_aim"):
            mx, my = world.get("mouse", (0, 0))
            if self.use_glow:
                T.glow(surf, (mx, my), 14, (0, 229, 255), 40)
            pygame.draw.circle(surf, (235, 245, 255), (int(mx), int(my)), 10, 2)
            for dx, dy in ((-16, 0), (16, 0), (0, -16), (0, 16)):
                pygame.draw.line(surf, (235, 245, 255), (mx + dx * 0.45, my + dy * 0.45),
                                 (mx + dx, my + dy), 2)
            pygame.draw.circle(surf, (0, 229, 255), (int(mx), int(my)), 2)

    def _particles(self, surf, cam, z):
        for p in self.particles:
            a = clamp(p["life"] / p["t"], 0, 1)
            sx = (p["x"] - cam[0]) * z + self.w / 2
            sy = (p["y"] - cam[1]) * z + self.h / 2
            if sx < -20 or sx > self.w + 20 or sy < -20 or sy > self.h + 20:
                continue
            r = max(1, p["r"] * z * (0.4 + a * 0.8))
            col = p["c"]
            if self.use_glow and p["r"] > 1.8:
                T.glow(surf, (sx, sy), r * 3.2, col, int(70 * a))
            s = pygame.Surface((int(r * 2) + 2, int(r * 2) + 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*col, int(255 * a)), (int(r) + 1, int(r) + 1), int(r))
            surf.blit(s, (sx - r, sy - r))

        for r in self.rings:
            a = clamp(r["life"] / r["t"], 0, 1)
            rad = r["r"] + (r["max"] - r["r"]) * (1 - a)
            sx = (r["x"] - cam[0]) * z + self.w / 2
            sy = (r["y"] - cam[1]) * z + self.h / 2
            s = pygame.Surface((int(rad * 2) + 6, int(rad * 2) + 6), pygame.SRCALPHA)
            pygame.draw.circle(s, (*r["c"], int(190 * a)), (int(rad) + 3, int(rad) + 3),
                               int(rad), max(1, int(r["w"] * a)))
            surf.blit(s, (sx - rad - 3, sy - rad - 3))

        for b in self.beams:
            a = clamp(b["life"] / b["t"], 0, 1)
            x1 = (b["x1"] - cam[0]) * z + self.w / 2
            y1 = (b["y1"] - cam[1]) * z + self.h / 2
            x2 = (b["x2"] - cam[0]) * z + self.w / 2
            y2 = (b["y2"] - cam[1]) * z + self.h / 2
            s = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
            if b.get("zigzag"):
                pts = []
                n = 8
                for i in range(n + 1):
                    t_ = i / n
                    px = x1 + (x2 - x1) * t_ + random.uniform(-10, 10) * (1 - abs(t_ - 0.5) * 2)
                    py = y1 + (y2 - y1) * t_ + random.uniform(-10, 10) * (1 - abs(t_ - 0.5) * 2)
                    pts.append((px, py))
                pygame.draw.lines(s, (*b["c"], int(230 * a)), False, pts, max(1, int(b["w"] * a * 0.6)))
            else:
                pygame.draw.line(s, (*b["c"], int(120 * a)), (x1, y1), (x2, y2), max(2, int(b["w"] * a)))
                pygame.draw.line(s, (255, 255, 255, int(230 * a)), (x1, y1), (x2, y2), max(1, int(b["w"] * a * 0.3)))
            surf.blit(s, (0, 0))

        for sl in self.slashes:
            a = clamp(sl["life"] / sl["t"], 0, 1)
            sx = (sl["x"] - cam[0]) * z + self.w / 2
            sy = (sl["y"] - cam[1]) * z + self.h / 2
            rad = sl["r"] * z
            s = pygame.Surface((int(rad * 2) + 8, int(rad * 2) + 8), pygame.SRCALPHA)
            col = (255, 255, 255) if sl.get("hit") else (170, 210, 255)
            width = max(2, int((10 if sl.get("big") else 6) * a * z))
            rect = pygame.Rect(4, 4, int(rad * 2), int(rad * 2))
            start = sl["a"] - 0.9
            pygame.draw.arc(s, (*col, int(210 * a)), rect, start, start + 1.8, width)
            surf.blit(s, (sx - rad - 4, sy - rad - 4))

        for t in self.texts:
            a = clamp(t["life"] / t["t"], 0, 1)
            sx = (t["x"] - cam[0]) * z + self.w / 2
            sy = (t["y"] - cam[1]) * z + self.h / 2
            T.text(surf, t["s"], (sx, sy), t["size"], t["c"], align="center",
                   alpha=int(255 * a), bold=True, shadow=True)

        for s in self.smoke:
            a = clamp(s["life"] / s["t"], 0, 1)
            sx = (s["x"] - cam[0]) * z + self.w / 2
            sy = (s["y"] - cam[1]) * z + self.h / 2
            rad = s["r"] * z
            spr = pygame.Surface((int(rad * 2), int(rad * 2)), pygame.SRCALPHA)
            pygame.draw.circle(spr, (90, 90, 110, int(50 * a)), (int(rad), int(rad)), int(rad))
            surf.blit(spr, (sx - rad, sy - rad))

    def _marks(self, surf, cam, z):
        for m in self.marks:
            a = clamp(m["life"] / m["t"], 0, 1)
            sx = (m["x"] - cam[0]) * z + self.w / 2
            sy = (m["y"] - cam[1]) * z + self.h / 2
            rad = m["r"] * z
            s = pygame.Surface((int(rad * 2) + 6, int(rad * 2) + 6), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 140, 60, int(70 * a)), (int(rad) + 3, int(rad) + 3), int(rad), 2)
            pygame.draw.circle(s, (255, 140, 60, int(130 * a)), (int(rad) + 3, int(rad) + 3), int(rad * (1 - a * 0.4)), 1)
            surf.blit(s, (sx - rad - 3, sy - rad - 3))

    # ---------------- minimap + mu tay chi huong ----------------
    def _minimap(self, surf, m, world):
        # .hud-topright #minimap: 200x200, radius 12, nam tren ben phai
        size = 200
        x = self.w - size - 14
        y = 14
        T.rect(surf, (x, y, size, size), (6, 8, 14, 210), 12)
        pygame.draw.rect(surf, T.LINE, (x, y, size, size), 1, border_radius=12)
        sx = (size - 12) / MAP_SIZE
        ox, oy = x + 6, y + 6
        inner = size - 12
        # tuong
        for w in m["walls"]:
            if w.get("t") == "r":
                pygame.draw.rect(surf, (46, 60, 92),
                                 (ox + w["x"] * sx, oy + w["y"] * sx, max(1, w["w"] * sx), max(1, w["h"] * sx)))
            else:
                pygame.draw.circle(surf, (46, 60, 92),
                                   (int(ox + w["x"] * sx), int(oy + w["y"] * sx)), max(1, int(w["r"] * sx)))
        for b in m["bushes"]:
            pygame.draw.circle(surf, (26, 74, 50),
                               (int(ox + b["x"] * sx), int(oy + b["y"] * sx)), max(1, int(b["r"] * sx)))
        # nguoi choi
        for p in world.get("players", []):
            ch = CHAR_MAP.get(p.get("c"), CHAR_MAP["shadow"])
            col = hex_rgb(ch["color"])
            px, py = ox + p["x"] * sx, oy + p["y"] * sx
            if p.get("id") == world.get("self_id"):
                pygame.draw.circle(surf, (255, 255, 255), (int(px), int(py)), 4)
                pygame.draw.circle(surf, col, (int(px), int(py)), 2)
            else:
                pygame.draw.circle(surf, col, (int(px), int(py)), 3)
        # khung nhin
        cam = world["cam"]
        vw = self.w / world.get("zoom", 1) * sx
        vh = self.h / world.get("zoom", 1) * sx
        pygame.draw.rect(surf, (90, 120, 180),
                         (ox + cam[0] * sx - vw / 2, oy + cam[1] * sx - vh / 2, vw, vh), 1)

    def _arrows(self, surf, world, cam, z):
        me = world.get("self_pos")
        if not me:
            return
        for p in world.get("players", []):
            if p.get("id") == world.get("self_id"):
                continue
            sx = (p["x"] - cam[0]) * z + self.w / 2
            sy = (p["y"] - cam[1]) * z + self.h / 2
            if 30 < sx < self.w - 30 and 30 < sy < self.h - 30:
                continue
            ch = CHAR_MAP.get(p.get("c"), CHAR_MAP["shadow"])
            col = hex_rgb(ch["color"])
            a = math.atan2(p["y"] - cam[1], p["x"] - cam[0])
            rad = 40
            cx = self.w / 2 + math.cos(a) * (min(self.w, self.h) / 2 - rad - 10)
            cy = self.h / 2 + math.sin(a) * (min(self.w, self.h) / 2 - rad - 10)
            pts = [(cx + math.cos(a) * 13, cy + math.sin(a) * 13),
                   (cx + math.cos(a + 2.5) * 11, cy + math.sin(a + 2.5) * 11),
                   (cx + math.cos(a - 2.5) * 11, cy + math.sin(a - 2.5) * 11)]
            s = pygame.Surface((44, 44), pygame.SRCALPHA)
            pygame.draw.polygon(s, (*col, 220), [(px - cx + 22, py - cy + 22) for px, py in pts])
            surf.blit(s, (cx - 22, cy - 22))

    # ---------------- nen cho menu ----------------
    def draw_backdrop(self, surf, t, dim=0.55):
        m = self.map
        w, h = surf.get_size()
        if not m:
            surf.fill(T.BG)
            return
        # render o do phan giai thap roi phong len -> mo (depth of field) + nhe may
        sc = 0.34
        sw, sh = max(180, int(w * sc)), max(120, int(h * sc))
        small = pygame.Surface((sw, sh))
        ow, oh, oz = self.w, self.h, self.zoom
        self.w, self.h = sw, sh
        self.zoom = 0.52 * sc
        cam = (MAP_SIZE / 2 + math.cos(t * 0.05) * 900, MAP_SIZE / 2 + math.sin(t * 0.04) * 700)
        l = cam[0] - self.w / 2 / self.zoom
        tt = cam[1] - self.h / 2 / self.zoom
        r = cam[0] + self.w / 2 / self.zoom
        b = cam[1] + self.h / 2 / self.zoom
        self._floor(small, l, tt, r, b, {"cam": cam, "floor": (14, 19, 32), "grid": (34, 47, 74)})
        self._bushes(small, m, l, tt, r, b, {"cam": cam})
        self._walls(small, m, l, tt, r, b, {"cam": cam})
        self.w, self.h, self.zoom = ow, oh, oz
        surf.blit(pygame.transform.smoothscale(small, (w, h)), (0, 0))

        # diem sang troi
        for i in range(20):
            a = t * (0.2 + i * 0.01) + i * 1.7
            px = (w / 2 + math.cos(a) * (120 + i * 41)) % w
            py = (h / 2 + math.sin(a * 1.3) * (90 + i * 33)) % h
            T.glow(surf, (px, py), 2 + (i % 4), (0, 150, 210) if i % 3 else (110, 85, 220), 26)

        # phu gradient toi dan
        key = (w, h, round(dim, 2))
        ov = self._ov_cache.get(key)
        if ov is None:
            ov = pygame.Surface((w, h), pygame.SRCALPHA)
            for y in range(h):
                k = 0.45 + 0.55 * (y / max(1, h - 1))
                a = int(255 * dim * k)
                pygame.draw.line(ov, (6, 8, 15, a), (0, y), (w, y))
            self._ov_cache[key] = ov
        surf.blit(ov, (0, 0))
        # vignette
        vg = pygame.Surface((w, h), pygame.SRCALPHA)
        for i in range(7):
            a = 26 - i * 3
            pygame.draw.rect(vg, (0, 0, 0, a), (i * 14, i * 10, w - i * 28, h - i * 20), border_radius=40)
        surf.blit(vg, (0, 0))
