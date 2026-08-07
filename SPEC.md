# SPEC: Slide2Quiz (AI Quiz Generator)

## 1. แอปทำอะไร
Slide2Quiz เป็นเว็บแอปพลิเคชันที่ช่วยในการสร้างแบบทดสอบ (Quiz) จากสไลด์การเรียนการสอน โดยผู้ใช้เพียงแค่อัปโหลดรูปภาพสไลด์ (เช่น สไลด์วิชา Forensic Biology หรือ Physics) จากนั้นระบบจะใช้ AI วิเคราะห์เนื้อหาและสร้างคำถามแบบปรนัย 3 ข้อ พร้อมตัวเลือก เฉลย และคำอธิบายที่อ้างอิงจากรูปภาพนั้นอย่างแม่นยำ

## 2. Input / Output
- **Input:** 
  - ไฟล์รูปภาพ (Image) ของสไลด์เรียน (.png, .jpg)
  - Text Prompt ผ่านช่องแชท (ในกรณีที่ผู้ใช้พิมพ์ถาม-ตอบเพิ่มเติมในฟีเจอร์ Chat)
- **Output:** 
  - โครงสร้าง JSON ของแบบทดสอบ ประกอบด้วย คำถาม (Question), ตัวเลือก 4 ข้อ (Options), เฉลย (Correct Answer) และคำอธิบาย (Explanation) 
  - ข้อความแชทตอบกลับ (Text) อธิบายเนื้อหาเพิ่มเติม

## 3. การออกแบบ Prompt & System Instruction
- **System Instruction:**
  `You are an expert university professor. Your task is to analyze the provided educational slide image and generate a 3-question multiple-choice quiz based strictly on the content found in the image. Ensure the questions test concepts, not just rote memorization. Respond in Thai language.`
- **Prompt:**
  `Generate a quiz from this slide image.`