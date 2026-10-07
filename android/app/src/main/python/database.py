import sqlite3
import os
import json
import sys
from datetime import datetime

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

DATA_DIR = os.environ.get("APP_DATA_DIR", os.path.dirname(os.path.abspath(__file__)))
DB_FILE = os.path.join(DATA_DIR, "laza_deals.db")

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS deals (
            id TEXT PRIMARY KEY,
            title TEXT,
            sku_id TEXT,
            category TEXT,
            brand TEXT,
            original_price REAL,
            flash_price REAL,
            voucher_price REAL,
            display_price REAL,
            discount_percent TEXT,
            sold_count INTEGER,
            stock_count INTEGER,
            image_url TEXT,
            product_url TEXT,
            affiliate_url TEXT,
            source TEXT,
            scm TEXT,
            raw_data TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Try adding brand column if table already exists
    try:
        c.execute("ALTER TABLE deals ADD COLUMN brand TEXT")
    except Exception:
        pass

    c.execute("CREATE INDEX IF NOT EXISTS idx_display_price ON deals(display_price)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_voucher_price ON deals(voucher_price)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_category ON deals(category)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_brand ON deals(brand)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_updated_at ON deals(updated_at)")

    c.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def detect_brand(title):
    title_lower = (title or "").lower()
    brand_map = {
        "Lock&Lock": ["lock&lock", "lock & lock", "lock and lock", "locknlock"],
        "Sữa Vinamilk": ["vinamilk", "ông thọ", "ngôi sao phương nam"],
        "Anker": ["anker", "soundcore"],
        "Maxkleen": ["maxkleen"],
        "Masan Consumer": ["masan", "chin-su", "nam ngư", "omachi", "kokomi"],
        "TH TrueMilk": ["th true", "th truemilk", "th true milk"],
        "Adidas": ["adidas"],
        "Bỉm Huggies": ["huggies"],
        "Anessa": ["anessa"],
        "Coca Cola": ["coca-cola", "coca cola", "fanta", "sprite"],
        "Bia Heineken": ["heineken", "tiger", "bia saigon", "strongbow"],
        "Pepsi & Suntory": ["pepsi", "suntory", "sting", "7up", "mirinda", "aquafina", "tea+"],
        "Cafe Trung Nguyên": ["trung nguyên", "trung nguyen", "g7"],
        "Sữa Ensure": ["ensure", "abbott", "pediasure", "similac"],
        "P&G": ["p&g", "ariel", "downy", "tide", "pantene", "head & shoulders", "gillette", "oral-b"],
        "Unilever": ["unilever", "omo", "comfort", "sunlight", "clear", "dove", "lifebuoy", "knorr"],
        "Apple": ["apple", "iphone", "ipad", "airpods", "macbook"],
        "Samsung": ["samsung", "galaxy"],
        "Xiaomi": ["xiaomi", "redmi", "poco"],
        "Tefal": ["tefal"],
        "Sunhouse": ["sunhouse"],
        "Elmich": ["elmich"],
        "Philips": ["philips"],
        "Bluestone": ["bluestone"],
        "Kangaroo": ["kangaroo"],
        "Bỉm Bobby": ["bobby"],
        "Bỉm Merries": ["merries"],
        "Bỉm Moony": ["moony"],
        "Durex": ["durex"],
        "Maybelline": ["maybelline"],
        "Bioderma": ["bioderma"],
    }
    for brand_name, keywords in brand_map.items():
        if any(kw in title_lower for kw in keywords):
            return brand_name
    return ""

def detect_category(title, brand=""):
    t = f"{brand} {title}".lower()
    
    # 1. Điện tử / Công nghệ
    tech_kw = [
        "điện thoại", "tai nghe", "bàn phím", "chuột", "laptop", "loa ", "loa bluetooth", 
        "sạc", "cáp sạc", "pin dự phòng", "camera", "máy ảnh", "tivi", "smartwatch", 
        "đồng hồ thông minh", "màn hình", "pc ", "ổ cứng", "soundcore", "anker", "apple", 
        "iphone", "ipad", "airpods", "macbook", "samsung", "galaxy", "xiaomi", "redmi", 
        "poco", "baseus", "ugreen", "hoco", "remax", "bluetooth", "gaming", "ram", "ssd", 
        "usb", "củ sạc", "mic ", "micro", "webcam", "giá đỡ điện thoại", "ốp lưng", "cường lực"
    ]
    if any(k in t for k in tech_kw):
        return "dien_tu"

    # 2. Mỹ phẩm / Sắc đẹp
    beauty_kw = [
        "son ", "son môi", "kem chống nắng", "kem dưỡng", "serum", "sữa rửa mặt", "toner", 
        "nước tẩy trang", "tẩy trang", "mặt nạ", "dầu gội", "dầu xả", "sữa tắm", "lăn khử mùi", 
        "nước hoa", "mascara", "phấn", "cushion", "chăm sóc da", "trị mụn", "dưỡng trắng", 
        "anessa", "maybelline", "bioderma", "l'oreal", "la roche-posay", "innisfree", "senka", 
        "cocoon", "klairs", "the ordinary", "durex", "bông tẩy trang", "kem nền", "chì kẻ mày", 
        "tẩy tế bào chết", "kem mắt", "xịt khoáng", "dưỡng ẩm"
    ]
    if any(k in t for k in beauty_kw):
        return "my_pham"

    # 3. Bách hóa / Thực phẩm / Mẹ & Bé
    fmcg_kw = [
        "sữa ", "sữa bột", "bỉm", "tã", "vinamilk", "huggies", "bobby", "merries", "moony", 
        "coca", "pepsi", "bia ", "trung nguyên", "cà phê", "cafe", "bánh", "kẹo", "mì ", 
        "nước mắm", "gia vị", "dầu ăn", "nước giặt", "bột giặt", "xả vải", "nước rửa chén", 
        "maxkleen", "masan", "th true", "ensure", "p&g", "unilever", "ariel", "downy", 
        "omo", "comfort", "sunlight", "knorr", "chin-su", "omachi", "mẹ và bé", "ăn dặm", 
        "bình sữa", "khăn ướt", "sting", "heineken", "tiger", "nestle", "milo"
    ]
    if any(k in t for k in fmcg_kw):
        return "bach_hoa"

    # 4. Thời trang / Phụ kiện
    fashion_kw = [
        "áo ", "áo thun", "áo khoác", "áo sơ mi", "quần ", "quần jean", "quần đùi", "váy", 
        "đầm", "giày", "dép", "túi xách", "balo", "ví ", "thắt lưng", "dây nịt", "mắt kính", 
        "kính mát", "nón", "mũ", "tất ", "vớ", "đồ lót", "bra", "boxer", "sneaker", "sandal", 
        "adidas", "nike", "crocs", "chân váy", "hoodie", "cardigan", "blazer", "vest", 
        "polo", "thời trang", "trang sức", "dây chuyền", "nhẫn", "vòng tay"
    ]
    if any(k in t for k in fashion_kw):
        return "thoi_trang"

    # 5. Gia dụng & Đời sống
    return "gia_dung"

def save_or_update_deals(deals_list):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    saved = 0
    now = datetime.now().isoformat()
    for d in deals_list:
        item_id = str(d.get("id"))
        if not item_id:
            continue
        title = (d.get("title") or "").strip()
        if not title:
            continue
        
        display_price = float(d.get("display_price") or 0)
        flash_price = float(d.get("flash_price") or 0)
        if display_price <= 0 and flash_price <= 0:
            continue

        prod_url = str(d.get("product_url") or "")
        if "/catalog/?" in prod_url or "?q=" in prod_url or "&q=" in prod_url:
            continue
        if title.lower().startswith("top deal ") and "toàn sàn" in title.lower():
            continue

        brand = d.get("brand") or detect_brand(title)
        cat = d.get("category", "")
        if not cat or cat in ["flash_sale", "flashsale", "all"]:
            cat = detect_category(title, brand)

        c.execute("""
            INSERT INTO deals (
                id, title, sku_id, category, brand, original_price, flash_price,
                voucher_price, display_price, discount_percent, sold_count,
                stock_count, image_url, product_url, affiliate_url, source,
                scm, raw_data, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title = excluded.title,
                sku_id = excluded.sku_id,
                category = excluded.category,
                brand = excluded.brand,
                original_price = excluded.original_price,
                flash_price = excluded.flash_price,
                voucher_price = excluded.voucher_price,
                display_price = excluded.display_price,
                discount_percent = excluded.discount_percent,
                sold_count = excluded.sold_count,
                stock_count = excluded.stock_count,
                image_url = excluded.image_url,
                product_url = excluded.product_url,
                affiliate_url = excluded.affiliate_url,
                source = excluded.source,
                scm = excluded.scm,
                raw_data = excluded.raw_data,
                updated_at = excluded.updated_at
        """, (
            item_id,
            title,
            str(d.get("sku_id", "")),
            cat,
            brand,
            float(d.get("original_price") or 0),
            float(d.get("flash_price") or 0),
            float(d.get("voucher_price") or 0),
            float(d.get("display_price") or 0),
            str(d.get("discount_percent") or ""),
            int(d.get("sold_count") or 0),
            int(d.get("stock_count") or 0),
            d.get("image_url", ""),
            d.get("product_url", ""),
            d.get("affiliate_url", ""),
            d.get("source", "lazada"),
            d.get("scm", ""),
            json.dumps(d.get("raw", {}), ensure_ascii=False),
            now
        ))
        saved += 1
    conn.commit()
    conn.close()
    return saved

def query_deals(min_price=None, max_price=None, min_discount=None, category=None, brand=None, is_tmall=False, search=None, limit=50, offset=0, sort_by="discount_desc"):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    query = "SELECT * FROM deals WHERE 1=1"
    params = []
    
    if min_price is not None:
        query += " AND (display_price >= ? OR (display_price = 0 AND flash_price >= ?))"
        params.extend([min_price, min_price])
    if max_price is not None:
        query += " AND ((display_price > 0 AND display_price <= ?) OR (display_price = 0 AND flash_price <= ?))"
        params.extend([max_price, max_price])
    if min_discount is not None:
        query += " AND CAST(REPLACE(discount_percent, '%', '') AS INTEGER) >= ?"
        params.append(min_discount)
    if is_tmall:
        query += " AND (source LIKE '%tmall%' OR source LIKE '%lazglobal%' OR scm LIKE '%tmall%' OR brand IS NOT NULL AND brand != '')"
    if category and category != "all":
        if category == "deal_hot":
            query += " AND CAST(REPLACE(discount_percent, '%', '') AS INTEGER) >= 50"
        elif category in ["dien_tu", "gia_dung", "thoi_trang", "my_pham", "bach_hoa"]:
            query += " AND category = ?"
            params.append(category)
        else:
            query += " AND category = ?"
            params.append(category)
    if brand and brand != "all":
        query += " AND (brand = ? OR title LIKE ?)"
        params.extend([brand, f"%{brand}%"])
    if search:
        query += " AND (title LIKE ? OR brand LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
        
    if sort_by == "discount_desc":
        query += " ORDER BY CAST(REPLACE(discount_percent, '%', '') AS INTEGER) DESC, CASE WHEN display_price > 0 THEN display_price ELSE flash_price END ASC"
    elif sort_by == "display_price_asc":
        query += " ORDER BY CASE WHEN display_price > 0 THEN display_price ELSE flash_price END ASC"
    elif sort_by == "display_price_desc":
        query += " ORDER BY CASE WHEN display_price > 0 THEN display_price ELSE flash_price END DESC"
    elif sort_by == "sold_desc":
        query += " ORDER BY sold_count DESC"
    else:
        query += " ORDER BY updated_at DESC"
        
    query += " LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    c.execute(query, params)
    rows = c.fetchall()
    
    # Get total count
    count_query = "SELECT COUNT(*) FROM deals WHERE 1=1"
    count_params = []
    if min_price is not None:
        count_query += " AND (display_price >= ? OR (display_price = 0 AND flash_price >= ?))"
        count_params.extend([min_price, min_price])
    if max_price is not None:
        count_query += " AND ((display_price > 0 AND display_price <= ?) OR (display_price = 0 AND flash_price <= ?))"
        count_params.extend([max_price, max_price])
    if min_discount is not None:
        count_query += " AND CAST(REPLACE(discount_percent, '%', '') AS INTEGER) >= ?"
        count_params.append(min_discount)
    if is_tmall:
        count_query += " AND (source LIKE '%tmall%' OR source LIKE '%lazglobal%' OR scm LIKE '%tmall%' OR brand IS NOT NULL AND brand != '')"
    if category and category != "all":
        if category == "deal_hot":
            count_query += " AND CAST(REPLACE(discount_percent, '%', '') AS INTEGER) >= 50"
        elif category in ["dien_tu", "gia_dung", "thoi_trang", "my_pham", "bach_hoa"]:
            count_query += " AND category = ?"
            count_params.append(category)
        else:
            count_query += " AND category = ?"
            count_params.append(category)
    if brand and brand != "all":
        count_query += " AND (brand = ? OR title LIKE ?)"
        count_params.extend([brand, f"%{brand}%"])
    if search:
        count_query += " AND (title LIKE ? OR brand LIKE ?)"
        count_params.extend([f"%{search}%", f"%{search}%"])
        
    c.execute(count_query, count_params)
    total = c.fetchone()[0]
    
    conn.close()
    return [dict(r) for r in rows], total

def get_stats():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM deals")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM deals WHERE (display_price > 0 AND display_price <= 1000) OR (display_price = 0 AND flash_price <= 1000)")
    c1k = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM deals WHERE (display_price > 0 AND display_price <= 9000) OR (display_price = 0 AND flash_price <= 9000)")
    c9k = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM deals WHERE (display_price > 0 AND display_price <= 50000) OR (display_price = 0 AND flash_price <= 50000)")
    c50k = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM deals WHERE CAST(REPLACE(discount_percent, '%', '') AS INTEGER) >= 50")
    c50 = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM deals WHERE (source LIKE '%tmall%' OR source LIKE '%lazglobal%' OR scm LIKE '%tmall%' OR brand IS NOT NULL AND brand != '')")
    ctmall = c.fetchone()[0]
    c.execute("SELECT MAX(updated_at) FROM deals")
    last_updated = c.fetchone()[0]
    conn.close()
    return {
        "total_deals": total,
        "deals_1k": c1k,
        "deals_9k": c9k,
        "deals_50k": c50k,
        "deals_over_50": c50,
        "deals_tmall": ctmall,
        "last_updated": last_updated
    }

def get_setting(key, default=""):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else default

def set_setting(key, value):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        INSERT INTO settings (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
    """, (key, str(value)))
    conn.commit()
    conn.close()

def get_brands_summary():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT brand, COUNT(*) as cnt FROM deals WHERE brand IS NOT NULL AND brand != '' GROUP BY brand ORDER BY cnt DESC")
    rows = c.fetchall()
    conn.close()
    return [{"brand": r[0], "count": r[1]} for r in rows]

def populate_existing_brands():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, title FROM deals WHERE brand IS NULL OR brand = ''")
    rows = c.fetchall()
    updated = 0
    for r in rows:
        b = detect_brand(r[1])
        if b:
            c.execute("UPDATE deals SET brand = ? WHERE id = ?", (b, r[0]))
            updated += 1
    conn.commit()
    conn.close()
    return updated

def populate_existing_categories():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, title, brand FROM deals")
    rows = c.fetchall()
    updated = 0
    for r in rows:
        cat = detect_category(r[1], r[2] or "")
        c.execute("UPDATE deals SET category = ? WHERE id = ?", (cat, r[0]))
        updated += 1
    conn.commit()
    conn.close()
    return updated

if __name__ == "__main__":
    init_db()
    up_b = populate_existing_brands()
    up_c = populate_existing_categories()
    print(f"Database initialized. Populated brand for {up_b} deals, category for {up_c} deals.")
    print("Top brands:", get_brands_summary()[:10])
