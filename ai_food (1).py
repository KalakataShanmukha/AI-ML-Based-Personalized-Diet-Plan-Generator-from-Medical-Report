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

# -------------------- BACKGROUND CSS --------------------
st.markdown("""
<style>
.stApp {
    background-image: url("https://d1csarkz8obe9u.cloudfront.net/posterpreviews/powerpoint-healthy-fruits-background-design-template-32ec152ef88b2fa8e280d9832e6bb0ff_screen.jpg");
    background-size: cover;
    background-attachment: fixed;
    background-repeat: no-repeat;
}
table.dataframe {
    border-collapse: collapse;
    width: 100%;
    font-family: Arial, sans-serif;
}
table.dataframe th, table.dataframe td {
    border: 1px solid #ddd;
    padding: 8px;
    text-align: center;
}
table.dataframe tr:nth-child(even) {
    background-color: #f2f2f2;
}
table.dataframe tr:hover {
    background-color: #ddd;
}
</style>
""", unsafe_allow_html=True)

# -------------------- TITLE --------------------
st.markdown("""
<h1 style='text-align:center;'>🥗 AI_DietPlanner</h1>
<p style='text-align:center;color:gray;'>AI-based Personalized Diet Recommendation System</p>
<hr>
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

# -------------------- DIET GENERATION --------------------
def generate_diet(text, category="Veg"):
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
        "Sleep at least 7 hours"
    ]

    # -------------------- Meal options --------------------
    if category == "Veg":
        meal_options = {
            "Breakfast": ["Oats with fruits", "Vegetable upma", "Idli with sambar", "Poha", "Dosa with chutney", "Multigrain toast", "Smoothie bowl"],
            "Lunch": ["Brown rice with dal", "Chapati with veg curry", "Millet khichdi", "Quinoa salad", "Paneer stir fry", "Lentil soup", "Vegetable biryani"],
            "Snacks": ["Fruit bowl", "Roasted nuts", "Sprouts salad", "Yogurt with berries", "Hummus with veggies", "Boiled eggs", "Protein smoothie"],
            "Dinner": ["Vegetable soup", "Grilled vegetables", "Light salad", "Stuffed bell peppers", "Zucchini noodles", "Tofu stir fry", "Paneer tikka"]
        }
    else:  # Non-Veg
        meal_options = {
            "Breakfast": ["Egg omelette", "Chicken sandwich", "Scrambled eggs", "Multigrain toast with eggs", "Smoothie bowl", "Egg bhurji", "Boiled eggs"],
            "Lunch": ["Grilled chicken salad", "Fish curry with rice", "Chicken biryani", "Paneer+chicken stir fry", "Lentil soup with chicken", "Brown rice with fish", "Quinoa with shrimp"],
            "Snacks": ["Protein smoothie", "Boiled eggs", "Roasted nuts", "Yogurt with berries", "Chicken wraps", "Cheese cubes", "Fruit bowl"],
            "Dinner": ["Steamed fish with veggies", "Grilled chicken", "Tofu+chicken stir fry", "Vegetable soup with egg", "Light salad with tuna", "Stuffed bell peppers with paneer", "Zucchini noodles with shrimp"]
        }

    # 7 unique meals per category
    breakfast_list = random.sample(meal_options["Breakfast"], 7)
    lunch_list = random.sample(meal_options["Lunch"], 7)
    snacks_list = random.sample(meal_options["Snacks"], 7)
    dinner_list = random.sample(meal_options["Dinner"], 7)

    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    rows = []
    for i in range(7):
        rows.append({
            "Day": days_of_week[i],
            "Breakfast": breakfast_list[i],
            "Lunch": lunch_list[i],
            "Snacks": snacks_list[i],
            "Dinner": dinner_list[i]
        })
    df = pd.DataFrame(rows)
    return condition, avoid, lifestyle, df

# -------------------- PDF GENERATION IN MEMORY --------------------
def generate_pdf_bytes(name, age, condition, df, avoid, lifestyle):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("AI Diet Planner – Health Report", styles["Title"]))
    elements.append(Paragraph(f"<b>Name:</b> {name}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Age:</b> {age}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Condition:</b> {condition}", styles["Normal"]))
    elements.append(Paragraph("<br/>", styles["Normal"]))

    table_data = [df.columns.tolist()] + df.values.tolist()
    table = Table(table_data)
    table.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold")
    ]))
    elements.append(table)
    elements.append(Paragraph("<br/>", styles["Normal"]))

    elements.append(Paragraph("<b>Foods to Avoid</b>", styles["Heading2"]))
    for a in avoid:
        elements.append(Paragraph(f"- {a}", styles["Normal"]))

    elements.append(Paragraph("<br/>", styles["Normal"]))
    elements.append(Paragraph("<b>Lifestyle Recommendations</b>", styles["Heading2"]))
    for l in lifestyle:
        elements.append(Paragraph(f"- {l}", styles["Normal"]))

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

    st.subheader("📊 7-Day Diet Plan")
    header_color = '#D3D3D3'
    styled_df = diet_df.style.set_table_styles([
        {'selector': 'thead th', 'props': [('background-color', header_color),
                                           ('font-weight', 'bold'),
                                           ('font-size', '14px'),
                                           ('color', 'black'),
                                           ('text-align', 'center')]}
    ]).set_properties(**{"text-align": "center", "padding": "8px"})\
      .set_caption(f"🍽 {category} 7-Day Meal Plan")

    st.dataframe(styled_df.hide(axis="index"), use_container_width=True)

    st.subheader("❌ Foods to Avoid")
    st.write(", ".join(avoid))

    st.subheader("🏃 Lifestyle Recommendations")
    for l in lifestyle:
        st.write("•", l)

    pdf_bytes = generate_pdf_bytes(patient_name, patient_age, condition, diet_df, avoid, lifestyle)
    st.download_button("📄 Download PDF Report", data=pdf_bytes, file_name="Diet_Report.pdf")
    st.download_button("📥 Download JSON", data=json.dumps(diet_df.to_dict(), indent=4), file_name="diet_plan.json")
