import streamlit as st
import pandas as pd
import pdfplumber
import pytesseract
from PIL import Image
import spacy

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


process_btn = st.button("🍽 Generate Diet Recommendation")

# -------------------- OUTPUT --------------------
if process_btn:
    text = extract_text(uploaded_file) if uploaded_file else manual_text

    diet = generate_diet(text)

    # ---------- Extracted Text ----------
    st.markdown("""
    <div class='card'>
        <h4>📄 Extracted Text</h4>
        <p>{}</p>
    </div>
    """.format(text[:800]), unsafe_allow_html=True)

    # ---------- Health Status ----------
    st.markdown("""
    <div class='card'>
        <h4>🩺 Health Status</h4>
        <p>Health condition inferred using medical text analysis.</p>
    </div>
    """, unsafe_allow_html=True)

    # ---------- Diet Recommendation ----------
    st.markdown("""
    <div class='card'>
        <h4>🍽 Personalized Diet Recommendation</h4>

        <b>❤️ Condition</b>
        <p>{}</p>

        <b>✅ Allowed Foods</b>
        <p>{}</p>

        <b>❌ Restricted Foods</b>
        <p>{}</p>

        <b>🥗 Diet Plan</b>
        <p>{}</p>

        <b>🏃 Lifestyle Advice</b>
        <p>{}</p>
    </div>
    """.format(
        ", ".join(diet["condition"]),
        ", ".join(diet["allowed"]),
        ", ".join(set(diet["restricted"])),
        " ".join(diet["diet"]),
        " ".join(diet["lifestyle"])
    ), unsafe_allow_html=True)

# -------------------- CSS --------------------
st.markdown("""
<style>
.stApp {
    background-image: url("");
    background-size: cover;
    background-attachment: fixed;
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