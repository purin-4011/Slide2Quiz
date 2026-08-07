import os
import json
import streamlit as st
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from PIL import Image

# โหลดตัวแปรจากไฟล์ .env
load_dotenv()

# กำหนด Schema สำหรับ Structured Output
class QuizQuestion(BaseModel):
    question: str = Field(description="ข้อความคำถาม")
    options: list[str] = Field(description="รายการตัวเลือก 4 ข้อ")
    correct_answer: str = Field(description="เฉลยข้อที่ถูกต้อง (ต้องตรงกับหนึ่งในตัวเลือก)")
    explanation: str = Field(description="คำอธิบายสั้นๆ ว่าทำไมข้อนี้ถึงถูก อ้างอิงจากเนื้อหา")

class QuizSummary(BaseModel):
    quiz: list[QuizQuestion]

# ตั้งค่าหน้าเว็บ
st.set_page_config(page_title="Slide2Quiz AI", page_icon="📝", layout="centered")
st.title("📝 Slide2Quiz: AI สร้างแบบทดสอบจากสไลด์และ PDF")

# ตรวจสอบ API Key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    st.warning("⚠️ ไม่พบ GEMINI_API_KEY ในไฟล์ .env โปรดใส่ API Key ด้านล่างเพื่อทดสอบ")
    api_key = st.text_input("Enter Gemini API Key", type="password")

if api_key:
    # ใช้งาน Gen AI SDK แบบใหม่ตาม Lab
    client = genai.Client(api_key=api_key)

    st.markdown('''
    **คุณสมบัติ:** สวมบทบาท (System Instruction) + รองรับรูปภาพและ PDF (Multimodality) + 
    บังคับ Output รูปแบบ JSON (Structured Output) + ระบบแชทถามต่อ (Multi-turn chat)
    ''')

    # เพิ่มให้รองรับไฟล์ PDF ใน file_uploader
    uploaded_file = st.file_uploader("อัปโหลดรูปภาพสไลด์เรียน หรือไฟล์เอกสาร (JPG, PNG, PDF)", type=["jpg", "jpeg", "png", "pdf"])

    if uploaded_file is not None:
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        # เตรียมเนื้อหา (Contents) ที่จะส่งให้ AI ตามประเภทไฟล์
        if file_extension == 'pdf':
            st.success(f"📄 อัปโหลดไฟล์ PDF สำเร็จ: {uploaded_file.name}")
            pdf_bytes = uploaded_file.read()
            # ใช้ Part.from_bytes สำหรับส่งไฟล์ PDF ให้ Gemini
            document_part = types.Part.from_bytes(data=pdf_bytes, mime_type='application/pdf')
            contents_to_send = [document_part, "Generate a quiz from this PDF document."]
        else:
            image = Image.open(uploaded_file)
            st.image(image, caption="รูปภาพที่อัปโหลด", use_container_width=True)
            contents_to_send = [image, "Generate a quiz from this slide image."]

        if st.button("🚀 สร้างแบบทดสอบ (Generate Quiz)"):
            with st.spinner("อาจารย์ AI กำลังวิเคราะห์ข้อมูล..."):
                try:
                    # 1. System Instruction (ปรับคำสั่งให้ครอบคลุมทั้ง slide และ document)
                    sys_inst = (
                        "You are an expert university professor. Your task is to analyze the provided "
                        "educational document or slide and generate a 3-question multiple-choice quiz based strictly "
                        "on the content found in it. Ensure the questions test concepts. Respond in Thai language."
                    )

                    # 2. Config & Structured Output (JSON) & Temperature
                    config = types.GenerateContentConfig(
                        system_instruction=sys_inst,
                        temperature=0.2, # อุณหภูมิต่ำเพื่อความแม่นยำ
                        response_mime_type="application/json",
                        response_schema=QuizSummary,
                    )

                    # 3. Multimodality (รูปภาพ/PDF + ข้อความ)
                    response = client.models.generate_content(
                        model='gemini-1.5-flash', 
                        contents=contents_to_send,
                        config=config
                    )

                    # แปลง JSON String เป็น Python Dictionary
                    quiz_data = json.loads(response.text)
                    st.session_state['quiz_data'] = quiz_data
                    st.session_state['chat_history'] = [] # ล้างประวัติแชทเมื่อเจนใหม่
                    
                except Exception as e:
                    st.error(f"เกิดข้อผิดพลาด: {e}")

    # แสดงผลแบบทดสอบ และระบบ Chat (Bonus)
    if 'quiz_data' in st.session_state:
        st.divider()
        st.subheader("🎯 แบบทดสอบของคุณ")
        
        for i, q in enumerate(st.session_state['quiz_data'].get('quiz', [])):
            st.markdown(f"**ข้อ {i+1}: {q['question']}**")
            for opt in q['options']:
                st.markdown(f"- {opt}")
            with st.expander("ดูเฉลย"):
                st.success(f"**เฉลย:** {q['correct_answer']}")
                st.info(f"**เหตุผล:** {q['explanation']}")
        
        # 4. Multi-turn chat (โจทย์เสริม DETERMINATION)
        st.divider()
        st.subheader("💬 สงสัยข้อไหน ถามอาจารย์ AI ต่อได้เลย (Multi-turn Chat)")
        
        # แสดงประวัติแชท
        for msg in st.session_state['chat_history']:
            with st.chat_message(msg["role"]):
                st.markdown(msg["text"])

        # ช่องกรอกแชท
        if prompt := st.chat_input("พิมพ์คำถาม เช่น 'ทำไมข้อ 1 ถึงตอบแบบนั้น?'"):
            with st.chat_message("user"):
                st.markdown(prompt)
            st.session_state['chat_history'].append({"role": "user", "text": prompt})
            
            with st.chat_message("model"):
                with st.spinner("กำลังพิมพ์..."):
                    # แนบ Context ข้อสอบไปด้วยเพื่อให้โมเดลรู้เรื่อง
                    chat_contents = [
                        "You are an expert tutor answering questions about this quiz you just generated: " + 
                        json.dumps(st.session_state['quiz_data'], ensure_ascii=False)
                    ]
                    # นำประวัติการคุยมาใส่ต่อกัน
                    for msg in st.session_state['chat_history']:
                        chat_contents.append(msg["text"])
                    
                    chat_config = types.GenerateContentConfig(temperature=0.4)
                    chat_response = client.models.generate_content(
                        model='gemini-1.5-flash',
                        contents=chat_contents,
                        config=chat_config
                    )
                    st.markdown(chat_response.text)
            st.session_state['chat_history'].append({"role": "model", "text": chat_response.text})