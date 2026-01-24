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

/* Diet Cards */
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

/* Info Cards */
.info-card {
    background: rgba(255, 255, 255, 0.94);
    border-radius: 16px;
    padding: 18px;
    margin-bottom: 20px;
    box-shadow: 0 6px 14px rgba(0,0,0,0.18);
    color: #1e1e1e;
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
def generate_diet(text):
    if "diabetes" in text:
        condition = "Diabetes"
        avoid = ["Sugar", "White rice", "Soft drinks"]
    elif "hypertension" in text or "blood pressure" in text:
        condition = "Hypertension"
        avoid = ["Salt", "Pickles", "Processed food"]
    else:
        condition = "General Health"
        avoid = ["Junk food", "Excess sugar"]

    lifestyle = [
        "Exercise at least 30 minutes daily",
        "Drink 2–3 liters of water",
        "Sleep 7–8 hours daily"
    ]

    meals = {
        "Breakfast": ["Oats", "Idli", "Dosa", "Poha", "Smoothie", "Upma", "Toast"],
        "Lunch": ["Dal Rice", "Chapati Curry", "Khichdi", "Quinoa Bowl", "Paneer", "Veg Biryani", "Salad"],
        "Snacks": ["Fruits", "Nuts", "Sprouts", "Yogurt", "Protein Shake", "Seeds", "Boiled Eggs"],
        "Dinner": ["Soup", "Salad", "Grilled Veg", "Tofu", "Paneer", "Zoodles", "Light Curry"]
    }

    days = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

    df = pd.DataFrame({
        "Day": days,
        "Breakfast": random.sample(meals["Breakfast"], 7),
        "Lunch": random.sample(meals["Lunch"], 7),
        "Snacks": random.sample(meals["Snacks"], 7),
        "Dinner": random.sample(meals["Dinner"], 7)
    })

    return condition, avoid, lifestyle, df

# -------------------- PDF GENERATION --------------------
def create_pdf(name, age, condition, diet_type, avoid, lifestyle, diet_df):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("<b>AI Diet Planner Report</b>", styles["Title"]))
    story.append(Paragraph(f"<b>Name:</b> {name}", styles["Normal"]))
    story.append(Paragraph(f"<b>Age:</b> {age}", styles["Normal"]))
    story.append(Paragraph(f"<b>Condition:</b> {condition}", styles["Normal"]))
    story.append(Paragraph(f"<b>Diet Type:</b> {diet_type}", styles["Normal"]))
    story.append(Paragraph("<br/>", styles["Normal"]))

    table_data = [diet_df.columns.tolist()] + diet_df.values.tolist()
    table = Table(table_data, repeatRows=1)

    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.green),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("ALIGN", (1,1), (-1,-1), "CENTER")
    ]))

    story.append(table)
    story.append(Paragraph("<br/><b>Foods to Avoid:</b> " + ", ".join(avoid), styles["Normal"]))
    story.append(Paragraph("<br/><b>Lifestyle Recommendations:</b>", styles["Normal"]))

    for l in lifestyle:
        story.append(Paragraph(f"- {l}", styles["Normal"]))

    doc.build(story)
    buffer.seek(0)
    return buffer


# -------------------- USER INPUT --------------------
uploaded_file = st.file_uploader("📄 Upload Medical Report", type=["pdf","png","jpg","jpeg","txt","csv"])
diet_type = st.selectbox("🥦 Select Diet Type", ["Veg","Non-Veg"])

if st.button("🍽 Generate Diet Plan") and uploaded_file:
    text = extract_text(uploaded_file)
    name, age = extract_patient_info(text)
    condition, avoid, lifestyle, diet_df = generate_diet(text)

    # Patient Info
    st.markdown(f"""
    <div class="info-card">
        <div class="info-header">👤 Patient Information</div>
        <b>Name:</b> {name}<br>
        <b>Age:</b> {age}<br>
        <b>Condition:</b> {condition}<br>
        <b>Diet Type:</b> {diet_type}
    </div>
    """, unsafe_allow_html=True)

    # Diet Cards
    st.subheader("📅 7-Day Diet Plan")
    for i in range(0, 7, 2):
        col1, col2 = st.columns(2)
        for col, idx in zip([col1,col2],[i,i+1]):
            if idx < 7:
                row = diet_df.iloc[idx]
                with col:
                    st.markdown(f"""
                    <div class="diet-card">
                        <div class="card-header">{row['Day']}</div>
                        Breakfast: {row['Breakfast']}<br>
                        Lunch: {row['Lunch']}<br>
                        Snacks: {row['Snacks']}<br>
                        Dinner: {row['Dinner']}
                    </div>
                    """, unsafe_allow_html=True)

    # Foods to Avoid
    st.markdown(f"""
    <div class="info-card">
        <div class="info-header">❌ Foods to Avoid</div>
        {", ".join(avoid)}
    </div>
    """, unsafe_allow_html=True)

    # ✅ Lifestyle Card (FIXED)
    lifestyle_html = "".join([f"<li>{l}</li>" for l in lifestyle])

    st.markdown(f"""
    <div class="info-card">
        <div class="info-header">🏃 Lifestyle Recommendations</div>
        <ul style="font-size:15px; margin-left:20px;">
            {lifestyle_html}
        </ul>
    </div>
    """, unsafe_allow_html=True)

    # Downloads
    st.download_button(
        "📥 Download Diet Plan JSON",
        json.dumps(diet_df.to_dict(), indent=4),
        "diet_plan.json"
    )
    st.download_button(
        "📄 Download Diet Plan PDF",
        pdf_file,
        "diet_plan.pdf",
        mime="application/pdf"
    )
