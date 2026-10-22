"""Man hinh choi: du doan vi tri, camera, HUD, spectator, pause, ket thuc."""
import math
import random

import pygame

from ..gamedata import (
    CHAR_MAP, CHARS, SKILL_MAP, GROUP_MAP, MAP_SIZE, WALL_THICK,
    compute_build, hex_rgb, RANGE_MAP,
)
from . import theme as T

TAU = math.pi * 2


def clamp(v, a, b):
    return a if v < a else (b if v > b else v)


class Play:
    def __init__(self, app, msg):
        self.app = app
        self.renderer = app.renderer
        self.map = msg["map"]
        self.settings = msg["settings"]
        self.me_id = msg["you"]
        self.host_id = msg["hostId"]
        self.roster = {p["id"]: p for p in msg.get("players", [])}
        self.renderer.set_map(self.map)

        self.self = {"x": MAP_SIZE / 2, "y": MAP_SIZE / 2, "hp": 100, "mhp": 100, "sh": 0,
                     "al": 1, "k": 0, "d": 0, "rs": 0, "bn": 0, "rt": 0, "sl": 0,
                     "hs": 0, "ph": 0, "is": 0, "atkCd": 0, "cds": []}
        self.pos = [MAP_SIZE / 2, MAP_SIZE / 2]
        self.speed = 230.0
        me = self.roster.get(self.me_id)
        if me:
            b = compute_build({"char": me.get("char"), "stats": me.get("stats"),
                               "gear": me.get("gear"), "skills": me.get("skills")},
                              self.settings.get("startHp", 100))
            self.speed = b["speed"]
        self.others = {}
        self.ents = []
        self.score = []
        self.cds = []
        self.left = 0
        self.spec_list = []
        self.spec_target = 0
        self.spectating = False
        self.chat_log = []
        self.kill_feed = []
        self.chat_open = False
        self.chat_text = ""
        self.paused = False
        self.end = None
        self.shake = 0.0
        self.hurt = 0.0
        self.last_hp = None
        self.keys = {"w": False, "a": False, "s": False, "d": False}
        self.attack = False
        self.aim = 0.0
        self.mouse_world = (MAP_SIZE / 2, MAP_SIZE / 2)
        self.input_acc = 0.0
        self.cam = [self.pos[0], self.pos[1]]
        self.zoom = 1.0
        self.time = 0.0
        self.fps_on = bool(app.profile.settings.get("fps"))
        self.last_snap_at = 0.0
        self.dead_sent = False

    # ---------------- message ----------------
    def on_msg(self, m):
        t = m.get("t")
        if t == "snap":
            self.on_snap(m)
        elif t == "end":
            self.end = m
            self.paused = False
            self.app.sfx.death()
        elif t == "chat":
            self.chat_log.append((m.get("from", "?"), m.get("text", "")))
            if len(self.chat_log) > 40:
                self.chat_log.pop(0)
        elif t == "room":
            # ve lobby do server chuyen
            pass

    def on_snap(self, m):
        y = m.get("you") or {}
        prev_hp = self.self.get("hp")
        self.self.update(y)
        self.cds = y.get("cds", [])
        self.score = m.get("score", [])
        self.left = m.get("left", 0)
        self.ents = m.get("ents", [])
        self.spec_target = m.get("spec", 0)
        if m.get("specList") is not None:
            self.spec_list = m["specList"]
        self.spectating = not bool(y.get("al"))
        if self.spectating and not self.spec_target and self.spec_list:
            self.spec_target = self.spec_list[0]["id"]
            self.app.net.send({"t": "spec", "id": self.spec_target})

        # du doan vi tri
        if not y.get("al"):
            self.pos = [y.get("x", self.pos[0]), y.get("y", self.pos[1])]
        else:
            ex, ey = self.pos[0] - y.get("x", 0), self.pos[1] - y.get("y", 0)
            if math.hypot(ex, ey) > 160:
                self.pos = [y.get("x", 0), y.get("y", 0)]
            else:
                self.pos[0] -= ex * 0.25
                self.pos[1] -= ey * 0.25

        # nguoi khac: lam muot
        seen = set()
        for e in self.ents:
            if e.get("k") != "p":
                continue
            pid = e.get("id")
            if pid == self.me_id:
                continue
            seen.add(pid)
            o = self.others.get(pid)
            if o is None:
                self.others[pid] = {"x": e["x"], "y": e["y"], **e}
            else:
                o["tx"], o["ty"] = e["x"], e["y"]
                o.update({k: v for k, v in e.items() if k not in ("x", "y")})
        for pid in list(self.others.keys()):
            if pid not in seen and pid != self.me_id:
                del self.others[pid]

        # hieu ung
        for e in m.get("fx", []):
            self.renderer.spawn_fx(e)
            k = e.get("k")
            if k == "shoot":
                self.app.sfx.shoot(e.get("w", "gun"))
            elif k == "hit":
                self.app.sfx.hit()
            elif k == "boom":
                self.app.sfx.boom()
                d = math.hypot(e.get("x", 0) - self.pos[0], e.get("y", 0) - self.pos[1])
                if d < 420:
                    self.shake = max(self.shake, 9 * (1 - d / 420))
            elif k in ("beam", "snipe", "chain"):
                self.app.sfx.beam()
            elif k == "slash":
                self.app.sfx.slash()
            elif k == "kill":
                self.kill_feed.append({"a": e.get("a", ""), "b": e.get("b", ""),
                                       "c": e.get("c", "#fff"), "t": 6.0})
                if len(self.kill_feed) > 5:
                    self.kill_feed.pop(0)
                if e.get("b") == self.roster.get(self.me_id, {}).get("name"):
                    self.shake = max(self.shake, 12)
                self.app.sfx.kill()
            elif k == "heal":
                self.app.sfx.heal()
            elif k == "spawn":
                self.app.sfx.spawn()

        # mat mau -> rung + am
        if prev_hp is not None and y.get("hp", 0) < prev_hp - 0.5:
            self.hurt = min(1.0, self.hurt + 0.55)
            self.shake = max(self.shake, 5)
            self.app.sfx.hurt()

    # ---------------- update ----------------
    def update(self, dt, events, ui):
        self.time += dt
        self.renderer.update(dt)
        self.shake = max(0.0, self.shake - dt * 26)
        self.hurt = max(0.0, self.hurt - dt * 1.5)
        for kf in self.kill_feed:
            kf["t"] -= dt
        self.kill_feed = [k for k in self.kill_feed if k["t"] > 0]

        if self.end:
            self.update_end(dt, events, ui)
            return

        if self.paused:
            self.update_pause(dt, events, ui)
            return

        # chat
        if self.chat_open:
            # o nhap duoc ve trong draw_hud; o day chi giu: dung di chuyen, ESC dong
            for e in events:
                if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    self.chat_open = False
                    ui.focus = None
            return

        # phim
        for e in events:
            if e.type == pygame.KEYDOWN:
                k = e.key
                if k == pygame.K_ESCAPE:
                    self.set_paused(True)
                    continue
                if k == pygame.K_RETURN:
                    self.chat_open = True
                    self.chat_text = ""
                    ui.focus = "gchat"
                    continue
                if k == pygame.K_F3:
                    self.fps_on = not self.fps_on
                    continue
                if k in (pygame.K_q, pygame.K_e) and self.spectating:
                    self.cycle_spec(-1 if k == pygame.K_q else 1)
                    continue
                if pygame.K_1 <= k <= pygame.K_5:
                    self.cast(k - pygame.K_1)
                    continue

        pressed = pygame.key.get_pressed()
        self.keys["w"] = pressed[pygame.K_w] or pressed[pygame.K_UP]
        self.keys["a"] = pressed[pygame.K_a] or pressed[pygame.K_LEFT]
        self.keys["s"] = pressed[pygame.K_s] or pressed[pygame.K_DOWN]
        self.keys["d"] = pressed[pygame.K_d] or pressed[pygame.K_RIGHT]
        self.attack = pygame.mouse.get_pressed()[0]

        self.update_self(dt)
        self.update_others(dt)
        self.update_camera(dt)

        # gui input 30Hz
        self.input_acc += dt
        if self.input_acc >= 1 / 30:
            self.input_acc = 0.0
            self.send_input()

    def update_self(self, dt):
        if not self.self.get("al"):
            return
        mx = (1 if self.keys["d"] else 0) - (1 if self.keys["a"] else 0)
        my = (1 if self.keys["s"] else 0) - (1 if self.keys["w"] else 0)
        ml = math.hypot(mx, my)
        sp = self.speed
        if self.self.get("rt"):
            sp = 0
        elif self.self.get("sl"):
            sp *= 0.7
        if ml > 0 and sp > 0:
            self.pos[0] += (mx / ml) * sp * dt
            self.pos[1] += (my / ml) * sp * dt
        self.resolve_walls()
        self.pos[0] = clamp(self.pos[0], WALL_THICK + 18, MAP_SIZE - WALL_THICK - 18)
        self.pos[1] = clamp(self.pos[1], WALL_THICK + 18, MAP_SIZE - WALL_THICK - 18)

        # ngam theo chuot
        r = self.renderer
        self.mouse_world = r.screen_to_world(pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1], self.cam)
        self.aim = math.atan2(self.mouse_world[1] - self.pos[1], self.mouse_world[0] - self.pos[0])

    def resolve_walls(self):
        """Day nhan vat ra khoi vat can ngay tren client (khop voi server)."""
        r = 17
        x, y = self.pos
        walls = self.map.get("walls", []) + [e for e in self.ents if e.get("k") == "w"]
        for w in walls:
            if w.get("t") == "r":
                nx = clamp(x, w["x"], w["x"] + w["w"])
                ny = clamp(y, w["y"], w["y"] + w["h"])
                dx, dy = x - nx, y - ny
                dd = dx * dx + dy * dy
                if dd < r * r:
                    if dd < 1e-6:
                        left = x - w["x"]
                        right = w["x"] + w["w"] - x
                        top = y - w["y"]
                        bot = w["y"] + w["h"] - y
                        m = min(left, right, top, bot)
                        if m == left:
                            x = w["x"] - r
                        elif m == right:
                            x = w["x"] + w["w"] + r
                        elif m == top:
                            y = w["y"] - r
                        else:
                            y = w["y"] + w["h"] + r
                    else:
                        d = math.sqrt(dd)
                        push = (r - d) / d
                        x += dx * push
                        y += dy * push
            else:
                dx, dy = x - w["x"], y - w["y"]
                rr = r + w["r"]
                dd = dx * dx + dy * dy
                if dd < rr * rr:
                    d = math.sqrt(dd) or 1
                    x = w["x"] + dx / d * rr
                    y = w["y"] + dy / d * rr
        self.pos[0], self.pos[1] = x, y

    def update_others(self, dt):
        k = min(1.0, dt * 16)
        for o in self.others.values():
            tx = o.get("tx", o["x"])
            ty = o.get("ty", o["y"])
            o["x"] += (tx - o["x"]) * k
            o["y"] += (ty - o["y"]) * k

    def update_camera(self, dt):
        r = self.renderer
        self.zoom = clamp(min(r.w / 1180.0, r.h / 720.0), 0.62, 1.35)
        fx, fy = self.pos
        if self.spectating and self.spec_target in self.others:
            o = self.others[self.spec_target]
            fx, fy = o["x"], o["y"]
        mx, my = pygame.mouse.get_pos()
        dx = clamp((mx - r.w / 2) * 0.14, -110, 110)
        dy = clamp((my - r.h / 2) * 0.14, -90, 90)
        tx, ty = fx + dx, fy + dy
        # gioi han camera trong map
        half_w = r.w / 2 / self.zoom
        half_h = r.h / 2 / self.zoom
        tx = clamp(tx, half_w, MAP_SIZE - half_w)
        ty = clamp(ty, half_h, MAP_SIZE - half_h)
        self.cam[0] += (tx - self.cam[0]) * min(1.0, dt * 9)
        self.cam[1] += (ty - self.cam[1]) * min(1.0, dt * 9)

    def send_input(self):
        if self.paused or self.end:
            return
        ax, ay = math.cos(self.aim), math.sin(self.aim)
        self.app.net.send({
            "t": "input",
            "u": 1 if self.keys["w"] else 0,
            "d": 1 if self.keys["s"] else 0,
            "l": 1 if self.keys["a"] else 0,
            "r": 1 if self.keys["d"] else 0,
            "a": 1 if self.attack else 0,
            "ax": round(ax, 3), "ay": round(ay, 3),
        })

    def send_neutral(self):
        self.app.net.send({"t": "input", "u": 0, "d": 0, "l": 0, "r": 0, "a": 0,
                           "ax": round(math.cos(self.aim), 3), "ay": round(math.sin(self.aim), 3)})

    def cast(self, slot):
        if not self.self.get("al"):
            return
        if slot < len(self.cds) and self.cds[slot].get("left", 0) > 0:
            return
        self.app.net.send({"t": "cast", "slot": slot,
                           "ax": round(math.cos(self.aim), 3), "ay": round(math.sin(self.aim), 3),
                           "tx": round(self.mouse_world[0], 1), "ty": round(self.mouse_world[1], 1)})
        self.app.sfx.cast()

    def cycle_spec(self, d):
        if not self.spec_list:
            return
        ids = [s["id"] for s in self.spec_list]
        try:
            i = ids.index(self.spec_target)
        except ValueError:
            i = 0
        self.spec_target = ids[(i + d) % len(ids)]
        self.app.net.send({"t": "spec", "id": self.spec_target})
        self.app.sfx.ui()

    # ---------------- pause ----------------
    def set_paused(self, v):
        self.paused = v
        if v:
            self.keys = {"w": False, "a": False, "s": False, "d": False}
            self.attack = False
            self.send_neutral()

    def update_pause(self, dt, events, ui):
        for e in events:
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                self.set_paused(False)
                return

    # ---------------- end ----------------
    def update_end(self, dt, events, ui):
        pass

    # ---------------- draw ----------------
    def draw(self, surf, ui, dt):
        r = self.renderer
        r.w, r.h = surf.get_size()
        cam = list(self.cam)
        if self.shake > 0.3:
            cam[0] += random.uniform(-1, 1) * self.shake
            cam[1] += random.uniform(-1, 1) * self.shake

        players = []
        for o in self.others.values():
            players.append(o)
        if self.self.get("al"):
            me = self.roster.get(self.me_id, {})
            players.append({
                "k": "p", "id": self.me_id, "n": self.app.profile.display_name,
                "c": me.get("char", "shadow"), "x": self.pos[0], "y": self.pos[1],
                "a": self.aim, "hp": self.self.get("hp", 0), "mhp": self.self.get("mhp", 100),
                "sh": self.self.get("sh", 0), "bn": self.self.get("bn", 0),
                "ph": self.self.get("ph", 0), "hs": self.self.get("hs", 0),
                "is": self.self.get("is", 0), "sl": self.self.get("sl", 0),
                "rt": self.self.get("rt", 0),
            })

        projs = [e for e in self.ents if e.get("k") == "b"]
        mines = [e for e in self.ents if e.get("k") == "m"]
        snares = [e for e in self.ents if e.get("k") == "t"]
        smokes = [e for e in self.ents if e.get("k") == "s"]
        dwalls = [e for e in self.ents if e.get("k") == "w"]
        turrets = [e for e in self.ents if e.get("k") == "u"]

        world = {
            "map": self.map, "cam": cam, "zoom": self.zoom,
            "players": players, "projs": projs, "mines": mines, "snares": snares,
            "smokes": smokes, "dyn_walls": dwalls, "turrets": turrets,
            "self_id": self.me_id, "self_pos": self.pos,
            "show_aim": bool(self.self.get("al")) and not self.paused and not self.end,
            "mouse": pygame.mouse.get_pos(),
        }
        r.draw(surf, world)

        # vignette nhe cho co do sau
        key = (r.w, r.h)
        vg = self.app.vignette(key)
        if vg:
            surf.blit(vg, (0, 0))

        # am do khi mat mau
        if self.hurt > 0.01:
            ov = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
            a = int(70 * self.hurt)
            for i in range(6):
                pygame.draw.rect(ov, (200, 20, 40, max(0, a - i * 8)),
                                 (i * 12, i * 8, r.w - i * 24, r.h - i * 16), border_radius=40)
            surf.blit(ov, (0, 0))

        self.draw_hud(surf, ui, dt)
        if self.paused:
            self.draw_pause(surf, ui, dt)
        if self.end:
            self.draw_end(surf, ui, dt)

    # ---------------- HUD ----------------
    def draw_hud(self, surf, ui, dt):
        r = self.renderer
        w, h = r.w, r.h
        me = self.self
        alive = bool(me.get("al"))
        mode = self.settings.get("mode")

        # ---- match-info (pill tren cung giua) ----
        mode_data = None
        from ..gamedata import MODE_MAP as _MM
        mode_data = _MM.get(mode, {"name": "FFA"})
        mi_w = 240
        mi = pygame.Rect(w / 2 - mi_w / 2, 12, mi_w, 32)
        T.rect(surf, mi, (10, 12, 22, 204), 10)
        pygame.draw.rect(surf, T.LINE, mi, 1, border_radius=10)
        T.text(surf, mode_data["name"], (mi.x + 18, mi.y + 9), 12, T.TXT)
        if mode == "time":
            t = max(0, int(self.left))
            T.text(surf, "%d:%02d" % (t // 60, t % 60), (mi.right - 18, mi.y + 7), 14,
                   T.CYAN, align="right", bold=True, mono=True)
        elif mode == "kills":
            T.text(surf, "%d/%d" % (me.get("k", 0), self.settings.get("killTarget", 20)),
                   (mi.right - 18, mi.y + 7), 14, T.CYAN, align="right", bold=True, mono=True)

        # ---- killfeed (tren ben trai) ----
        fy = 14
        for kf in self.kill_feed:
            a = int(255 * clamp(kf["t"] / 1.2, 0, 1))
            name_a = kf["a"] or "?"
            w1 = T.text_size(name_a, 11, True)[0]
            w2 = T.text_size(kf["b"], 11)[0]
            total = w1 + 26 + w2
            rr = pygame.Rect(14, fy, total + 20, 24)
            T.rect(surf, rr, (10, 12, 22, 191), 7)
            # border-left 3px accent
            pygame.draw.rect(surf, T.ACCENT, (rr.x, rr.y, 3, rr.h), border_radius=2)
            T.text(surf, name_a, (rr.x + 12, fy + 5), 11, T.CYAN, bold=True, alpha=a)
            T.text(surf, "▸", (rr.x + 12 + w1 + 4, fy + 5), 10, T.TXT, alpha=a)
            T.text(surf, kf["b"], (rr.x + 12 + w1 + 22, fy + 5), 11, T.PINK, bold=True, alpha=a)
            fy += 29

        # ---- mini-score (ben phai, duoi minimap) ----
        sx = w - 200 - 14
        sy = 228
        for i, row in enumerate(self.score[:6]):
            is_me = row.get("id") == self.me_id
            rr = pygame.Rect(sx, sy, 200, 24)
            T.rect(surf, rr, (0, 229, 255, 26) if is_me else (10, 12, 22, 184), 8)
            T.rect(surf, rr, (0, 229, 255, 102) if is_me else (255, 255, 255, 15), 8, width=1)
            ch = CHAR_MAP.get(row.get("char"), CHARS[0])
            T.text(surf, str(i + 1), (rr.x + 9, rr.y + 5), 11, T.MUTED, mono=True)
            T.text(surf, T.fit(row.get("name", "?"), 11.5, 120), (rr.x + 26, rr.y + 5), 11.5,
                   hex_rgb(ch["color"]))
            T.text(surf, "%d" % row.get("kills", 0), (rr.right - 10, rr.y + 4), 12.5, T.CYAN,
                   align="right", bold=True, mono=True)
            sy += 28

        # ---- self-status (duoi ben trai): thanh mau + ten ----
        if alive:
            hx, hy = 16, h - 16 - 26 - 22
            bw2 = 300
            # .self-name (tren thanh mau)
            ch = CHAR_MAP.get(self.roster.get(self.me_id, {}).get("char"), CHARS[0])
            nm = self.app.profile.display_name
            T.text(surf, nm, (hx, hy), 12, hex_rgb(ch["color"]), bold=True)
            kd_x = hx + T.text_size(nm, 12, True)[0] + 12
            T.text(surf, "%d mạng · %d chết" % (me.get("k", 0), me.get("d", 0)),
                   (kd_x, hy), 11, T.MUTED)
            hy += 18
            # .hp-wrap 26px
            wrap_r = pygame.Rect(hx, hy, bw2, 26)
            T.rect(surf, wrap_r, (0, 0, 0, 153), 8)
            T.rect(surf, wrap_r, (255, 255, 255, 31), 8, width=1)
            t = clamp(me.get("hp", 0) / max(1, me.get("mhp", 1)), 0, 1)
            if t > 0.55:
                g1, g2 = (34, 196, 122), (61, 220, 151)
            elif t > 0.28:
                g1, g2 = (255, 155, 61), (255, 182, 72)
            else:
                g1, g2 = T.ACCENT, T.ORANGE
            if t > 0.001:
                fw = max(8, int(bw2 * t) // 4 * 4)   # luong tuong hoa de cache gradient
                fill = T.rounded_hgrad(fw, 26, g1, g2, 8)
                surf.blit(fill, (wrap_r.x, wrap_r.y))
            # shield: cyan->purple, chieu rong = sh/60
            shf = clamp(me.get("sh", 0) / 60.0, 0, 1)
            if shf > 0.001:
                sw4 = max(8, int(bw2 * shf) // 4 * 4)
                sf = T.rounded_hgrad(sw4, 26, T.CYAN, T.PURPLE, 8)
                sf = sf.copy()
                sf.set_alpha(191)
                surf.blit(sf, (wrap_r.x, wrap_r.y))
            # hp text
            sh_txt = ("  +%d" % round(me.get("sh", 0))) if me.get("sh", 0) > 0 else ""
            T.text(surf, "%d / %d%s" % (max(0, round(me.get("hp", 0))), me.get("mhp", 100), sh_txt),
                   (wrap_r.centerx, wrap_r.centery - 8), 12, T.WHITE, align="center",
                   bold=True, mono=True, shadow=True)
            by = hy + 26 + 8

            # ---- weapon-info + skillbar (duoi giua) ----
            weapon = self.roster.get(self.me_id, {})
            wpname = ""
            try:
                from ..gamedata import GEAR_MAP
                wpname = GEAR_MAP.get((weapon.get("gear") or {}).get("weapon"), {}).get("name", "")
            except Exception:
                pass
            slot_w, slot_h, gap = 70, 72, 8
            # Edge: skillbar chi gom cac chiêu da chon (co the it hon 5)
            n_slots = max(1, min(5, len(self.cds)))
            total = n_slots * slot_w + (n_slots - 1) * gap
            bx = w / 2 - total / 2
            by_s = h - 26 - slot_h
            # weapon-info phia tren skillbar
            T.text(surf, wpname, (w / 2, by_s - 18), 11, T.MUTED, align="center")
            for i in range(n_slots):
                cds = self.cds[i] if i < len(self.cds) else None
                left = cds.get("left", 0) if cds else 0
                cd = cds.get("cd", 1) if cds else 1
                sid = cds.get("id") if cds else None
                sk = SKILL_MAP.get(sid)
                x = bx + i * (slot_w + gap)
                ready = left <= 0.05
                hov = ui.hovered((x, by_s, slot_w, slot_h))
                # .slot: gradient doc 180deg
                g = T.rounded_vgrad(slot_w, slot_h, (22, 26, 42), (10, 12, 22), 12)
                surf.blit(g, (x, by_s))
                if ready:
                    T.rect(surf, (x, by_s, slot_w, slot_h), (0, 229, 255, 115), 12, width=1)
                else:
                    pygame.draw.rect(surf, T.LINE, (x, by_s, slot_w, slot_h), 1, border_radius=12)
                T.text(surf, str(i + 1), (x + 6, by_s + 3), 9.5, T.MUTED, mono=True)
                if sk:
                    grp = GROUP_MAP.get(sk["group"], {"color": "#fff"})
                    col = hex_rgb(grp["color"])
                    if ready and r.use_glow:
                        T.glow(surf, (x + slot_w / 2, by_s + 28), 20, col, 60)
                    T.text(surf, sk["icon"], (x + slot_w / 2, by_s + 17), 20, col, align="center")
                    nm2 = T.fit(sk["name"], 8.5, slot_w - 8)
                    T.text(surf, nm2, (x + slot_w / 2, by_s + 44), 8.5, T.MUTED, align="center")
                if not ready:
                    # cdmask tu duoi len
                    frac = clamp(left / max(0.01, cd), 0, 1)
                    hh = int(slot_h * frac)
                    ov = pygame.Surface((slot_w - 2, hh), pygame.SRCALPHA)
                    ov.fill((0, 0, 0, 184))
                    surf.blit(ov, (x + 1, by_s + slot_h - 1 - hh))
                    T.text(surf, "%d" % math.ceil(left), (x + slot_w / 2, by_s + slot_h / 2 - 9), 16,
                           T.WHITE, align="center", bold=True, mono=True, shadow=True)
                if ui.click and hov:
                    ui.click = None
                    self.cast(i)
            # phim tat chat ngay phia tren skillbar (thay the weapon-info khi trong tran)
            if self.time < 12:
                T.text(surf, "WASD di chuyển · Chuột ngắm · Giữ chuột trái bắn · 1-5 dùng chiêu",
                       (w / 2, by_s - 40), 10.5, T.MUTED, align="center",
                       alpha=int(255 * clamp((12 - self.time) / 4, 0, 1)))

        # ---- hud-help (cuoi man hinh, luon hien) ----
        T.text(surf, "WASD di chuyển · Chuột ngắm · Giữ chuột trái bắn · 1-5 dùng chiêu · Enter chat · ESC thoát",
               (w / 2, h - 20), 10, (63, 70, 100), align="center")

        # ---- man hinh hoi sinh (center-overlay) ----
        if not alive and not self.end:
            # nen radial do nhe
            ov = pygame.Surface((w, h), pygame.SRCALPHA)
            T.glow(ov, (w / 2, h / 2), int(max(w, h) * 0.42), T.ACCENT, 26)
            ov.fill((3, 4, 8, 110))
            surf.blit(ov, (0, 0))
            if mode == "last":
                T.text(surf, "BẠN ĐÃ BỊ HẠ", (w / 2, h / 2 - 60), 24, T.WHITE, align="center",
                       bold=True, shadow=True)
                T.text(surf, "Đang xem trận đấu...", (w / 2, h / 2 - 20), 12, T.MUTED, align="center")
            else:
                T.text(surf, "BẠN ĐÃ BỊ HẠ", (w / 2, h / 2 - 90), 24, T.WHITE, align="center",
                       bold=True, shadow=True)
                T.text(surf, "%.0f" % math.ceil(self.self.get("rs", 0)), (w / 2, h / 2 - 50), 52,
                       T.CYAN, align="center", bold=True, mono=True)
                T.text(surf, "Hồi sinh sau", (w / 2, h / 2 + 22), 12, T.MUTED, align="center")
            self.draw_spec(surf, ui)

        # ---- chat ----
        if not self.chat_open and self.chat_log:
            cy = h - 170 - len(self.chat_log[-6:]) * 22
            for who, text in self.chat_log[-6:]:
                rr = pygame.Rect(w / 2 - 210, cy, 420, 20)
                T.rect(surf, rr, (10, 12, 22, 204), 7)
                T.text(surf, who + ":", (rr.x + 10, cy + 3), 10.5, T.CYAN, bold=True)
                T.text(surf, text, (rr.x + 10 + T.text_size(who + ":", 10.5, True)[0] + 5, cy + 3),
                       10.5, T.TXT)
                cy += 22
        if self.chat_open:
            inp = pygame.Rect(w / 2 - 210, h - 120, 420, 34)
            self.chat_text, sub = ui.text_input("gchat", inp, self.chat_text,
                                                "Nhắn tin rồi Enter...", 140, size=12)
            if sub:
                if self.chat_text.strip():
                    self.app.net.send({"t": "chat", "text": self.chat_text.strip()})
                self.chat_text = ""
                self.chat_open = False
                ui.focus = None

        # ---- fps ----
        if self.fps_on:
            rr = pygame.Rect(w / 2 - 34, 14, 68, 22)
            T.rect(surf, rr, (0, 0, 0, 102), 5)
            T.text(surf, "%d FPS" % self.app.fps, (w / 2, rr.y + 4), 10.5, (124, 134, 168),
                   align="center", mono=True)

    def draw_spec(self, surf, ui):
        r = self.renderer
        w = r.w
        name = "—"
        for s in self.spec_list:
            if s["id"] == self.spec_target:
                name = s["n"]
        # .spec-bar: pill tren cung giua (top 58)
        name_w = T.text_size(name, 13, True)[0]
        host = self.me_id == self.host_id
        bw = 150 + name_w + (230 if host else 96)
        bx = w / 2 - bw / 2
        bar = pygame.Rect(bx, 58, bw, 40)
        T.rect(surf, bar, (10, 12, 22, 219), 12)
        T.rect(surf, bar, (255, 255, 255, 26), 12, width=1)
        # sb-tag gradient "ĐANG XEM"
        tag = "ĐANG XEM"
        tw = T.text_size(tag, 8.5, True)[0]
        tg = T.rounded_hgrad(tw + 14, 15, T.CYAN, T.PURPLE, 5)
        surf.blit(tg, (bar.x + 10, bar.y + 12))
        T.text(surf, tag, (bar.x + 17, bar.y + 14), 8.5, (4, 18, 26), bold=True)
        T.text(surf, T.fit(name, 13, 190), (bar.x + 32 + tw, bar.y + 12), 13, T.WHITE, bold=True)
        if ui.button("sp", (bar.right - (96 if host else 88), bar.y + 8, 40, 24), "◀ Q",
                     "normal", size=9.5, radius=7):
            self.cycle_spec(-1)
        if ui.button("sn", (bar.right - 50, bar.y + 8, 40, 24), "E ▶", "normal", size=9.5, radius=7):
            self.cycle_spec(1)
        if host:
            if ui.button("shres", (bar.right - 208, bar.y + 8, 74, 24), "Chơi lại", "normal", size=9.5, radius=7):
                self.app.net.send({"t": "admin", "cmd": "restart"})
            if ui.button("shlob", (bar.right - 288, bar.y + 8, 74, 24), "Về phòng chờ", "normal",
                         size=9.5, radius=7):
                self.app.net.send({"t": "admin", "cmd": "lobby"})

    def draw_pause(self, surf, ui, dt):
        r = self.renderer
        ov = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
        ov.fill((3, 4, 8, 199))
        surf.blit(ov, (0, 0))
        box = pygame.Rect(0, 0, 460, 382)
        box.center = (r.w // 2, r.h // 2)
        T.panel(surf, box, 16)
        T.text(surf, "TẠM DỪNG", (box.centerx, box.y + 30), 24, T.WHITE, bold=True, align="center",
               shadow=True)
        T.text(surf, "Trận đấu vẫn tiếp tục — nhân vật của bạn đang đứng yên.",
               (box.centerx, box.y + 70), 10.5, T.MUTED, align="center")
        bw = 300
        bx = box.centerx - bw / 2
        by = box.y + 108
        if ui.button("pres", (bx, by, bw, 44), "Tiếp tục", "primary", size=14):
            self.set_paused(False)
        if ui.button("pset", (bx, by + 52, bw, 38), "Cài đặt", "normal", size=12):
            self.app.open_settings()
        if ui.button("pleave", (bx, by + 96, bw, 38), "Rời trận", "danger", size=12):
            self.app.ask_confirm("Rời trận?", "Bạn sẽ trở về Hub và rời khỏi phòng.",
                                 "Rời trận", self.app.leave_room, danger=True)
        T.text(surf, "Nhấn ESC để quay lại trận", (box.centerx, box.bottom - 32), 9.5,
               T.DIM, align="center")

    def draw_end(self, surf, ui, dt):
        r = self.renderer
        ov = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
        ov.fill((3, 4, 8, 199))
        surf.blit(ov, (0, 0))
        w = r.w
        end = self.end
        winner = end.get("winner") or {}
        score = end.get("score") or []
        me_in = any(s.get("id") == self.me_id for s in score)

        # .end-box: 560px panel giua
        bw2 = min(560, w - 40)
        rows = min(len(score), 8)
        bh = 66 + 26 + rows * 30 + 30 + 70
        box = pygame.Rect((w - bw2) // 2, max(20, (r.h - bh) // 2), bw2, bh)
        T.panel(surf, box, 16)
        # tieu de gradient giong CSS .end-box h2
        if winner and winner.get("id") == self.me_id:
            title = "BẠN THẮNG!"
        elif winner:
            title = (winner.get("name") or "Ai đó") + " thắng"
        else:
            title = "Kết thúc trận"
        T.grad_text(surf, title, (box.centerx, box.y + 20), 24,
                    [(0.0, T.WHITE), (0.5, T.LAVENDER), (1.0, T.CYAN)],
                    bold=True, align="center")

        # .escore rows
        yy = box.y + 66
        for i, row in enumerate(score[:8]):
            rr = pygame.Rect(box.x + 20, yy, bw2 - 40, 26)
            ch = CHAR_MAP.get(row.get("char"), CHARS[0])
            if i == 0:
                g = T.rounded_hgrad(rr.w, rr.h, (255, 182, 72, 56), (255, 45, 111, 31), 9)
                surf.blit(g, rr.topleft)
                T.rect(surf, rr, (255, 182, 72, 102), 9, width=1)
            else:
                T.rect(surf, rr, (255, 255, 255, 10), 9)
            T.text(surf, "#%d" % (i + 1), (rr.x + 12, rr.y + 6), 11.5, T.MUTED, mono=True)
            T.text(surf, T.fit(row.get("name", "?"), 12, rr.w - 260), (rr.x + 46, rr.y + 6), 12,
                   hex_rgb(ch["color"]), bold=True)
            st = "%d mạng · %d chết · %d dmg" % (row.get("kills", 0), row.get("deaths", 0),
                                                 row.get("dmg", 0))
            T.text(surf, st, (rr.right - 12, rr.y + 7), 10.5, T.MUTED, align="right", mono=True)
            yy += 30

        # nut hanh dong
        by = box.bottom - 62
        T.text(surf, "Tự động về phòng chờ sau ít giây, hoặc bấm nút bên dưới.",
               (box.centerx, box.bottom - 82), 10, T.MUTED, align="center")
        is_host = self.me_id == self.host_id
        btn_w = 150
        if is_host:
            if ui.button("ereplay", (box.centerx - btn_w - 6, by, btn_w, 38), "Chơi lại", "primary", size=13):
                self.app.net.send({"t": "admin", "cmd": "restart"})
            if ui.button("elobby", (box.centerx + 6, by, btn_w, 38), "Về phòng chờ", "normal", size=12):
                self.app.net.send({"t": "leave"})
                self.app.back_to_hub()
        else:
            if ui.button("elobby", (box.centerx - btn_w / 2, by, btn_w, 38), "Về phòng chờ", "primary", size=13):
                self.app.net.send({"t": "leave"})
                self.app.back_to_hub()


# import muon de tranh vong lap
from .screens import avatar  # noqa: E402
