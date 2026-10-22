# ============================================================
#  NEON CLASH - server (asyncio + websockets)
#  Dung duoc ca trong app (thread rieng) va che do --server
# ============================================================
import asyncio
import json
import os
import random
import socket
import threading
import time
from urllib.parse import urlparse
from urllib.request import ProxyHandler, build_opener

from websockets.asyncio.server import serve

from .gamedata import DEFAULT_SETTINGS, MODES, GAME_NAME
from .version import VERSION, PROTOCOL
from .room import Room, make_map


def local_ips():
    """Danh sach IPv4 cua may, uu tien IP LAN de ban be de nhap."""
    out = set()
    try:
        for name in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ip = name[4][0]
            if ip and not ip.startswith("127."):
                out.add(ip)
    except Exception:
        pass
    # fallback: UDP trick (khong gui goi nao)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.2)
        s.connect(("8.8.8.8", 80))
        out.add(s.getsockname()[0])
        s.close()
    except Exception:
        pass

    def score(ip):
        if ip.startswith("192.168."):
            return 0
        if ip.startswith("10."):
            return 1
        if ip.startswith("172."):
            try:
                second = int(ip.split(".")[1])
                if 16 <= second <= 31:
                    return 2
            except Exception:
                pass
        if ip.startswith("100."):
            return 3
        if ip.startswith("26."):
            return 4
        return 5

    return sorted(out, key=lambda ip: (score(ip), ip))


def port_free(port, host="0.0.0.0"):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, int(port)))
        return True
    except OSError:
        return False
    finally:
        try:
            s.close()
        except Exception:
            pass


_opener = build_opener(ProxyHandler({}))


def probe_server(addr, timeout=2.5):
    """Kiem tra mot dia chi co phai server NEON CLASH khong."""
    addr = str(addr or "").strip()
    addr = addr.replace("http://", "").replace("https://", "").replace("ws://", "").replace("wss://", "")
    addr = addr.split("/")[0]
    if not addr:
        return None
    if ":" not in addr:
        addr = addr + ":3000"
    try:
        with _opener.open("http://" + addr + "/health", timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8"))
        if data.get("game") == GAME_NAME:
            data["addr"] = addr
            return data
    except Exception:
        return None
    return None


class Client:
    __slots__ = ("id", "ws", "name", "roomId", "queue", "task", "msgCount", "msgReset")

    def __init__(self, cid, ws):
        self.id = cid
        self.ws = ws
        self.name = "Người chơi %d" % cid
        self.roomId = None
        self.queue = asyncio.Queue(maxsize=512)
        self.task = None
        self.msgCount = 0
        self.msgReset = time.monotonic()


class GameServer:
    def __init__(self, port=3000, host="0.0.0.0", log=None, auto_port=True, max_tries=10):
        self.port = int(port or 3000)
        self.host = host
        self.log = log or (lambda *a: None)
        self.auto_port = auto_port
        self.max_tries = max_tries

        self.clients = {}
        self.rooms = {}
        self.nextId = 1
        self.loop = None
        self.actual_port = 0
        self._server = None
        self._ticker = None
        self._thread = None
        self._stopping = False
        self.preview_map = make_map(20261021)

    # ---------------- vong doi ----------------
    async def start(self):
        self.loop = asyncio.get_running_loop()
        port = self.port
        tries = 0
        while True:
            try:
                self._server = await serve(
                    self._handler, self.host, port,
                    process_request=self._process_request,
                    max_size=512 * 1024, ping_interval=20, ping_timeout=25,
                )
                self.actual_port = port
                break
            except OSError:
                if not self.auto_port or tries >= self.max_tries:
                    raise
                tries += 1
                self.log("Cổng %d đang bận → thử cổng %d..." % (port, port + 1))
                port += 1
        self._ticker = asyncio.create_task(self._tick())
        return self.actual_port

    async def stop(self):
        self._stopping = True
        if self._ticker:
            self._ticker.cancel()
            self._ticker = None
        for c in list(self.clients.values()):
            if c.task:
                c.task.cancel()
            try:
                await c.ws.close()
            except Exception:
                pass
        self.clients.clear()
        self.rooms.clear()
        if self._server:
            self._server.close()
            try:
                await self._server.wait_closed()
            except Exception:
                pass
            self._server = None

    def start_thread(self, timeout=10.0):
        """Chay server trong thread rieng (dung cho app). Tra ve (ok, port|error)."""
        ready = threading.Event()
        box = {}

        def run():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self.loop = loop
            try:
                box["port"] = loop.run_until_complete(self.start())
            except Exception as e:
                box["error"] = str(e)
                ready.set()
                loop.close()
                return
            ready.set()
            try:
                loop.run_forever()
            finally:
                try:
                    loop.close()
                except Exception:
                    pass

        t = threading.Thread(target=run, daemon=True, name="neon-server")
        self._thread = t
        t.start()
        ready.wait(timeout)
        if "port" in box:
            return True, box["port"]
        return False, box.get("error", "không khởi động được server")

    def stop_thread(self):
        if self.loop and self._server:
            try:
                asyncio.run_coroutine_threadsafe(self.stop(), self.loop)
            except Exception:
                pass

    # ---------------- HTTP nho ----------------
    async def _process_request(self, connection, request):
        path = urlparse(request.path).path
        if path == "/health":
            body = json.dumps({
                "ok": True, "game": GAME_NAME,
                "version": VERSION, "protocol": PROTOCOL,
                "rooms": len(self.rooms), "players": len(self.clients),
                "port": self.actual_port or self.port,
            })
            try:
                return connection.respond(200, body)
            except Exception:
                return None
        return None

    # ---------------- gui tin ----------------
    def send(self, cid, obj):
        c = self.clients.get(cid)
        if not c:
            return
        try:
            c.queue.put_nowait(json.dumps(obj, separators=(",", ":")))
        except asyncio.QueueFull:
            pass

    async def _writer(self, c):
        try:
            while True:
                msg = await c.queue.get()
                await c.ws.send(msg)
        except asyncio.CancelledError:
            pass
        except Exception:
            pass

    # ---------------- ket noi ----------------
    async def _handler(self, ws):
        cid = self.nextId
        self.nextId += 1
        c = Client(cid, ws)
        self.clients[cid] = c
        c.task = asyncio.create_task(self._writer(c))

        self.send(cid, {
            "t": "welcome", "id": cid, "rooms": self.room_list(),
            "game": GAME_NAME, "version": VERSION, "protocol": PROTOCOL,
            "map": self.preview_map, "ips": local_ips(),
        })
        self.broadcast_room_list()

        try:
            async for raw in ws:
                now = time.monotonic()
                if now - c.msgReset > 1.0:
                    c.msgReset = now
                    c.msgCount = 0
                c.msgCount += 1
                if c.msgCount > 240:
                    continue
                try:
                    m = json.loads(raw)
                except Exception:
                    continue
                if not isinstance(m, dict) or not isinstance(m.get("t"), str):
                    continue
                try:
                    self.handle(c, m)
                except Exception as e:
                    self.log("Lỗi xử lý %s: %s" % (m.get("t"), e))
        except Exception:
            pass
        finally:
            room = self.rooms.get(c.roomId) if c.roomId else None
            if room:
                room.remove_player(cid)
            self.clients.pop(cid, None)
            if c.task:
                c.task.cancel()
            self.broadcast_room_list()

    # ---------------- phong ----------------
    def gen_code(self):
        chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
        while True:
            code = "".join(random.choice(chars) for _ in range(4))
            if code not in self.rooms:
                return code

    def room_list(self):
        out = []
        for r in self.rooms.values():
            mode = next((m for m in MODES if m["id"] == r.settings["mode"]), MODES[0])
            out.append({
                "id": r.id, "name": r.settings["name"], "players": len(r.players),
                "max": r.settings["maxPlayers"], "mode": r.settings["mode"],
                "modeName": mode["name"], "hasPass": bool(r.settings["password"]),
                "state": r.state,
            })
        return out

    def broadcast_room_list(self):
        payload = {"t": "rooms", "rooms": self.room_list()}
        for c in self.clients.values():
            if not c.roomId:
                self.send(c.id, payload)

    def _schedule(self, delay, fn):
        try:
            return self.loop.call_later(delay, fn)
        except Exception:
            return None

    def _cancel(self, handle):
        try:
            handle.cancel()
        except Exception:
            pass

    def join_room(self, c, room, password=""):
        if not room.add_player(c.id, c.name):
            self.send(c.id, {"t": "err", "msg": "Không vào được phòng."})
            return
        c.roomId = room.id
        self.send(c.id, {"t": "joined", "id": room.id})
        room.broadcast_lobby()
        room.send_map_preview(c.id)

    # ---------------- xu ly tin ----------------
    def handle(self, c, m):
        t = m["t"]

        if t == "ping":
            self.send(c.id, {"t": "pong", "ts": m.get("ts")})
            return
        if t == "list":
            self.send(c.id, {"t": "rooms", "rooms": self.room_list()})
            return
        if t == "hello":
            n = str(m.get("name") or "").strip()[:16]
            if n:
                c.name = n
            self.send(c.id, {"t": "hello", "name": c.name})
            return
        if t == "create":
            if c.roomId:
                return
            s = dict(DEFAULT_SETTINGS)
            s.update(m.get("settings") or {})

            def nint(v, default, lo, hi):
                try:
                    n = float(v)
                except (TypeError, ValueError):
                    return default
                if n != n:
                    return default
                return int(max(lo, min(hi, int(n))))

            s["name"] = (str(s.get("name") or "Phòng").strip()[:28]) or "Phòng"
            s["password"] = str(s.get("password") or "")[:16]
            s["maxPlayers"] = nint(s.get("maxPlayers"), 16, 2, 64)
            s["killTarget"] = nint(s.get("killTarget"), 20, 1, 999)
            s["timeLimit"] = nint(s.get("timeLimit"), 300, 30, 3600)
            s["respawn"] = nint(s.get("respawn"), 3, 0, 30)
            s["startHp"] = nint(s.get("startHp"), 100, 50, 500)
            if s.get("mode") not in ("kills", "time", "last"):
                s["mode"] = "kills"

            code = self.gen_code()
            room = Room(
                code, s, c.id,
                send=lambda pid, obj: self.send(pid, obj),
                on_empty=lambda: (self.rooms.pop(code, None), self.broadcast_room_list()),
                on_room_list=self.broadcast_room_list,
                schedule=self._schedule, cancel=self._cancel,
            )
            self.rooms[code] = room
            self.join_room(c, room)
            self.broadcast_room_list()
            return
        if t == "join":
            if c.roomId:
                return
            room = self.rooms.get(str(m.get("id") or "").upper())
            if not room:
                self.send(c.id, {"t": "err", "msg": "Không tìm thấy phòng."})
                return
            if room.settings["password"] and str(m.get("password") or "") != room.settings["password"]:
                self.send(c.id, {"t": "err", "msg": "Sai mật khẩu phòng."})
                return
            if len(room.players) >= room.settings["maxPlayers"]:
                self.send(c.id, {"t": "err", "msg": "Phòng đã đầy."})
                return
            if room.state != "lobby":
                self.send(c.id, {"t": "err", "msg": "Trận đang diễn ra, thử lại sau."})
                return
            self.join_room(c, room, m.get("password") or "")
            self.broadcast_room_list()
            return
        if t == "leave":
            if not c.roomId:
                return
            room = self.rooms.get(c.roomId)
            c.roomId = None
            if room:
                room.remove_player(c.id)
            self.send(c.id, {"t": "left"})
            self.send(c.id, {"t": "rooms", "rooms": self.room_list()})
            self.broadcast_room_list()
            return
        if t == "loadout":
            room = self.rooms.get(c.roomId)
            if room:
                room.set_loadout(c.id, m.get("loadout"))
            return
        if t == "ready":
            room = self.rooms.get(c.roomId)
            if room:
                room.set_ready(c.id, bool(m.get("ready")))
            return
        if t == "start":
            room = self.rooms.get(c.roomId)
            if room and room.hostId == c.id:
                room.start()
            return
        if t == "input":
            room = self.rooms.get(c.roomId)
            if room:
                room.handle_input(c.id, m)
            return
        if t == "cast":
            room = self.rooms.get(c.roomId)
            if room:
                room.handle_cast(c.id, m)
            return
        if t == "spec":
            room = self.rooms.get(c.roomId)
            if room:
                room.handle_spec(c.id, m.get("id"))
            return
        if t == "chat":
            room = self.rooms.get(c.roomId)
            if not room:
                return
            text = str(m.get("text") or "")[:140].strip()
            if text:
                room.chat(c.id, text)
            return
        if t == "admin":
            room = self.rooms.get(c.roomId)
            if room and room.hostId == c.id:
                room.admin(c.id, m)
            return

    # ---------------- tick ----------------
    async def _tick(self):
        last = time.monotonic()
        while True:
            await asyncio.sleep(1.0 / 30.0)
            now = time.monotonic()
            dt = now - last
            last = now
            if dt > 0.25:
                dt = 0.25
            for room in list(self.rooms.values()):
                if room.state != "playing":
                    continue
                try:
                    room.step(dt)
                except Exception as e:
                    self.log("Lỗi room %s: %s" % (room.id, e))
