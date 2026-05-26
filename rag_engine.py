# rag_engine.py
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

class RAGEngine:
    def __init__(self, kb_file_path):
        # 1. โหลดโมเดลแปลงข้อความเป็นเวกเตอร์ภาษาไทย-อังกฤษ
        self.encoder = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        self.chunks = []
        
        # 2. อ่านไฟล์คู่มือร้านเสื้อผ้าและตัดท่อนข้อมูลแยกกันเมื่อเว้นบรรทัด
        with open(kb_file_path, "r", encoding="utf-8") as f:
            content = f.read()
            raw_chunks = content.split("\n\n")
            self.chunks = [chunk.strip() for chunk in raw_chunks if chunk.strip()]
        
        # 3. สร้างเวกเตอร์จากคำในคู่มือร้าน
        embeddings = self.encoder.encode(self.chunks)
        
        # 4. สรรสร้างฐานข้อมูล Vector DB แบบความแม่นยำสูง L2 ด้วย FAISS
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(np.array(embeddings).astype('float32'))

    def search(self, query, top_k=2):
        # ค้นหาท่อนข้อความที่ใกล้เคียงกับเจตนาลูกค้าที่สุด
        query_vector = self.encoder.encode([query])
        distances, indices = self.index.search(np.array(query_vector).astype('float32'), top_k)
        
        results = []
        for idx in indices[0]:
            if idx < len(self.chunks) and idx >= 0:
                results.append(self.chunks[idx])
        return results