# agent_tools.py
from datetime import datetime

# 📦 สร้างคลังเก็บข้อมูลออร์เดอร์สะสมจำลอง (In-Memory Database)
# ทุกครั้งที่มีการสั่งซื้อสำเร็จ ข้อมูลจะถูกนำมาเก็บรวมกันในกล่องนี้
SALES_DATABASE = []

def validate_sale(menu: str, quantity: int, price: float) -> None:
    """Guardrails: raise ValueError แจ้งเตือนถ้าข้อมูลไม่ถูกต้องป้องกันข้อมูลขยะ"""
    if not menu or not menu.strip():
        raise ValueError("ชื่อเมนูสินค้าห้ามว่าง")
    if quantity <= 0:
        raise ValueError("จำนวนต้องมากกว่า 0")
    if price <= 0:
        raise ValueError("ราคาต้องมากกว่า 0")

def log_sale(menu: str, quantity: int, price: float) -> dict:
    """บันทึกยอดขายลงคลังสะสม เพื่อเตรียมเอาไว้คำนวณและสรุปยอด"""
    # วิ่งผ่านด่านตรวจ Guardrails ก่อน
    validate_sale(menu, quantity, price)
    
    total = quantity * price
    sale_record = {
        "menu": menu,
        "quantity": quantity,
        "price": price,
        "total": total,
        "timestamp": datetime.now().isoformat(),
    }
    
    # ⭐ เอาประวัติการขายชิ้นนี้ไปสะสมลงในคลังกลางของร้านค้ารวมกันไว้
    SALES_DATABASE.append(sale_record)
    
    return {
        "status": "success",
        "message": f"🛍️ บันทึกรายการขาย {menu} จำนวน {quantity} ชิ้น เรียบร้อยแล้วค่ะ",
        "data": sale_record
    }

# ⭐ ฟังก์ชันสำหรับสรุปยอดขายทั้งหมด (ตัวนี้แหละที่ Telegram/Harness จะมาดึงไปโชว์)
def get_sales_summary() -> str:
    """ดึงข้อมูลจากคลังสะสมมาคำนวณบวกเลขรวม เพื่อแสดงรายงานผู้บริหาร"""
    if not SALES_DATABASE:
        return "📊 **[StyleStudio รายงาน]**\nขณะนี้ยังไม่มีรายการยอดขายของวันนี้เข้ามาในระบบค่ะ"
        
    total_sales = sum(order["total"] for order in SALES_DATABASE)
    total_items = sum(order["quantity"] for order in SALES_DATABASE)
    
    # จัดหน้าตารายงานสรุปส่งกลับไปให้สวยงาม
    report = "🛍️ **[StyleStudio หลังบ้าน]**\n"
    report += "📊 **รายงานสรุปยอดขายประจำวันนี้**\n"
    report += "--------------------------------------\n"
    for order in SALES_DATABASE:
        report += f"🔹 {order['menu']} x{order['quantity']} -> {order['total']:,} บาท\n"
    report += "--------------------------------------\n"
    report += f"💰 **ยอดขายรวมทั้งหมด:** {total_sales:,} บาท\n"
    report += f"📦 **จำนวนสินค้าที่ขายได้:** {total_items} ชิ้น\n"
    report += "🟢 สถานะฐานข้อมูลหลังบ้าน: ปกติ"
    return report

# คลังรวมเครื่องมือทั้งหมดที่ระบบอนุญาตให้ AI หรือระบบภายนอกสั่งใช้งานได้
TOOLS = {
    "log_sale": log_sale,
    "get_sales_summary": get_sales_summary, # ⭐ ลงทะเบียนเครื่องมือสรุปยอดขายเข้าคลังหลัก
}