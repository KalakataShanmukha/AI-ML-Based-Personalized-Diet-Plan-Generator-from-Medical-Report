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

from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

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

.info-card {
    background: rgba(255, 255, 255, 0.94);
    border-radius: 16px;
    padding: 18px;
    margin-bottom: 20px;
    box-shadow: 0 6px 14px rgba(0,0,0,0.18);
}

.info-header {
    font-weight: bold;
    font-size: 18px;
    margin-bottom: 12px;
    padding: 8px;
    border-radius: 10px;
    text-align: center;
    background: linear-gradient(90deg, #81C784, #388E3C);
    color: white;
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
    margin-bottom: 25px;
">
    <h1 style="color:white;margin:0;">🥗 AI Diet Planner</h1>
    <p style="color:#E8F5E9;">Personalized Diet Recommendation System</p>
</div>
""", unsafe_allow_html=True)

# -------------------- NLP --------------------
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
                    text += page.extract_text()

    elif ext in ["png", "jpg", "jpeg"]:
        text = pytesseract.image_to_string(Image.open(uploaded_file))

    elif ext == "txt":
        text = uploaded_file.read().decode("utf-8")

    elif ext == "csv":
        text = pd.read_csv(uploaded_file).to_string()

    return text.lower()

# -------------------- PATIENT INFO --------------------
def extract_patient_info(text):
    name = re.search(r"name[:\-]?\s*([A-Za-z ]+)", text)
    age = re.search(r"age[:\-]?\s*(\d+)", text)
    return (
        name.group(1).strip() if name else "Not Found",
        age.group(1) if age else "Not Found"
    )

# -------------------- DIET GENERATION --------------------
def generate_diet(text, diet_type="Veg"):

    veg_meals = {
        "Diabetes": {
            "Breakfast": ["Oats with berries","Moong dal chilla","Vegetable upma","Poha with veggies","Greek yogurt"],
            "Lunch": ["Brown rice with dal","Quinoa salad","Vegetable curry with roti","Millet khichdi","Paneer stir fry"],
            "Snacks": ["Nuts","Sprouts salad","Roasted chana","Greek yogurt","Fruit bowl"],
            "Dinner": ["Vegetable soup","Paneer tikka","Zoodles","Steamed veggies","Tofu stir fry"]
        },
        "High Cholesterol": {
            "Breakfast": ["Oats with apple","Avocado toast","Smoothie","Vegetable idli","Chia pudding"],
            "Lunch": ["Quinoa bowl","Dal with roti","Vegetable soup","Paneer salad","Brown rice veggies"],
            "Snacks": ["Fruit bowl","Hummus with veggies","Roasted seeds","Air popcorn","Nuts"],
            "Dinner": ["Grilled tofu","Vegetable stew","Zucchini noodles","Soup","Paneer with salad"]
        },
        "General Health": {
            "Breakfast": ["Idli","Dosa","Oats","Upma","Smoothie"],
            "Lunch": ["Dal Rice","Chapati Curry","Veg Biryani","Paneer","Salad"],
            "Snacks": ["Fruits","Nuts","Yogurt","Sprouts","Seeds"],
            "Dinner": ["Soup","Salad","Grilled Veg","Paneer","Light Curry"]
        }
    }

    nonveg_meals = {
        "Diabetes": {
            "Breakfast": ["Boiled eggs","Egg omelette","Oats with milk","Protein smoothie","Scrambled eggs"],
            "Lunch": ["Grilled chicken","Fish curry","Egg curry","Chicken salad","Baked fish"],
            "Snacks": ["Boiled eggs","Greek yogurt","Protein shake","Nuts","Roasted chana"],
            "Dinner": ["Chicken soup","Grilled fish","Egg stir fry","Chicken veggies","Baked fish"]
        },
        "High Cholesterol": {
            "Breakfast": ["Egg white omelette","Oats","Protein smoothie","Boiled eggs","Toast"],
            "Lunch": ["Grilled chicken salad","Fish curry","Egg curry","Chicken stir fry","Baked fish"],
            "Snacks": ["Greek yogurt","Protein shake","Fruit bowl","Nuts","Seeds"],
            "Dinner": ["Grilled fish","Chicken soup","Egg stir fry","Low-fat curry","Veggies"]
        },
        "General Health": {
            "Breakfast": ["Eggs","Oats","Smoothie","Scrambled eggs","Toast"],
            "Lunch": ["Grilled chicken","Fish curry","Egg curry","Chicken salad","Tuna sandwich"],
            "Snacks": ["Boiled eggs","Protein shake","Yogurt","Nuts","Fruits"],
            "Dinner": ["Chicken soup","Fish curry","Egg stir fry","Grilled chicken","Veggies"]
        }
    }

    if "diabetes" in text:
        condition = "Diabetes"
        avoid = ["Sugar","White rice","Sweets","Soft drinks","Refined flour"]
    elif "cholesterol" in text:
        condition = "High Cholesterol"
        avoid = ["Fried food","Butter","Red meat","Full-fat dairy","Processed snacks"]
    else:
        condition = "General Health"
        avoid = ["Junk food","Excess sugar","Overeating"]

    meals = veg_meals[condition] if diet_type == "Veg" else nonveg_meals[condition]

    lifestyle = [
        "Exercise at least 30 minutes daily",
        "Drink 2–3 liters of water",
        "Sleep 7–8 hours daily",
        "Avoid smoking and alcohol",
        "Manage stress with yoga or meditation"
    ]

    days = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

    df = pd.DataFrame({
        "Day": days,
        "Breakfast": random.sample(meals["Breakfast"], 7),
        "Lunch": random.sample(meals["Lunch"], 7),
        "Snacks": random.sample(meals["Snacks"], 7),
        "Dinner": random.sample(meals["Dinner"], 7)
    })

    return condition, avoid, lifestyle, df

# -------------------- PDF GENERATOR --------------------
def generate_diet_pdf(name, age, condition, diet_type, avoid, lifestyle, diet_df):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("<b>AI Diet Planner – 7 Day Diet Plan</b>", styles["Title"]))
    elements.append(Paragraph("<br/>", styles["Normal"]))

    elements.append(Paragraph(f"Name: {name}", styles["Normal"]))
    elements.append(Paragraph(f"Age: {age}", styles["Normal"]))
    elements.append(Paragraph(f"Condition: {condition}", styles["Normal"]))
    elements.append(Paragraph(f"Diet Type: {diet_type}", styles["Normal"]))
    elements.append(Paragraph("<br/>", styles["Normal"]))

    for _, row in diet_df.iterrows():
        elements.append(Paragraph(
            f"<b>{row['Day']}</b><br/>"
            f"Breakfast: {row['Breakfast']}<br/>"
            f"Lunch: {row['Lunch']}<br/>"
            f"Snacks: {row['Snacks']}<br/>"
            f"Dinner: {row['Dinner']}<br/><br/>",
            styles["Normal"]
        ))

    elements.append(Paragraph("<b>Foods to Avoid</b>", styles["Heading2"]))
    elements.append(Paragraph(", ".join(avoid), styles["Normal"]))

    elements.append(Paragraph("<br/><b>Lifestyle Recommendations</b>", styles["Heading2"]))
    for l in lifestyle:
        elements.append(Paragraph(f"• {l}", styles["Normal"]))

    doc.build(elements)
    buffer.seek(0)
    return buffer

# -------------------- USER INPUT --------------------
uploaded_file = st.file_uploader("📄 Upload Medical Report", type=["pdf","png","jpg","jpeg","txt","csv"])
diet_type = st.selectbox("🥦 Select Diet Type", ["Veg","Non-Veg"])

if st.button("🍽 Generate Diet Plan") and uploaded_file:

    text = extract_text(uploaded_file)
    name, age = extract_patient_info(text)
    condition, avoid, lifestyle, diet_df = generate_diet(text, diet_type)

    st.markdown(f"""
    <div class="info-card">
        <div class="info-header">👤 Patient Information</div>
        <b>Name:</b> {name}<br>
        <b>Age:</b> {age}<br>
        <b>Condition:</b> {condition}<br>
        <b>Diet Type:</b> {diet_type}
    </div>
    """, unsafe_allow_html=True)

    st.subheader("📅 7-Day Diet Plan")

    for i in range(0, 7, 2):
        col1, col2 = st.columns(2)
        for col, idx in zip([col1, col2], [i, i+1]):
            if idx < 7:
                row = diet_df.iloc[idx]
                with col:
                    st.markdown(f"""
                    <div class="diet-card">
                        <div class="card-header">{row['Day']}</div>
                        <b>Breakfast:</b> {row['Breakfast']}<br>
                        <b>Lunch:</b> {row['Lunch']}<br>
                        <b>Snacks:</b> {row['Snacks']}<br>
                        <b>Dinner:</b> {row['Dinner']}
                    </div>
                    """, unsafe_allow_html=True)

    # -------- Avoid & Lifestyle Cards --------
    colA, colB = st.columns(2)

    with colA:
        st.markdown(f"""
        <div class="info-card">
            <div class="info-header">🚫 Foods to Avoid</div>
            <ul>{''.join([f'<li>{a}</li>' for a in avoid])}</ul>
        </div>
        """, unsafe_allow_html=True)

    with colB:
        st.markdown(f"""
        <div class="info-card">
            <div class="info-header">🏃 Lifestyle Recommendations</div>
            <ul>{''.join([f'<li>{l}</li>' for l in lifestyle])}</ul>
        </div>
        """, unsafe_allow_html=True)

    pdf_file = generate_diet_pdf(name, age, condition, diet_type, avoid, lifestyle, diet_df)

    st.download_button("📄 Download Diet Plan PDF", pdf_file, "AI_Diet_Plan.pdf", mime="application/pdf")
    st.download_button("📥 Download Diet Plan JSON", json.dumps(diet_df.to_dict(), indent=4), "diet_plan.json")