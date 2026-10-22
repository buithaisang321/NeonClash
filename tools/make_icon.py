"""Sinh file .ico cho app (khong can thu vien ngoai)."""
import os
import struct
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame


def draw(size):
    pygame.display.init()
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    r = size
    pygame.draw.rect(surf, (8, 11, 20), (0, 0, r, r), border_radius=int(r * 0.22))
    # vien
    pygame.draw.rect(surf, (40, 56, 86), (0, 0, r, r), max(1, r // 32), border_radius=int(r * 0.22))
    # tam giac neon
    cx, cy = r / 2, r * 0.53
    rad = r * 0.3
    pts = [(cx, cy - rad), (cx + rad * 0.95, cy + rad * 0.72), (cx - rad * 0.95, cy + rad * 0.72)]
    pygame.draw.polygon(surf, (0, 229, 255), pts)
    pygame.draw.polygon(surf, (235, 250, 255), pts, max(1, r // 24))
    pygame.draw.circle(surf, (124, 92, 255), (int(cx), int(cy + rad * 0.12)), max(2, int(r * 0.1)))
    return surf


def main(out="build/icon.ico"):
    pygame.init()
    pygame.display.set_mode((64, 64))
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    sizes = [16, 24, 32, 48, 64, 128, 256]
    blobs = []
    for s in sizes:
        surf = draw(s)
        tmp = "build/_ico_%d.png" % s
        pygame.image.save(surf, tmp)
        with open(tmp, "rb") as f:
            blobs.append((s, f.read()))
        os.remove(tmp)
    # ICONDIR
    head = struct.pack("<HHH", 0, 1, len(blobs))
    offset = 6 + 16 * len(blobs)
    entries = b""
    data = b""
    for s, png in blobs:
        w = 0 if s >= 256 else s
        entries += struct.pack("<BBBBHHII", w, w, 0, 0, 1, 32, len(png), offset)
        offset += len(png)
        data += png
    with open(out, "wb") as f:
        f.write(head + entries + data)
    print("icon:", out, os.path.getsize(out), "bytes")
    pygame.quit()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "build/icon.ico")
