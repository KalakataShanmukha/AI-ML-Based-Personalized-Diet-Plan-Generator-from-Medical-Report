import streamlit as st
import pandas as pd
import pdfplumber
import pytesseract
from PIL import Image
import spacy
import json
import random
import re
import io
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

# -------------------- PAGE CONFIG --------------------
st.set_page_config(
    page_title="AI_DietPlanner",
    page_icon="🥗",
    layout="centered"
)

# -------------------- GLOBAL CSS --------------------
st.markdown("""
<style>
.stApp {
    background-image: url("https://images.freeimages.com/images/large-previews/4a5/fruit-background-1638569.jpg");
    background-size: cover;
    background-attachment: fixed;
}

/* Card Styling */
.diet-card {
    background: rgba(255, 255, 255, 0.92);
    border-radius: 16px;
    padding: 16px;
    margin-bottom: 20px;
    box-shadow: 0 6px 14px rgba(0,0,0,0.2);
}

.card-header {
    background: linear-gradient(90deg, #66BB6A, #2E7D32);
    padding: 10px;
    border-radius: 12px;
    color: white;
    font-weight: bold;
    text-align: center;
    margin-bottom: 12px;
}

.meal {
    margin: 6px 0;
    font-size: 15px;
}
.meal span {
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# -------------------- TITLE --------------------
st.markdown("""
<div style="
    background: linear-gradient(90deg, #4CAF50, #2E7D32);
    padding: 20px;
    border-radius: 14px;
    text-align: center;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    margin-bottom: 25px;
">
    <h1 style="color:white;margin:0;">🥗 AI_DietPlanner</h1>
    <p style="color:#E8F5E9;margin-top:6px;">
        AI-based Personalized Diet Recommendation System
    </p>
</div>
""", unsafe_allow_html=True)

# -------------------- LOAD NLP --------------------
@st.cache_resource
def load_spacy():
    return spacy.blank("en")

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
        text = df.to_string()

    return text.strip()

# -------------------- PATIENT INFO --------------------
def extract_patient_info(text):
    name = "Not Found"
    age = "Not Found"

    name_match = re.search(r"Name[:\-]?\s*([A-Za-z ]+)", text, re.I)
    age_match = re.search(r"Age[:\-]?\s*(\d{1,3})", text)

    if name_match:
        name = name_match.group(1).strip()
    if age_match:
        age = age_match.group(1)

    return name, age

# -------------------- DIET GENERATION --------------------
def generate_diet(text, category):
    text = text.lower()

    if "diabetes" in text:
        condition = "Diabetes"
        avoid = ["Sugar", "White rice", "Soft drinks"]
    elif "blood pressure" in text or "hypertension" in text:
        condition = "Hypertension"
        avoid = ["Salt", "Pickles", "Processed food"]
    elif "cholesterol" in text:
        condition = "High Cholesterol"
        avoid = ["Fried food", "Butter", "Red meat"]
    else:
        condition = "General Health"
        avoid = ["Junk food"]

    lifestyle = [
        "Exercise 30 minutes daily",
        "Drink 2–3 liters of water",
        "Sleep 7–8 hours"
    ]

    meals = {
        "Breakfast": ["Oats", "Idli", "Dosa", "Poha", "Smoothie", "Upma", "Toast"],
        "Lunch": ["Dal Rice", "Chapati Curry", "Khichdi", "Quinoa Bowl", "Paneer", "Veg Biryani", "Salad"],
        "Snacks": ["Fruits", "Nuts", "Sprouts", "Yogurt", "Protein Shake", "Seeds", "Boiled Eggs"],
        "Dinner": ["Soup", "Salad", "Grilled Veg", "Tofu", "Paneer", "Zoodles", "Light Curry"]
    }

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    df = pd.DataFrame({
        "Day": days,
        "Breakfast": random.sample(meals["Breakfast"], 7),
        "Lunch": random.sample(meals["Lunch"], 7),
        "Snacks": random.sample(meals["Snacks"], 7),
        "Dinner": random.sample(meals["Dinner"], 7)
    })

    return condition, avoid, lifestyle, df

# -------------------- USER INPUT --------------------
uploaded_file = st.file_uploader(
    "📄 Upload Medical Report",
    type=["pdf", "png", "jpg", "jpeg", "txt", "csv"]
)

category = st.selectbox("🥦 Select Diet Type", ["Veg", "Non-Veg"])

if st.button("🍽 Generate Diet Plan") and uploaded_file:
    text = extract_text(uploaded_file)
    name, age = extract_patient_info(text)
    condition, avoid, lifestyle, diet_df = generate_diet(text, category)

    st.subheader("👤 Patient Information")
    st.write(f"**Name:** {name}")
    st.write(f"**Age:** {age}")
    st.write(f"**Condition:** {condition}")
    st.write(f"**Diet Type:** {category}")

    st.subheader("📅 7-Day Diet Plan")

    # -------------------- CARD DISPLAY (2 PER ROW) --------------------
    for i in range(0, len(diet_df), 2):
        col1, col2 = st.columns(2)

        for col, idx in zip([col1, col2], [i, i+1]):
            if idx < len(diet_df):
                row = diet_df.iloc[idx]
                with col:
                    st.markdown(f"""
                    <div class="diet-card">
                        <div class="card-header">📆 {row['Day']}</div>
                        <div class="meal">🍳 <span>Breakfast:</span> {row['Breakfast']}</div>
                        <div class="meal">🍛 <span>Lunch:</span> {row['Lunch']}</div>
                        <div class="meal">☕ <span>Snacks:</span> {row['Snacks']}</div>
                        <div class="meal">🌙 <span>Dinner:</span> {row['Dinner']}</div>
                    </div>
                    """, unsafe_allow_html=True)

    st.subheader("❌ Foods to Avoid")
    st.write(", ".join(avoid))

    st.subheader("🏃 Lifestyle Recommendations")
    for l in lifestyle:
        st.write("•", l)

    st.download_button(
        "📥 Download JSON",
        json.dumps(diet_df.to_dict(), indent=4),
        "diet_plan.json"
    )