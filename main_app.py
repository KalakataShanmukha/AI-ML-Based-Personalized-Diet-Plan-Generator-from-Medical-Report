import streamlit as st
import pandas as pd
import pdfplumber
import pytesseract
from PIL import Image
import spacy

# -------------------- PAGE CONFIG --------------------
st.set_page_config(
    page_title="MyDiet_AI",
    page_icon="🍎",
    layout="centered"
)

st.title("🍎 MyDiet_AI")
st.caption("AI-based Personalized Diet Recommendation System")
st.markdown("---")

# -------------------- LOAD NLP SAFELY --------------------
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
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

    elif ext in ["png", "jpg", "jpeg"]:
        try:
            img = Image.open(uploaded_file)
            text = pytesseract.image_to_string(img)
        except Exception:
            text = "⚠️ Image OCR is not supported here. Please upload PDF / TXT / CSV files or paste text manually."

    elif ext == "txt":
        text = uploaded_file.read().decode("utf-8")

    elif ext == "csv":
        df = pd.read_csv(uploaded_file)
        if "doctor_prescription" in df.columns:
            text = df["doctor_prescription"].iloc[0]
        else:
            text = "⚠️ CSV file does not contain 'doctor_prescription' column."

    return text.strip()

# -------------------- DIET LOGIC --------------------
def generate_diet(text):
    diet = {
        "condition": [],
        "allowed_foods": ["vegetables", "whole grains", "fruits"],
        "restricted_foods": [],
        "diet_plan": [],
        "lifestyle_advice": []
    }

    text = text.lower()

    if "diabetes" in text:
        diet["condition"].append("Diabetes")
        diet["restricted_foods"].append("sugar")
        diet["diet_plan"].append("Follow a diabetic-friendly low sugar diet.")
        diet["lifestyle_advice"].append("Walk daily for 30 minutes.")

    if "cholesterol" in text:
        diet["condition"].append("High Cholesterol")
        diet["restricted_foods"].append("oily food")
        diet["diet_plan"].append("Increase fiber intake and avoid fried foods.")

    if "blood pressure" in text or "hypertension" in text:
        diet["condition"].append("Hypertension")
        diet["restricted_foods"].append("salt")
        diet["diet_plan"].append("Reduce sodium intake.")
        diet["lifestyle_advice"].append("Practice stress management.")

    if not diet["condition"]:
        diet["condition"].append("General Health")
        diet["diet_plan"].append("Maintain a balanced diet.")
        diet["lifestyle_advice"].append("Stay active and hydrated.")

    return {
        "condition": ", ".join(diet["condition"]),
        "allowed_foods": list(set(diet["allowed_foods"])),
        "restricted_foods": list(set(diet["restricted_foods"])),
        "diet_plan": " ".join(diet["diet_plan"]),
        "lifestyle_advice": " ".join(diet["lifestyle_advice"])
    }

# -------------------- USER INPUT UI --------------------
st.subheader("📄 Upload Medical Report")
uploaded_file = st.file_uploader(
    "Upload PDF / Image / TXT / CSV",
    type=["pdf", "png", "jpg", "jpeg", "txt", "csv"]
)

exp = st.expander("📝 Doctor's Prescription (optional)")
with exp:
    manual_text = st.text_area("Paste doctor prescription text here", height=150)

process_btn = st.button("🔍 Generate Diet Recommendation")

# -------------------- PIPELINE EXECUTION --------------------
if process_btn:
    st.success("✅ Processing input...")

    if uploaded_file:
        text = extract_text(uploaded_file)
    else:
        text = manual_text.strip()

    st.subheader("📝 Extracted Text")
    st.write(text[:1000])

    st.subheader("🩺 Health Status")
    st.info("Health condition inferred using medical text analysis.")

    diet = generate_diet(text)

    st.subheader("🍽️ Personalized Diet Recommendation")
    # Display in cards style
    st.markdown(f"**Condition:** {diet['condition']}")
    st.markdown(f"**✅ Allowed Foods:** {', '.join(diet['allowed_foods'])}")
    st.markdown(f"**❌ Restricted Foods:** {', '.join(diet['restricted_foods'])}")
    st.markdown(f"**🍽 Diet Plan:** {diet['diet_plan']}")
    st.markdown(f"**🏃 Lifestyle Advice:** {diet['lifestyle_advice']}")

    st.download_button(
        label="⬇️ Download Diet Plan (JSON)",
        data=pd.Series(diet).to_json(),
        file_name="diet_plan.json",
        mime="application/json"
    )

# -------------------- CUSTOM CSS --------------------
st.markdown(
    """
    <style>
    .stApp {
        background: url('https://images.unsplash.com/photo-1506806732259-39c2d0268443?auto=format&fit=crop&w=1470&q=80');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    section.main > div {
        background-color: rgba(255, 255, 255, 0.95);
        padding: 2rem;
        border-radius: 18px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
    }
    h1, h2, h3 {
        color: #1b5e20;
    }
    .stButton > button {
        background-color: #2e7d32;
        color: white;
        border-radius: 10px;
        padding: 0.6em 1.2em;
        font-weight: 600;
    }
    .stButton > button:hover {
        background-color: #1b5e20;
        color: white;
    }
    </style>
    """,
    unsafe_allow_html=True
)