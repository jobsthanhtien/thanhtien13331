import urllib.request
import json
from database import get_setting

def send_telegram_alert(deal):
    """
    Sends notification to Telegram Channel / Group / Bot.
    Reads telegram_bot_token and telegram_chat_id from settings.
    """
    bot_token = get_setting("telegram_bot_token", "")
    chat_id = get_setting("telegram_chat_id", "")
    
    if not bot_token or not chat_id:
        return False, "Chưa cấu hình Telegram Bot Token hoặc Chat ID"
        
    title = deal.get("title", "")
    price = int(deal.get("display_price", 0))
    orig_price = int(deal.get("original_price", 0))
    discount = deal.get("discount_percent", "")
    url = deal.get("affiliate_url") or deal.get("product_url")
    
    message = (
        f"⚡ <b>[KÈO THƠM LAZADA] DEAL GIÁ CỰC SỐC!</b> ⚡\n\n"
        f"📦 <b>Sản phẩm:</b> {title}\n"
        f"🔥 <b>Giá săn được:</b> <code>{price:,}đ</code>\n"
        f"🏷️ <b>Giá gốc:</b> <s>{orig_price:,}đ</s> (-{discount})\n"
        f"🔗 <b>Link chốt đơn ngay:</b> <a href='{url}'>Bấm vào đây để mua</a>\n\n"
        f"<i>⏰ Quét tự động bởi DZUx Lazada Flash Hunter</i>"
    )
    
    api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            api_url,
            data=data,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            res_data = json.loads(resp.read().decode('utf-8'))
            if res_data.get("ok"):
                return True, "Gửi tin nhắn thành công!"
            else:
                return False, res_data.get("description", "Lỗi gửi tin")
    except Exception as e:
        return False, str(e)
