"""Am thanh sinh bang code (khong can file mp3/wav)."""
import array
import math
import random

import pygame

RATE = 44100


def _make(freq=440.0, dur=0.1, kind="sine", vol=0.35, decay=8.0,
          sweep=0.0, noise=0.0, attack=0.004):
    n = max(1, int(RATE * dur))
    buf = array.array("h")
    phase = 0.0
    for i in range(n):
        t = i / RATE
        f = max(20.0, freq + sweep * t)
        phase += 2 * math.pi * f / RATE
        if kind == "square":
            v = 1.0 if math.sin(phase) > 0 else -1.0
        elif kind == "saw":
            v = 2.0 * ((phase / (2 * math.pi)) % 1.0) - 1.0
        elif kind == "tri":
            v = 2.0 * abs(2.0 * ((phase / (2 * math.pi)) % 1.0) - 1.0) - 1.0
        elif kind == "noise":
            v = random.uniform(-1.0, 1.0)
        else:
            v = math.sin(phase)
        if noise:
            v = v * (1 - noise) + random.uniform(-1.0, 1.0) * noise
        env = math.exp(-decay * t)
        if t < attack:
            env *= t / attack
        s = v * env * vol
        buf.append(int(max(-1.0, min(1.0, s)) * 32000))
    try:
        return pygame.mixer.Sound(buffer=buf.tobytes())
    except Exception:
        return None


class Sfx:
    def __init__(self, volume=0.6):
        self.ok = False
        self.volume = volume
        self.s = {}
        try:
            pygame.mixer.pre_init(RATE, -16, 1, 512)
            pygame.mixer.init(RATE, -16, 1, 512)
            pygame.mixer.set_num_channels(24)
            self.ok = True
        except Exception:
            return
        self._build()

    def _build(self):
        self.s = {
            "shoot": _make(760, 0.055, "square", 0.16, 26, -5200, 0.35),
            "shoot2": _make(420, 0.07, "saw", 0.14, 20, -2600, 0.3),
            "hit": _make(240, 0.05, "noise", 0.18, 30, 0, 0.85),
            "boom": _make(90, 0.36, "noise", 0.42, 8, -140, 0.75),
            "beam": _make(1200, 0.2, "saw", 0.16, 9, -5200, 0.1),
            "slash": _make(520, 0.09, "noise", 0.16, 22, -2200, 0.6),
            "kill": _make(660, 0.16, "tri", 0.28, 7, 520),
            "ui": _make(880, 0.045, "sine", 0.12, 24, 260),
            "hurt": _make(150, 0.14, "saw", 0.22, 14, -80),
            "cast": _make(300, 0.12, "sine", 0.13, 12, 900),
            "heal": _make(520, 0.18, "sine", 0.14, 6, 700),
            "spawn": _make(300, 0.2, "sine", 0.12, 8, 600),
            "death": _make(180, 0.4, "tri", 0.24, 5, -260),
        }

    def play(self, name, vol=1.0):
        if not self.ok:
            return
        snd = self.s.get(name)
        if not snd:
            return
        try:
            snd.set_volume(max(0.0, min(1.0, self.volume * vol)))
            snd.play()
        except Exception:
            pass

    def set_volume(self, v):
        self.volume = max(0.0, min(1.0, v))

    # ten goi y
    def shoot(self, weapon="gun"):
        self.play("shoot2" if weapon == "melee" else "shoot", 0.8)

    def hit(self):
        self.play("hit", 0.7)

    def boom(self):
        self.play("boom", 0.9)

    def beam(self):
        self.play("beam", 0.8)

    def kill(self):
        self.play("kill", 0.9)

    def ui(self):
        self.play("ui", 0.6)

    def hurt(self):
        self.play("hurt", 0.8)

    def cast(self):
        self.play("cast", 0.6)

    def slash(self):
        self.play("slash", 0.7)

    def heal(self):
        self.play("heal", 0.7)

    def spawn(self):
        self.play("spawn", 0.6)

    def death(self):
        self.play("death", 0.8)
