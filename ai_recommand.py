import streamlit as st
import pandas as pd
import pdfplumber
import pytesseract
from PIL import Image
import spacy
import json
import random

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
AI-based Personalized 7-Day Diet Recommendation System
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
        text = pytesseract.image_to_string(Image.open(uploaded_file))

    elif ext == "txt":
        text = uploaded_file.read().decode("utf-8")

    elif ext == "csv":
        df = pd.read_csv(uploaded_file)
        if "doctor_prescription" in df.columns:
            text = df["doctor_prescription"].iloc[0]

    return text.strip()

# -------------------- RANDOM 7 DAY DIET LOGIC --------------------
def generate_7day_diet(text):
    text = text.lower()
    condition = "General Health"

    if "diabetes" in text:
        condition = "Diabetes"
    elif "cholesterol" in text:
        condition = "High Cholesterol"
    elif "blood pressure" in text or "hypertension" in text:
        condition = "Hypertension"

    meal_options = {
        "Day 1": {
            "Breakfast": ["Oats with fruits", "Vegetable omelette", "Poha", "Idli"],
            "Lunch": ["Brown rice & veg curry", "Chapati with dal", "Veg pulao", "Curd rice"],
            "Snacks": ["Roasted nuts", "Fruit bowl", "Sprouts salad", "Buttermilk"],
            "Dinner": ["Vegetable soup", "Steamed vegetables", "Salad", "Light curry"]
        },
        "Day 2": {
            "Breakfast": ["Idli with sambar", "Upma", "Smoothie", "Toast with peanut butter"],
            "Lunch": ["Millet rice", "Veg khichdi", "Dal rice", "Chapati & veg"],
            "Snacks": ["Fruit", "Roasted chana", "Green tea & nuts", "Yogurt"],
            "Dinner": ["Grilled vegetables", "Soup & salad", "Veg wrap", "Stir fry"]
        },
        "Day 3": {
            "Breakfast": ["Oats porridge", "Smoothie bowl", "Poha", "Boiled eggs"],
            "Lunch": ["Chapati & veg curry", "Curd rice", "Veg biryani (low oil)", "Dal roti"],
            "Snacks": ["Almonds", "Fruit", "Buttermilk", "Sprouts"],
            "Dinner": ["Vegetable stir fry", "Soup", "Paneer bhurji", "Salad"]
        },
        "Day 4": {
            "Breakfast": ["Upma", "Idli", "Omelette", "Fruit smoothie"],
            "Lunch": ["Veg pulao", "Chapati & dal", "Curd rice", "Veg thali"],
            "Snacks": ["Roasted nuts", "Green tea", "Fruit bowl", "Chana"],
            "Dinner": ["Soup & salad", "Veg curry", "Wrap", "Steamed veg"]
        },
        "Day 5": {
            "Breakfast": ["Poha", "Oats", "Toast", "Idli"],
            "Lunch": ["Chapati & paneer", "Veg khichdi", "Dal rice", "Veg biryani"],
            "Snacks": ["Fruit", "Yogurt", "Buttermilk", "Nuts"],
            "Dinner": ["Steamed vegetables", "Soup", "Light curry", "Salad"]
        },
        "Day 6": {
            "Breakfast": ["Smoothie", "Oats porridge", "Upma", "Egg whites"],
            "Lunch": ["Dal & rice", "Veg pulao", "Chapati & veg", "Curd rice"],
            "Snacks": ["Sprouts", "Fruit", "Nuts", "Green tea"],
            "Dinner": ["Veg curry", "Soup", "Wrap", "Stir fry"]
        },
        "Day 7": {
            "Breakfast": ["Toast & peanut butter", "Fruit smoothie", "Poha", "Oats"],
            "Lunch": ["Veg thali", "Chapati & dal", "Veg pulao", "Curd rice"],
            "Snacks": ["Fruit", "Buttermilk", "Roasted chana", "Yogurt"],
            "Dinner": ["Clear soup", "Vegetable stir fry", "Salad", "Light curry"]
        }
    }

    rows = []
    for day, meals in meal_options.items():
        rows.append({
            "Day": day,
            "Breakfast": random.choice(meals["Breakfast"]),
            "Lunch": random.choice(meals["Lunch"]),
            "Snacks": random.choice(meals["Snacks"]),
            "Dinner": random.choice(meals["Dinner"])
        })

    df = pd.DataFrame(rows)

    avoid = {
        "Diabetes": ["Sugar", "White rice", "Soft drinks"],
        "Hypertension": ["Salt", "Pickles", "Processed food"],
        "High Cholesterol": ["Fried food", "Butter", "Red meat"],
        "General Health": ["Excess junk food"]
    }

    return df, condition, avoid[condition]

# -------------------- USER INPUT --------------------
st.subheader("📄 Upload Medical Report")
uploaded_file = st.file_uploader(
    "Upload PDF / Image / TXT / CSV",
    type=["pdf", "png", "jpg", "jpeg", "txt", "csv"]
)

process_btn = st.button("🍽 Generate Random 7-Day Diet Plan")

# -------------------- PIPELINE --------------------
if process_btn:
    if uploaded_file:
        text = extract_text(uploaded_file)
        diet_df, condition, avoid_list = generate_7day_diet(text)

        st.markdown(f"""
        <div class='card'>
            <h4>🍽 7-Day Diet Plan</h4>
            <b>Detected Condition:</b> {condition}<br><br>
        </div>
        """, unsafe_allow_html=True)

        # ---------- TABLE OUTPUT ----------
        st.dataframe(diet_df, use_container_width=True)

        st.markdown(f"""
        <div class='card'>
            <b>❌ Avoid:</b> {", ".join(avoid_list)}
        </div>
        """, unsafe_allow_html=True)

        st.download_button(
            "📥 Download Diet Plan (JSON)",
            diet_df.to_json(orient="records", indent=4),
            "7_day_random_diet_plan.json",
            "application/json"
        )

    else:
        st.warning("⚠️ Please upload a medical report.")

# -------------------- CSS --------------------
st.markdown("""
<style>
.stApp {
    background-image: url("https://d1csarkz8obe9u.cloudfront.net/posterpreviews/powerpoint-healthy-fruits-background-design-template-32ec152ef88b2fa8e280d9832e6bb0ff_screen.jpg?ts=1703855188");
    background-size: cover;
    background-attachment: fixed;
}
.stApp::before {
    content: "";
    position: fixed;
    inset: 0;
    backdrop-filter: blur(8px);
    background: rgba(255,255,255,0.35);
    z-index: -1;
}
.card {
    background: rgba(255,255,255,0.95);
    padding: 15px;
    border-radius: 12px;
    margin-top: 10px;
}
</style>
""", unsafe_allow_html=True)
