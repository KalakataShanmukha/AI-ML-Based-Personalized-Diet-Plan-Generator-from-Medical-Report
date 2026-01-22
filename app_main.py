import streamlit as st
import pandas as pd
import pdfplumber
import pytesseract
from PIL import Image, ImageDraw, ImageFont
import io
import textwrap
import spacy
import json
import random
from pathlib import Path
from joblib import load

from Utils.Extraction import extract_text as util_extract_text
from Utils.Diet_generator import generate_diet as util_generate_diet


# -------------------- SAFE ML PREDICTION --------------------
def safe_predict_condition(numeric_data):
    try:
        model_path = Path(__file__).resolve().parent / "ML_model" / "ML_model.pkl"
        model = load(str(model_path))
        features = ["age", "glucose", "cholesterol", "blood_pressure", "bmi"]
        X = pd.DataFrame([[numeric_data[f] for f in features]], columns=features)
        pred = model.predict(X)[0]
        return "Abnormal" if int(pred) == 1 else "Normal"
    except Exception:
        return None


# -------------------- PAGE CONFIG --------------------
st.set_page_config(
    page_title="AI_DietPlanner",
    page_icon="🥗",
    layout="wide"
)


# -------------------- STYLES --------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Poppins', sans-serif;
}

/* Background */
.stApp {
    background-image: url("https://d1csarkz8obe9u.cloudfront.net/posterpreviews/powerpoint-healthy-fruits-background-design-template-32ec152ef88b2fa8e280d9832e6bb0ff_screen.jpg");
    background-size: cover;
    background-attachment: fixed;
    background-repeat: no-repeat;
}

/* Glass Card */
.glass-card {
    background: rgba(255, 255, 255, 0.82);
    backdrop-filter: blur(10px);
    border-radius: 20px;
    padding: 1.5rem;
    box-shadow: 0 12px 30px rgba(0,0,0,0.08);
    margin-bottom: 1.5rem;
}

.glass-card h3 {
    color: #2c3e50;
    margin-bottom: 0.8rem;
}

button {
    border-radius: 30px !important;
    padding: 0.6rem 1.8rem !important;
    font-weight: 600 !important;
}
</style>
""", unsafe_allow_html=True)


# -------------------- HEADER --------------------
st.markdown("""
<div class="glass-card" style="text-align:center;">
    <h1>🥗 AI_DietPlanner</h1>
    <p>AI-based Personalized Diet Recommendation System</p>
</div>
""", unsafe_allow_html=True)


# -------------------- LOAD NLP --------------------
@st.cache_resource
def load_spacy():
    nlp = spacy.blank("en")
    nlp.add_pipe("sentencizer")
    return nlp

nlp = load_spacy()


# -------------------- USER INPUT --------------------
st.markdown("## 📄 Upload Medical Report")

uploaded_file = st.file_uploader(
    "Supported formats: PDF, JPG, PNG, TXT, CSV",
    type=["pdf", "png", "jpg", "jpeg", "txt", "csv"]
)

process_btn = st.button("✨ Generate Diet Plan")


# -------------------- MEAL PLAN LOGIC --------------------
def generate_meal_plan(has_diabetes, has_cholesterol):
    plans = {
        "Breakfast": [
            "Oats porridge with fruits",
            "Vegetable upma",
            "Idli with sambar",
            "Poha with vegetables",
            "Ragi dosa"
        ],
        "Lunch": [
            "Brown rice with dal and vegetables",
            "Chapati with mixed veg curry",
            "Millet khichdi",
            "Quinoa salad",
            "Vegetable pulao"
        ],
        "Snack": [
            "Fruit bowl",
            "Roasted chana",
            "Sprouts salad",
            "Yogurt with seeds",
            "Nuts and seeds"
        ],
        "Dinner": [
            "Vegetable soup",
            "Light salad",
            "Chapati with dal",
            "Stir-fried vegetables",
            "Khichdi"
        ]
    }

    week = []
    for i in range(7):
        week.append({
            "breakfast": random.choice(plans["Breakfast"]),
            "lunch": random.choice(plans["Lunch"]),
            "snack": random.choice(plans["Snack"]),
            "dinner": random.choice(plans["Dinner"])
        })
    return week


# -------------------- PDF GENERATION --------------------
def meal_plan_pdf(plan):
    font = ImageFont.load_default()
    width, height = 800, 1100
    margin = 40
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    y = margin
    for i, day in enumerate(plan, 1):
        lines = [
            f"Day {i}",
            f"Breakfast: {day['breakfast']}",
            f"Lunch: {day['lunch']}",
            f"Snack: {day['snack']}",
            f"Dinner: {day['dinner']}",
            ""
        ]
        for line in lines:
            draw.text((margin, y), line, fill="black", font=font)
            y += 22

    buf = io.BytesIO()
    img.save(buf, format="PDF")
    return buf.getvalue()


# -------------------- PIPELINE --------------------
if process_btn:
    if not uploaded_file:
        st.warning("Please upload a medical report to continue.")
        st.stop()

    with st.spinner("🔍 Analyzing medical report..."):
        text, numeric_data = util_extract_text(uploaded_file)
        diet = util_generate_diet(text)
        ml_pred = safe_predict_condition(numeric_data)

    # -------------------- RESULTS --------------------
    st.markdown("## 🩺 Health Analysis")
    st.markdown(f"""
    <div class="glass-card">
        <p><b>Detected Condition:</b> {diet['condition']}</p>
        {f"<p><b>ML Risk Assessment:</b> {ml_pred}</p>" if ml_pred else ""}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("## 🍽 Dietary Recommendations")

    st.markdown(f"""
    <div class="glass-card">
        <h3>✅ Foods to Include</h3>
        <ul>{"".join(f"<li>{x}</li>" for x in diet["allowed_foods"])}</ul>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="glass-card">
        <h3>❌ Foods to Avoid</h3>
        <ul>{"".join(f"<li>{x}</li>" for x in diet["restricted_foods"])}</ul>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="glass-card">
        <h3>💡 Lifestyle Advice</h3>
        <p>{diet["diet_plan"]}</p>
        <p>{diet["lifestyle_advice"]}</p>
    </div>
    """, unsafe_allow_html=True)

    # -------------------- MEAL PLAN --------------------
    has_d = "diabetes" in diet["condition"].lower()
    has_c = "cholesterol" in diet["condition"].lower()
    plan = generate_meal_plan(has_d, has_c)

    st.markdown("## 📅 7-Day Meal Plan")

    for i, day in enumerate(plan, 1):
        st.markdown(f"""
        <div class="glass-card">
            <h3>Day {i}</h3>
            <p><b>Breakfast:</b> {day['breakfast']}</p>
            <p><b>Lunch:</b> {day['lunch']}</p>
            <p><b>Snack:</b> {day['snack']}</p>
            <p><b>Dinner:</b> {day['dinner']}</p>
        </div>
        """, unsafe_allow_html=True)

    # -------------------- DOWNLOADS --------------------
    st.markdown("## 📥 Download")

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "📄 Download PDF",
            data=meal_plan_pdf(plan),
            file_name="diet_plan.pdf",
            mime="application/pdf"
        )
    with col2:
        st.download_button(
            "📥 Download JSON",
            data=json.dumps({"diet": diet, "meal_plan": plan}, indent=2),
            file_name="diet_plan.json",
            mime="application/json"
        )