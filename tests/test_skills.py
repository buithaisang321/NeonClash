"""Harness test toan bo 35 chieu: cast tung chieu trong room that, step 10s,
kiem tra: khong crash, co hieu ung/trang thai thay doi, cooldown duoc tinh.

Chay: python tests/test_skills.py
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.gamedata import SKILLS, SKILL_MAP
from game.room import Room, point_in_walls

DT = 1 / 30
SETTINGS = {
    "name": "Test", "password": "", "maxPlayers": 8, "startHp": 100,
    "mode": "kills", "killTarget": 999, "timeLimit": 9999, "respawn": 1,
    "mapSeed": 12345,
}


def find_free_spot(room, cx, cy, clear=220):
    """Tim diem trong quanh (cx, cy) co vung bao quang 'clear' khong cham tuong."""
    step = 40
    best = (cx, cy)
    for radius in range(0, 1200, step):
        for a in range(0, 360, 15):
            x = cx + math.cos(math.radians(a)) * radius
            y = cy + math.sin(math.radians(a)) * radius
            ok = True
            for dd in range(0, clear, 40):
                for ang in range(0, 360, 45):
                    px = x + math.cos(math.radians(ang)) * dd
                    py = y + math.sin(math.radians(ang)) * dd
                    if point_in_walls(room.map["walls"], px, py, 30):
                        ok = False
                        break
                if not ok:
                    break
            if ok:
                best = (x, y)
                return best
    return best


def make_room(sid):
    sent = []
    room = Room("t_" + sid, dict(SETTINGS), 1,
                send=lambda pid, m: sent.append((pid, m)))
    room.add_player(1, "A")
    room.add_player(2, "B")
    lo = {"skills": [sid], "stats": {"dmg": 2, "speed": 1}}
    room.set_loadout(1, lo)
    room.set_loadout(2, {"skills": ["shield"], "stats": {}})
    room.start()

    # dat A va B gan nhau, mat dang nhau, vung trong
    from game.gamedata import MAP_SIZE
    cx, cy = MAP_SIZE / 2, MAP_SIZE / 2
    ax, ay = find_free_spot(room, cx, cy)
    a = room.players[1]
    b = room.players[2]
    a.x, a.y = ax, ay
    b.x, b.y = ax + 150, ay
    room.resolve_walls(a)
    room.resolve_walls(b)
    a.input["ax"], a.input["ay"] = 1.0, 0.0
    # qua thoi diem bao ve spawn (spawnUntil = 1.6s) de chieu co gay damage
    for _ in range(60):
        room.step(DT)
    return room, sent


def run_skill(sid, ticks=320):
    room, sent = make_room(sid)
    a = room.players[1]
    b = room.players[2]
    bhp0 = b.hp
    ahp0 = a.hp
    fx_kinds = set()

    room.handle_cast(1, {"slot": 0, "ax": 1.0, "ay": 0.0,
                         "tx": b.x, "ty": b.y})
    charged = sid in a.cds

    err = None
    for i in range(ticks):
        try:
            room.step(DT)
            for f in room.fx:
                fx_kinds.add(f.get("k"))
        except Exception as ex:
            err = "%s: %s" % (type(ex).__name__, ex)
            import traceback
            traceback.print_exc()
            break
    # gom ca fx phat sinh ngay khi cast
    state_effect = bool(room.projs or room.mines or room.snares or room.smokes
                        or room.turrets or room.dynWalls or room.pending
                        or room.timers)
    changed = (b.hp != bhp0 or a.hp != ahp0 or a.shield != 0
               or a.buffs != {"phaseUntil": 0, "shieldUntil": 0, "hasteUntil": 0,
                              "ironskinUntil": 0, "rootUntil": 0, "slowUntil": 0,
                              "slowAmt": 0}
               or a.x != room.players[1].x)
    moved = True  # vi tri da thay doi la binh thuong
    # chieu "buff an" (phase/haste...) chi thay doi buffs -> da tinh trong changed
    has_fx = bool(fx_kinds - {"cast"})
    return {
        "sid": sid,
        "charged": charged,
        "fx": sorted(fx_kinds - {"cast"}),
        "state_effect": state_effect,
        "changed": changed,
        "err": err,
        "bhp": b.hp, "bhp0": bhp0,
        "bdeaths": b.deaths,
    }


def main():
    fails = []
    print("%-10s %-7s %-40s %s" % ("SKILL", "CD", "FX", "KQ"))
    for sk in SKILLS:
        sid = sk["id"]
        r = run_skill(sid)
        if r["err"]:
            print("%-10s %-7s %-40s LOI: %s" % (sid, r["charged"], ",".join(r["fx"]), r["err"]))
            fails.append((sid, r["err"]))
            continue
        effect = r["fx"] or r["state_effect"] or r["changed"]
        if not r["charged"] and sid not in ("mine",):
            # mine co the tu choi khi da dat 2; nhung room moi -> phai duoc chap nhan
            print("%-10s %-7s %-40s KHONG TINH CD" % (sid, r["charged"], ",".join(r["fx"])))
            fails.append((sid, "cast bi tu choi (khong tinh cooldown)"))
            continue
        if not effect:
            print("%-10s %-7s %-40s KHONG CO HIEU UNG" % (sid, r["charged"], ",".join(r["fx"])))
            fails.append((sid, "khong co fx / trang thai thay doi"))
            continue
        print("%-10s %-7s %-40s OK" % (sid, r["charged"], ",".join(r["fx"])))

    print("")
    if fails:
        print("FAIL %d chieu:" % len(fails))
        for sid, why in fails:
            print("  -", sid, "->", why)
        return 1
    print("TAT CA %d CHIEU PASS" % len(SKILLS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
