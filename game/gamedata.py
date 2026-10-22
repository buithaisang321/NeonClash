# ============================================================
#  NEON CLASH - du lieu dung chung (server + client)
# ============================================================
GAME_NAME = "NEON CLASH"

STAT_POINTS = 10
STAT_MAX = 3
STAT_STEP = 0.08

STATS = [
    {"id": "dmg",    "name": "Sát thương",     "short": "DMG", "desc": "+8% sát thương tất cả đòn đánh và chiêu"},
    {"id": "atkspd", "name": "Tốc đánh",       "short": "ATK", "desc": "+8% tốc độ đánh thường"},
    {"id": "speed",  "name": "Tốc chạy",       "short": "SPD", "desc": "+7% tốc độ di chuyển"},
    {"id": "hp",     "name": "Máu",            "short": "HP",  "desc": "+10% máu tối đa"},
    {"id": "armor",  "name": "Giáp",           "short": "DEF", "desc": "+7% giảm sát thương nhận vào"},
    {"id": "cdr",    "name": "Giảm hồi chiêu", "short": "CDR", "desc": "+8% giảm thời gian hồi chiêu"},
    {"id": "range",  "name": "Tầm bắn",        "short": "RNG", "desc": "+8% tầm bắn và tầm chiêu"},
    {"id": "regen",  "name": "Hồi phục",       "short": "REG", "desc": "+0.55 máu hồi mỗi giây"},
]
STAT_MAP = {s["id"]: s for s in STATS}

CHARS = [
    {"id": "shadow", "name": "Bóng Đêm", "color": "#7c5cff", "accent": "#c9b8ff", "shape": "triangle",
     "passiveName": "Nhanh Nhẹn", "passiveDesc": "+8% tốc chạy", "passive": {"speed": 0.08}},
    {"id": "titan", "name": "Titan", "color": "#ff8a3d", "accent": "#ffd0a8", "shape": "square",
     "passiveName": "Thể Chất", "passiveDesc": "+12% máu tối đa", "passive": {"hp": 0.12}},
    {"id": "gunner", "name": "Xạ Thủ", "color": "#3ddc97", "accent": "#b6ffe0", "shape": "hex",
     "passiveName": "Thiện Xạ", "passiveDesc": "+10% tầm bắn", "passive": {"range": 0.10}},
    {"id": "mage", "name": "Pháp Sư", "color": "#4ea8ff", "accent": "#bcdcff", "shape": "diamond",
     "passiveName": "Mạch Ma", "passiveDesc": "+10% giảm hồi chiêu", "passive": {"cdr": 0.10}},
    {"id": "assassin", "name": "Sát Thủ", "color": "#ff4d6d", "accent": "#ffb8c4", "shape": "star",
     "passiveName": "Sát Ý", "passiveDesc": "+8% sát thương", "passive": {"dmg": 0.08}},
    {"id": "medic", "name": "Y Sĩ", "color": "#ffd166", "accent": "#fff0c2", "shape": "circle",
     "passiveName": "Tái Sinh", "passiveDesc": "+0.9 máu hồi mỗi giây", "passive": {"regen": 0.9}},
]
CHAR_MAP = {c["id"]: c for c in CHARS}

SLOTS = [
    {"id": "head",   "name": "Mũ",     "icon": "⌂"},
    {"id": "body",   "name": "Áo",     "icon": "▤"},
    {"id": "legs",   "name": "Quần",   "icon": "∥"},
    {"id": "shoes",  "name": "Giày",   "icon": "⌄"},
    {"id": "weapon", "name": "Vũ khí", "icon": "➤"},
]

GEAR = [
    {"id": "helm_leather", "slot": "head", "name": "Mũ Da",          "buff": {"speed": 0.06},    "desc": "+6% tốc chạy"},
    {"id": "helm_iron",    "slot": "head", "name": "Mũ Sắt",         "buff": {"hp": 0.15},       "desc": "+15% máu tối đa"},
    {"id": "helm_focus",   "slot": "head", "name": "Mũ Tập Trung",   "buff": {"cdr": 0.10},      "desc": "+10% giảm hồi chiêu"},
    {"id": "helm_hawk",    "slot": "head", "name": "Mũ Ưng",         "buff": {"range": 0.10},    "desc": "+10% tầm bắn"},

    {"id": "body_kevlar",  "slot": "body", "name": "Áo Kevlar",       "buff": {"armor": 0.12},    "desc": "+12% giáp"},
    {"id": "body_light",   "slot": "body", "name": "Áo Nhẹ",          "buff": {"atkspd": 0.10},   "desc": "+10% tốc đánh"},
    {"id": "body_vamp",    "slot": "body", "name": "Áo Hút Máu",      "buff": {"lifesteal": 0.14}, "desc": "Hồi 14% sát thương gây ra thành máu"},
    {"id": "body_regen",   "slot": "body", "name": "Áo Tái Sinh",     "buff": {"regen": 1.2},     "desc": "+1.2 máu hồi mỗi giây"},

    {"id": "legs_combat",  "slot": "legs", "name": "Quần Tác Chiến",  "buff": {"hp": 0.10},       "desc": "+10% máu tối đa"},
    {"id": "legs_swift",   "slot": "legs", "name": "Quần Nhanh Nhẹn", "buff": {"speed": 0.08},    "desc": "+8% tốc chạy"},
    {"id": "legs_ammo",    "slot": "legs", "name": "Quần Đạn Dược",   "buff": {"atkspd": 0.10},   "desc": "+10% tốc đánh"},
    {"id": "legs_rune",    "slot": "legs", "name": "Quần Phù Văn",    "buff": {"cdr": 0.10},      "desc": "+10% giảm hồi chiêu"},

    {"id": "boots_speed",  "slot": "shoes", "name": "Giày Tốc Độ",    "buff": {"speed": 0.12},    "desc": "+12% tốc chạy"},
    {"id": "boots_armor",  "slot": "shoes", "name": "Giày Bọc Thép",  "buff": {"armor": 0.10},    "desc": "+10% giáp"},
    {"id": "boots_dodge",  "slot": "shoes", "name": "Giày Né Tránh",  "buff": {"dodge": 0.12},    "desc": "12% cơ hội né hoàn toàn đòn đánh"},
    {"id": "boots_grip",   "slot": "shoes", "name": "Giày Bám Đất",   "buff": {"ccResist": 0.35}, "desc": "Giảm 35% hiệu ứng làm chậm / trói"},

    {"id": "wp_pistol", "slot": "weapon", "name": "Súng Lục", "buff": {},
     "desc": "Bắn nhanh, sát thương vừa, tầm trung",
     "weapon": {"dmg": 12, "rate": 4.2, "pspd": 950, "range": 640, "spread": 0.05, "pellets": 1, "kind": "gun"}},
    {"id": "wp_rifle", "slot": "weapon", "name": "Súng Trường", "buff": {},
     "desc": "Chuẩn xác, tầm rất xa, tốc đánh chậm",
     "weapon": {"dmg": 18, "rate": 2.4, "pspd": 1500, "range": 1000, "spread": 0.015, "pellets": 1, "kind": "gun"}},
    {"id": "wp_shotgun", "slot": "weapon", "name": "Shotgun", "buff": {},
     "desc": "6 viên đạn xoè, cực mạnh ở cự ly gần",
     "weapon": {"dmg": 8, "rate": 1.5, "pspd": 850, "range": 400, "spread": 0.20, "pellets": 6, "kind": "gun"}},
    {"id": "wp_blade", "slot": "weapon", "name": "Kiếm Năng Lượng", "buff": {},
     "desc": "Chém cận chiến hình quạt, sát thương cao",
     "weapon": {"dmg": 28, "rate": 2.1, "pspd": 0, "range": 100, "spread": 0, "pellets": 1, "kind": "melee", "arc": 1.8}},
]
GEAR_MAP = {g["id"]: g for g in GEAR}


def gear_by_slot(slot):
    return [g for g in GEAR if g["slot"] == slot]


SKILL_GROUPS = [
    {"id": "atk", "name": "Tấn công",  "color": "#ff5c7a"},
    {"id": "mob", "name": "Cơ động",   "color": "#3ddc97"},
    {"id": "def", "name": "Phòng thủ", "color": "#4ea8ff"},
    {"id": "ctl", "name": "Khống chế", "color": "#c07bff"},
]
GROUP_MAP = {g["id"]: g for g in SKILL_GROUPS}

SKILL_RANGES = [
    {"id": "melee", "name": "Cận chiến", "color": "#ff8a3d"},
    {"id": "mid",   "name": "Tầm trung", "color": "#ffd166"},
    {"id": "long",  "name": "Tầm xa",    "color": "#4ea8ff"},
    {"id": "util",  "name": "Tiện ích",  "color": "#3ddc97"},
]
RANGE_MAP = {r["id"]: r for r in SKILL_RANGES}

SKILLS = [
    # ---- tấn công / tầm xa ----
    {"id": "pierce",   "group": "atk", "range": "long", "name": "Đạn Xuyên Phá", "icon": "➤", "cd": 5,
     "desc": "Bắn viên đạn xuyên qua tối đa 3 kẻ địch, 22 sát thương mỗi mục tiêu."},
    {"id": "beam",     "group": "atk", "range": "long", "name": "Tia Laser", "icon": "≡", "cd": 7,
     "desc": "Bắn tia laser tức thì dài 700, xuyên mọi kẻ địch trên đường, 30 sát thương."},
    {"id": "snipe",    "group": "atk", "range": "long", "name": "Bắn Tỉa", "icon": "⊸", "cd": 12,
     "desc": "Phát bắn tức thì dài 1100, xuyên mọi mục tiêu, 45 sát thương. Tầm xa nhất game."},
    {"id": "meteor",   "group": "atk", "range": "long", "name": "Mưa Thiên Thạch", "icon": "✹", "cd": 12,
     "desc": "Gọi thiên thạch rơi xuống vị trí ngắm sau 0.8s: 45 sát thương lan 140."},
    {"id": "chain",    "group": "atk", "range": "long", "name": "Sét Dây Chuyền", "icon": "⌁", "cd": 10,
     "desc": "Sét đánh mục tiêu gần nhất (500), rồi nhảy sang tối đa 3 mục tiêu trong 260. Mỗi lần 28 sát thương."},

    # ---- tấn công / tầm trung ----
    {"id": "burst",    "group": "atk", "range": "mid", "name": "Bão Đạn", "icon": "⋔", "cd": 6,
     "desc": "Bắn 3 viên đạn toả ra, mỗi viên 12 sát thương."},
    {"id": "fireball", "group": "atk", "range": "mid", "name": "Cầu Lửa", "icon": "◉", "cd": 8,
     "desc": "Cầu lửa bay chậm, nổ khi chạm: 30 sát thương trực tiếp + 20 sát thương lan 90."},
    {"id": "glaive",   "group": "atk", "range": "mid", "name": "Dao Bay", "icon": "✧", "cd": 7,
     "desc": "Ném dao xoay bay đi rồi quay lại, 18 sát thương mỗi lần chạm."},
    {"id": "barrage",  "group": "atk", "range": "mid", "name": "Mưa Đạn", "icon": "⋮", "cd": 9,
     "desc": "Xả 7 viên đạn toả hình quạt 60°, mỗi viên 9 sát thương. Cực mạnh ở cự ly vừa."},
    {"id": "homing",   "group": "atk", "range": "mid", "name": "Tên Truy Kích", "icon": "↝", "cd": 9,
     "desc": "Phóng tên tự động bám theo kẻ địch gần nhất, 22 sát thương."},
    {"id": "ricochet", "group": "atk", "range": "mid", "name": "Đạn Nảy", "icon": "⟳", "cd": 8,
     "desc": "Đạn nảy tường tối đa 3 lần, 18 sát thương mỗi lần trúng. Bắn được qua góc khuất."},
    {"id": "grenade",  "group": "atk", "range": "mid", "name": "Lựu Đạn", "icon": "◍", "cd": 10,
     "desc": "Ném lựu đạn nảy tường, sau 1.2s nổ: 50 sát thương lan 120."},

    # ---- tấn công / cận chiến ----
    {"id": "triple",   "group": "atk", "range": "melee", "name": "Liên Hoàn Trảm", "icon": "⫽", "cd": 7,
     "desc": "Chém 3 nhát liên tiếp trong 0.6s, mỗi nhát 16 sát thương hình quạt 100°."},
    {"id": "whirl",    "group": "atk", "range": "melee", "name": "Xoay Kiếm", "icon": "✺", "cd": 8,
     "desc": "Xoay 360° quanh người: 28 sát thương bán kính 120 và làm chậm 30% trong 1.5s."},
    {"id": "uppercut", "group": "atk", "range": "melee", "name": "Thăng Long Kích", "icon": "⇡", "cd": 9,
     "desc": "Chém móc: 26 sát thương hình quạt 90° và đẩy lùi kẻ địch 90px."},
    {"id": "execute",  "group": "atk", "range": "melee", "name": "Kết Liễu", "icon": "⚡", "cd": 14,
     "desc": "Chém 40 sát thương; nếu mục tiêu dưới 30% máu thì gây 90 sát thương."},
    {"id": "nova",     "group": "atk", "range": "melee", "name": "Xung Kích", "icon": "◎", "cd": 8,
     "desc": "Sóng xung kích quanh người bán kính 170: 24 sát thương và đẩy lùi."},

    # ---- cơ động ----
    {"id": "dash",     "group": "mob", "range": "util", "name": "Lướt", "icon": "»", "cd": 4,
     "desc": "Lướt nhanh 260 theo hướng ngắm trong 0.18s."},
    {"id": "blink",    "group": "mob", "range": "util", "name": "Dịch Chuyển", "icon": "⋈", "cd": 8,
     "desc": "Dịch chuyển tức thì 320 theo hướng ngắm (không xuyên vật cản)."},
    {"id": "leap",     "group": "mob", "range": "util", "name": "Nhảy Vọt", "icon": "⇟", "cd": 9,
     "desc": "Nhảy xa 220, bất tử trong lúc bay (0.35s)."},
    {"id": "haste",    "group": "mob", "range": "util", "name": "Tăng Tốc", "icon": "≫", "cd": 12,
     "desc": "+55% tốc chạy trong 3.5s."},
    {"id": "charge",   "group": "mob", "range": "melee", "name": "Xung Phong", "icon": "⇢", "cd": 9,
     "desc": "Lao tới 300px trong 0.25s, gây 30 sát thương cho mọi kẻ địch trên đường lao."},
    {"id": "hook",     "group": "mob", "range": "mid", "name": "Móc Xích", "icon": "⤙", "cd": 10,
     "desc": "Bắn móc dài 380: kéo kẻ địch trúng về sát bên mình và gây 10 sát thương."},
    {"id": "swap",     "group": "mob", "range": "long", "name": "Hoán Đổi", "icon": "⇄", "cd": 16,
     "desc": "Đổi vị trí tức thì với kẻ địch gần nhất trong 500. Dùng để thoát hoặc áp sát."},

    # ---- phòng thủ ----
    {"id": "shield",   "group": "def", "range": "util", "name": "Khiên Năng Lượng", "icon": "⛊", "cd": 14,
     "desc": "Tạo khiên hấp thụ 60 sát thương trong 4s."},
    {"id": "heal",     "group": "def", "range": "util", "name": "Hồi Máu", "icon": "✚", "cd": 16,
     "desc": "Hồi ngay 45 máu."},
    {"id": "phase",    "group": "def", "range": "util", "name": "Bất Tử", "icon": "◇", "cd": 16,
     "desc": "Bất tử hoàn toàn trong 1.3s."},
    {"id": "ironskin", "group": "def", "range": "util", "name": "Giáp Sắt", "icon": "▣", "cd": 14,
     "desc": "+35% giáp trong 4s."},
    {"id": "wall",     "group": "def", "range": "util", "name": "Tường Chắn", "icon": "▮", "cd": 14,
     "desc": "Dựng tường năng lượng chắn đạn và chặn đường trong 6s."},

    # ---- khống chế ----
    {"id": "mine",     "group": "ctl", "range": "mid", "name": "Mìn", "icon": "✱", "cd": 9,
     "desc": "Đặt mìn, sau 0.8s kích hoạt: 55 sát thương lan 110. Tối đa 2 quả."},
    {"id": "smoke",    "group": "ctl", "range": "util", "name": "Bom Khói", "icon": "☁", "cd": 14,
     "desc": "Vùng khói bán kính 200 trong 4s, kẻ địch bên trong bị chậm 30%."},
    {"id": "frost",    "group": "ctl", "range": "mid", "name": "Đạn Băng", "icon": "❄", "cd": 8,
     "desc": "Đạn 14 sát thương, làm chậm 45% trong 2.5s."},
    {"id": "snare",    "group": "ctl", "range": "mid", "name": "Lưới Điện", "icon": "⌗", "cd": 10,
     "desc": "Đặt bẫy, kẻ địch giẫm vào bị trói 1.4s và nhận 10 sát thương."},
    {"id": "venom",    "group": "ctl", "range": "mid", "name": "Độc Tố", "icon": "☠", "cd": 9,
     "desc": "Đạn độc: 8 sát thương + 6 sát thương/giây trong 4s."},
    {"id": "turret",   "group": "ctl", "range": "long", "name": "Trụ Súng", "icon": "⌸", "cd": 18,
     "desc": "Đặt trụ tự bắn kẻ địch trong 550 tầm, 10 sát thương mỗi phát, tồn tại 8s."},
]
SKILL_MAP = {s["id"]: s for s in SKILLS}
SKILL_SLOTS = 5

# Kit mac dinh cho nguoi choi chua tung gui loadout (nhu vong dem cu cua Edge)
DEFAULT_LOADOUT = {
    "char": "gunner",
    "stats": {"dmg": 3, "atkspd": 3, "range": 3, "speed": 1},
    "gear": {"weapon": "wp_rifle", "head": "helm_hawk", "body": "body_light",
             "legs": "legs_ammo", "shoes": "boots_speed"},
    "skills": ["snipe", "barrage", "pierce", "dash", "shield"],
}

MAP_SIZE = 4000
WALL_THICK = 60

DEFAULT_SETTINGS = {
    "name": "Phòng của tôi",
    "password": "",
    "maxPlayers": 16,
    "mode": "kills",
    "killTarget": 20,
    "timeLimit": 300,
    "respawn": 3,
    "startHp": 100,
    "mapSeed": 0,
    "friendlyFire": True,
}

MODES = [
    {"id": "kills", "name": "Đạt mạng trước", "desc": "Ai đạt số mạng mục tiêu trước thì thắng. Chết vẫn hồi sinh."},
    {"id": "time",  "name": "Tính giờ",       "desc": "Hết thời gian, ai nhiều mạng nhất thắng."},
    {"id": "last",  "name": "Sống sót cuối",  "desc": "Không hồi sinh, người cuối cùng còn sống thắng."},
]
MODE_MAP = {m["id"]: m for m in MODES}


def clamp(v, a, b):
    return a if v < a else (b if v > b else v)


def _int(v, default=0):
    try:
        n = float(v)
    except (TypeError, ValueError):
        return default
    if n != n or n in (float("inf"), float("-inf")):
        return default
    return int(n)


def sanitize_loadout(raw):
    l = raw if isinstance(raw, dict) else {}
    char = l.get("char") if l.get("char") in CHAR_MAP else CHARS[0]["id"]

    stats = {}
    used = 0
    raw_stats = l.get("stats") if isinstance(l.get("stats"), dict) else {}
    for s in STATS:
        v = max(0, min(STAT_MAX, _int(raw_stats.get(s["id"]), 0)))
        if used + v > STAT_POINTS:
            v = max(0, STAT_POINTS - used)
        stats[s["id"]] = v
        used += v

    gear = {}
    raw_gear = l.get("gear") if isinstance(l.get("gear"), dict) else {}
    for slot in SLOTS:
        pool = gear_by_slot(slot["id"])
        pick = next((g for g in pool if g["id"] == raw_gear.get(slot["id"])), None)
        gear[slot["id"]] = (pick or pool[0])["id"]

    skills = []
    src = l.get("skills") if isinstance(l.get("skills"), list) else []
    for sid in src:
        if sid in SKILL_MAP and sid not in skills and len(skills) < SKILL_SLOTS:
            skills.append(sid)
    # KHONG dem chiêu: cho phep kit it hon 5 chiêu (bam the da chon de bo)

    return {"char": char, "stats": stats, "gear": gear, "skills": skills}


def compute_build(loadout, start_hp=100):
    l = sanitize_loadout(loadout)
    ch = CHAR_MAP[l["char"]]

    add = {"dmg": 0.0, "atkspd": 0.0, "speed": 0.0, "hp": 0.0, "armor": 0.0,
           "cdr": 0.0, "range": 0.0, "lifesteal": 0.0, "dodge": 0.0, "ccResist": 0.0}
    regen_flat = 0.0

    for s in STATS:
        n = l["stats"].get(s["id"], 0)
        if not n:
            continue
        if s["id"] == "regen":
            regen_flat += n * 0.55
        elif s["id"] == "speed":
            add["speed"] += n * 0.07
        elif s["id"] == "hp":
            add["hp"] += n * 0.10
        elif s["id"] == "armor":
            add["armor"] += n * 0.07
        else:
            add[s["id"]] += n * STAT_STEP

    for slot in SLOTS:
        g = GEAR_MAP.get(l["gear"][slot["id"]])
        if not g:
            continue
        for k, v in (g.get("buff") or {}).items():
            if k == "regen":
                regen_flat += v
            else:
                add[k] = add.get(k, 0) + v

    for k, v in (ch.get("passive") or {}).items():
        if k == "regen":
            regen_flat += v
        else:
            add[k] = add.get(k, 0) + v

    w = (GEAR_MAP.get(l["gear"]["weapon"], {}).get("weapon")
         or GEAR_MAP["wp_pistol"]["weapon"])
    dmg_mul = 1 + add["dmg"]
    atkspd_mul = 1 + add["atkspd"]
    range_mul = 1 + add["range"]

    return {
        "char": l["char"],
        "stats": l["stats"],
        "gear": l["gear"],
        "skills": l["skills"],
        "charData": ch,
        "maxHp": int(start_hp * (1 + add["hp"]) + 0.5),
        "dmgMul": dmg_mul,
        "atkSpdMul": atkspd_mul,
        "speed": 230 * (1 + add["speed"]),
        "armor": clamp(add["armor"], 0, 0.65),
        "cdrMul": clamp(1 - add["cdr"], 0.3, 1),
        "rangeMul": range_mul,
        "regen": 0.8 + regen_flat,
        "lifesteal": add.get("lifesteal", 0),
        "dodge": clamp(add.get("dodge", 0), 0, 0.5),
        "ccResist": clamp(add.get("ccResist", 0), 0, 0.8),
        "weapon": {
            "kind": w["kind"],
            "dmg": w["dmg"] * dmg_mul,
            "rate": w["rate"] * atkspd_mul,
            "pspd": w["pspd"],
            "range": w["range"] * range_mul,
            "spread": w["spread"],
            "pellets": w["pellets"],
            "arc": w.get("arc", 1.6),
            "name": GEAR_MAP.get(l["gear"]["weapon"], {}).get("name", "Súng Lục"),
        },
    }


def hex_rgb(c):
    c = c.lstrip("#")
    return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16))


def build_summary(loadout, start_hp=100):
    """So lieu nhanh de hien thi trong hub."""
    b = compute_build(loadout, start_hp)
    w = b["weapon"]
    dps = w["dmg"] * w["rate"] * (w["pellets"] if w["kind"] == "gun" else 1)
    return {
        "hp": b["maxHp"],
        "dmg": w["dmg"],
        "dmgMul": b["dmgMul"],
        "speed": b["speed"],
        "atkspd": b["atkSpdMul"],
        "armor": b["armor"],
        "cdr": b["cdrMul"],
        "range": b["rangeMul"],
        "regen": b["regen"],
        "dps": dps,
    }
