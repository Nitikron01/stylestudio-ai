import os
import json
import requests
from datetime import datetime, timedelta
from collections import Counter
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

# โหลดค่าคอนฟิกจากไฟล์ .env (สำหรับการรันในคอมพิวเตอร์ตัวเอง)
load_dotenv()

# ==========================================
# 📂 ส่วนที่ 1: การเชื่อมต่อ Google Sheets ด่วนพิเศษ
# ==========================================
def get_google_sheet():
    SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
    
    # 1. ตรวจสอบโหมดรันบน GitHub Actions (ดึงค่า JSON string จาก Secrets)
    json_str = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    
    # 2. ตรวจสอบโหมดรันในคอมพิวเตอร์ตัวเอง (ดึงไฟล์กุญแจ .json Local)
    file_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE") or os.getenv("GOOGLE_SERVICES_ACCOUNT_FILE")
    
    if json_str:
        info = json.loads(json_str)
        creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    elif file_path and os.path.exists(file_path):
        creds = Credentials.from_service_account_file(file_path, scopes=SCOPES)
    else:
        raise RuntimeError("❌ ไม่พบการตั้งค่ากุญแจสิทธิ์ Google Service Account ในระบบ")
        
    client = gspread.authorize(creds)
    sheet_id = os.getenv("GOOGLE_SHEETS_ID")
    if not sheet_id:
        raise RuntimeError("❌ ไม่พบ GOOGLE_SHEETS_ID ในตั้งค่า")
        
    return client.open_by_key(sheet_id).sheet1


# ==========================================
# 🚀 ส่วนที่ 2: การส่งข้อความหา Telegram (เพิ่มความอึด)
# ==========================================
def send_telegram_message(message):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("❌ ไม่พบ TELEGRAM TOKEN หรือ CHAT ID ในระบบ")
        return

    # พิมพ์รายงานออกมาดูบนหน้าจอ Terminal ทันที เผื่อเน็ตคอมพิวเตอร์ค้าง
    print("\n--- 📋 [ข้อความสรุปที่จะส่งเข้า Telegram] ---")
    print(message.strip())
    print("-------------------------------------------\n")

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"  # รองรับการแต่งตัวหนา/โค้ด
    }

    try:
        print("กำลังส่งข้อความเข้า Telegram... 🚀")
        # ขยายเวลารอเป็น 30 วินาที เพื่อสู้กับเน็ตหน่วงในคอมพิวเตอร์
        response = requests.post(url, data=payload, timeout=30)
        print("Status Code จาก Telegram:", response.status_code)
        
        if response.status_code == 200:
            print("ส่งข้อมูลเข้า Telegram สำเร็จเรียบร้อยแล้วจ้า! ✅📱")
        else:
            print("ส่งเข้า Telegram ไม่สำเร็จน้า ❌")
            print("รายละเอียด:", response.text)
            
    except Exception as e:
        print("เกิดข้อผิดพลาดตอนส่ง Telegram (เน็ตคอมฯ อาจจะโดนบล็อกชั่วคราว) ⚠️")
        print(f"Error: {e}")


# ==========================================
# 📊 ส่วนที่ 3: ดึงข้อมูลและคำนวณสรุปยอดขายร้าน MilkLab
# ==========================================
def generate_report():
    print("กำลังโหลด Google Sheet... ☕")
    try:
        sheet = get_google_sheet()
        raw_rows = sheet.get_all_values()
        # กรองเอาแถวว่าง ๆ ทิ้งไปก่อนเพื่อความรวดเร็วในการประมวลผล
        rows = [row for row in raw_rows if row and any(cell.strip() for cell in row)]
        print("โหลดข้อมูลจาก Google Sheet สำเร็จ ✅")
    except Exception as e:
        print(f"โหลด Google Sheet ไม่สำเร็จ ❌\nError: {e}")
        return

    if len(rows) <= 1:
        send_telegram_message("☀️ มอนิ่งค๊าา วันนี้ยังไม่มีข้อมูลยอดขายในตารางเลยน้า")
        return

    # คำนวณหาวันที่ของเมื่อวานนี้ (ฟอร์แมต YYYY-MM-DD)
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    total_sales = 0
    menu_counter = Counter()
    sales_count = 0

    # วนลูปอ่านข้อมูลและข้ามหัวตาราง (Header)
    for row in rows[1:]:
        try:
            if len(row) < 5 or not row[0]:
                continue

            date = row[0].strip()

            # กรองจับเฉพาะยอดขายที่เป็นของเมื่อวานเท่านั้น
            if date != yesterday:
                continue

            menu = row[1].strip()
            qty = int(row[2])
            
            # เคลียร์ฟอร์แมตตัวเลขราคา (ลบคอมม่า ป้องกันเลขทศนิยมเออร์เรอร์)
            clean_price = row[4].replace(',', '').strip()
            total = int(float(clean_price))

            total_sales += total
            sales_count += 1
            menu_counter[menu] += qty

        except Exception:
            continue

    # 📝 กรณีที่เมื่อวานนี้ไม่มียอดขายเลย
    if sales_count == 0:
        message = f"""
☀️ *Morning Report จ้าา!* ☀️

เมื่อวาน ({yesterday})
ร้านเรายังไม่มียอดขายบันทึกเข้ามาเลยค๊าา 🥹

วันนี้เปิดร้านรับทรัพย์ ขอให้ลูกค้าเข้าแน่น ๆ เลยน้าา 🥛✨🚀
"""
        send_telegram_message(message)
        return

    # 👑 คำนวณหาเมนูที่ขายดีที่สุด
    best_menu = max(menu_counter, key=menu_counter.get)
    best_qty = menu_counter[best_menu]

    # ✉️ หน้าตาข้อความสรุปยอดขายสุดปัง
    message = f"""
☀️ *Morning Milk Report* ☀️

📅 *รายงานประจำวันที่:* {yesterday}

🧾 *จำนวนบิลขายทั้งหมด:* {sales_count} รายการ
💰 *ยอดขายรวมทั้งสิ้น:* `{total_sales:,}` บาท
🔥 *เมนูขายดีสุดปัง:* {best_menu}

🥤 *ยอดจำหน่ายเมนูขายดี:* {best_qty} แก้ว

วันนี้ขอให้เฮง ๆ ปัง ๆ ออเดอร์เด้งเข้าไม่หยุดเลยน้าค้าาา ✨🚀🍼
"""
    send_telegram_message(message)


if __name__ == "__main__":
    generate_report()