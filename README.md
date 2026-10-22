# NEON CLASH

Game bắn nhau **2D góc nhìn từ trên xuống**, nhiều người chơi tự do (FFA), chơi qua **IP** như Minecraft.

Đây là **ứng dụng game thật**: cửa sổ riêng, icon riêng, không trình duyệt, không Node, không Java.
Viết bằng **Python + pygame** (engine game 2D), server nhúng ngay trong app.

| | |
|---|---|
| File chạy | `dist/NeonClash.exe` — **một file duy nhất, ~16 MB** |
| Cần cài gì | **không cần gì** (Windows 10/11) |
| Người chơi khác | cũng chỉ cần file đó, hoặc vào bằng IP |
| Đồ hoạ | neon tối, glow, hạt, tia laser, minimap, camera rung |

---

## 1. Chơi ngay

Nhấp đúp **`dist/NeonClash.exe`** → menu chính:

```
        NEON CLASH
   ĐẤU TRƯỜNG 2D · FFA · CHƠI QUA IP

 ┌ ◆ TẠO PHÒNG ─────────────┐   ┌ ▸ VÀO PHÒNG ────────────┐
 │ Cổng [3000]  Tên phòng    │   │ Địa chỉ [26.1.2.3:3000] │
 │ [        Bắt đầu       ]  │   │ [      Kết nối        ] │
 │ Bạn bè nhập: 192.168…:3000│   │                         │
 └───────────────────────────┘   └─────────────────────────┘
```

- **Tạo phòng**: chọn cổng → app mở server ngay trong máy rồi vào game.
- **Tùy chọn**: đặt trước tên phòng, **mật khẩu**, số người tối đa, máu đầu trận, chế độ thắng,
  mục tiêu mạng / thời gian, thời gian hồi sinh. Các giá trị này được nhớ cho lần sau.
- **Vào phòng**: nhập `IP:cổng` của người tạo phòng (kiểm tra server trước khi vào).

Vào game sẽ thấy **HUB**: hồ sơ, bộ **kit**, cài đặt, và các nút vào trận.

## 2. Bạn bè vào phòng

Người tạo phòng mở **Tạo phòng**, trong phòng chờ có ô **“Bạn bè vào bằng …”** kèm nút **Copy IP**.
Người khác mở game → **Vào phòng** → dán IP đó.

| Cách chơi | Địa chỉ |
|---|---|
| Cùng máy | `localhost:3000` |
| Cùng WiFi / LAN | `192.168.x.x:3000` |
| **Radmin VPN** | `26.x.x.x:3000` |
| Hamachi / ZeroTier / Tailscale | IP ảo của phần mềm đó |
| Internet | Mở port **3000 TCP** ở router → `IP-công-khai:3000` |

> Không vào được? Kiểm tra **Windows Firewall** đang cho phép `NeonClash.exe` (lần đầu chạy Windows sẽ hỏi).

## 3. Test nhiều client trên 1 máy

Mỗi lần mở `NeonClash.exe` là một client. App tự chọn profile trống
(`main`, `main2`, `main3`…) nên mỗi client có kit / tên / cài đặt riêng.

1. Mở lần 1 → **Tạo phòng** (cổng 3000).
2. Mở lần 2 → **Vào phòng** → `localhost:3000`.
3. Mở tiếp lần 3, 4… (tối đa 8 profile).

Đặt tên profile cụ thể: `NeonClash.exe --profile test3`
Mở thẳng vào server, bỏ qua menu: `NeonClash.exe --join localhost:3000`
Tự mở server rồi vào luôn: `NeonClash.exe --port 3000`

## 4. Điều khiển

| Phím | Việc |
|---|---|
| `WASD` / phím mũi tên | Di chuyển |
| Chuột | Ngắm |
| Giữ chuột trái | Đánh thường (theo vũ khí) |
| `1` – `5` | Dùng 5 chiêu đã chọn |
| `Q` / `E` | Đổi người đang xem (khi đã bị hạ) |
| `Enter` | Chat trong trận |
| `ESC` | Menu tạm dừng (Tiếp tục · Cài đặt · Rời trận) |
| `F11` | Toàn màn hình |
| `F3` | Hiện / ẩn FPS |

## 5. HUB — hồ sơ, kit, cài đặt

- **Hồ sơ**: avatar nhân vật, tên, nội tại, 6 chỉ số nhanh của kit đang dùng.
- **Kit của bạn**: mỗi thẻ kit hiển thị nhân vật, vũ khí, 5 icon chiêu, trang bị và chỉ số.
  Bấm thẻ để **đổi kit ngay**; nút **Chỉnh sửa** mở bảng kit.
  Mỗi kit = *nhân vật + 5 trang bị + 5 chiêu + 10 điểm chỉ số*. Tối đa 12 kit, lưu vào profile trên máy.
- **Cài đặt**: âm lượng, hiệu ứng hạt, ánh sáng/glow, rung màn hình, hiện FPS, đặt lại kit.
  Tắt hạt/glow là nhẹ máy đáng kể.

Có sẵn 3 kit mẫu: **Xạ Thủ**, **Cận Chiến**, **Hỗn Hợp**.

## 6. 35 chiêu — trộn cận chiến và tầm xa tuỳ thích

Mỗi chiêu có nhãn tầm: **Cận chiến / Tầm trung / Tầm xa / Tiện ích**, lọc được trong bảng chọn.

- **Cận chiến**: Liên Hoàn Trảm, Xoay Kiếm, Thăng Long Kích, Kết Liễu, Xung Phong, Xung Kích.
- **Tầm xa**: Bắn Tỉa (1100 tầm), Sét Dây Chuyền, Trụ Súng, Hoán Đổi, Mưa Thiên Thạch, Tia Laser, Đạn Xuyên Phá.
- **Tầm trung**: Mưa Đạn, Tên Truy Kích, Đạn Nảy, Lựu Đạn, Móc Xích, Cầu Lửa, Dao Bay, Bão Đạn…
- **Tiện ích**: Lướt, Dịch Chuyển, Nhảy Vọt, Tăng Tốc, Khiên, Hồi Máu, Bất Tử, Giáp Sắt, Tường Chắn, Bom Khói.

Chọn 5 chiêu bất kỳ: 5 cận, 5 xa, hay 2 cận + 3 xa đều được.

## 7. Luật chơi

- FFA: mọi người đánh nhau tự do.
- Chủ phòng chọn: **Đạt X mạng** / **Tính giờ** / **Sống sót cuối**, kèm máu đầu trận, thời gian hồi sinh.
- Núp trong **bụi cỏ** thì người ở xa không thấy bạn.
- Bị hạ → chuyển sang **khách xem** (camera bám người còn sống, `Q/E` đổi người xem); trận vẫn tiếp tục.
- Chủ phòng bị hạ **không** làm mất phòng; chỉ khi không còn ai thì phòng mới đóng.

## 8. Chạy từ mã nguồn

```bash
python -m venv .venv
.venv/Scripts/pip install pygame websocket-client websockets pyinstaller

python main.py                 # mở game
python main.py --port 3000     # mở game + tự mở server
python main.py --join 1.2.3.4:3000
python main.py --server --port 3000   # chỉ chạy server (VPS, không cần màn hình)
```

Đóng gói lại:

```bash
python tools/build.py          # → dist/NeonClash.exe (~16 MB)
```

## 8.1. Tự động cập nhật (auto-update)

Người chơi chỉ cài exe **một lần**. Từ lần sau, khi bạn phát hành bản mới,
game sẽ **tự tải bản cập nhật (~100 KB)** từ GitHub về
`%APPDATA%/NeonClash/app` và dùng bản mới ở lần mở kế tiếp — không cần ai
tải lại exe. Nếu offline, game vẫn chạy bình thường với bản hiện có.

Phát hành bản mới (khi bạn có `GITHUB_TOKEN`):

```bash
set GITHUB_TOKEN=ghp_xxx
python tools/release.py 1.4.3 --push
```

Hoặc không cần token: chạy `python tools/release.py 1.4.3` rồi nhờ
WorkBuddy (đã nối GitHub) đẩy 2 file `release/version.json` +
`release/game.zip.b64` lên repo.

Server nhúng trong exe trả thêm `version`/`protocol` ở `/health` và tin
`welcome` — khi 2 máy khác phiên bản, game sẽ cảnh báo ngay khi vào Hub.

## 9. Cấu trúc

```
g1/
├─ main.py                 điểm khởi động (game / --server)
├─ updater.py              tự tải bản cập nhật từ GitHub vào %APPDATA%/NeonClash/app
├─ game/
│  ├─ version.py           số phiên bản + protocol (phát hành bằng tools/release.py)
│  ├─ gamedata.py          chỉ số, nhân vật, trang bị, 35 chiêu, compute_build()
│  ├─ room.py              gameplay server: tick 30Hz, va chạm, chiêu, hồi sinh, thắng thua
│  ├─ server.py            asyncio + websockets, /health, quản lý phòng
│  └─ client/
│     ├─ app.py            cửa sổ, vòng lặp, điều hướng, host/join
│     ├─ theme.py          màu, font (tự fallback icon), glow, gradient
│     ├─ ui.py             nút, ô nhập, slider, toggle, tab, scroll
│     ├─ screens.py        launcher, hub, kit editor, lobby, modal
│     ├─ play.py           vào trận: dự đoán vị trí, HUD, spectator, pause
│     ├─ render.py         vẽ map, tường, bụi cỏ, nhân vật, đạn, hiệu ứng, minimap
│     ├─ net.py            WebSocket client
│     ├─ audio.py          âm thanh sinh bằng code (không cần file)
│     └─ profile.py        lưu kit / cài đặt / cấu hình cổng
├─ tools/
│  ├─ build.py             đóng gói PyInstaller
│  └─ make_icon.py         sinh icon .ico
└─ dist/NeonClash.exe      bản chạy
```

Dữ liệu người chơi nằm cạnh file exe: `data/profiles/<tên>/profile.json`.

## 10. Xử lý sự cố

| Hiện tượng | Cách xử lý |
|---|---|
| Cổng đang bận | App tự thử cổng kế tiếp và báo cổng đang dùng; hoặc đổi cổng ở menu |
| Bạn bè không vào được | Kiểm tra Firewall, đúng IP, cùng mạng LAN/Radmin chưa |
| Vào game giật | Cài đặt → tắt **Hiệu ứng hạt** và **Ánh sáng/glow**, bật **Hiện FPS** |
| Mất kết nối giữa trận | App tự về Hub và báo lỗi — vào lại phòng là được |
| Muốn xoá hết kit | Xoá thư mục `data/` cạnh file exe |
| Không thấy cửa sổ game | Chạy `NeonClash.exe` từ Command Prompt để xem lỗi |
