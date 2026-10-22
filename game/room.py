# ============================================================
#  NEON CLASH - Room: toan bo gameplay (server authoritative)
# ============================================================
import math
import random

from .gamedata import (
    MAP_SIZE, WALL_THICK, compute_build, sanitize_loadout, SKILL_MAP,
    CHAR_MAP, DEFAULT_SETTINGS, DEFAULT_LOADOUT,
)

TICK_RATE = 30
DT = 1.0 / TICK_RATE
TAU = math.pi * 2
PLAYER_R = 17


def clamp(v, a, b):
    return a if v < a else (b if v > b else v)


def r0(v):
    return int(v + 0.5) if v >= 0 else -int(-v + 0.5)


def r1(v):
    return (int(v * 10 + 0.5) if v >= 0 else -int(-v * 10 + 0.5)) / 10.0


def r2(v):
    return (int(v * 100 + 0.5) if v >= 0 else -int(-v * 100 + 0.5)) / 100.0


def d2(ax, ay, bx, by):
    return (ax - bx) ** 2 + (ay - by) ** 2


def mulberry32(seed):
    a = seed & 0xFFFFFFFF

    def rnd():
        nonlocal a
        a = (a + 0x6D2B79F5) & 0xFFFFFFFF
        t = a
        t = ((t ^ (t >> 15)) * (1 | t)) & 0xFFFFFFFF
        t = ((t + ((t ^ (t >> 7)) * (61 | t))) ^ t) & 0xFFFFFFFF
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296.0

    return rnd


# ---------------- hinh hoc ----------------
def seg_circle(x1, y1, x2, y2, cx, cy, r):
    dx, dy = x2 - x1, y2 - y1
    l2 = dx * dx + dy * dy
    t = ((cx - x1) * dx + (cy - y1) * dy) / l2 if l2 > 0 else 0
    t = clamp(t, 0, 1)
    px, py = x1 + dx * t, y1 + dy * t
    return (px - cx) ** 2 + (py - cy) ** 2 <= r * r


def seg_rect(x1, y1, x2, y2, rect, pad=0):
    min_x, max_x = rect["x"] - pad, rect["x"] + rect["w"] + pad
    min_y, max_y = rect["y"] - pad, rect["y"] + rect["h"] + pad
    t0, t1 = 0.0, 1.0
    dx, dy = x2 - x1, y2 - y1
    tests = [(-dx, x1 - min_x), (dx, max_x - x1), (-dy, y1 - min_y), (dy, max_y - y1)]
    for p, q in tests:
        if p == 0:
            if q < 0:
                return False
        else:
            t = q / p
            if p < 0:
                if t > t1:
                    return False
                if t > t0:
                    t0 = t
            else:
                if t < t0:
                    return False
                if t < t1:
                    t1 = t
    return True


def seg_walls_list(walls, x1, y1, x2, y2, pad=0):
    for w in walls:
        if w.get("t") == "r":
            if seg_rect(x1, y1, x2, y2, w, pad):
                return True
        elif seg_circle(x1, y1, x2, y2, w["x"], w["y"], w["r"] + pad):
            return True
    return False


def point_in_walls(walls, x, y, pad=0):
    for w in walls:
        if w.get("t") == "r":
            if w["x"] - pad < x < w["x"] + w["w"] + pad and w["y"] - pad < y < w["y"] + w["h"] + pad:
                return True
        elif d2(x, y, w["x"], w["y"]) < (w["r"] + pad) ** 2:
            return True
    return False


# ---------------- sinh map ----------------
def make_map(seed):
    rng = mulberry32(int(seed) & 0x7FFFFFFF)
    walls = []
    T = WALL_THICK
    walls.append({"t": "r", "x": 0, "y": 0, "w": MAP_SIZE, "h": T})
    walls.append({"t": "r", "x": 0, "y": MAP_SIZE - T, "w": MAP_SIZE, "h": T})
    walls.append({"t": "r", "x": 0, "y": 0, "w": T, "h": MAP_SIZE})
    walls.append({"t": "r", "x": MAP_SIZE - T, "y": 0, "w": T, "h": MAP_SIZE})

    inner = []
    # khoi chu nhat
    for _ in range(46):
        for _k in range(40):
            w = 90 + rng() * 240
            h = 70 + rng() * 190
            x = 160 + rng() * (MAP_SIZE - 320 - w)
            y = 160 + rng() * (MAP_SIZE - 320 - h)
            if d2(x + w / 2, y + h / 2, MAP_SIZE / 2, MAP_SIZE / 2) < 260 ** 2:
                continue
            ok = True
            for o in inner:
                if (x < o["x"] + o["w"] + 110 and x + w + 110 > o["x"]
                        and y < o["y"] + o["h"] + 110 and y + h + 110 > o["y"]):
                    ok = False
                    break
            if not ok:
                continue
            rect = {"t": "r", "x": r0(x), "y": r0(y), "w": r0(w), "h": r0(h)}
            inner.append(rect)
            walls.append(rect)
            break

    # cot tron
    for _ in range(26):
        for _k in range(30):
            rr = 42 + rng() * 70
            x = 200 + rng() * (MAP_SIZE - 400)
            y = 200 + rng() * (MAP_SIZE - 400)
            if d2(x, y, MAP_SIZE / 2, MAP_SIZE / 2) < 240 ** 2:
                continue
            ok = True
            for o in inner:
                if (o["x"] - rr - 90 < x < o["x"] + o["w"] + rr + 90
                        and o["y"] - rr - 90 < y < o["y"] + o["h"] + rr + 90):
                    ok = False
                    break
            if not ok:
                continue
            c = {"t": "c", "x": r0(x), "y": r0(y), "r": r0(rr)}
            inner.append({"x": x - rr, "y": y - rr, "w": rr * 2, "h": rr * 2})
            walls.append(c)
            break

    # bui co
    bushes = []
    for _ in range(34):
        for _k in range(30):
            rr = 80 + rng() * 65
            x = 180 + rng() * (MAP_SIZE - 360)
            y = 180 + rng() * (MAP_SIZE - 360)
            if point_in_walls(walls, x, y, rr + 10):
                continue
            ok = True
            for b in bushes:
                if d2(x, y, b["x"], b["y"]) < (rr + b["r"] + 60) ** 2:
                    ok = False
                    break
            if not ok:
                continue
            bushes.append({"x": r0(x), "y": r0(y), "r": r0(rr)})
            break

    # diem spawn
    spawns = []
    for _ in range(24):
        for _k in range(40):
            x = 200 + rng() * (MAP_SIZE - 400)
            y = 200 + rng() * (MAP_SIZE - 400)
            if point_in_walls(walls, x, y, 46):
                continue
            ok = True
            for s in spawns:
                if d2(x, y, s["x"], s["y"]) < 380 ** 2:
                    ok = False
                    break
            if not ok:
                continue
            spawns.append({"x": r0(x), "y": r0(y)})
            break
    if not spawns:
        spawns.append({"x": MAP_SIZE / 2, "y": MAP_SIZE / 2})

    return {"size": MAP_SIZE, "walls": walls, "bushes": bushes, "spawns": spawns, "seed": seed}


class Player:
    __slots__ = (
        "id", "name", "ready", "loadout", "build", "x", "y", "angle", "hp", "maxHp",
        "shield", "alive", "respawnAt", "kills", "deaths", "streak", "cds",
        "attackReadyAt", "buffs", "dash", "poison", "input", "inBush",
        "lastHitBy", "dmgDone", "spectate", "charge",
    )

    def __init__(self, pid, name, loadout, build, x, y):
        self.id = pid
        self.name = name
        self.ready = False
        self.loadout = loadout
        self.build = build
        self.x = x
        self.y = y
        self.angle = 0.0
        self.hp = build["maxHp"]
        self.maxHp = build["maxHp"]
        self.shield = 0.0
        self.alive = True
        self.respawnAt = 0.0
        self.kills = 0
        self.deaths = 0
        self.streak = 0
        self.cds = {}
        self.attackReadyAt = 0.0
        self.buffs = self.blank_buffs()
        self.dash = None
        self.poison = None
        self.input = {"up": False, "down": False, "left": False, "right": False,
                      "ax": 1.0, "ay": 0.0, "atk": False}
        self.inBush = False
        self.lastHitBy = None
        self.dmgDone = 0.0
        self.spectate = None
        self.charge = None

    @staticmethod
    def blank_buffs():
        return {"hasteUntil": 0.0, "slowUntil": 0.0, "slowAmt": 0.0, "rootUntil": 0.0,
                "phaseUntil": 0.0, "ironskinUntil": 0.0, "spawnUntil": 0.0, "shieldUntil": 0.0}


class Room:
    def __init__(self, rid, settings, host_id, send, on_empty=None,
                 on_room_list=None, schedule=None, cancel=None):
        self.id = rid
        self.settings = settings
        self.hostId = host_id
        self.send_fn = send
        self.onEmpty = on_empty or (lambda: None)
        self.onRoomList = on_room_list or (lambda: None)
        self.schedule = schedule or (lambda delay, fn: None)
        self.cancel = cancel or (lambda handle: None)

        self.players = {}
        self.state = "lobby"
        self.time = 0.0
        self.tick = 0
        self.projs = []
        self.mines = []
        self.snares = []
        self.smokes = []
        self.pending = []
        self.dynWalls = []
        self.turrets = []
        self.timers = []
        self.fx = []
        self.nextEntId = 1
        self.endHandle = None
        self.winner = None

        self.seed = settings.get("mapSeed") or random.randint(0, 10 ** 9)
        self.map = make_map(self.seed)

    # danh sach vat can hien tai (map + tuong tam)
    def wall_list(self):
        if not self.dynWalls:
            return self.map["walls"]
        return self.map["walls"] + self.dynWalls

    def _clear_entities(self):
        self.projs = []
        self.mines = []
        self.snares = []
        self.smokes = []
        self.pending = []
        self.dynWalls = []
        self.turrets = []
        self.timers = []
        self.fx = []

    # ---------- thanh vien ----------
    def add_player(self, pid, name):
        if len(self.players) >= self.settings["maxPlayers"]:
            return False
        spawn = self.pick_spawn(None)
        loadout = sanitize_loadout(DEFAULT_LOADOUT)
        build = compute_build(loadout, self.settings["startHp"])
        self.players[pid] = Player(pid, name, loadout, build, spawn["x"], spawn["y"])
        return True

    def remove_player(self, pid):
        p = self.players.pop(pid, None)
        if not p:
            return
        self.projs = [x for x in self.projs if x["owner"] != pid]
        self.mines = [x for x in self.mines if x["owner"] != pid]
        self.snares = [x for x in self.snares if x["owner"] != pid]
        self.turrets = [x for x in self.turrets if x["owner"] != pid]

        if not self.players:
            if self.endHandle is not None:
                self.cancel(self.endHandle)
                self.endHandle = None
            self.onEmpty()
            return
        if self.hostId == pid:
            self.hostId = next(iter(self.players))
            self.broadcast_lobby()
        self.check_end()

    def set_loadout(self, pid, raw):
        p = self.players.get(pid)
        if not p or self.state != "lobby":
            return
        p.loadout = sanitize_loadout(raw)
        p.build = compute_build(p.loadout, self.settings["startHp"])
        p.maxHp = p.build["maxHp"]
        p.hp = p.build["maxHp"]
        self.broadcast_lobby()

    def set_ready(self, pid, v):
        p = self.players.get(pid)
        if not p or self.state != "lobby":
            return
        p.ready = bool(v)
        self.broadcast_lobby()

    def chat(self, pid, text):
        p = self.players.get(pid)
        if not p:
            return
        for q in self.players.values():
            self.send_fn(q.id, {"t": "chat", "from": p.name, "id": p.id, "text": text})

    def send_map_preview(self, pid):
        self.send_fn(pid, {"t": "map", "map": self.map})

    def broadcast_lobby(self):
        players = [{
            "id": p.id, "name": p.name, "ready": p.ready, "loadout": p.loadout,
            "isHost": p.id == self.hostId, "kills": p.kills, "deaths": p.deaths,
        } for p in self.players.values()]
        for p in self.players.values():
            self.send_fn(p.id, {
                "t": "room",
                "room": {
                    "id": self.id,
                    "hostId": self.hostId,
                    "settings": self.settings,
                    "state": self.state,
                    "players": players,
                    "you": p.id,
                },
            })
        self.onRoomList()

    # ---------- bat dau / ket thuc ----------
    def start(self):
        if self.state != "lobby" or not self.players:
            return
        self.state = "playing"
        self.time = 0.0
        self.tick = 0
        self._clear_entities()
        self.winner = None
        if self.endHandle is not None:
            self.cancel(self.endHandle)
            self.endHandle = None

        for p in self.players.values():
            p.kills = 0
            p.deaths = 0
            p.streak = 0
            p.dmgDone = 0.0
            p.ready = False
            p.build = compute_build(p.loadout, self.settings["startHp"])
            p.maxHp = p.build["maxHp"]
            p.cds = {}
            p.buffs = Player.blank_buffs()
            p.shield = 0.0
            p.poison = None
            p.dash = None
            p.charge = None
            p.spectate = None
            self.spawn_player(p, True)

        roster = [{
            "id": q.id, "name": q.name, "char": q.loadout["char"],
            "skills": q.loadout["skills"], "gear": q.loadout["gear"],
            "stats": q.loadout["stats"], "maxHp": q.maxHp,
        } for q in self.players.values()]
        for p in self.players.values():
            self.send_fn(p.id, {
                "t": "start",
                "map": self.map,
                "settings": self.settings,
                "you": p.id,
                "hostId": self.hostId,
                "players": roster,
            })

    def end(self):
        if self.state == "ended":
            return
        self.state = "ended"
        score = self.scoreboard()
        self.winner = score[0] if score else None
        for p in self.players.values():
            self.send_fn(p.id, {"t": "end", "score": score,
                                "winner": self.winner, "settings": self.settings})
        if self.endHandle is not None:
            self.cancel(self.endHandle)
        self.endHandle = self.schedule(12.0, self.back_to_lobby)

    def back_to_lobby(self):
        if self.endHandle is not None:
            self.cancel(self.endHandle)
            self.endHandle = None
        self.state = "lobby"
        self._clear_entities()
        for p in self.players.values():
            p.alive = True
            p.hp = p.maxHp
            p.shield = 0.0
            p.poison = None
            p.dash = None
            p.charge = None
            p.spectate = None
            p.buffs = Player.blank_buffs()
            s = self.pick_spawn(p)
            p.x, p.y = s["x"], s["y"]
        self.broadcast_lobby()

    def scoreboard(self):
        rows = [{
            "id": p.id, "name": p.name, "kills": p.kills, "deaths": p.deaths,
            "dmg": r0(p.dmgDone), "char": p.loadout["char"],
        } for p in self.players.values()]
        rows.sort(key=lambda x: (-x["kills"], x["deaths"], -x["dmg"]))
        return rows

    def check_end(self):
        if self.state != "playing":
            return
        ps = list(self.players.values())
        if self.settings["mode"] == "kills":
            if any(p.kills >= self.settings["killTarget"] for p in ps):
                self.end()
        elif self.settings["mode"] == "time":
            if self.time >= self.settings["timeLimit"]:
                self.end()
        elif self.settings["mode"] == "last":
            alive = sum(1 for p in ps if p.alive)
            if len(ps) > 1 and alive <= 1:
                self.end()

    # ---------- vi tri ----------
    def pick_spawn(self, for_player):
        spawns = self.map["spawns"]
        others = [p for p in self.players.values() if p is not for_player and p.alive]
        cx, cy = MAP_SIZE / 2, MAP_SIZE / 2
        best = spawns[0]
        best_score = float("-inf")
        for s in spawns:
            if point_in_walls(self.map["walls"], s["x"], s["y"], PLAYER_R + 6):
                continue
            d_enemy = 1e9
            for o in others:
                d_enemy = min(d_enemy, math.hypot(s["x"] - o.x, s["y"] - o.y))
            if not others:
                d_enemy = 900
            d_center = math.hypot(s["x"] - cx, s["y"] - cy)
            score = min(d_enemy, 1200) - d_center * 0.45 + random.random() * 40
            if score > best_score:
                best_score = score
                best = s
        return best

    def spawn_player(self, p, first):
        s = self.pick_spawn(p)
        p.x, p.y = s["x"], s["y"]
        p.hp = p.maxHp
        p.shield = 0.0
        p.alive = True
        p.respawnAt = 0.0
        p.spectate = None
        p.poison = None
        p.dash = None
        p.charge = None
        p.buffs["spawnUntil"] = self.time + (1.2 if first else 1.6)
        p.attackReadyAt = self.time + 0.3
        p.cds = {}
        color = CHAR_MAP.get(p.loadout["char"], {}).get("color", "#fff")
        self.push_fx({"k": "spawn", "x": p.x, "y": p.y, "c": color})

    def handle_spec(self, pid, target_id):
        p = self.players.get(pid)
        if not p or p.alive:
            return
        try:
            tid = int(target_id)
        except (TypeError, ValueError):
            tid = 0
        t = self.players.get(tid)
        p.spectate = t.id if (t and t.alive and t.id != pid) else None

    # ---------- input ----------
    def handle_input(self, pid, m):
        p = self.players.get(pid)
        if not p:
            return
        p.input["up"] = bool(m.get("u"))
        p.input["down"] = bool(m.get("d"))
        p.input["left"] = bool(m.get("l"))
        p.input["right"] = bool(m.get("r"))
        p.input["atk"] = bool(m.get("a"))
        try:
            ax = float(m.get("ax"))
            ay = float(m.get("ay"))
        except (TypeError, ValueError):
            ax, ay = 1.0, 0.0
        if ax != ax or ay != ay or (ax == 0 and ay == 0):
            ax, ay = 1.0, 0.0
        ln = math.hypot(ax, ay) or 1
        p.input["ax"] = ax / ln
        p.input["ay"] = ay / ln

    def handle_cast(self, pid, m):
        p = self.players.get(pid)
        if not p or not p.alive or self.state != "playing":
            return
        try:
            slot = int(m.get("slot") or 0)
        except (TypeError, ValueError):
            slot = 0
        slot = int(clamp(slot, 0, 4))
        skills = p.loadout["skills"]
        if slot >= len(skills):
            return
        skill_id = skills[slot]
        sk = SKILL_MAP.get(skill_id)
        if not sk:
            return
        if p.cds.get(skill_id, 0) > self.time:
            return
        if p.buffs["rootUntil"] > self.time and skill_id in ("dash", "blink", "leap"):
            return

        try:
            ax = float(m.get("ax"))
            ay = float(m.get("ay"))
        except (TypeError, ValueError):
            ax, ay = p.input["ax"], p.input["ay"]
        if ax != ax or ay != ay or (ax == 0 and ay == 0):
            ax, ay = p.input["ax"], p.input["ay"]
        ln = math.hypot(ax, ay) or 1
        angle = math.atan2(ay / ln, ax / ln)

        if not self.cast_skill(p, skill_id, angle, m.get("tx"), m.get("ty")):
            return
        p.cds[skill_id] = self.time + sk["cd"] * p.build["cdrMul"]
        self.push_fx({"k": "cast", "x": p.x, "y": p.y, "s": skill_id, "a": angle, "c": "#fff"})

    def cast_skill(self, p, sid, angle, tx=None, ty=None):
        b = p.build
        R = b["rangeMul"]

        if sid == "pierce":
            self.spawn_proj(p, angle, {"dmg": 22 * b["dmgMul"], "speed": 1150, "range": 700 * R,
                                       "pierce": 3, "r": 7, "color": "#ffe066", "kind": "bullet"})
            self.push_fx({"k": "shoot", "x": p.x, "y": p.y, "a": angle, "w": "gun"})
            return True
        if sid == "burst":
            for i in (-1, 0, 1):
                self.spawn_proj(p, angle + i * 0.19, {"dmg": 12 * b["dmgMul"], "speed": 1050,
                                                     "range": 620 * R, "r": 5, "color": "#ffb066", "kind": "bullet"})
            self.push_fx({"k": "shoot", "x": p.x, "y": p.y, "a": angle, "w": "gun"})
            return True
        if sid == "beam":
            ln = 700 * R
            x2 = p.x + math.cos(angle) * ln
            y2 = p.y + math.sin(angle) * ln
            end_x, end_y = x2, y2
            t = 0.05
            while t <= 1.0:
                px = p.x + math.cos(angle) * ln * t
                py = p.y + math.sin(angle) * ln * t
                if point_in_walls(self.wall_list(), px, py, 2):
                    end_x, end_y = px, py
                    break
                t += 0.05
            for q in self.players.values():
                if q.id == p.id or not q.alive:
                    continue
                if seg_circle(p.x, p.y, end_x, end_y, q.x, q.y, PLAYER_R + 8):
                    self.damage(q, 30 * b["dmgMul"], p, "beam")
            self.push_fx({"k": "beam", "x": p.x, "y": p.y, "x2": end_x, "y2": end_y, "a": angle})
            return True
        if sid == "fireball":
            self.spawn_proj(p, angle, {"dmg": 30 * b["dmgMul"], "speed": 430, "range": 800 * R, "r": 13,
                                       "color": "#ff7b3d", "kind": "fireball",
                                       "explode": {"r": 90, "dmg": 20 * b["dmgMul"]}})
            return True
        if sid == "glaive":
            self.spawn_proj(p, angle, {"dmg": 18 * b["dmgMul"], "speed": 720, "range": 520 * R, "r": 11,
                                       "color": "#8ef0ff", "kind": "glaive", "boomerang": True})
            return True
        if sid == "nova":
            rr = 170
            for q in self.players.values():
                if q.id == p.id or not q.alive:
                    continue
                if d2(p.x, p.y, q.x, q.y) < (rr + PLAYER_R) ** 2:
                    self.damage(q, 24 * b["dmgMul"], p, "nova")
                    a = math.atan2(q.y - p.y, q.x - p.x)
                    q.x += math.cos(a) * 26
                    q.y += math.sin(a) * 26
                    self.resolve_walls(q)
            self.push_fx({"k": "nova", "x": p.x, "y": p.y, "r": rr})
            return True
        if sid == "meteor":
            try:
                x, y = float(tx), float(ty)
            except (TypeError, ValueError):
                x, y = float("nan"), float("nan")
            if x != x or y != y:
                x = p.x + math.cos(angle) * 500
                y = p.y + math.sin(angle) * 500
            max_r = 600 * R
            dd = math.hypot(x - p.x, y - p.y)
            if dd > max_r:
                x = p.x + (x - p.x) / dd * max_r
                y = p.y + (y - p.y) / dd * max_r
            self.pending.append({"x": x, "y": y, "r": 140, "dmg": 45 * b["dmgMul"],
                                 "at": self.time + 0.8, "owner": p.id})
            self.push_fx({"k": "meteorMark", "x": x, "y": y, "r": 140, "d": 0.8})
            return True
        if sid == "dash":
            spd = 260 / 0.18
            p.dash = {"until": self.time + 0.18,
                      "vx": math.cos(angle) * spd, "vy": math.sin(angle) * spd}
            self.push_fx({"k": "dash", "x": p.x, "y": p.y, "a": angle})
            return True
        if sid == "blink":
            max_d = 320 * R
            last_x, last_y = p.x, p.y
            t = 10
            while t <= max_d:
                nx = p.x + math.cos(angle) * t
                ny = p.y + math.sin(angle) * t
                if point_in_walls(self.wall_list(), nx, ny, PLAYER_R):
                    break
                last_x, last_y = nx, ny
                t += 10
            self.push_fx({"k": "blinkFrom", "x": p.x, "y": p.y})
            p.x, p.y = last_x, last_y
            self.push_fx({"k": "blinkTo", "x": p.x, "y": p.y})
            return True
        if sid == "leap":
            spd = 220 / 0.35
            p.dash = {"until": self.time + 0.35,
                      "vx": math.cos(angle) * spd, "vy": math.sin(angle) * spd}
            p.buffs["phaseUntil"] = max(p.buffs["phaseUntil"], self.time + 0.4)
            return True
        if sid == "haste":
            p.buffs["hasteUntil"] = self.time + 3.5
            return True
        if sid == "shield":
            p.shield = 60 * (1 + (b.get("armor") or 0))
            p.buffs["shieldUntil"] = self.time + 4
            return True
        if sid == "heal":
            p.hp = min(p.maxHp, p.hp + 45)
            self.push_fx({"k": "heal", "x": p.x, "y": p.y})
            return True
        if sid == "phase":
            p.buffs["phaseUntil"] = self.time + 1.3
            return True
        if sid == "ironskin":
            p.buffs["ironskinUntil"] = self.time + 4
            return True
        if sid == "mine":
            if sum(1 for m in self.mines if m["owner"] == p.id) >= 2:
                return False
            self.mines.append({"x": p.x, "y": p.y, "owner": p.id,
                               "at": self.time + 0.8, "dmg": 55 * b["dmgMul"], "r": 110})
            return True
        if sid == "smoke":
            self.smokes.append({"x": p.x + math.cos(angle) * 90, "y": p.y + math.sin(angle) * 90,
                                "r": 200, "until": self.time + 4, "owner": p.id})
            return True
        if sid == "frost":
            self.spawn_proj(p, angle, {"dmg": 14 * b["dmgMul"], "speed": 900, "range": 640 * R, "r": 8,
                                       "color": "#7fd8ff", "kind": "frost",
                                       "slow": {"amt": 0.45, "dur": 2.5}})
            return True
        if sid == "snare":
            self.snares.append({"x": p.x + math.cos(angle) * 60, "y": p.y + math.sin(angle) * 60,
                                "r": 70, "owner": p.id, "armed": self.time + 0.5,
                                "dmg": 10 * b["dmgMul"]})
            return True
        if sid == "venom":
            self.spawn_proj(p, angle, {"dmg": 8 * b["dmgMul"], "speed": 820, "range": 600 * R, "r": 8,
                                       "color": "#9dff6b", "kind": "venom",
                                       "poison": {"dps": 6 * b["dmgMul"], "dur": 4}})
            return True

        # ===== tam xa moi =====
        if sid == "snipe":
            ln = 1100 * R
            end_x = p.x + math.cos(angle) * ln
            end_y = p.y + math.sin(angle) * ln
            walls = self.wall_list()
            t = 0.03
            while t <= 1.0:
                px = p.x + math.cos(angle) * ln * t
                py = p.y + math.sin(angle) * ln * t
                if point_in_walls(walls, px, py, 2):
                    end_x, end_y = px, py
                    break
                t += 0.03
            for q in self.players.values():
                if q.id == p.id or not q.alive:
                    continue
                if seg_circle(p.x, p.y, end_x, end_y, q.x, q.y, PLAYER_R + 5):
                    self.damage(q, 45 * b["dmgMul"], p, "snipe")
            self.push_fx({"k": "snipe", "x": p.x, "y": p.y, "x2": end_x, "y2": end_y, "a": angle})
            return True
        if sid == "chain":
            hit_ids = {p.id}
            src = {"x": p.x, "y": p.y}
            found = False
            for step in range(3):
                best = None
                bd = (500 if step == 0 else 260) ** 2
                for q in self.players.values():
                    if q.id in hit_ids or not q.alive:
                        continue
                    dd = d2(src["x"], src["y"], q.x, q.y)
                    if dd < bd:
                        bd = dd
                        best = q
                if not best:
                    break
                hit_ids.add(best.id)
                found = True
                self.damage(best, 28 * b["dmgMul"], p, "chain")
                self.push_fx({"k": "chain", "x": src["x"], "y": src["y"], "x2": best.x, "y2": best.y})
                src = {"x": best.x, "y": best.y}
            return found

        # ===== tam trung moi =====
        if sid == "barrage":
            for i in range(-3, 4):
                self.spawn_proj(p, angle + i * 0.09 + (random.random() - 0.5) * 0.04,
                                {"dmg": 9 * b["dmgMul"], "speed": 1000, "range": 560 * R,
                                 "r": 4.5, "color": "#ffd166", "kind": "bullet"})
            self.push_fx({"k": "shoot", "x": p.x, "y": p.y, "a": angle, "w": "gun"})
            return True
        if sid == "homing":
            self.spawn_proj(p, angle, {"dmg": 22 * b["dmgMul"], "speed": 620, "range": 900 * R, "r": 7,
                                       "color": "#c07bff", "kind": "homing", "homing": True})
            return True
        if sid == "ricochet":
            self.spawn_proj(p, angle, {"dmg": 18 * b["dmgMul"], "speed": 900, "range": 1200 * R, "r": 6,
                                       "color": "#8ef0ff", "kind": "ricochet", "bounces": 3})
            return True
        if sid == "grenade":
            self.spawn_proj(p, angle, {"dmg": 50 * b["dmgMul"], "speed": 560, "range": 700 * R, "r": 9,
                                       "color": "#ffb066", "kind": "grenade", "bounces": 2, "fuse": 1.2,
                                       "explode": {"r": 120, "dmg": 50 * b["dmgMul"]}})
            return True

        # ===== can chien moi =====
        if sid == "triple":
            for i in range(3):
                def strike(_p=p, _a=angle, _b=b):
                    if not _p.alive:
                        return
                    self.melee_arc(_p, _a, 108, math.pi * 0.55, 16 * _b["dmgMul"], "triple")
                    self.push_fx({"k": "slash", "x": _p.x, "y": _p.y, "a": _a, "r": 108, "hit": 0})
                self.timers.append({"at": self.time + i * 0.22, "fn": strike})
            return True
        if sid == "whirl":
            rr = 120
            for q in self.players.values():
                if q.id == p.id or not q.alive:
                    continue
                if d2(p.x, p.y, q.x, q.y) < (rr + PLAYER_R) ** 2:
                    self.damage(q, 28 * b["dmgMul"], p, "whirl")
                    q.buffs["slowUntil"] = self.time + 1.5
                    q.buffs["slowAmt"] = 0.3
            self.push_fx({"k": "whirl", "x": p.x, "y": p.y, "r": rr})
            return True
        if sid == "uppercut":
            hit = self.melee_arc(p, angle, 110, math.pi * 0.5, 26 * b["dmgMul"], "uppercut")
            for q in hit:
                a = math.atan2(q.y - p.y, q.x - p.x)
                q.x += math.cos(a) * 90
                q.y += math.sin(a) * 90
                self.resolve_walls(q)
            self.push_fx({"k": "slash", "x": p.x, "y": p.y, "a": angle, "r": 110, "hit": 1 if hit else 0})
            return True
        if sid == "execute":
            self.melee_arc(p, angle, 125, math.pi * 0.45, 40 * b["dmgMul"], "execute", True)
            self.push_fx({"k": "execute", "x": p.x, "y": p.y, "a": angle, "r": 125})
            return True
        if sid == "charge":
            spd = 300 / 0.25
            p.dash = {"until": self.time + 0.25,
                      "vx": math.cos(angle) * spd, "vy": math.sin(angle) * spd}
            p.charge = {"dmg": 30 * b["dmgMul"], "hit": set()}
            self.push_fx({"k": "dash", "x": p.x, "y": p.y, "a": angle})
            return True
        if sid == "hook":
            max_d = 380 * R
            best = None
            best_t = max_d + 1
            for q in self.players.values():
                if q.id == p.id or not q.alive:
                    continue
                dx, dy = q.x - p.x, q.y - p.y
                dist = math.hypot(dx, dy)
                if dist > max_d:
                    continue
                da = math.atan2(dy, dx) - angle
                while da > math.pi:
                    da -= TAU
                while da < -math.pi:
                    da += TAU
                if abs(da) > 0.5:
                    continue
                if dist < best_t:
                    best_t = dist
                    best = q
            if not best:
                return False
            self.push_fx({"k": "hook", "x": p.x, "y": p.y, "x2": best.x, "y2": best.y})
            self.damage(best, 10 * b["dmgMul"], p, "hook")
            if best.alive:
                a = math.atan2(best.y - p.y, best.x - p.x)
                best.x = p.x + math.cos(a) * (PLAYER_R * 2.2)
                best.y = p.y + math.sin(a) * (PLAYER_R * 2.2)
                self.resolve_walls(best)
                best.buffs["slowUntil"] = self.time + 0.6
                best.buffs["slowAmt"] = 0.4
            return True
        if sid == "swap":
            best = None
            bd = 500 * 500
            for q in self.players.values():
                if q.id == p.id or not q.alive:
                    continue
                dd = d2(p.x, p.y, q.x, q.y)
                if dd < bd:
                    bd = dd
                    best = q
            if not best:
                return False
            ox, oy = p.x, p.y
            self.push_fx({"k": "blinkFrom", "x": p.x, "y": p.y})
            p.x, p.y = best.x, best.y
            best.x, best.y = ox, oy
            self.resolve_walls(p)
            self.resolve_walls(best)
            self.push_fx({"k": "blinkTo", "x": p.x, "y": p.y})
            self.push_fx({"k": "blinkTo", "x": best.x, "y": best.y})
            return True

        # ===== tien ich moi =====
        if sid == "wall":
            cx = p.x + math.cos(angle) * 70
            cy = p.y + math.sin(angle) * 70
            ln, thick = 170, 26
            nx, ny = -math.sin(angle), math.cos(angle)
            x = cx - (abs(nx) * ln + abs(math.cos(angle)) * thick) / 2
            y = cy - (abs(ny) * ln + abs(math.sin(angle)) * thick) / 2
            w = abs(math.cos(angle)) * thick + abs(nx) * ln
            h = abs(math.sin(angle)) * thick + abs(ny) * ln
            self.dynWalls.append({"t": "r", "x": r0(x), "y": r0(y),
                                  "w": max(20, r0(w)), "h": max(20, r0(h)),
                                  "until": self.time + 6, "owner": p.id})
            self.push_fx({"k": "wall", "x": r0(x), "y": r0(y), "w": r0(w), "h": r0(h)})
            return True
        if sid == "turret":
            self.turrets.append({"x": p.x + math.cos(angle) * 45,
                                 "y": p.y + math.sin(angle) * 45,
                                 "owner": p.id, "until": self.time + 8,
                                 "next": self.time + 0.4, "angle": angle})
            return True
        return False

    # chem hinh quat, tra ve danh sach muc tieu trung
    def melee_arc(self, p, angle, reach, arc, dmg, kind, execute=False):
        hit = []
        for q in self.players.values():
            if q.id == p.id or not q.alive:
                continue
            d = math.hypot(q.x - p.x, q.y - p.y)
            if d > reach + PLAYER_R:
                continue
            da = math.atan2(q.y - p.y, q.x - p.x) - angle
            while da > math.pi:
                da -= TAU
            while da < -math.pi:
                da += TAU
            if abs(da) > arc / 2:
                continue
            amount = dmg
            if execute and q.hp / q.maxHp < 0.3:
                amount *= 2.25
            self.damage(q, amount, p, kind)
            hit.append(q)
        return hit

    def spawn_proj(self, p, angle, o, origin=None):
        ox, oy = origin if origin else (p.x, p.y)
        speed = o["speed"]
        rng = o["range"]
        pr = {
            "id": self.nextEntId,
            "owner": p.id,
            "x": ox + math.cos(angle) * (PLAYER_R + 6),
            "y": oy + math.sin(angle) * (PLAYER_R + 6),
            "vx": math.cos(angle) * speed,
            "vy": math.sin(angle) * speed,
            "angle": angle,
            "speed": speed,
            "dmg": o["dmg"],
            "r": o.get("r", 6),
            "color": o.get("color", "#ffe066"),
            "ttl": rng / speed,
            "traveled": 0.0,
            "maxDist": rng,
            "pierce": o.get("pierce", 0),
            "hit": set(),
            "kind": o.get("kind", "bullet"),
            "explode": o.get("explode"),
            "slow": o.get("slow"),
            "poison": o.get("poison"),
            "boomerang": bool(o.get("boomerang")),
            "returning": False,
            "homing": bool(o.get("homing")),
            "bounces": o.get("bounces", 0),
            "fuse": o.get("fuse", 0),
            "fuseMax": o.get("fuse", 0),
            "spin": 0.0,
        }
        self.nextEntId += 1
        self.projs.append(pr)
        return pr

    # ---------- vong lap ----------
    def step(self, dt):
        if self.state != "playing":
            return
        self.time += dt
        self.tick += 1

        for p in list(self.players.values()):
            self.update_player(p, dt)
        self.update_projectiles(dt)
        self.update_hazards(dt)
        self.update_turrets(dt)
        self.update_timers()
        self.separate_players()

        if self.dynWalls:
            self.dynWalls = [w for w in self.dynWalls if w["until"] > self.time]

        self.send_snapshots()
        self.fx.clear()

        self.check_end()

    def update_timers(self):
        if not self.timers:
            return
        due = [t for t in self.timers if t["at"] <= self.time]
        if not due:
            return
        self.timers = [t for t in self.timers if t["at"] > self.time]
        for t in due:
            try:
                t["fn"]()
            except Exception as e:  # pragma: no cover
                print("timer error:", e)

    def update_turrets(self, dt):
        if not self.turrets:
            return
        self.turrets = [t for t in self.turrets if t["until"] > self.time]
        for t in self.turrets:
            if self.time < t["next"]:
                continue
            t["next"] = self.time + 0.55
            best = None
            bd = 550 * 550
            for q in self.players.values():
                if q.id == t["owner"] or not q.alive:
                    continue
                dd = d2(t["x"], t["y"], q.x, q.y)
                if dd < bd:
                    bd = dd
                    best = q
            if not best:
                continue
            a = math.atan2(best.y - t["y"], best.x - t["x"])
            t["angle"] = a
            owner = self.players.get(t["owner"])
            if not owner:
                continue
            self.spawn_proj(owner, a, {"dmg": 10 * owner.build["dmgMul"], "speed": 900,
                                       "range": 600, "r": 4.5, "color": "#8ef0ff", "kind": "turret"},
                            origin=(t["x"], t["y"]))
            self.push_fx({"k": "shoot", "x": t["x"], "y": t["y"], "a": a, "w": "gun"})

    def update_player(self, p, dt):
        b = p.build

        if not p.alive:
            if self.settings["mode"] != "last" and p.respawnAt and self.time >= p.respawnAt:
                self.spawn_player(p, False)
            return

        # doc
        if p.poison:
            if self.time >= p.poison["until"]:
                p.poison = None
            else:
                p.poison["acc"] = p.poison.get("acc", 0.0) + dt
                if p.poison["acc"] >= 0.5:
                    p.poison["acc"] -= 0.5
                    self.damage(p, p.poison["dps"] * 0.5,
                                self.players.get(p.poison["src"]), "poison", True)
        if not p.alive:
            return

        # hoi mau
        if p.hp < p.maxHp:
            p.hp = min(p.maxHp, p.hp + b["regen"] * dt)

        # khien het han
        if p.shield > 0 and p.buffs["shieldUntil"] and self.time > p.buffs["shieldUntil"]:
            p.shield = 0.0

        p.angle = math.atan2(p.input["ay"], p.input["ax"])

        speed = b["speed"]
        if p.buffs["hasteUntil"] > self.time:
            speed *= 1.55
        if p.buffs["slowUntil"] > self.time:
            speed *= 1 - p.buffs["slowAmt"] * (1 - b["ccResist"])
        if p.buffs["rootUntil"] > self.time:
            speed = 0

        mx = (1 if p.input["right"] else 0) - (1 if p.input["left"] else 0)
        my = (1 if p.input["down"] else 0) - (1 if p.input["up"] else 0)
        ml = math.hypot(mx, my)

        if p.dash:
            if self.time >= p.dash["until"]:
                p.dash = None
                p.charge = None
            else:
                ox, oy = p.x, p.y
                p.x += p.dash["vx"] * dt
                p.y += p.dash["vy"] * dt
                self.resolve_walls(p)
                if d2(ox, oy, p.x, p.y) < 0.6:
                    p.dash = None
                    p.charge = None
                if p.charge:
                    for q in self.players.values():
                        if q.id == p.id or not q.alive or q.id in p.charge["hit"]:
                            continue
                        if d2(p.x, p.y, q.x, q.y) < (PLAYER_R * 2 + 6) ** 2:
                            p.charge["hit"].add(q.id)
                            self.damage(q, p.charge["dmg"], p, "charge")
                            self.push_fx({"k": "hit", "x": q.x, "y": q.y, "c": "#8ef0ff"})
        elif ml > 0 and speed > 0:
            p.x += (mx / ml) * speed * dt
            p.y += (my / ml) * speed * dt
            self.resolve_walls(p)

        p.x = clamp(p.x, WALL_THICK + PLAYER_R, MAP_SIZE - WALL_THICK - PLAYER_R)
        p.y = clamp(p.y, WALL_THICK + PLAYER_R, MAP_SIZE - WALL_THICK - PLAYER_R)

        p.inBush = any(d2(p.x, p.y, bs["x"], bs["y"]) < bs["r"] * bs["r"] for bs in self.map["bushes"])

        if p.input["atk"]:
            self.try_attack(p)

    def resolve_walls(self, p):
        r = PLAYER_R
        for w in self.wall_list():
            if w.get("t") == "r":
                nx = clamp(p.x, w["x"], w["x"] + w["w"])
                ny = clamp(p.y, w["y"], w["y"] + w["h"])
                dx, dy = p.x - nx, p.y - ny
                dd = dx * dx + dy * dy
                if dd < r * r:
                    if dd < 1e-6:
                        left = p.x - w["x"]
                        right = w["x"] + w["w"] - p.x
                        top = p.y - w["y"]
                        bot = w["y"] + w["h"] - p.y
                        m = min(left, right, top, bot)
                        if m == left:
                            p.x = w["x"] - r
                        elif m == right:
                            p.x = w["x"] + w["w"] + r
                        elif m == top:
                            p.y = w["y"] - r
                        else:
                            p.y = w["y"] + w["h"] + r
                    else:
                        d = math.sqrt(dd)
                        push = (r - d) / d
                        p.x += dx * push
                        p.y += dy * push
            else:
                dx, dy = p.x - w["x"], p.y - w["y"]
                rr = r + w["r"]
                dd = dx * dx + dy * dy
                if dd < rr * rr:
                    d = math.sqrt(dd) or 1
                    p.x = w["x"] + (dx / d) * rr
                    p.y = w["y"] + (dy / d) * rr

    def separate_players(self):
        ps = [p for p in self.players.values() if p.alive]
        for i in range(len(ps)):
            for j in range(i + 1, len(ps)):
                a, b = ps[i], ps[j]
                dx, dy = b.x - a.x, b.y - a.y
                dd = dx * dx + dy * dy
                mn = PLAYER_R * 2
                if dd < mn * mn and dd > 0.01:
                    d = math.sqrt(dd)
                    push = (mn - d) / 2
                    ux, uy = dx / d, dy / d
                    a.x -= ux * push
                    a.y -= uy * push
                    b.x += ux * push
                    b.y += uy * push

    def try_attack(self, p):
        if self.time < p.attackReadyAt:
            return
        w = p.build["weapon"]
        p.attackReadyAt = self.time + 1 / max(0.2, w["rate"])

        if w["kind"] == "melee":
            reach = w["range"]
            arc = w.get("arc", 1.6)
            hit_any = False
            for q in self.players.values():
                if q.id == p.id or not q.alive:
                    continue
                d = math.hypot(q.x - p.x, q.y - p.y)
                if d > reach + PLAYER_R:
                    continue
                da = math.atan2(q.y - p.y, q.x - p.x) - p.angle
                while da > math.pi:
                    da -= TAU
                while da < -math.pi:
                    da += TAU
                if abs(da) <= arc / 2:
                    self.damage(q, w["dmg"], p, "melee")
                    hit_any = True
            self.push_fx({"k": "slash", "x": p.x, "y": p.y, "a": p.angle,
                          "r": reach, "hit": 1 if hit_any else 0})
            return

        for _ in range(w["pellets"]):
            spread = (random.random() - 0.5) * w["spread"] * 2
            self.spawn_proj(p, p.angle + spread, {
                "dmg": w["dmg"], "speed": w["pspd"], "range": w["range"], "r": 5.5,
                "color": "#ffe066", "kind": "bullet",
            })
        self.push_fx({"k": "shoot", "x": p.x, "y": p.y, "a": p.angle, "w": "gun"})

    def update_projectiles(self, dt):
        alive = []
        walls = self.wall_list()

        for pr in self.projs:
            if pr["fuse"] > 0:
                pr["fuse"] -= dt
                if pr["fuse"] <= 0:
                    if pr["explode"]:
                        self.explode(pr["x"], pr["y"], pr["explode"]["r"],
                                     pr["explode"]["dmg"], pr["owner"], pr["color"])
                    continue

            ox, oy = pr["x"], pr["y"]

            if pr["boomerang"] and pr["returning"]:
                owner = self.players.get(pr["owner"])
                if not owner or not owner.alive:
                    continue
                a = math.atan2(owner.y - pr["y"], owner.x - pr["x"])
                pr["vx"] = math.cos(a) * pr["speed"] * 1.1
                pr["vy"] = math.sin(a) * pr["speed"] * 1.1
                if d2(pr["x"], pr["y"], owner.x, owner.y) < 26 * 26:
                    continue

            if pr["homing"]:
                best = None
                bd = 720 * 720
                for q in self.players.values():
                    if q.id == pr["owner"] or not q.alive:
                        continue
                    dd = d2(pr["x"], pr["y"], q.x, q.y)
                    if dd < bd:
                        bd = dd
                        best = q
                if best:
                    target = math.atan2(best.y - pr["y"], best.x - pr["x"])
                    da = target - pr["angle"]
                    while da > math.pi:
                        da -= TAU
                    while da < -math.pi:
                        da += TAU
                    turn = clamp(da, -3.4 * dt, 3.4 * dt)
                    pr["angle"] += turn
                    pr["vx"] = math.cos(pr["angle"]) * pr["speed"]
                    pr["vy"] = math.sin(pr["angle"]) * pr["speed"]

            nx = pr["x"] + pr["vx"] * dt
            ny = pr["y"] + pr["vy"] * dt

            if pr["bounces"] > 0:
                bounced = False
                if seg_walls_list(walls, pr["x"], pr["y"], nx, pr["y"], pr["r"]):
                    pr["vx"] = -pr["vx"]
                    pr["bounces"] -= 1
                    bounced = True
                else:
                    pr["x"] = nx
                if seg_walls_list(walls, pr["x"], pr["y"], pr["x"], ny, pr["r"]):
                    pr["vy"] = -pr["vy"]
                    pr["bounces"] -= 1
                    bounced = True
                else:
                    pr["y"] = ny
                if bounced:
                    self.push_fx({"k": "spark", "x": pr["x"], "y": pr["y"], "c": pr["color"]})
                    if pr["bounces"] <= 0:
                        if pr["explode"]:
                            self.explode(pr["x"], pr["y"], pr["explode"]["r"],
                                         pr["explode"]["dmg"], pr["owner"], pr["color"])
                        continue
            else:
                pr["x"] = nx
                pr["y"] = ny

            pr["traveled"] += math.hypot(pr["vx"], pr["vy"]) * dt
            pr["ttl"] -= dt
            pr["spin"] += dt * 18

            if pr["boomerang"] and not pr["returning"] and pr["traveled"] >= pr["maxDist"]:
                pr["returning"] = True
                pr["hit"].clear()
            if pr["ttl"] <= 0:
                if pr["explode"]:
                    self.explode(pr["x"], pr["y"], pr["explode"]["r"],
                                 pr["explode"]["dmg"], pr["owner"], pr["color"])
                continue

            if pr["bounces"] <= 0:
                if seg_walls_list(walls, ox, oy, pr["x"], pr["y"], pr["r"]):
                    if pr["explode"]:
                        self.explode(pr["x"], pr["y"], pr["explode"]["r"],
                                     pr["explode"]["dmg"], pr["owner"], pr["color"])
                    else:
                        self.push_fx({"k": "spark", "x": pr["x"], "y": pr["y"], "c": pr["color"]})
                    continue

            removed = False
            for q in self.players.values():
                if q.id == pr["owner"] or not q.alive or q.id in pr["hit"]:
                    continue
                if seg_circle(ox, oy, pr["x"], pr["y"], q.x, q.y, PLAYER_R + pr["r"]):
                    pr["hit"].add(q.id)
                    src = self.players.get(pr["owner"])
                    if pr["explode"]:
                        self.explode(pr["x"], pr["y"], pr["explode"]["r"],
                                     pr["explode"]["dmg"], pr["owner"], pr["color"])
                        self.damage(q, pr["dmg"], src, pr["kind"])
                        removed = True
                        break
                    self.damage(q, pr["dmg"], src, pr["kind"])
                    if pr["slow"]:
                        q.buffs["slowUntil"] = self.time + pr["slow"]["dur"]
                        q.buffs["slowAmt"] = pr["slow"]["amt"]
                    if pr["poison"]:
                        q.poison = {"dps": pr["poison"]["dps"],
                                    "until": self.time + pr["poison"]["dur"],
                                    "src": pr["owner"], "acc": 0.0}
                    self.push_fx({"k": "hit", "x": q.x, "y": q.y, "c": pr["color"]})
                    if pr["pierce"] > 0:
                        pr["pierce"] -= 1
                    else:
                        removed = True
                        break
            if removed:
                continue
            alive.append(pr)
        self.projs = alive

    def update_hazards(self, dt):
        for m in self.mines:
            if self.time < m["at"]:
                continue
            for q in self.players.values():
                if q.id == m["owner"] or not q.alive:
                    continue
                if d2(q.x, q.y, m["x"], m["y"]) < 62 * 62:
                    self.explode(m["x"], m["y"], m["r"], m["dmg"], m["owner"], "#ff7b3d")
                    m["dead"] = True
                    break
        self.mines = [m for m in self.mines if not m.get("dead")]

        for s in self.snares:
            if self.time < s["armed"]:
                continue
            for q in self.players.values():
                if q.id == s["owner"] or not q.alive:
                    continue
                if d2(q.x, q.y, s["x"], s["y"]) < (s["r"] + PLAYER_R) ** 2:
                    q.buffs["rootUntil"] = self.time + 1.4 * (1 - q.build["ccResist"])
                    self.damage(q, s["dmg"], self.players.get(s["owner"]), "snare")
                    self.push_fx({"k": "snare", "x": s["x"], "y": s["y"], "r": s["r"]})
                    s["dead"] = True
                    break
        self.snares = [s for s in self.snares if not s.get("dead")]

        self.smokes = [s for s in self.smokes if s["until"] > self.time]
        for s in self.smokes:
            for q in self.players.values():
                if not q.alive or q.id == s["owner"]:
                    continue
                if d2(q.x, q.y, s["x"], s["y"]) < s["r"] * s["r"]:
                    if q.buffs["slowUntil"] < self.time + 0.2:
                        q.buffs["slowUntil"] = self.time + 0.2
                        q.buffs["slowAmt"] = 0.3

        for p in self.pending:
            if self.time >= p["at"]:
                self.explode(p["x"], p["y"], p["r"], p["dmg"], p["owner"], "#ff9b3d")
                p["dead"] = True
        self.pending = [p for p in self.pending if not p.get("dead")]

    def explode(self, x, y, r, dmg, owner_id, color="#ff9b3d"):
        src = self.players.get(owner_id)
        for q in self.players.values():
            if not q.alive or q.id == owner_id:
                continue
            if d2(x, y, q.x, q.y) < (r + PLAYER_R) ** 2:
                self.damage(q, dmg, src, "explosion")
        self.push_fx({"k": "boom", "x": x, "y": y, "r": r, "c": color})

    def damage(self, target, amount, source, kind="hit", ignore_dodge=False):
        if not target or not target.alive or self.state != "playing":
            return 0
        if target.buffs["phaseUntil"] > self.time:
            return 0
        if target.buffs["spawnUntil"] > self.time:
            return 0
        if not ignore_dodge and random.random() < target.build["dodge"]:
            self.push_fx({"k": "dodge", "x": target.x, "y": target.y})
            return 0
        armor = target.build["armor"]
        if target.buffs["ironskinUntil"] > self.time:
            armor += 0.35
        armor = clamp(armor, 0, 0.8)
        dmg = amount * (1 - armor)

        if target.shield > 0:
            absorb = min(target.shield, dmg)
            target.shield -= absorb
            dmg -= absorb
            if target.shield <= 0:
                target.shield = 0.0
                target.buffs["shieldUntil"] = 0.0

        target.hp -= dmg
        target.lastHitBy = source.id if source else None

        if source and source.build["lifesteal"] > 0:
            source.hp = min(source.maxHp, source.hp + dmg * source.build["lifesteal"])
        if source:
            source.dmgDone += dmg

        self.push_fx({"k": "dmg", "x": target.x, "y": target.y, "v": r0(dmg)})

        if target.hp <= 0:
            self.kill(target, source)
        return dmg

    def kill(self, target, source):
        if not target.alive:
            return
        target.alive = False
        target.hp = 0.0
        target.deaths += 1
        target.streak = 0
        target.poison = None
        target.dash = None
        target.charge = None
        target.shield = 0.0
        target.inBush = False
        target.spectate = None

        if source and source.id != target.id:
            source.kills += 1
            source.streak += 1

        self.push_fx({
            "k": "kill", "x": target.x, "y": target.y,
            "a": source.name if source else "", "b": target.name,
            "c": CHAR_MAP.get(target.loadout["char"], {}).get("color", "#fff"),
            "streak": source.streak if source else 0,
        })

        if self.settings["mode"] != "last" and self.settings["respawn"] >= 0:
            target.respawnAt = self.time + max(0.5, self.settings["respawn"])

    def push_fx(self, e):
        if len(self.fx) < 260:
            self.fx.append(e)

    # ---------- gui du lieu ----------
    def send_snapshots(self):
        time_left = (max(0, self.settings["timeLimit"] - self.time)
                     if self.settings["mode"] == "time" else 0)
        score = self.scoreboard()[:8]

        for v in list(self.players.values()):
            ents = []
            vt = None if v.alive else self.players.get(v.spectate) if v.spectate else None
            view = vt if (vt and vt.alive) else v

            for q in self.players.values():
                if not q.alive:
                    continue
                dd = d2(q.x, q.y, view.x, view.y)
                if q.id != v.id:
                    if dd > 1900 * 1900:
                        continue
                    if q.inBush and dd > 165 * 165:
                        continue
                ents.append({
                    "k": "p", "id": q.id, "n": q.name, "c": q.loadout["char"],
                    "x": r1(q.x), "y": r1(q.y), "a": r2(q.angle),
                    "hp": r0(q.hp), "mhp": q.maxHp, "sh": r0(q.shield),
                    "bn": 1 if q.inBush else 0,
                    "ph": 1 if q.buffs["phaseUntil"] > self.time else 0,
                    "hs": 1 if q.buffs["hasteUntil"] > self.time else 0,
                    "is": 1 if q.buffs["ironskinUntil"] > self.time else 0,
                    "sl": 1 if q.buffs["slowUntil"] > self.time else 0,
                    "rt": 1 if q.buffs["rootUntil"] > self.time else 0,
                    "kl": q.kills,
                })

            for pr in self.projs:
                if d2(pr["x"], pr["y"], view.x, view.y) > 1950 * 1950:
                    continue
                ents.append({"k": "b", "id": pr["id"], "x": r1(pr["x"]), "y": r1(pr["y"]),
                             "a": r2(pr["angle"]), "c": pr["color"], "r": pr["r"],
                             "s": r2(pr["spin"]), "bm": 1 if pr["boomerang"] else 0})
            for m in self.mines:
                if d2(m["x"], m["y"], view.x, view.y) > 1950 * 1950:
                    continue
                ents.append({"k": "m", "x": r1(m["x"]), "y": r1(m["y"]),
                             "armed": 1 if self.time >= m["at"] else 0,
                             "own": 1 if m["owner"] == v.id else 0})
            for s in self.snares:
                if d2(s["x"], s["y"], view.x, view.y) > 1950 * 1950:
                    continue
                ents.append({"k": "t", "x": r1(s["x"]), "y": r1(s["y"]),
                             "own": 1 if s["owner"] == v.id else 0})
            for s in self.smokes:
                if d2(s["x"], s["y"], view.x, view.y) > 2000 * 2000:
                    continue
                ents.append({"k": "s", "x": r1(s["x"]), "y": r1(s["y"]), "r": s["r"]})
            for w in self.dynWalls:
                if d2(w["x"], w["y"], view.x, view.y) > 1950 * 1950:
                    continue
                ents.append({"k": "w", "x": r0(w["x"]), "y": r0(w["y"]), "w": w["w"], "h": w["h"],
                             "left": r1(max(0, w["until"] - self.time))})
            for t in self.turrets:
                if d2(t["x"], t["y"], view.x, view.y) > 1950 * 1950:
                    continue
                ents.append({"k": "u", "x": r1(t["x"]), "y": r1(t["y"]),
                             "a": r2(t.get("angle", 0)), "own": 1 if t["owner"] == v.id else 0})

            fx = [e for e in self.fx
                  if e.get("x") is None or d2(e["x"], e["y"], view.x, view.y) < 1700 * 1700]

            me = v
            cds = []
            for sid in me.loadout["skills"]:
                sk = SKILL_MAP.get(sid)
                ready = me.cds.get(sid, 0)
                cds.append({"id": sid, "left": r1(max(0, ready - self.time)),
                            "cd": r1(sk["cd"] * me.build["cdrMul"]) if sk else 1})

            snap = {
                "t": "snap",
                "tick": self.tick,
                "time": r2(self.time),
                "spec": 0 if me.alive else (vt.id if vt else 0),
                "you": {
                    "x": r1(me.x), "y": r1(me.y), "hp": r0(me.hp), "mhp": me.maxHp,
                    "sh": r0(me.shield), "al": 1 if me.alive else 0,
                    "k": me.kills, "d": me.deaths,
                    "rs": 0 if me.alive else r1(max(0, (me.respawnAt or 0) - self.time)),
                    "bn": 1 if me.inBush else 0,
                    "rt": 1 if me.buffs["rootUntil"] > self.time else 0,
                    "sl": 1 if me.buffs["slowUntil"] > self.time else 0,
                    "hs": 1 if me.buffs["hasteUntil"] > self.time else 0,
                    "ph": 1 if me.buffs["phaseUntil"] > self.time else 0,
                    "is": 1 if me.buffs["ironskinUntil"] > self.time else 0,
                    "atkCd": r1(max(0, me.attackReadyAt - self.time)),
                    "cds": cds,
                },
                "ents": ents,
                "fx": fx,
                "score": score,
                "left": r0(time_left),
            }
            if not me.alive:
                snap["specList"] = [{"id": q.id, "n": q.name}
                                    for q in self.players.values() if q.alive]
            self.send_fn(v.id, snap)

    # ---------- admin ----------
    def admin(self, pid, m):
        cmd = m.get("cmd")
        if cmd == "kick":
            try:
                tid = int(m.get("target"))
            except (TypeError, ValueError):
                return
            target = self.players.get(tid)
            if target and target.id != self.hostId:
                self.send_fn(target.id, {"t": "kicked"})
                self.remove_player(target.id)
        elif cmd == "settings":
            s = m.get("settings") or {}
            if isinstance(s.get("killTarget"), (int, float)):
                self.settings["killTarget"] = int(clamp(int(s["killTarget"]), 1, 999))
            if isinstance(s.get("timeLimit"), (int, float)):
                self.settings["timeLimit"] = int(clamp(int(s["timeLimit"]), 30, 3600))
            if isinstance(s.get("respawn"), (int, float)):
                self.settings["respawn"] = int(clamp(int(s["respawn"]), 0, 30))
            if isinstance(s.get("startHp"), (int, float)):
                self.settings["startHp"] = int(clamp(int(s["startHp"]), 50, 500))
            if isinstance(s.get("maxPlayers"), (int, float)):
                self.settings["maxPlayers"] = int(clamp(int(s["maxPlayers"]), 2, 64))
            if s.get("mode") in ("kills", "time", "last"):
                self.settings["mode"] = s["mode"]
            if isinstance(s.get("name"), str):
                self.settings["name"] = s["name"][:28] or self.settings["name"]
            if isinstance(s.get("password"), str):
                self.settings["password"] = s["password"][:16]
            if self.state == "lobby":
                self.broadcast_lobby()
        elif cmd == "restart":
            self.back_to_lobby()
            self.start()
        elif cmd == "lobby":
            self.back_to_lobby()
