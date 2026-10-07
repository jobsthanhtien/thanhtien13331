# ⚡ DZUx LAZADA HUNTER PRO

Hệ thống săn Flash Sale & lọc Deal trợ giá sốc (1K, 9K, >50%) tự động từ Lazada dành riêng cho DZUx.

## 🚀 Các Tính Năng Chính
1. **Quét siêu tốc 0 Captcha**: Trích xuất dữ liệu trực tiếp từ các kênh SSR và feed tính giá tập trung của Lazada mà không bị chặn WAF/Baxia.
2. **Bộ tính giá Subsidies**: Tự động bóc tách các tầng trợ giá (`priceCompare`), voucher toàn sàn, voucher shop để ra mức giá săn cuối cùng (`displayPrice`, `voucherPrice`).
3. **Database SQLite cục bộ**: Lưu trữ độc lập, tốc độ truy vấn mili-giây, phục vụ hàng nghìn lượt lọc cùng lúc mà không cần spam Lazada.
4. **Dashboard Quản Trị Hiện Đại**: Giao diện Glassmorphism với Dark Mode siêu mượt, lọc deal 1K, 9K, sắp xếp theo % giảm sâu, sao chép link 1-click.
5. **Bộ Gắn Link Tiếp Thị (Affiliate Auto-wrapper)**: Tự động chuyển đổi link gốc sang link tiếp thị liên kết theo `sub_aff_id` của anh để kiếm hoa hồng.
6. **Telegram Auto-Alert**: Tự động bắn thông báo kèo thơm vào Channel / Group Telegram.

## 🛠️ Cấu Trúc Mã Nguồn
- [database.py](file:///d:/THANH%20TIEN/CODE/laza/database.py): Khởi tạo cơ sở dữ liệu SQLite, lưu trữ và đánh index tìm kiếm deal.
- [crawler.py](file:///d:/THANH%20TIEN/CODE/laza/crawler.py): Engine cào ngầm đa nguồn (Lazada SSR + Feed trợ giá Flash Sale).
- [notifier.py](file:///d:/THANH%20TIEN/CODE/laza/notifier.py): Module bắn thông báo deal sốc qua Telegram Bot API.
- [server.py](file:///d:/THANH%20TIEN/CODE/laza/server.py): Máy chủ HTTP REST API và Worker tự động quét định kỳ.
- [index.html](file:///d:/THANH%20TIEN/CODE/laza/index.html): Giao diện web Dashboard.
- [style.css](file:///d:/THANH%20TIEN/CODE/laza/style.css): Hệ thống phong cách Glassmorphism & Micro-animations.
- [app.js](file:///d:/THANH%20TIEN/CODE/laza/app.js): Logic lọc động, tìm kiếm, kết nối API và cài đặt.

## 🌐 Cách Sử Dụng
Máy chủ đang chạy ngầm tại: **http://127.0.0.1:8888**

Anh chỉ cần mở trình duyệt và truy cập:
👉 **[http://127.0.0.1:8888](http://127.0.0.1:8888)**

---

## 📱 Dành Cho Android (Standalone All-in-One APK)
Hệ thống đã được thiết kế sẵn toàn bộ kiến trúc Standalone APK chạy nhúng Python ngầm bên trong:
- **Thư mục dự án Android**: [android/](file:///d:/THANH%20TIEN/CODE/laza/android/)
- **Đồng bộ mã nguồn**: Chạy `py sync_to_android.py` mỗi khi chỉnh sửa code backend hoặc web.
- **Tự động build APK trên đám mây (Miễn phí qua GitHub Actions)**: Xem file [.github/workflows/build-apk.yml](file:///d:/THANH%20TIEN/CODE/laza/.github/workflows/build-apk.yml). Khi đẩy code lên GitHub, mục **Actions** sẽ tự động build và xuất file `app-debug.apk` để tải về cài đặt ngay.
- **Build bằng Android Studio**: Mở thư mục `android/` trong Android Studio và chọn **Build > Build Bundle(s) / APK(s) > Build APK(s)**.

