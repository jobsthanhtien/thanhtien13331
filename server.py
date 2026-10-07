import os
import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import time

from database import init_db, query_deals, get_stats, get_setting, set_setting, get_brands_summary
from crawler import run_crawler
from notifier import send_telegram_alert

PORT = 8888
HOST = "127.0.0.1"

# Background Auto Crawler Worker
IS_CRAWLING = False
CRAWLER_INTERVAL_MINUTES = 15
LAST_CRAWL_TIME = None
LAST_CRAWL_COUNT = 0

# Flash Sale key slot hours on Lazada VN
FLASH_SALE_SLOTS = [0, 8, 12, 16, 20]
LAST_SLOT_TRIGGERED = None
LAST_CRAWL_TIMESTAMP = 0

def background_crawler_loop():
    global IS_CRAWLING, LAST_CRAWL_TIME, LAST_CRAWL_COUNT, LAST_SLOT_TRIGGERED, LAST_CRAWL_TIMESTAMP
    print("[Worker] 🚀 Khởi động tiến trình quét tự động thông minh (Định kỳ + Canh khung giờ Flash Sale)...")
    
    while True:
        try:
            auto_enabled = get_setting("auto_crawl_enabled", "true") == "true"
            interval_min = int(get_setting("crawl_interval_minutes", "15"))
            interval_sec = max(180, interval_min * 60) # Min 3 minutes
            
            now_struct = time.localtime()
            cur_h = now_struct.tm_hour
            cur_m = now_struct.tm_min
            now_ts = time.time()
            
            should_crawl = False
            trigger_reason = ""
            
            if auto_enabled:
                # 1. Trigger on Flash Sale Slot drop (within the first 2 minutes of the slot hour)
                if cur_h in FLASH_SALE_SLOTS and cur_m <= 1:
                    slot_key = f"{now_struct.tm_year}-{now_struct.tm_mon}-{now_struct.tm_mday}_{cur_h}"
                    if LAST_SLOT_TRIGGERED != slot_key:
                        should_crawl = True
                        trigger_reason = f"Đúng khung giờ vàng Flash Sale {cur_h}:00!"
                        LAST_SLOT_TRIGGERED = slot_key
                
                # 2. Trigger on periodic interval
                if not should_crawl and (now_ts - LAST_CRAWL_TIMESTAMP >= interval_sec):
                    should_crawl = True
                    trigger_reason = f"Định kỳ {interval_min} phút"
            
            if should_crawl and not IS_CRAWLING:
                IS_CRAWLING = True
                print(f"[Worker] ⚡ Bắt đầu quét tự động: {trigger_reason}")
                count = run_crawler()
                LAST_CRAWL_COUNT = count
                LAST_CRAWL_TIMESTAMP = time.time()
                LAST_CRAWL_TIME = time.strftime("%H:%M:%S %d/%m/%Y")
                print(f"[Worker] ✅ Quét xong! Đã đồng bộ {count} deal vào cơ sở dữ liệu.")
                IS_CRAWLING = False
                
        except Exception as e:
            print("[Worker Error]:", e)
            IS_CRAWLING = False
            
        time.sleep(15)  # Check condition every 15 seconds

class DealRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Silence console spam
        return

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)
        
        if path == "/" or path == "/index.html":
            self.serve_file("index.html", "text/html; charset=utf-8")
        elif path == "/style.css":
            self.serve_file("style.css", "text/css; charset=utf-8")
        elif path == "/app.js":
            self.serve_file("app.js", "application/javascript; charset=utf-8")
        elif path == "/api/deals":
            self.handle_api_deals(query)
        elif path == "/api/brands":
            self.send_json({"status": "success", "brands": get_brands_summary()})
        elif path == "/api/stats":
            self.handle_api_stats()
        elif path == "/api/settings":
            self.handle_api_get_settings()
        elif path == "/api/crawler/status":
            self.handle_crawler_status()
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else ""
        
        if path == "/api/crawl/now":
            self.handle_crawl_now()
        elif path == "/api/settings":
            self.handle_api_save_settings(post_data)
        elif path == "/api/notify/test":
            self.handle_test_telegram(post_data)
        else:
            self.send_error(404, "Not Found")

    def serve_file(self, filename, content_type):
        web_dir = os.environ.get("APP_WEB_DIR", os.path.dirname(os.path.abspath(__file__)))
        filepath = os.path.join(web_dir, filename)
        if os.path.exists(filepath):
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.end_headers()
            with open(filepath, "rb") as f:
                self.wfile.write(f.read())
        else:
            self.send_error(404, f"File {filename} not found")

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def handle_api_deals(self, query):
        min_p = float(query["min_price"][0]) if "min_price" in query and query["min_price"][0] else None
        max_p = float(query["max_price"][0]) if "max_price" in query and query["max_price"][0] else None
        min_disc = int(query["min_discount"][0]) if "min_discount" in query and query["min_discount"][0] else None
        cat = query["category"][0] if "category" in query and query["category"][0] else None
        brand = query["brand"][0] if "brand" in query and query["brand"][0] else None
        is_tmall = query.get("is_tmall", ["false"])[0].lower() in ["true", "1"]
        search = query["q"][0] if "q" in query and query["q"][0] else None
        limit = int(query["limit"][0]) if "limit" in query else 40
        offset = int(query["offset"][0]) if "offset" in query else 0
        sort = query["sort"][0] if "sort" in query else "discount_desc"
        
        deals, total = query_deals(
            min_price=min_p, max_price=max_p, min_discount=min_disc, category=cat, brand=brand,
            is_tmall=is_tmall, search=search, limit=limit, offset=offset, sort_by=sort
        )
        self.send_json({
            "status": "success",
            "total": total,
            "count": len(deals),
            "deals": deals
        })

    def handle_api_stats(self):
        stats = get_stats()
        self.send_json({
            "status": "success",
            "stats": stats
        })

    def handle_api_get_settings(self):
        settings = {
            "affiliate_id": get_setting("affiliate_id", "cheetah"),
            "telegram_bot_token": get_setting("telegram_bot_token", ""),
            "telegram_chat_id": get_setting("telegram_chat_id", ""),
            "auto_crawl_enabled": get_setting("auto_crawl_enabled", "true"),
            "crawl_interval_minutes": get_setting("crawl_interval_minutes", "15")
        }
        self.send_json({"status": "success", "settings": settings})

    def handle_api_save_settings(self, body):
        try:
            data = json.loads(body)
            for k, v in data.items():
                set_setting(k, str(v))
            self.send_json({"status": "success", "message": "Đã lưu cài đặt thành công!"})
        except Exception as e:
            self.send_json({"status": "error", "message": str(e)}, status=400)

    def handle_crawler_status(self):
        self.send_json({
            "is_crawling": IS_CRAWLING,
            "last_crawl_time": LAST_CRAWL_TIME,
            "last_crawl_count": LAST_CRAWL_COUNT
        })

    def handle_crawl_now(self):
        global IS_CRAWLING, LAST_CRAWL_TIME, LAST_CRAWL_COUNT
        if IS_CRAWLING:
            self.send_json({"status": "busy", "message": "Hệ thống đang quét, vui lòng đợi giây lát!"})
            return
            
        def do_crawl():
            global IS_CRAWLING, LAST_CRAWL_TIME, LAST_CRAWL_COUNT
            IS_CRAWLING = True
            try:
                count = run_crawler()
                LAST_CRAWL_COUNT = count
                LAST_CRAWL_TIME = time.strftime("%H:%M:%S %d/%m/%Y")
            finally:
                IS_CRAWLING = False

        t = threading.Thread(target=do_crawl, daemon=True)
        t.start()
        self.send_json({"status": "started", "message": "Đã kích hoạt quét Flash Sale ngầm!"})

    def handle_test_telegram(self, body):
        try:
            deals, total = query_deals(max_price=1000, limit=1)
            if not deals:
                deals, total = query_deals(limit=1)
            if not deals:
                self.send_json({"status": "error", "message": "Chưa có deal nào trong cơ sở dữ liệu để test!"})
                return
            ok, msg = send_telegram_alert(deals[0])
            if ok:
                self.send_json({"status": "success", "message": "Đã bắn thử thông báo tới Telegram thành công!"})
            else:
                self.send_json({"status": "error", "message": f"Telegram lỗi: {msg}"})
        except Exception as e:
            self.send_json({"status": "error", "message": str(e)})

def run_server():
    init_db()
    
    # Start background crawler thread
    crawler_thread = threading.Thread(target=background_crawler_loop, daemon=True)
    crawler_thread.start()
    
    server_address = (HOST, PORT)
    httpd = HTTPServer(server_address, DealRequestHandler)
    print(f"🔥 [DZUx LAZADA HUNTER PRO] Server đang hoạt động tại: http://{HOST}:{PORT}")
    print(f"📊 Dashboard quản trị & săn deal đã sẵn sàng!")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nĐang dừng máy chủ...")
        httpd.server_close()

def start_android_server(host=HOST, port=PORT):
    def target():
        init_db()
        crawler_thread = threading.Thread(target=background_crawler_loop, daemon=True)
        crawler_thread.start()
        server_address = (host, port)
        httpd = HTTPServer(server_address, DealRequestHandler)
        print(f"🔥 [DZUx LAZADA HUNTER PRO] Android Server running on http://{host}:{port}")
        httpd.serve_forever()
    t = threading.Thread(target=target, daemon=True)
    t.start()
    return t

if __name__ == "__main__":
    run_server()
