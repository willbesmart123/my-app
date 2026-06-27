import streamlit as st
import os
from groq import Groq
import PyPDF2
from PIL import Image
import pytesseract
from datetime import datetime
import base64

# --- API кілтін жүктеу ---
try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("❌ API кілті табылмады. .env файлын тексеріңіз.")
    st.stop()

# --- Клиент ---
client = Groq(api_key=api_key)

# --- Бет ---
st.set_page_config(page_title="Мәтінді мазмұндау", layout="centered")
st.title("📄 Мәтінді қысқаша мазмұндаушы")
st.markdown("Groq-тың көмегімен мәтінді қысқа әрі түсінікті етіп беремін.")

# --- Файл жүктеу ---
uploaded_file = st.file_uploader(
    "📂 PDF, JPG, PNG жүктеңіз",
    type=["pdf", "jpg", "jpeg", "png"]
)

# --- Мәтін енгізу ---
user_input = st.text_area("✍️ Немесе мәтінді енгізіңіз:", height=150)

# --- Мәтінді оқу функциясы ---
def extract_text(file):
    try:
        if file.type == "application/pdf":
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text
        elif file.type.startswith("image/"):
            image = Image.open(file)
            return pytesseract.image_to_string(image, lang="kaz+rus+eng")
    except Exception as e:
        return None
    return None

# --- Негізгі мәтін ---
main_text = ""
if uploaded_file:
    with st.spinner("Оқылуда..."):
        text = extract_text(uploaded_file)
        if text:
            main_text = text[:4000]
            st.success(f"✅ {len(main_text)} таңба оқылды")
        else:
            st.warning("Файлдан мәтін оқылмады")
elif user_input.strip():
    main_text = user_input.strip()[:4000]

if not main_text:
    st.info("👆 Файл жүктеңіз немесе мәтінді енгізіңіз")
    st.stop()

# --- Параметрлер ---
col1, col2 = st.columns(2)
with col1:
    option = st.selectbox("📝 Түрі:", ("Қысқаша түйін", "Негізгі ойлар", "Бір абзац"))
with col2:
    lang = st.selectbox("🌐 Тілі:", ("Қазақша", "Орысша", "Ағылшынша"))

# --- Батырма ---
if st.button("🚀 Мазмұндау", type="primary", use_container_width=True):
    with st.spinner("🤖 Өңделуде..."):
        try:
            lang_map = {"Қазақша": "қазақ тілінде", "Орысша": "орыс тілінде", "Ағылшынша": "ағылшын тілінде"}
            inst = lang_map[lang]
            
            if option == "Қысқаша түйін":
                prompt = f"Қысқаша мазмұнда ({inst}): {main_text}"
            elif option == "Негізгі ойлар":
                prompt = f"Негізгі ойларды тізімде ({inst}): {main_text}"
            else:
                prompt = f"Бір абзацқа жинақта ({inst}): {main_text}"
            
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500
            )
            
            result = response.choices[0].message.content
            
            st.success("✅ Дайын!")
            st.markdown(result)
            
            # --- TXT сақтау ---
            b64 = base64.b64encode(result.encode('utf-8')).decode()
            st.markdown(
                f'<a href="data:text/plain;base64,{b64}" download="mazmunda_{datetime.now().strftime("%H%M")}.txt">📥 TXT жүктеп алу</a>',
                unsafe_allow_html=True
            )
            
        except Exception as e:
            st.error(f"❌ Қате: {e}")
