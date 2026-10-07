import urllib.request
import urllib.parse
import ssl
import json
import re
import sys
from datetime import datetime
from bs4 import BeautifulSoup
from database import save_or_update_deals, get_setting

# Safe UTF-8 printing in Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

HEADERS_PC = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
}

HEADERS_MOBILE = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Lazada/VN/7.20.0",
    "Accept": "application/json, text/plain, */*",
}

# 31 Verified High-Traffic & Specific Ngành Hàng Lazada GCP Router Channels (Zero Captcha WAF)
GCP_CHANNELS = [
    # 1. Điện Tử & Công Nghệ
    ("Điện Tử Tech Fanatic", "/lazada/channel/vn/dien-tu-dien-gia-dung/Tech-Fanatic", "dien_tu", False),
    ("Mê Công Nghệ", "/lazada/channel/vn/lazglobalchannel/Me-Cong-Nghe", "dien_tu", True),
    
    # 2. Thời Trang & Phụ Kiện
    ("Thời Trang LazFashion", "/lazada/channel/vn/fashion/lazada-fashion", "thoi_trang", False),
    ("Thời Trang Hotdeal", "/lazada/channel/vn/fashion/Hotdeal", "thoi_trang", False),
    ("Thời Trang Nam Global", "/lazada/channel/vn/lazglobalchannel/MenFashionGlobal", "thoi_trang", True),
    ("Thể Thao & Dã Ngoại", "/lazada/channel/vn/lazglobalchannel/SportsandOutdoor", "thoi_trang", True),
    ("Taobao Collection Thời Trang", "/lazada/channel/vn/lazglobalchannel/taobao-colection", "thoi_trang", True),
    
    # 3. Mỹ Phẩm & Sắc Đẹp
    ("Mỹ Phẩm LazBeauty", "/lazada/channel/vn/VNlazbeauty/lazbeauty", "my_pham", False),
    ("Tmall Girly Mỹ Phẩm", "/lazada/channel/vn/lazmall-channel/tmall-womenday-girly", "my_pham", True),
    
    # 4. Gia Dụng & Đời Sống
    ("Gia Dụng LazHomey", "/lazada/channel/vn/nha-cua-doi-song-o-to-xe-may/Lazhomey_MCP", "gia_dung", False),
    ("Tmall Homelover Gia Dụng", "/lazada/channel/vn/lazmall-channel/tmall-womenday-homelover", "gia_dung", True),
    
    # 5. Bách Hóa & Mẹ Bé
    ("Bách Hóa & Mẹ Bé LazMom", "/lazada/channel/vn/lazmomvn/lazmom", "bach_hoa", False),
    ("LazMom Lazmall Chính Hãng", "/lazada/channel/vn/lazmomvn/Lazmall", "bach_hoa", False),
    ("Sữa Chính Hãng Bách Hóa", "/lazada/channel/vn/milk-guarantee/trang-chinh", "bach_hoa", False),
    
    # 6. Kênh Toàn Sàn, Flash Sale & Trợ Giá Lớn
    ("LazFlash Mobile", "/lazada/channel/vn/shopping-guide/lazflash", "all", False),
    ("LazSubsidy Trợ Giá 3 Bên", "/lazada/channel/vn/shopping-guide/lazsubsidy-three-party", "all", False),
    ("FlashSale Chủ Đề", "/lazada/channel/vn/shopping-guide/flashsale-theme", "all", False),
    ("FlashSale Bán Chạy", "/lazada/channel/vn/shopping-guide/flashsale-hot-deals", "all", False),
    ("LazGlobal Quốc Tế", "/lazada/channel/vn/lazglobalchannel/Laz-Quoc-Te", "all", True),
    ("Tmall Trung Chính Hãng", "/lazada/channel/vn/lazmall-channel/thuong-hieu-trung-chinh-hang", "all", True),
    ("Global Hits Thịnh Hành", "/lazada/channel/vn/ac_guide/global-hits", "all", True),
    ("Top Deal Hàng Hiệu", "/lazada/channel/vn/lazglobalchannel/topdealhanghieu", "all", True),
    ("Bestsellers Toàn Sàn", "/lazada/channel/vn/homepage/bestsellers_nav", "all", False),
    ("Bestsellers Chủ Đề", "/lazada/channel/vn/homepage/bestsellers-topic-guide", "all", False),
    ("Siêu Hội FreeShip MAX", "/lazada/channel/vn/FreeShipMAX/tpNs6PFGs4_copy_f6tnDF6KrZ", "all", False),
    ("Mua Càng Nhiều Giảm Càng Sâu", "/lazada/channel/vn/buy_more_channel/Yz8GrZ8aEm", "all", False),
    ("LazMall Hàng Mới Về", "/lazada/channel/vn/lazmall-channel/new-in", "all", False),
    ("LazMall Flagship", "/lazada/channel/vn/LazMallOne/Homepage", "all", False),
    ("Sự Kiện Khuyến Mãi LazEvent", "/lazada/channel/vn/khuyen-mai/lazevent", "all", False),
    ("Lazada Home Featured", "/lazada/channel/vn/homepage/home", "all", False),
    ("Lịch Siêu Sale Giữ Chuỗi", "/lazada/megascenario/vn/sale-10-10-2026/lich-sale-giu-chuoi", "all", False),
]

def clean_price_val(val):
    if not val:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).replace("₫", "").replace("đ", "").replace(" ", "").strip()
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except Exception:
        return 0.0

def build_affiliate_link(original_url):
    aff_id = get_setting("affiliate_id", "cheetah")
    if not original_url:
        return ""
    if original_url.startswith("//"):
        original_url = "https:" + original_url
    elif not original_url.startswith("http"):
        original_url = "https://" + original_url.lstrip("/")
    enc = urllib.parse.quote(original_url)
    return f"https://c.lazada.vn/t/c.0Oe54N?sub_aff_id={aff_id}&url={enc}"

def find_all_items(obj, depth=0):
    """
    Recursively scans arbitrary nested JSON trees to extract product item dictionaries.
    """
    found = []
    if depth > 10:
        return found
    if isinstance(obj, dict):
        if any(k in obj for k in ["itemId", "skuId", "itemTitle", "itemPrice"]):
            found.append(obj)
        else:
            for k, v in obj.items():
                found.extend(find_all_items(v, depth + 1))
    elif isinstance(obj, list):
        for elem in obj:
            found.extend(find_all_items(elem, depth + 1))
    return found

def parse_gcp_item(it, channel_name, default_cat, is_tmall):
    """
    Standardizes raw JSON dictionaries from Lazada GCP channels into unified deal format.
    STRICT: Rejects dummy keyword searches and 0-price items.
    """
    item_id = str(it.get("itemId") or it.get("skuId") or it.get("id") or "")
    if not item_id or not item_id.isdigit():
        return None
        
    title = str(it.get("itemTitle") or it.get("title") or "").strip()
    if not title or (title.lower().startswith("top deal ") and "toàn sàn" in title.lower()):
        return None
        
    raw_url = it.get("itemUrl") or it.get("url") or ""
    if not raw_url:
        return None
        
    if raw_url.startswith("//"):
        raw_url = "https:" + raw_url
    elif not raw_url.startswith("http"):
        raw_url = "https://" + raw_url.lstrip("/")
        
    # Reject search keyword URLs
    if "/catalog/?" in raw_url or "?q=" in raw_url or "&q=" in raw_url:
        return None
        
    img = it.get("itemImg") or it.get("skuMainImg") or it.get("image") or ""
    if img:
        if img.startswith("//"):
            img = "https:" + img
        elif not img.startswith("http"):
            img = "https://" + img.lstrip("/")
        
    price_obj = it.get("itemPrice", {})
    o_price = 0.0
    f_price = 0.0
    disc = str(it.get("itemDiscount") or "")
    
    if isinstance(price_obj, dict):
        o_price = clean_price_val(price_obj.get("itemPrice"))
        f_price = clean_price_val(price_obj.get("itemDiscountPrice"))
        if not disc:
            disc = str(price_obj.get("itemDiscount", ""))
    elif isinstance(price_obj, (int, float, str)):
        f_price = clean_price_val(price_obj)
        
    if not f_price:
        f_price = clean_price_val(it.get("itemDiscountPrice") or it.get("displayPrice"))
    if not o_price:
        o_price = clean_price_val(it.get("itemPrice") or it.get("originPrice"))
        
    v_price = f_price
    d_price = f_price
    scm = ""
    
    if raw_url:
        m_scm = re.search(r'scm=([^&]+)', raw_url)
        if m_scm:
            scm = m_scm.group(1)
        m_orig = re.search(r'originPrice(?:%3A|:)([0-9.]+)', raw_url)
        if m_orig:
            o_price = float(m_orig.group(1))
        m_subsidy = re.search(r'subsidyPrice(?:%3A|:)([0-9.]+)', raw_url)
        if m_subsidy:
            f_price = float(m_subsidy.group(1))
        m_vouc = re.search(r'voucherPrice(?:%3A|:)([0-9.]+)', raw_url)
        if m_vouc:
            v_price = float(m_vouc.group(1))
        m_disp = re.search(r'displayPrice(?:%3A|:)([0-9.]+)', raw_url)
        if m_disp:
            d_price = float(m_disp.group(1))
            
    # Reject 0 price items
    if d_price <= 0 and f_price <= 0:
        return None
        
    if disc and not disc.endswith("%"):
        disc += "%"
    if not disc and o_price > 0 and d_price > 0 and o_price > d_price:
        disc = f"{int(round((1 - (d_price / o_price)) * 100))}%"
        
    brand = str(it.get("brandName") or "")
    
    return {
        "id": item_id,
        "title": title,
        "sku_id": str(it.get("skuId", "")),
        "brand": brand,
        "category": default_cat,
        "original_price": o_price,
        "flash_price": f_price or d_price,
        "voucher_price": v_price or d_price,
        "display_price": d_price or f_price,
        "discount_percent": disc,
        "sold_count": int(it.get("itemSoldCnt") or 0) if str(it.get("itemSoldCnt") or "").isdigit() else 0,
        "stock_count": int(it.get("itemCurrentStock") or 100) if str(it.get("itemCurrentStock") or "").isdigit() else 100,
        "image_url": img,
        "product_url": raw_url,
        "affiliate_url": build_affiliate_link(raw_url),
        "source": "lazada_gcp_" + channel_name.lower().replace(" ", "_"),
        "scm": scm or ("tmall" if is_tmall else ""),
        "raw": it
    }

def fetch_lazada_pc_flashsale():
    """
    Scrapes Flash Sale PC SSR data (__FIRST_SCREEN_DATA) ONLY for real products.
    """
    url = "https://www.lazada.vn/flash-sale/"
    req = urllib.request.Request(url, headers=HEADERS_PC)
    deals = []
    try:
        with urllib.request.urlopen(req, timeout=15, context=CTX) as resp:
            content = resp.read().decode("utf-8", errors="ignore")
        m = re.search(r'window\.__FIRST_SCREEN_DATA\s*=\s*(\{.*?\});', content)
        if not m:
            return deals
        raw_data = json.loads(m.group(1))
        sections = (
            raw_data.get("data", {})
            .get("8849744590", {})
            .get("pcHomepageData", {})
            .get("sections", [])
        )
        for sec in sections:
            m_id = sec.get("moduleId")
            # ONLY Direct Flash Sale Items (NO dummy category seeds!)
            if m_id == "flashSalePC":
                for d_entry in sec.get("fields", {}).get("datas", []):
                    items = d_entry.get("items", [])
                    for item in items:
                        i_id = str(item.get("itemId", ""))
                        title = item.get("itemTitle", "")
                        f_price = clean_price_val(item.get("itemDiscountPrice"))
                        o_price = clean_price_val(item.get("itemPrice"))
                        disc = item.get("itemDiscount", "")
                        sold = int(item.get("itemSoldCnt") or 0)
                        stock = int(item.get("itemCurrentStock") or 0)
                        img = item.get("itemImg", "")
                        if img:
                            if img.startswith("//"):
                                img = "https:" + img
                            elif not img.startswith("http"):
                                img = "https://" + img.lstrip("/")
                        p_url = item.get("itemUrl", "")
                        if p_url:
                            if p_url.startswith("//"):
                                p_url = "https:" + p_url
                            elif not p_url.startswith("http"):
                                p_url = "https://" + p_url.lstrip("/")
                        
                        if f_price <= 0 and o_price <= 0:
                            continue
                        if not p_url or "/catalog/?" in p_url or "?q=" in p_url:
                            continue
                        
                        track = item.get("trackInfo", "")
                        v_price = f_price
                        d_price = f_price
                        if "voucher_price" in track:
                            m_v = re.search(r'voucher_price%3A([0-9.]+)', track)
                            if m_v:
                                v_price = clean_price_val(m_v.group(1))
                                d_price = v_price
                                
                        deals.append({
                            "id": i_id,
                            "title": title,
                            "sku_id": "",
                            "category": "flash_sale",
                            "original_price": o_price,
                            "flash_price": f_price,
                            "voucher_price": v_price,
                            "display_price": d_price,
                            "discount_percent": disc,
                            "sold_count": sold,
                            "stock_count": stock,
                            "image_url": img,
                            "product_url": p_url,
                            "affiliate_url": build_affiliate_link(p_url),
                            "source": "lazada_pc_flashsale",
                            "scm": item.get("scm", ""),
                            "raw": item
                        })
                        
    except Exception as e:
        print("[!] Error scraping Lazada PC Flash Sale:", e)
    return deals

def fetch_lazada_gcp_channels():
    """
    Crawls 31 high-traffic and specific ngành hàng GCP router channels.
    """
    all_channel_deals = []
    seen_ids = set()
    
    for name, wh_pid, default_cat, is_tmall in GCP_CHANNELS:
        url = f"https://pages.lazada.vn/wow/gcp/route/lazada/vn/upr_1000345_lazada/channel/vn/upr-router/vn?wh_pid={wh_pid}&hybrid=1&data_prefetch=true"
        try:
            req = urllib.request.Request(url, headers=HEADERS_MOBILE)
            with urllib.request.urlopen(req, timeout=12, context=CTX) as r:
                html = r.read().decode('utf-8', errors='ignore')
            m = re.search(r'window\.__FIRST_SCREEN_DATA\s*=\s*(\{.*?\});', html)
            if not m:
                continue
            data = json.loads(m.group(1))
            raw_items = find_all_items(data)
            count = 0
            for raw_it in raw_items:
                parsed = parse_gcp_item(raw_it, name, default_cat, is_tmall)
                if parsed and parsed["id"] not in seen_ids:
                    seen_ids.add(parsed["id"])
                    all_channel_deals.append(parsed)
                    count += 1
            print(f" -> [{name}] Thu thập được {count} deal mới.")
        except Exception as e:
            print(f"[!] Lỗi khi quét {name}: {e}")
            
    return all_channel_deals

def fetch_gocsandeal_feed():
    """
    Crawls pre-calculated and aggregated Lazada Flash Sale deals snapshot.
    """
    base_url = "https://gocsandeal.com/san-sale-lazada"
    deals = []
    try:
        req = urllib.request.Request(base_url, headers=HEADERS_PC)
        with urllib.request.urlopen(req, timeout=15, context=CTX) as resp:
            content = resp.read().decode("utf-8", errors="ignore")
            
        soup = BeautifulSoup(content, "html.parser")
        items = soup.select(".product-item")
        
        for it in items:
            item_id = it.get("data-item-id")
            if not item_id:
                continue
            
            a_tag = it.select_one(".product-title") or it.select_one(".product-img a")
            title = ""
            aff_link = ""
            orig_laz_url = ""
            
            if a_tag:
                title = a_tag.get_text(strip=True)
                aff_link = a_tag.get("href", "")
                if "url=" in aff_link:
                    m_url = re.search(r'url=([^&]+)', aff_link)
                    if m_url:
                        orig_laz_url = urllib.parse.unquote(m_url.group(1))
            
            img_tag = it.select_one(".product-img img")
            img_url = img_tag.get("src", "") if img_tag else ""
            if not img_url and img_tag:
                img_url = img_tag.get("data-src", "")
                
            p_elem = it.select_one(".price")
            op_elem = it.select_one(".original_price")
            
            display_price = clean_price_val(p_elem.get_text(strip=True)) if p_elem else 0.0
            original_price = clean_price_val(op_elem.get_text(strip=True)) if op_elem else 0.0
            flash_price = display_price
            voucher_price = display_price
            scm = ""
            
            if orig_laz_url:
                m_scm = re.search(r'scm=([^&]+)', orig_laz_url)
                if m_scm:
                    scm = m_scm.group(1)
                m_orig = re.search(r'originPrice(?:%3A|:)([0-9.]+)', orig_laz_url)
                if m_orig:
                    original_price = float(m_orig.group(1))
                m_subsidy = re.search(r'subsidyPrice(?:%3A|:)([0-9.]+)', orig_laz_url)
                if m_subsidy:
                    flash_price = float(m_subsidy.group(1))
                m_voucher = re.search(r'voucherPrice(?:%3A|:)([0-9.]+)', orig_laz_url)
                if m_voucher:
                    voucher_price = float(m_voucher.group(1))
                m_disp = re.search(r'displayPrice(?:%3A|:)([0-9.]+)', orig_laz_url)
                if m_disp:
                    display_price = float(m_disp.group(1))
            
            if display_price <= 0 and flash_price <= 0:
                continue
            if not title:
                continue
            
            disc_str = ""
            if original_price > 0 and display_price > 0:
                pct = int(round((1 - (display_price / original_price)) * 100))
                if pct > 0:
                    disc_str = f"{pct}%"
                    
            deals.append({
                "id": str(item_id),
                "title": title,
                "sku_id": "",
                "category": "flash_sale",
                "original_price": original_price,
                "flash_price": flash_price,
                "voucher_price": voucher_price,
                "display_price": display_price,
                "discount_percent": disc_str,
                "sold_count": 0,
                "stock_count": 0,
                "image_url": img_url,
                "product_url": orig_laz_url or aff_link,
                "affiliate_url": build_affiliate_link(orig_laz_url) if orig_laz_url else aff_link,
                "source": "aggregator_feed",
                "scm": scm,
                "raw": {"title": title, "url": aff_link}
            })
            
    except Exception as e:
        pass
    return deals

def run_crawler():
    """
    Multi-channel crawler engine that scans all Lazada marketplace ngành hàng channels, 
    flash sales, subsidy deals, Tmall global, and brand feeds without CAPTCHA.
    """
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🚀 Bắt đầu quét Flash Sale & Deal Ẩn Lazada TOÀN BỘ NGÀNH HÀNG...")
    all_deals = []
    
    # 1. Scrape Lazada Direct PC Flash Sale SSR
    print("[*] 1/3 Quét Lazada PC Flash Sale SSR...")
    d1 = fetch_lazada_pc_flashsale()
    print(f" -> Thu thập được {len(d1)} deal.")
    all_deals.extend(d1)

    # 2. Scrape 31 Lazada GCP Channels (Categories, Subsidy, Tmall, Bestsellers, Freeship, Mega Sale)
    print("[*] 2/3 Quét 31 Kênh Ngành Hàng & Deal Ẩn Lazada Toàn Sàn...")
    d2 = fetch_lazada_gcp_channels()
    print(f" -> Tổng cộng thu thập được {len(d2)} deal từ các kênh ngành hàng.")
    all_deals.extend(d2)

    # 3. Scrape Aggregated Flash Sale Feed (if not rate limited)
    print("[*] 3/3 Quét kênh phân phối Flash Sale toàn sàn...")
    d3 = fetch_gocsandeal_feed()
    if d3:
        print(f" -> Thu thập được {len(d3)} deal.")
        all_deals.extend(d3)
    else:
        print(" -> Feed tạm thời bỏ qua (sử dụng kho deal ngành hàng trực tiếp từ Lazada).")
    
    # Save & Deduplicate in DB
    print(f"[*] Đang ghi và phân loại {len(all_deals)} sản phẩm vào cơ sở dữ liệu...")
    count = save_or_update_deals(all_deals)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Đã cập nhật thành công {count} sản phẩm Flash Sale & Deal Toàn Sàn vào Database!")
    return count

if __name__ == "__main__":
    run_crawler()
