"""Ket noi WebSocket toi server (chay thread rieng, main loop poll message)."""
import json
import threading
import time
from collections import deque

import websocket


class Net:
    def __init__(self):
        self.host = ""
        self.connected = False
        self.msgq = deque()
        self.lock = threading.Lock()
        self.ws = None
        self.thread = None
        self.manual = False
        self.retry = 0
        self.last_error = ""
        self.was_in_game = False
        self.on_open = None

    # ---------------- ket noi ----------------
    def connect(self, addr):
        addr = str(addr or "").strip()
        addr = addr.replace("http://", "").replace("https://", "").replace("ws://", "").replace("wss://", "")
        addr = addr.split("/")[0]
        if not addr:
            return
        if ":" not in addr:
            addr += ":3000"
        self.close()
        self.host = addr
        self.manual = False
        self.retry = 0
        self._spawn()

    def _spawn(self):
        url = "ws://" + self.host

        def run():
            self.ws = websocket.WebSocketApp(
                url,
                on_open=self._on_open,
                on_message=self._on_message,
                on_close=self._on_close,
                on_error=self._on_error,
            )
            try:
                self.ws.run_forever(ping_interval=20, ping_timeout=12, skip_utf8_validation=True)
            except Exception as e:
                self.last_error = str(e)
            self.connected = False
            if not self.manual:
                self.retry += 1
                delay = min(4.0, 0.6 + self.retry * 0.4)
                t = threading.Timer(delay, self._reconnect)
                t.daemon = True
                t.start()

        self.thread = threading.Thread(target=run, daemon=True, name="neon-net")
        self.thread.start()

    def _reconnect(self):
        if self.manual:
            return
        try:
            self._spawn()
        except Exception:
            pass

    def _on_open(self, ws):
        self.connected = True
        self.retry = 0
        if self.on_open:
            try:
                self.on_open()
            except Exception:
                pass

    def _on_message(self, ws, raw):
        try:
            m = json.loads(raw)
        except Exception:
            return
        if not isinstance(m, dict):
            return
        with self.lock:
            self.msgq.append(m)
            while len(self.msgq) > 800:
                self.msgq.popleft()

    def _on_close(self, ws, code=None, msg=None):
        self.connected = False

    def _on_error(self, ws, err):
        self.last_error = str(err)

    # ---------------- gui / nhan ----------------
    def send(self, obj):
        ws = self.ws
        if not ws or not self.connected:
            return False
        try:
            ws.send(json.dumps(obj, separators=(",", ":")))
            return True
        except Exception:
            return False

    def poll(self):
        with self.lock:
            out = list(self.msgq)
            self.msgq.clear()
        return out

    def close(self):
        self.manual = True
        self.connected = False
        ws = self.ws
        if ws:
            try:
                ws.close()
            except Exception:
                pass
        self.ws = None
        with self.lock:
            self.msgq.clear()
