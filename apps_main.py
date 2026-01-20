import streamlit as st
import pandas as pd
import pdfplumber
import pytesseract
from PIL import Image
from fpdf import FPDF
import spacy
import io

# -------------------- PAGE CONFIG --------------------
st.set_page_config(
    page_title="AI_DietPlanner",
    page_icon="🥗",
    layout="centered"
)

# -------------------- TITLE --------------------
st.markdown("""
<h1 style='text-align:center;'>🥗 AI_DietPlanner</h1>
<p style='text-align:center;color:gray;'>
AI-based Personalized Diet Recommendation System
</p>
<hr>
""", unsafe_allow_html=True)

# -------------------- LOAD NLP --------------------
@st.cache_resource
def load_spacy():
    nlp = spacy.blank("en")
    nlp.add_pipe("sentencizer")
    return nlp

nlp = load_spacy()

# -------------------- TEXT EXTRACTION --------------------
def extract_text(uploaded_file):
    ext = uploaded_file.name.split(".")[-1].lower()
    text = ""

    if ext == "pdf":
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                if page.extract_text():
                    text += page.extract_text() + "\n"

    elif ext in ["png", "jpg", "jpeg"]:
        img = Image.open(uploaded_file)
        text = pytesseract.image_to_string(img)

    elif ext == "txt":
        text = uploaded_file.read().decode("utf-8")

    elif ext == "csv":
        df = pd.read_csv(uploaded_file)
        if "doctor_prescription" in df.columns:
            text = df["doctor_prescription"].iloc[0]

    return text.strip()

# -------------------- DIET LOGIC --------------------
def generate_diet(text):
    diet = {
        "condition": [],
        "allowed": ["Vegetables", "Whole grains", "Fruits"],
        "restricted": [],
        "diet": [],
        "lifestyle": []
    }

    text = text.lower()

    if "diabetes" in text:
        diet["condition"].append("Diabetes")
        diet["restricted"].append("Sugar")
        diet["diet"].append("Follow a diabetic-friendly low sugar diet.")
        diet["lifestyle"].append("Walk daily for 30 minutes.")

    if "cholesterol" in text:
        diet["condition"].append("High Cholesterol")
        diet["restricted"].append("Oily food")
        diet["diet"].append("Increase fiber intake.")

    if "blood pressure" in text or "hypertension" in text:
        diet["condition"].append("Hypertension")
        diet["restricted"].append("Salt")
        diet["diet"].append("Reduce sodium intake.")
        diet["lifestyle"].append("Practice stress management.")

    if not diet["condition"]:
        diet["condition"].append("General Health")
        diet["diet"].append("Maintain a balanced diet.")
        diet["lifestyle"].append("Stay active.")

    return diet

# -------------------- INPUT --------------------
st.subheader("📄 Upload Medical Report")
uploaded_file = st.file_uploader(
    "Upload PDF / Image / TXT / CSV",
    type=["pdf", "png", "jpg", "jpeg", "txt", "csv"]
)

process_btn = st.button("🍽 Generate Diet Recommendation")

# -------------------- OUTPUT --------------------
if process_btn and uploaded_file:
    text = extract_text(uploaded_file)
    diet = generate_diet(text)

    # ---------- Display Extracted Text ----------
    st.markdown(f"""
    <div class='card'>
        <h4>📄 Extracted Text</h4>
        <p>{text[:800]}</p>
    </div>
    """, unsafe_allow_html=True)

    # ---------- Display Diet Recommendation ----------
    diet_text = f"""
❤️ Condition: {', '.join(diet['condition'])}
✅ Allowed Foods: {', '.join(diet['allowed'])}
❌ Restricted Foods: {', '.join(set(diet['restricted']))}
🥗 Diet Plan: {' '.join(diet['diet'])}
🏃 Lifestyle Advice: {' '.join(diet['lifestyle'])}
"""

    st.markdown(f"""
    <div class='card'>
        <h4>🍽 Personalized Diet Recommendation</h4>
        <pre>{diet_text}</pre>
    </div>
    """, unsafe_allow_html=True)

    # ---------- GENERATE PDF ----------
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "AI DietPlanner Recommendation", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", '', 12)
    for line in diet_text.split("\n"):
        pdf.multi_cell(0, 8, line)
    pdf_output = io.BytesIO()
    pdf.output(pdf_output)
    pdf_output.seek(0)

    st.download_button(
        label="📥 Download Diet PDF",
        data=pdf_output,
        file_name="diet_recommendation.pdf",
        mime="application/pdf"
    )

# -------------------- CSS --------------------
st.markdown("""
<style>
.stApp {
    background-image: url("https://images.unsplash.com/photo-1571044029871-9fda3a7e6f92?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=1080");
    background-size: cover;
    background-attachment: fixed;
}
.stApp::before {
    content: "";
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    background: rgba(255, 255, 255, 0.35);
    z-index: -1;
}
.card {
    background: rgba(255,255,255,0.95);
    padding: 20px;
    margin-top: 15px;
    border-radius: 14px;
    box-shadow: 0px 4px 14px rgba(0,0,0,0.1);
}
h4 {
    color: #2e7d32;
}
.stButton>button {
    background-color: #2e7d32;
    color: white;
    font-weight: bold;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)
