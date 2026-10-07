import os
import shutil
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
ANDROID_PYTHON_DIR = os.path.join(ROOT_DIR, "android", "app", "src", "main", "python")

FILES_TO_SYNC = [
    "server.py",
    "crawler.py",
    "database.py",
    "notifier.py",
    "index.html",
    "style.css",
    "app.js"
]

def sync():
    os.makedirs(ANDROID_PYTHON_DIR, exist_ok=True)
    print(f"🔄 Đồng bộ mã nguồn vào Android Chaquopy folder: {ANDROID_PYTHON_DIR}")
    for fname in FILES_TO_SYNC:
        src = os.path.join(ROOT_DIR, fname)
        dst = os.path.join(ANDROID_PYTHON_DIR, fname)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"  [+] Đã copy: {fname} -> android/app/src/main/python/{fname}")
        else:
            print(f"  [-] Cảnh báo: Không tìm thấy {fname}")
    print("✅ Hoàn tất đồng bộ mã nguồn cho Android Standalone App!")

if __name__ == "__main__":
    sync()
