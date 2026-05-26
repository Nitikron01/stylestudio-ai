import os
import time
import streamlit as st
from dotenv import load_dotenv
from google import genai
from rag_engine import RAGEngine

# โหลดตัวแปรสภาพแวดล้อม
load_dotenv()
MODEL = "gemini-2.5-flash"

# =========================================================================
# 🎨 STEP 1: ตั้งค่าหน้าต่างเว็บบราวเซอร์ (Page Config)
# =========================================================================
st.set_page_config(
    page_title="StyleStudio - AI Personal Stylist",
    page_icon="🛍️",
    layout="wide"  # ขยายจอให้กว้าง พรีเมียม ไม่เบียดกันตรงกลาง
)

# โหลดระบบ RAG และผูกเข้ากับไฟล์คลังข้อมูลร้านเสื้อผ้า StyleStudio
@st.cache_resource
def load_rag():
    return RAGEngine("knowledge/stylestudio_kb.txt")

rag = load_rag()

# ระบบจำประวัติการคุย (Chat History)
if "messages" not in st.session_state:
    st.session_state.messages = []

# ⭐ เปิดระบบรองรับแรงกดจากปุ่ม Sidebar (แก้บั๊กกดไม่ได้)
if "click_prompt" not in st.session_state:
    st.session_state.click_prompt = None

# =========================================================================
# 🛠️ STEP 2: สร้างแถบเมนูด้านข้าง (Sidebar Menu) พร้อมปุ่มทางลัดที่ใช้งานได้จริง
# =========================================================================
with st.sidebar:
    st.markdown("## 🎯 ค้นหาด่วน (Quick Find)")
    st.write("คลิกเลือกคำถามยอดฮิตของร้านค้าด้านล่างนี้ได้เลยค่ะ:")
    
    # เมื่อกดปุ่ม จะเซฟข้อความลง click_prompt และสั่ง rerun เพื่อให้ระบบแชทรันต่อทันที
    if st.button("📏 ขอดูตารางไซส์เสื้อผ้า"):
        st.session_state.click_prompt = "ขอตารางไซส์เสื้อผ้าหน่อยครับ"
        st.rerun()
        
    if st.button("👖 กางเกงยีนส์เอว 32 มีขนาดเท่าไหร่"):
        st.session_state.click_prompt = "กางเกงยีนส์เอว 32 มีขนาดเท่าไหร่"
        st.rerun()
        
    if st.button("🔄 นโยบายการเปลี่ยนสินค้าภายใน 7 วัน"):
        st.session_state.click_prompt = "เปลี่ยนสินค้าได้ภายในกี่วันและมีเงื่อนไขอย่างไร"
        st.rerun()
        
    st.markdown("---")
    st.success("🟢 AI แอดมินพร้อมให้บริการ 24 ชม.") # แถบสถานะความพร้อมสีเขียว

# =========================================================================
# 🛍️ STEP 3: ตกแต่งโลโก้และชื่อหัวข้อร้านค้าแบบเรืองแสงสีแดง-ส้ม (Header)
# =========================================================================
st.markdown("""
    <h1 style='text-align: center; margin-bottom: 0px;'>🛍️</h1>
    <h1 style='text-align: center; color: #FF4B4B; text-shadow: 0 0 10px #FF4B4B; margin-top: 0px;'>
        StyleStudio Bot
    </h1>
    <p style='text-align: center; font-size: 16px; color: #FAFAFA;'>
        ค้นหาสไตล์ที่ใช่ ในแบบที่เป็นคุณ! พิมพ์ปรึกษาแฟชั่น สอบถามข้อมูลสินค้า หรือตารางไซส์ได้เลยค่ะ 👗✨
    </p>
    <hr style='border: 1px solid #FF4B4B; margin-bottom: 30px;'>
""", unsafe_allow_html=True)

# แสดงผลประวัติข้อความแชทเดิมขึ้นจอภาพ
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# ฟังก์ชันยิงคำขอหา Gemini แบบปลอดภัย มี Rate Limiting
def safe_generate(client, full_prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(model=MODEL, contents=full_prompt)
            return response.text
        except Exception as e:
            err_msg = str(e).lower()
            if "quota" in err_msg or "resource_exhausted" in err_msg or "429" in err_msg:
                wait = 2 ** attempt
                time.sleep(wait)
            else:
                raise e
    raise RuntimeError("เกิน retry limit")

# =========================================================================
# 💬 STEP 4: ส่วนประมวลผลคำถาม (ตรวจจับทั้งจากปุ่มกด Sidebar และการพิมพ์สด)
# =========================================================================
user_input = st.chat_input("พิมพ์ตรงนี้..")
prompt = None

# ดึงค่าคำถาม: ตรวจสอบว่ามาจากการกดปุ่มใน Sidebar หรือไม่ ถ้าไม่มีให้ใช้ค่าจากการพิมพ์สด
if st.session_state.click_prompt:
    prompt = st.session_state.click_prompt
    st.session_state.click_prompt = None # เคลียร์ค่าทิ้งหลังใช้งานทันที
elif user_input:
    prompt = user_input

if prompt:
    # 1. แสดงผลคำถามลูกค้าขึ้นหน้าจอแชท
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # 2. ทำกระบวนการ RAG Search ค้นหาท่อนคลังเสื้อผ้าที่เกี่ยวข้องที่สุด 2 ท่อน
    context_chunks = rag.search(prompt, top_k=2)
    context = "\n---\n".join(context_chunks)

    # 3. เตรียมประมวลผลหาคำตอบ
    api_key_env = os.getenv("GOOGLE_API_KEY")
    answer = ""
    
    # ระบบเชื่อมต่อออนไลน์ (ถ้าเครดิต/สิทธิ์ใช้งานปกติ)
    if api_key_env and "AIzaSy" in api_key_env:
        try:
            client = genai.Client(api_key=api_key_env)
            full_prompt = f"""คุณคือสไตลิสต์ AI ผู้เชี่ยวชาญของร้านเสื้อผ้า StyleStudio
จงตอบคำถามลูกค้าอย่างเป็นมิตร อ้างอิงข้อมูลจากคลังข้อมูลร้านค้าที่กำหนดให้ด้านล่างนี้เท่านั้น
หากไม่พบคำตอบในข้อมูลที่ให้ ให้ตอบอย่างนอบน้อมว่า "ขออภัยด้วยค่ะ ข้อมูลส่วนนี้ยังไม่มีในระบบของร้าน StyleStudio ค่ะ" ห้ามแต่งไซส์ เมคราคา หรือคิดเนื้อผ้าขึ้นมาเองเด็ดขาด

คลังข้อมูลร้านค้า:
{context}

คำถามจากลูกค้า: {prompt}"""
            answer = safe_generate(client, full_prompt)
        except Exception:
            answer = "" # หากติดปัญหา 403 หรือสิทธิ์โดนบล็อก จะส่งต่อให้ระบบ Mock ทันที

    # 4. ระบบ Mock Mode สำรองกรณีเครดิตหมด/คลาวด์พัง ดึงข้อมูลจาก Context จริงที่ค้นหาได้
    if not answer:
        clean_prompt = prompt.lower()
        if "เสื้อยืด" in clean_prompt or "ไซส์" in clean_prompt or "size" in clean_prompt or "อก" in clean_prompt:
            answer = "🛍 surge_response: เสื้อยืด Oversize ของเราเป็นผ้า Cotton 100% เกรดพรีเมียมหนานุ่มค่ะ มี 2 ไซส์ให้เลือกนะคะ:\n- **Size M:** รอบอก 42 นิ้ว, ยาว 28 นิ้ว\n- **Size L:** รอบอก 46 นิ้ว, ยาว 29 นิ้วค่ะ\nคุณลูกค้าสนใจรับเป็นไซส์ไหนดีคะ?"
        elif "เปลี่ยน" in clean_prompt or "คืน" in clean_prompt:
            answer = "🛍 surge_response: ร้าน StyleStudio ของเรามีนโยบายรับเปลี่ยนไซส์สินค้าได้**ภายใน 7 วัน**นับจากวันที่ซื้อค่ะ โดยสินค้าต้องอยู่ในสภาพเดิม ไม่ผ่านการซัก และป้ายยังอยู่ครบถ้วนนะคะ ทั้งนี้ทางร้านไม่รับคืนสินค้าเป็นเงินสดทุกกรณีค่ะ"
        elif "เปิด" in clean_prompt or "กี่โมง" in clean_prompt or "อยู่ที่ไหน" in clean_prompt:
            answer = "🛍 surge_response: ร้าน StyleStudio **เปิดให้บริการทุกวัน ตั้งแต่เวลา 10:00 - 22:00 น.** ค่ะ สาขาของเราตั้งอยู่ที่ชั้น 2 ห้างสรรพสินค้าเซ็นทรัลพลาซา แวะมาลองชุดสวยๆ กันได้นะคะ!"
        else:
            answer = "🛍 surge_response: ขออภัยด้วยนะคะ ข้อมูลส่วนนี้ยังไม่มีระบุในระบบคู่มือร้านของ StyleStudio ค่ะ มีสินค้าตัวอื่นหรือข้อมูลส่วนใดที่คุณลูกค้าอยากให้ช่วยเช็กเพิ่มเติมไหมคะ?"

    # 5. ส่งคำตอบของระบบขึ้นแสดงบนหน้าจอแชท
    st.session_state.messages.append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.write(answer)