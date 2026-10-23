"""Thong tin phien ban game — tools/release.py se cap nhat VERSION tu dong."""

VERSION = "1.6.0"   # phien ban hien thi (X.Y.Z) — patch = fix bug nho
PROTOCOL = 2        # tang len khi thay format tin hieu truc tiep (khong tuong thich nguoc)
GAME = "NEON CLASH"


def display():
    """Ma phien ban ngan gon cho nguoi choi: 1.4.2 -> V1.4, 2.3.0 -> V2.3."""
    parts = VERSION.split(".")
    return "V%s.%s" % (parts[0], parts[1]) if len(parts) >= 2 else "V" + VERSION
