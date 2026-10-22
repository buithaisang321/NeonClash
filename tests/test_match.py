"""Test vong dau hoan chinh: damage -> ha -> respawn -> end condition -> spectate."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.room import Room
from tests.test_skills import SETTINGS, find_free_spot, DT


def make_room(**over):
    st = dict(SETTINGS)
    st.update(over)
    sent = []
    room = Room("m1", st, 1, send=lambda pid, m: sent.append((pid, m)))
    room.add_player(1, "A")
    room.add_player(2, "B")
    room.set_loadout(1, {"skills": ["snipe", "heal", "dash"], "stats": {"dmg": 2}})
    room.set_loadout(2, {"skills": ["shield"], "stats": {}})
    room.start()
    a, b = room.players[1], room.players[2]
    ax, ay = find_free_spot(room, 2000, 2000)
    a.x, a.y = ax, ay
    b.x, b.y = ax + 150, ay
    room.resolve_walls(a)
    room.resolve_walls(b)
    # qua thoi diem bao ve spawn (spawnUntil = 1.6s)
    for _ in range(60):
        room.step(DT)
    return room, sent


def steps(room, n):
    for _ in range(n):
        room.step(DT)


def main():
    fails = []

    # --- 1. ha doi thu -> kills tang + end khi du killTarget ---
    room, sent = make_room(killTarget=1)
    a, b = room.players[1], room.players[2]
    b.hp = 1.0
    room.handle_cast(1, {"slot": 0, "ax": 1.0, "ay": 0.0, "tx": b.x, "ty": b.y})
    steps(room, 30)
    kills = a.kills
    end_msgs = [m for _, m in sent if m.get("t") == "end"]
    if kills != 1:
        fails.append("kills=%d (ky vong 1) sau khi ha doi thu" % kills)
    if not end_msgs:
        fails.append("khong co ban tin end khi du killTarget")
    elif end_msgs[0].get("winner", {}).get("id") != 1:
        fails.append("end winner sai: %r" % end_msgs[0].get("winner"))
    if room.state != "ended" and not end_msgs:
        fails.append("state chuyen %r nhung khong end" % room.state)
    print("1) kill + end:", "OK" if not any('kill' in f or 'end' in f for f in fails) else fails)

    # --- 2. hoi sinh sau respawn giay (mode kills, respawn=1) ---
    room2, sent2 = make_room(killTarget=999, respawn=1)
    a2, b2 = room2.players[1], room2.players[2]
    b2.hp = 1.0
    room2.handle_cast(1, {"slot": 0, "ax": 1.0, "ay": 0.0, "tx": b2.x, "ty": b2.y})
    steps(room2, 5)
    if b2.alive:
        fails.append("B chua bi ha sau khi trung snipe 1 HP")
    # spectate list gui cho nguoi chet
    if b2.alive is False and a2.alive:
        pass
    steps(room2, 40)  # ~1.3s > respawn 1s
    if not b2.alive:
        fails.append("B khong hoi sinh sau %s" % room2.time)
    else:
        print("2) respawn sau ha: OK (B hoi sinh tai t=%.1fs)" % room2.time)

    # --- 3. spectate: nguoi chet nhan specList, doi spec target bang handle_spec ---
    room3, sent3 = make_room(killTarget=999, respawn=10)
    a3, b3 = room3.players[1], room3.players[2]
    b3.hp = 1.0
    room3.handle_cast(1, {"slot": 0, "ax": 1.0, "ay": 0.0, "tx": b3.x, "ty": b3.y})
    steps(room3, 5)
    # server khong tu gan spec — client gui yeu cau (giong ban Edge)
    room3.handle_spec(b3.id, 1)
    snap = None
    room3.send_snapshots()
    for pid, m in sent3:
        if pid == b3.id and m.get("t") == "snap":
            snap = m
    if snap is None:
        fails.append("B khong nhan snapshot khi chet")
    else:
        if snap.get("spec") != 1:
            fails.append("spec target=%r (ky vong 1)" % snap.get("spec"))
        if not snap.get("specList"):
            fails.append("specList rong khi co nguoi song")
        else:
            print("3) spectate: OK (spec=%s, specList=%d nguoi)" % (
                snap.get("spec"), len(snap.get("specList"))))

    # --- 4. het thoi gian (mode time) -> end ---
    room4, sent4 = make_room(mode="time", timeLimit=30, killTarget=999)
    room4.time = 29.9
    steps(room4, 8)
    ends4 = [m for _, m in sent4 if m.get("t") == "end"]
    if not ends4:
        fails.append("mode time het gio khong end")
    else:
        print("4) end theo thoi gian: OK (winner=%r)" % (ends4[0].get("winner") or {}).get("name"))

    # --- 5. cast khi dead -> bo qua an toan ---
    room5, sent5 = make_room(killTarget=999, respawn=10)
    a5, b5 = room5.players[1], room5.players[2]
    b5.hp = 1.0
    room5.handle_cast(1, {"slot": 0, "ax": 1.0, "ay": 0.0, "tx": b5.x, "ty": b5.y})
    steps(room5, 3)
    projs_before = len(room5.projs)
    room5.handle_cast(1, {"slot": 0, "ax": 1.0, "ay": 0.0, "tx": 0, "ty": 0})
    if len(room5.projs) > projs_before + 0:
        pass  # A con song co the cast; neu A chet thi phai bo qua
    if not a5.alive:
        if len(room5.projs) > projs_before:
            fails.append("A chet van cast duoc")
        else:
            print("5) cast khi dead bi bo qua: OK")

    # --- 6. leave/remove giua tran + host chuyen ---
    room6, sent6 = make_room(killTarget=999)
    room6.remove_player(1)
    if room6.hostId != 2:
        fails.append("host khong chuyen sau khi host roi phong (%r)" % room6.hostId)
    else:
        print("6) host chuyen khi roi phong: OK")

    if fails:
        print("\nFAIL %d:" % len(fails))
        for f in fails:
            print("  -", f)
        return 1
    print("\nMATCH FLOW PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
