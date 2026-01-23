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
# -------------------- PAGE CONFIG --------------------
st.set_page_config(
    page_title="AI Diet Planner",
    page_icon="🥗",
    layout="wide"
)

# -------------------- CUSTOM CSS --------------------
st.markdown("""
<style>

.stApp {
    background-image: url("https://d1csarkz8obe9u.cloudfront.net/posterpreviews/powerpoint-healthy-fruits-background-design-template-32ec152ef88b2fa8e280d9832e6bb0ff_screen.jpg");
    background-size: cover;
    background-attachment: fixed;
    background-repeat: no-repeat;
}

/* ---------- CARD BASE ---------- */
.card {
    background: rgba(255, 255, 255, 0.85);
    border-radius: 18px;
    padding: 20px;
    margin: 12px 0;
    box-shadow: 0 8px 25px rgba(0,0,0,0.12);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.card:hover {
    transform: translateY(-5px);
    box-shadow: 0 14px 35px rgba(0,0,0,0.18);
}

/* ---------- HEADER CARD ---------- */
.header-card {
    background: linear-gradient(135deg, #81ecec, #74b9ff);
    color: #000;
    text-align: center;
    font-size: 26px;
    font-weight: bold;
}

/* ---------- DAY TITLE ---------- */
.day-title {
    font-size: 20px;
    font-weight: bold;
    margin-bottom: 12px;
    color: #2d3436;
}

/* ---------- MEAL TEXT ---------- */
.meal {
    margin: 6px 0;
    font-size: 15px;
}

/* ---------- AVOID CARD ---------- */
.avoid-card {
    background: linear-gradient(135deg, #ff7675, #fab1a0);
    color: white;
    font-weight: bold;
}

/* ---------- INFO TEXT ---------- */
.info {
    font-size: 16px;
}

</style>
""", unsafe_allow_html=True)

# -------------------- TITLE --------------------
st.markdown("""
<div class="card header-card">
🥗  AI-Based Personalized Diet Planner
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

# -------------------- PATIENT INFO EXTRACTION --------------------
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


# -------------------- DIET LOGIC --------------------
def generate_diet(text, category="Veg"):
    text = text.lower()

    if "diabetes" in text:
        condition = "Diabetes"
        avoid = ["Sugar", "White Rice", "Soft Drinks"]
    elif "blood pressure" in text or "hypertension" in text:
        condition = "Hypertension"
        avoid = ["Salt", "Pickles", "Processed Food"]
    else:
        condition = "General Health"
        avoid = ["Junk Food", "Deep Fried Items"]

    if category == "Veg":
        meals = {
            "Breakfast": ["Oats", "Idli", "Poha", "Smoothie", "Upma", "Dosa", "Fruit Bowl"],
            "Lunch": ["Brown Rice + Dal", "Chapati + Veg Curry", "Khichdi", "Quinoa Bowl", "Paneer Curry"],
            "Snacks": ["Sprouts", "Roasted Nuts", "Yogurt", "Fruits"],
            "Dinner": ["Veg Soup", "Grilled Veggies", "Light Salad", "Paneer Stir Fry"]
        }
    else:
        meals = {
            "Breakfast": ["Egg Omelette", "Boiled Eggs", "Toast + Eggs"],
            "Lunch": ["Grilled Chicken", "Fish Curry", "Chicken Biryani"],
            "Snacks": ["Protein Shake", "Boiled Eggs", "Nuts"],
            "Dinner": ["Grilled Fish", "Chicken Soup", "Light Salad + Chicken"]
        }

    # 7 unique meals per category
    breakfast_list = random.sample(meal_options["Breakfast"], 7)
    lunch_list = random.sample(meal_options["Lunch"], 7)
    snacks_list = random.sample(meal_options["Snacks"], 7)
    dinner_list = random.sample(meal_options["Dinner"], 7)


    days = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

    plan = []
    for d in days:
        plan.append({
            "Day": d,
            "Breakfast": random.choice(meals["Breakfast"]),
            "Lunch": random.choice(meals["Lunch"]),
            "Snacks": random.choice(meals["Snacks"]),
            "Dinner": random.choice(meals["Dinner"])
        })

    return condition, avoid, plan

def generate_pdf_card_style(condition, diet_type, plan, avoid):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    elements = []

    # -------- TITLE --------
    elements.append(Paragraph("<b>AI Diet Planner Report</b>", styles["Title"]))
    elements.append(Paragraph(f"<b>Condition:</b> {condition}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Diet Type:</b> {diet_type}", styles["Normal"]))
    elements.append(Paragraph("<br/>", styles["Normal"]))

    # -------- DAY CARDS --------
    for day in plan:
        card_data = [[
            Paragraph(f"""
            <b>{day[0]}</b><br/><br/>
            <b>Breakfast:</b> {day[1]}<br/>
            <b>Lunch:</b> {day[2]}<br/>
            <b>Snacks:</b> {day[3]}<br/>
            <b>Dinner:</b> {day[4]}
            """, styles["Normal"])
        ]]

        card = Table(card_data, colWidths=[450])
        card.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), colors.whitesmoke),
            ("BOX", (0,0), (-1,-1), 1, colors.grey),
            ("LEFTPADDING", (0,0), (-1,-1), 14),
            ("RIGHTPADDING", (0,0), (-1,-1), 14),
            ("TOPPADDING", (0,0), (-1,-1), 12),
            ("BOTTOMPADDING", (0,0), (-1,-1), 12),
        ]))

        elements.append(card)
        elements.append(Paragraph("<br/>", styles["Normal"]))

    # -------- AVOID CARD --------
    avoid_text = "<br/>".join([f"🚫 {a}" for a in avoid])

    avoid_card = Table(
        [[Paragraph(f"<b>Foods to Avoid</b><br/><br/>{avoid_text}", styles["Normal"])]],
        colWidths=[450]
    )

    avoid_card.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), colors.pink),
        ("BOX", (0,0), (-1,-1), 1, colors.red),
        ("LEFTPADDING", (0,0), (-1,-1), 14),
        ("RIGHTPADDING", (0,0), (-1,-1), 14),
        ("TOPPADDING", (0,0), (-1,-1), 12),
        ("BOTTOMPADDING", (0,0), (-1,-1), 12),
    ]))

    elements.append(avoid_card)

    doc.build(elements)
    buffer.seek(0)
    return buffer

# -------------------- USER INPUT --------------------
uploaded_file = st.file_uploader(
    "📄 Upload Medical Report",
    type=["pdf", "png", "jpg", "jpeg", "txt", "csv"]
)

category = st.selectbox("Select Diet Type", ["Veg", "Non-Veg"])

if st.button("🍽 Generate Diet Plan") and uploaded_file:
    text = extract_text(uploaded_file)
    patient_name, patient_age = extract_patient_info(text)
    condition, avoid, lifestyle, diet_df = generate_diet(text, category)

    st.subheader("👤 Patient Information")
    st.write(f"**Name:** {patient_name}")
    st.write(f"**Age:** {patient_age}")
    st.write(f"**Condition:** {condition}")
    st.write(f"**Diet Type:** {category}")


    # -------------------- INFO CARD --------------------
    st.markdown(f"""
    <div class="card">
        <p class="info"><b>Condition:</b> {condition}</p>
        <p class="info"><b>Diet Type:</b> {diet_type}</p>
    </div>
    """, unsafe_allow_html=True)

    # -------------------- DIET PLAN HEADER --------------------
    st.markdown("""
    <div class="card header-card">
    📅 7-Day Diet Plan
    </div>
    """, unsafe_allow_html=True)

    # -------------------- DIET CARDS (2 PER ROW) --------------------
    for i in range(0, len(plan), 2):
        col1, col2 = st.columns(2)

        for col, day_plan in zip([col1, col2], plan[i:i+2]):
            with col:
                st.markdown(f"""
                <div class="card">
                    <div class="day-title">📆 {day_plan['Day']}</div>
                    <div class="meal">🍳 <b>Breakfast:</b> {day_plan['Breakfast']}</div>
                    <div class="meal">🍛 <b>Lunch:</b> {day_plan['Lunch']}</div>
                    <div class="meal">☕ <b>Snacks:</b> {day_plan['Snacks']}</div>
                    <div class="meal">🍲 <b>Dinner:</b> {day_plan['Dinner']}</div>
                </div>
                """, unsafe_allow_html=True)

    # -------------------- FOODS TO AVOID --------------------
    st.markdown("""
    <div class="card header-card">
    ❌ Foods to Avoid
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(len(avoid))
    for col, food in zip(cols, avoid):
        with col:
            st.markdown(f"""
            <div class="card avoid-card">
            🚫 {food}
            </div>
            """, unsafe_allow_html=True)
# -------------------- DOWNLOAD SECTION --------------------
    st.subheader("📥 Download Reports")

    pdf_bytes = generate_pdf_card_style(
        condition=condition,
        diet_type=category,   # Veg / Non-Veg
        plan=diet_plan,       # card-based plan (list)
        avoid=avoid
    )

    st.download_button(
        label="📄 Download PDF Report",
        data=pdf_bytes,
        file_name="Diet_Report.pdf",
        mime="application/pdf"
    )

    st.download_button(
        label="📊 Download JSON",
        data=json.dumps(diet_plan, indent=4),
        file_name="diet_plan.json",
        mime="application/json"
    )