"""Profile: ten, bo kit, cai dat, cau hinh server. Luu JSON tren may."""
import json
import os
import sys
import uuid

from ..gamedata import sanitize_loadout, SLOTS, gear_by_slot, CHARS, SKILLS

DEFAULT_SETTINGS = {
    "volume": 0.6,
    "particles": True,
    "glow": True,
    "shake": True,
    "fps": False,
}

DEFAULT_ROOM = {
    "name": "",
    "password": "",
    "maxPlayers": 16,
    "startHp": 100,
    "mode": "kills",
    "killTarget": 20,
    "timeLimit": 300,
    "respawn": 3,
}

DEFAULT_SERVER = {"port": 3000, "lastAddr": "localhost:3000", "room": dict(DEFAULT_ROOM)}


def project_root():
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def data_dir():
    env = os.environ.get("NC_DATA_DIR")
    if env:
        d = os.path.abspath(env)
    else:
        root = project_root()
        d = os.path.join(root, "data")
        # thuong khong ghi duoc vao Program Files -> dung APPDATA
        try:
            os.makedirs(d, exist_ok=True)
            probe = os.path.join(d, ".w")
            with open(probe, "w") as f:
                f.write("1")
            os.remove(probe)
        except Exception:
            base = os.environ.get("APPDATA") or os.path.expanduser("~")
            d = os.path.join(base, "NeonClash")
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    return d


def profile_dir(name="main"):
    safe = "".join(c for c in str(name or "main") if c.isalnum() or c in "-_") or "main"
    d = os.path.join(data_dir(), "profiles", safe)
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    return d


def _kit(name, char, stats, gear_ids, skills):
    gear = {}
    for slot in SLOTS:
        pool = gear_by_slot(slot["id"])
        pick = next((g for g in pool if g["id"] == gear_ids.get(slot["id"])), pool[0])
        gear[slot["id"]] = pick["id"]
    l = sanitize_loadout({"char": char, "stats": stats, "gear": gear, "skills": skills})
    return {"id": uuid.uuid4().hex[:8], "name": name, **l}


def default_kits():
    return [
        _kit("Xạ Thủ", "gunner",
             {"dmg": 3, "atkspd": 3, "range": 3, "speed": 1},
             {"head": "helm_hawk", "body": "body_light", "legs": "legs_ammo",
              "shoes": "boots_speed", "weapon": "wp_rifle"},
             ["snipe", "barrage", "pierce", "dash", "shield"]),
        _kit("Cận Chiến", "assassin",
             {"dmg": 3, "hp": 3, "speed": 3, "armor": 1},
             {"head": "helm_leather", "body": "body_kevlar", "legs": "legs_combat",
              "shoes": "boots_speed", "weapon": "wp_blade"},
             ["triple", "whirl", "execute", "dash", "heal"]),
        _kit("Hỗn Hợp", "mage",
             {"dmg": 3, "cdr": 3, "hp": 3, "regen": 1},
             {"head": "helm_focus", "body": "body_regen", "legs": "legs_rune",
              "shoes": "boots_armor", "weapon": "wp_pistol"},
             ["fireball", "chain", "blink", "mine", "shield"]),
    ]


def default_profile():
    kits = default_kits()
    return {
        "name": "",
        "kits": kits,
        "activeKit": kits[0]["id"],
        "settings": dict(DEFAULT_SETTINGS),
    }


def _sanitize(p):
    if not isinstance(p, dict):
        p = {}
    out = default_profile()
    out["name"] = str(p.get("name") or "")[:16]

    kits = []
    for k in p.get("kits") or []:
        if not isinstance(k, dict):
            continue
        l = sanitize_loadout(k)
        kits.append({
            "id": str(k.get("id") or uuid.uuid4().hex[:8]),
            "name": (str(k.get("name") or "Kit")[:20]) or "Kit",
            **l,
        })
    if kits:
        out["kits"] = kits
    ids = {k["id"] for k in out["kits"]}
    out["activeKit"] = p.get("activeKit") if p.get("activeKit") in ids else out["kits"][0]["id"]

    s = p.get("settings") if isinstance(p.get("settings"), dict) else {}
    out["settings"] = dict(DEFAULT_SETTINGS)
    for k, v in s.items():
        if k in out["settings"] and isinstance(v, type(out["settings"][k])):
            out["settings"][k] = v
    out["settings"]["volume"] = max(0.0, min(1.0, float(out["settings"]["volume"])))
    return out


def _pid_alive(pid):
    if pid <= 0:
        return False
    if os.name == "nt":
        try:
            import ctypes
            h = ctypes.windll.kernel32.OpenProcess(0x1000, False, int(pid))
            if h:
                ctypes.windll.kernel32.CloseHandle(h)
                return True
            return False
        except Exception:
            return False
    try:
        os.kill(int(pid), 0)
        return True
    except Exception:
        return False


def pick_profile(requested="main"):
    """Chon profile con trong de mo nhieu client tren 1 may."""
    if requested and requested != "main":
        return requested
    names = ["main"] + ["main%d" % i for i in range(2, 9)]
    for name in names:
        d = profile_dir(name)
        lock = os.path.join(d, "app.lock")
        busy = False
        try:
            if os.path.exists(lock):
                with open(lock, "r") as f:
                    busy = _pid_alive(int(f.read().strip() or 0))
        except Exception:
            busy = False
        if busy:
            continue
        try:
            with open(lock, "w") as f:
                f.write(str(os.getpid()))
            import atexit

            def _clean(p=lock):
                try:
                    with open(p, "r") as f:
                        if f.read().strip() == str(os.getpid()):
                            os.remove(p)
                except Exception:
                    pass

            atexit.register(_clean)
        except Exception:
            pass
        return name
    return "main"


class Profile:
    def __init__(self, name="main"):
        self.pname = name
        self.dir = profile_dir(name)
        self.path = os.path.join(self.dir, "profile.json")
        self.data = default_profile()
        self.load()

    def load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                self.data = _sanitize(json.load(f))
        except Exception:
            self.data = default_profile()
            self.save()

    def save(self):
        try:
            os.makedirs(self.dir, exist_ok=True)
            tmp = self.path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=1)
            os.replace(tmp, self.path)
        except Exception:
            pass

    # ---------------- truy van ----------------
    @property
    def display_name(self):
        return self.data.get("name") or "Người chơi"

    @property
    def name(self):
        return self.data.get("name") or ""

    @name.setter
    def name(self, v):
        self.data["name"] = str(v or "")[:16]
        self.save()

    @property
    def settings(self):
        return self.data["settings"]

    @property
    def kits(self):
        return self.data["kits"]

    def active_kit(self):
        kid = self.data.get("activeKit")
        for k in self.kits:
            if k["id"] == kid:
                return k
        return self.kits[0]

    def set_active(self, kid):
        if any(k["id"] == kid for k in self.kits):
            self.data["activeKit"] = kid
            self.save()

    def loadout(self):
        k = self.active_kit()
        return {"char": k["char"], "stats": dict(k["stats"]),
                "gear": dict(k["gear"]), "skills": list(k["skills"])}

    def update_kit(self, kid, loadout):
        for k in self.kits:
            if k["id"] == kid:
                l = sanitize_loadout(loadout)
                k.update(l)
                self.save()
                return
        self.save()

    def new_kit(self, name="Kit mới", from_active=True):
        base = self.loadout() if from_active else sanitize_loadout(None)
        k = {"id": uuid.uuid4().hex[:8], "name": str(name or "Kit")[:20], **base}
        self.kits.append(k)
        self.data["activeKit"] = k["id"]
        self.save()
        return k

    def duplicate_kit(self, kid):
        src = next((k for k in self.kits if k["id"] == kid), None)
        if not src:
            return None
        k = {"id": uuid.uuid4().hex[:8], "name": (src["name"] + " 2")[:20],
             "char": src["char"], "stats": dict(src["stats"]),
             "gear": dict(src["gear"]), "skills": list(src["skills"])}
        self.kits.append(k)
        self.data["activeKit"] = k["id"]
        self.save()
        return k

    def rename_kit(self, kid, name):
        for k in self.kits:
            if k["id"] == kid:
                k["name"] = (str(name or "Kit")[:20]) or "Kit"
                self.save()
                return

    def delete_kit(self, kid):
        if len(self.kits) <= 1:
            return False
        self.data["kits"] = [k for k in self.kits if k["id"] != kid]
        if self.data.get("activeKit") == kid:
            self.data["activeKit"] = self.kits[0]["id"]
        self.save()
        return True


# ---------------- config chung (cong, dia chi gan nhat) ----------------
def config_path():
    return os.path.join(data_dir(), "config.json")


def load_config():
    cfg = dict(DEFAULT_SERVER)
    cfg["room"] = dict(DEFAULT_ROOM)
    try:
        with open(config_path(), "r", encoding="utf-8") as f:
            data = json.load(f)
        for k in ("port", "lastAddr"):
            if k in data:
                cfg[k] = data[k]
        room = data.get("room")
        if isinstance(room, dict):
            for k, v in room.items():
                if k in cfg["room"]:
                    cfg["room"][k] = v
    except Exception:
        pass
    return cfg


def save_config(**kw):
    cfg = load_config()
    for k, v in kw.items():
        if k in cfg:
            cfg[k] = v
    try:
        with open(config_path(), "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=1)
    except Exception:
        pass
    return cfg
