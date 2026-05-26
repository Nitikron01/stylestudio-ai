# StyleStudio - AI Personal Stylist 🛍️

ระบบผู้ช่วย AI ประจำร้านเสื้อผ้าแฟชั่นสไตล์มินิมอลและสตรีทแวร์ ที่ใช้เทคนิค Retrieval-Augmented Generation (RAG) ผสานพลังร่วมกับเวกเตอร์ฐานข้อมูลระดับสูง (FAISS) เพื่อตอบคำถามลูกค้าได้อย่างถูกต้อง ตรงประเด็น และไม่มีการเดาข้อมูลเอง (Anti-Hallucination)

## ฟีเจอร์หลักของระบบ
- **Fashion Expert FAQ:** ตอบข้อมูลชนิดเนื้อผ้า ราคา และสีสินค้าอย่างเป็นธรรมชาติ
- **Size Chart Matching:** บริการตรวจสอบตารางไซส์ รอบอก รอบเอว ความยาวเสื้อผ้า
- **Return Policy Guide:** ชี้แจงเงื่อนไขการเปลี่ยนไซส์สินค้าภายใน 7 วันอย่างแม่นยำ

## วิธีการติดตั้งและรันในเครื่อง (Local Setup)
1. ติดตั้งแพ็กเกจคอมโพเนนต์ที่จำเป็น:
   ```bash
   pip install streamlit google-genai sentence-transformers faiss-cpu python-dotenv