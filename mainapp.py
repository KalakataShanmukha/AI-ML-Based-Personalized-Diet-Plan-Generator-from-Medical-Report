import streamlit as st
import pandas as pd
import pdfplumber
import pytesseract
from PIL import Image
from fpdf import FPDF
import spacy
import io
import random
import os

# -------------------- PAGE CONFIG --------------------
st.set_page_config(
    page_title="AI_DietPlanner",
    page_icon="🥗",
    layout="centered"
)

# -------------------- TITLE --------------------
st.markdown("""
<h1 style='text-align:center;'>🥗 AI_DietPlanner</h1>
<p style='text-align:center;color:gray;'>AI-based Personalized 7-Day Diet Recommendation System</p>
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
    text = text.lower()
    diet = {
        "condition": [],
        "allowed": ["Vegetables", "Whole grains", "Fruits"],
        "restricted": [],
        "diet_plan": {},
        "lifestyle": []
    }

    # -------------------- Conditions --------------------
    if "diabetes" in text:
        diet["condition"].append("Diabetes")
        diet["restricted"].append("Sugar")
    if "cholesterol" in text:
        diet["condition"].append("High Cholesterol")
        diet["restricted"].append("Oily food")
    if "blood pressure" in text or "hypertension" in text:
        diet["condition"].append("Hypertension")
        diet["restricted"].append("Salt")
    if not diet["condition"]:
        diet["condition"].append("General Health")

    # -------------------- Meal Options --------------------
    breakfast_options = [
        "Oatmeal with fruits 🥣🍎",
        "Greek yogurt with berries 🍓🥛",
        "Whole grain toast with avocado 🥑🍞",
        "Vegetable smoothie 🥬🍏"
    ]
    lunch_options = [
        "Grilled vegetables with brown rice 🥗🍚",
        "Quinoa salad with chickpeas 🥗",
        "Vegetable stir-fry with tofu 🥦🍲",
        "Whole grain pasta with tomato sauce 🍝🍅"
    ]
    snack_options = [
        "Fruit smoothie 🍌🍓",
        "Handful of nuts 🥜",
        "Carrot sticks with hummus 🥕",
        "Apple slices with peanut butter 🍎🥜"
    ]
    dinner_options = [
        "Steamed vegetables with lean protein 🥦🍗",
        "Baked fish with salad 🐟🥗",
        "Vegetable soup with whole grain bread 🍲🍞",
        "Lentil curry with brown rice 🍛🍚"
    ]

    # -------------------- Generate 7-Day Plan --------------------
    for day in range(1, 8):
        diet["diet_plan"][f"Day {day}"] = {
            "Breakfast": random.choice(breakfast_options),
            "Lunch": random.choice(lunch_options),
            "Snack": random.choice(snack_options),
            "Dinner": random.choice(dinner_options)
        }

    # Lifestyle advice
    diet["lifestyle"].append("Walk daily, stay active, practice stress management 🏃🧘🚶")

    return diet

# -------------------- INPUT --------------------
st.subheader("📄 Upload Medical Report")
uploaded_file = st.file_uploader(
    "Upload PDF / Image / TXT / CSV",
    type=["pdf", "png", "jpg", "jpeg", "txt", "csv"]
)

process_btn = st.button("🍽 Generate 7-Day Diet Recommendation")

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

    # ---------- Display 7-Day Diet ----------
    diet_display = ""
    for day, meals in diet["diet_plan"].items():
        diet_display += f"<b>{day}</b><br>"
        for meal_name, meal in meals.items():
            diet_display += f"{meal_name}: {meal}<br>"
        diet_display += "<br>"

    st.markdown(f"""
    <div class='card'>
        <h4>🍽 Personalized 7-Day Diet Plan</h4>
        {diet_display}
        <b>Lifestyle Advice:</b> {', '.join(diet['lifestyle'])}
    </div>
    """, unsafe_allow_html=True)

    # ---------- Generate PDF ----------
    pdf = FPDF()
    pdf.add_page()

    # Use DejaVuSans.ttf for Unicode if uploaded
    font_path = "DejaVuSans.ttf"
    if os.path.exists(font_path):
        pdf.add_font("DejaVu", "", font_path, uni=True)
        pdf.set_font("DejaVu", 'B', 16)
        pdf.multi_cell(0, 10, "🥗 AI DietPlanner - 7-Day Recommendation\n\n")
        pdf.set_font("DejaVu", '', 12)
    else:
        pdf.set_font("Arial", 'B', 16)
        pdf.multi_cell(0, 10, "AI DietPlanner - 7-Day Recommendation\n\n")
        pdf.set_font("Arial", '', 12)

    pdf.multi_cell(0, 8, f"❤️ Condition: {', '.join(diet['condition'])}")
    pdf.multi_cell(0, 8, f"✅ Allowed Foods: {', '.join(diet['allowed'])}")
    pdf.multi_cell(0, 8, f"❌ Restricted Foods: {', '.join(set(diet['restricted']))}\n")

    for day, meals in diet["diet_plan"].items():
        pdf.multi_cell(0, 8, f"{day}")
        for meal_name, meal in meals.items():
            pdf.multi_cell(0, 8, f"{meal_name}: {meal}")
        pdf.multi_cell(0, 5, "")

    pdf.multi_cell(0, 8, f"\n🏃 Lifestyle Advice: {', '.join(diet['lifestyle'])}")

    pdf_output = io.BytesIO()
    pdf.output(pdf_output)
    pdf_output.seek(0)

    # ---------- Download Button ----------
    st.download_button(
        label="📥 Download 7-Day Diet PDF",
        data=pdf_output,
        file_name="7_day_diet_recommendation.pdf",
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
