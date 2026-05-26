import os
import requests
import time  # สำหรับหน่วงเวลาตอนส่งซ้ำ
from datetime import datetime, timedelta
from collections import Counter

from dotenv import load_dotenv
from sheets_client import get_sheet

# โหลดค่าใน .env
load_dotenv()

# debug ดูว่าอ่าน .env ได้ไหม
print("SERVICE ACCOUNT FILE =")
print(os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE"))


def send_telegram_message(message):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("❌ ไม่พบ TELEGRAM TOKEN หรือ CHAT ID ในระบบ")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    # ใช้ data=payload เพื่อส่งข้อมูลแบบ Form URL Encoded ตามมาตรฐานบอท Telegram
    payload = {
        "chat_id": chat_id,
        "text": message
    }

    # 🛠️ ป้องกันระบบเน็ตหน่วงด้วยระบบพยายามส่งซ้ำ 3 รอบ
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            print(f"กำลังส่งข้อความเข้า Telegram (รอบที่ {attempt}/{max_retries})... 🚀")
            
            # เปลี่ยนจาก json=payload เป็น data=payload และขยายเวลารอเป็น 60 วินาที
            response = requests.post(url, data=payload, timeout=60)
            
            if response.status_code == 200:
                print("ส่ง Telegram สำเร็จ ✅")
                return
            else:
                print(f"⚠️ รอบที่ {attempt} Telegram ปฏิเสธ (Status: {response.status_code})")
                print("รายละเอียด:", response.text)
                
        except requests.exceptions.Timeout:
            print(f"⏳ รอบที่ {attempt} หมดเวลารอ (Timeout) เนื่องจากสัญญาณอินเทอร์เน็ตแกว่ง...")
        except Exception as e:
            print(f"❌ รอบที่ {attempt} เกิดข้อผิดพลาดอื่น: {e}")
            
        # หน่วงเวลา 2 วินาทีก่อนลองส่งใหม่อีกรอบ
        time.sleep(2)
        
    print("❌ พยายามส่งครบ 3 รอบแล้ว ไม่สามารถติดต่อเซิร์ฟเวอร์ Telegram ได้ในขณะนี้")


def generate_morning_report():

    print("กำลังโหลด Google Sheet คลังข้อมูลร้าน StyleStudio... 🛍️")

    try:
        sheet = get_sheet()
        print("โหลด Google Sheet สำเร็จ ✅")
    except Exception as e:
        print("โหลด Google Sheet ไม่สำเร็จ ❌")
        print("Error:", e)
        return

    try:
        rows = sheet.get_all_values()
    except Exception as e:
        print("ดึงข้อมูลจาก Sheet ไม่สำเร็จ ❌")
        print("Error:", e)
        return

    if len(rows) <= 1:
        print("ยังไม่มีข้อมูลยอดขาย")
        return

    data_rows = rows[1:]

    yesterday = (
        datetime.now() - timedelta(days=1)
    ).strftime("%Y-%m-%d")

    total_sales = 0
    menu_counter = Counter()

    for row in data_rows:
        if len(row) < 5:
            continue

        row_date = row[0].strip()

        if row_date != yesterday:
            continue

        try:
            menu_name = row[1].strip()
            quantity = int(row[2])
            
            # เคลียร์ฟอร์แมตตัวเลขราคา เผื่อมีคอมม่า (,) ปนมาใน Google Sheets
            clean_price = row[4].replace(',', '').strip()
            total_price = float(clean_price)

            total_sales += total_price
            menu_counter[menu_name] += quantity
        except:
            continue

    if total_sales == 0:
        message = (
            f"☀️ *Morning Report ร้าน StyleStudio* ☀️\n\n"
            f"📅 เมื่อวาน ({yesterday})\n"
            f"ยังไม่มียอดขายบันทึกเข้าระบบเลยค่ะ 🥹\n\n"
            f"วันนี้เปิดร้านรับทรัพย์ ขอให้ออเดอร์เสื้อผ้าเด้งรัวๆ เลยน้าค๊าา ✨🚀🛍️"
        )
        print("\n===== REPORT =====")
        print(message)
        print("==================\n")
        send_telegram_message(message)
        return

    best_menu = menu_counter.most_common(1)[0]

    # 👗 ปรับธีมรายงานจาก "แก้ว" ให้เป็น "ตัว/ชิ้น" และใส่ฟอร์แมตเงินปัง ๆ
    message = (
        f"☀️ *Morning Report ร้าน StyleStudio* ☀️\n\n"
        f"📅 วันที่: {yesterday}\n"
        f"💰 ยอดขายแฟชั่นรวม: {total_sales:,.2f} บาท\n"
        f"🏆 สินค้าแฟชั่นขายดี: {best_menu[0]}\n"
        f"👗 จำนวนที่ขายได้: {best_menu[1]} ตัว/ชิ้น\n\n"
        f"วันนี้ขอให้ออเดอร์ถล่มทลาย ลูกค้าทักแชทแตกเลยนะค๊าาา 🚀✨🛍️"
    )

    print("\n===== REPORT =====")
    print(message)
    print("==================\n")

    send_telegram_message(message)


if __name__ == "__main__":
    generate_morning_report()