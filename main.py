"""NEON CLASH - diem khoi dong.

  python main.py                 mo game (cua so pygame)
  python main.py --port 3000     mo game + tu mo server
  python main.py --join 1.2.3.4:3000
  python main.py --server        chi chay server (cho VPS, khong giao dien)
"""
import argparse
import asyncio
import os
import sys

# stdout co the la cp1252 khi chay tu exe (khong co console) -> loi encode tieng Viet
for _s in (sys.stdout, sys.stderr):
    try:
        if _s is not None:
            _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Khi chay tu exe: uu tien code da tai ve tu GitHub (neu co) va kiem tra
# ban moi trong background. Dev chay bang python main.py thi bo qua.
if getattr(sys, "frozen", False):
    try:
        import updater
        updater.prepare()
        updater.check_async()
    except Exception:
        pass


def run_server_mode(port, host):
    from game.server import GameServer, local_ips

    async def _main():
        srv = GameServer(port=port, host=host, log=print)
        try:
            p = await srv.start()
        except Exception as e:
            print("Không mở được server:", e)
            return
        ips = local_ips()
        print("")
        print("  ==============================================")
        print("             NEON CLASH  -  SERVER")
        print("  ==============================================")
        print("  Cổng:        %d" % p)
        print("  Cục bộ:      localhost:%d" % p)
        for ip in ips:
            print("  Trong mạng:  %s:%d" % (ip, p))
        print("")
        print("  Bạn bè mở game → Vào phòng → nhập địa chỉ ở trên.")
        print("  Ctrl+C để dừng.")
        print("")
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            pass
        finally:
            await srv.stop()

    try:
        asyncio.run(_main())
    except KeyboardInterrupt:
        print("\nĐã dừng server.")


def main():
    ap = argparse.ArgumentParser(prog="NeonClash", description="NEON CLASH")
    ap.add_argument("--profile", default="main", help="ten profile (mo nhieu client)")
    ap.add_argument("--port", type=int, default=0, help="tu mo server o cong nay")
    ap.add_argument("--join", default="", help="vao thang server IP:cong")
    ap.add_argument("--server", action="store_true", help="chi chay server")
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--headless", action="store_true", help="chay khong can man hinh (test)")
    ap.add_argument("--size", default="1280x800")
    args = ap.parse_args()

    if args.headless:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ["SDL_AUDIODRIVER"] = "dummy"
        os.environ["NC_HEADLESS"] = "1"

    if args.server:
        run_server_mode(args.port or 3000, args.host)
        return

    try:
        w, h = [int(v) for v in args.size.lower().split("x")]
    except Exception:
        w, h = 1280, 800

    from game.client.app import App

    app = App(args.profile, w, h)
    if args.port:
        ok, res = app.host_server(args.port)
        if ok:
            app.connect_to("localhost:%d" % res)
            app.pending_create = {"name": "Phòng test"}
        else:
            app.toast("Không mở được server: %s" % res)
    elif args.join:
        app.connect_to(args.join)
    app.run()


def _fatal(msg):
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, msg, "NEON CLASH - Lỗi", 0x10)
    except Exception:
        try:
            print(msg)
        except Exception:
            pass


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        import traceback
        tb = traceback.format_exc()
        try:
            base = os.path.dirname(os.path.abspath(sys.executable)) if getattr(sys, "frozen", False) \
                else os.path.dirname(os.path.abspath(__file__))
            with open(os.path.join(base, "neonclash-error.log"), "w", encoding="utf-8") as f:
                f.write(tb)
        except Exception:
            pass
        _fatal("Không khởi động được game.\n\n" + tb[-900:])
