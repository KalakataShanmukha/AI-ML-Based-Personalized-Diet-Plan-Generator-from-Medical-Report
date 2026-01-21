import streamlit as st
import json
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import tempfile
import re

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="MyDiet_AI",
    page_icon="🥗",
    layout="wide"
)

# ---------------- BACKGROUND IMAGE ----------------
def set_bg(img_url):
    st.markdown(f"""
    <style>
    .stApp {{
        background-image: url("{img_url}");
        background-size: cover;
        background-position: center;
    }}
    </style>
    """, unsafe_allow_html=True)

set_bg("https://images.unsplash.com/photo-1546069901-ba9599a7e63c")

# ---------------- TITLE ----------------
st.markdown("<h1 style='text-align:center;'>🥗 MyDiet_AI</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;'>AI-Based Personalized Diet Recommendation System</p>", unsafe_allow_html=True)
st.divider()

# ---------------- MEDICAL TEXT EXTRACTION ----------------
def extract_info(text):
    data = {}

    name = re.search(r"Name[:\-]?\s*([A-Za-z ]+)", text)
    age = re.search(r"Age[:\-]?\s*(\d+)", text)
    condition = re.search(r"(Diabetes|Hypertension|Thyroid|Heart|Obesity)", text, re.I)
    restricted = re.search(r"Restricted[:\-]?\s*([A-Za-z ,]+)", text)

    data["name"] = name.group(1) if name else "Not Found"
    data["age"] = age.group(1) if age else "Not Found"
    data["condition"] = condition.group(1) if condition else "General"
    data["restricted"] = restricted.group(1) if restricted else "None"

    return data

# ---------------- SIDEBAR INPUT ----------------
st.sidebar.header("📄 Upload Medical Report / Paste Text")

report_text = st.sidebar.text_area("Medical Report Text", height=220)

diet_type = st.sidebar.radio(
    "Choose Diet Preference",
    ["Vegetarian", "Non-Vegetarian"]
)

generate = st.sidebar.button("Generate Diet Plan")

# ---------------- DIET DATA ----------------
veg_meals = [
    ("Oats porridge", "Vegetable upma"),
    ("Poha", "Idli"),
    ("Smoothie bowl", "Fruit bowl"),
    ("Besan chilla", "Vegetable paratha"),
    ("Dosa", "Ragi dosa"),
    ("Idli", "Steamed appam"),
    ("Upma", "Broken wheat upma")
]

veg_lunch = [
    ("Rajma + brown rice", "Chole + rice"),
    ("Vegetable pulao", "Curd rice"),
    ("Dal + roti", "Vegetable khichdi"),
    ("Mushroom curry", "Veg kurma"),
    ("Sambar rice", "Lemon rice"),
    ("Paneer rice", "Veg fried rice"),
    ("Dal makhani", "Jeera rice")
]

veg_snack = [
    ("Fruit salad", "Sprouts salad"),
    ("Roasted chana", "Nuts"),
    ("Green tea", "Buttermilk"),
    ("Fruit yogurt", "Apple"),
    ("Makhana", "Popcorn"),
    ("Smoothie", "Dates"),
    ("Coconut water", "Orange")
]

veg_dinner = [
    ("Paneer bhurji", "Veg stir fry"),
    ("Vegetable soup", "Tomato soup"),
    ("Palak paneer", "Tofu curry"),
    ("Vegetable stew", "Clear soup"),
    ("Baingan bharta", "Veg curry"),
    ("Dal tadka", "Vegetable dal"),
    ("Veg korma", "Mixed veg")
]

days = ["Day 1","Day 2","Day 3","Day 4","Day 5","Day 6","Day 7"]

# ---------------- GENERATE PLAN ----------------
if generate:

    patient = extract_info(report_text)

    plan = []
    for i in range(7):
        plan.append({
            "day": days[i],
            "breakfast": veg_meals[i][0],
            "breakfast_alt": veg_meals[i][1],
            "lunch": veg_lunch[i][0],
            "lunch_alt": veg_lunch[i][1],
            "snack": veg_snack[i][0],
            "snack_alt": veg_snack[i][1],
            "dinner": veg_dinner[i][0],
            "dinner_alt": veg_dinner[i][1],
        })

    # ---------------- PATIENT SUMMARY ----------------
    st.subheader("🧑 Patient Summary")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Name", patient["name"])
    col2.metric("Age", patient["age"])
    col3.metric("Condition", patient["condition"])
    col4.metric("Restricted", patient["restricted"])
    col5.metric("Diet", diet_type)

    st.divider()

    # ---------------- DAY TABS ----------------
    st.subheader("📆 7-Day AI Diet Recommendation")

    tabs = st.tabs(days)

    for i, tab in enumerate(tabs):
        with tab:
            d = plan[i]

            st.markdown(f"""
            **Breakfast**  
            → {d['breakfast']}  
            _Alternative:_ {d['breakfast_alt']}

            **Lunch**  
            → {d['lunch']}  
            _Alternative:_ {d['lunch_alt']}

            **Snack**  
            → {d['snack']}  
            _Alternative:_ {d['snack_alt']}

            **Dinner**  
            → {d['dinner']}  
            _Alternative:_ {d['dinner_alt']}
            """)

    # ---------------- DOWNLOAD JSON ----------------
    output = {
        "patient": patient,
        "diet_type": diet_type,
        "plan": plan
    }

    st.download_button(
        "⬇ Download as JSON",
        data=json.dumps(output, indent=4),
        file_name="diet_plan.json",
        mime="application/json"
    )

    # ---------------- DOWNLOAD PDF ----------------
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        doc = SimpleDocTemplate(tmp.name)
        styles = getSampleStyleSheet()
        content = []

        content.append(Paragraph("AI Generated Diet Plan", styles["Title"]))
        content.append(Paragraph(f"Name: {patient['name']}", styles["Normal"]))
        content.append(Paragraph(f"Age: {patient['age']}", styles["Normal"]))
        content.append(Paragraph(f"Condition: {patient['condition']}", styles["Normal"]))
        content.append(Paragraph(f"Diet: {diet_type}", styles["Normal"]))

        for d in plan:
            content.append(Paragraph(f"<b>{d['day']}</b>", styles["Heading2"]))
            content.append(Paragraph(f"Breakfast: {d['breakfast']} (Alt: {d['breakfast_alt']})", styles["Normal"]))
            content.append(Paragraph(f"Lunch: {d['lunch']} (Alt: {d['lunch_alt']})", styles["Normal"]))
            content.append(Paragraph(f"Snack: {d['snack']} (Alt: {d['snack_alt']})", styles["Normal"]))
            content.append(Paragraph(f"Dinner: {d['dinner']} (Alt: {d['dinner_alt']})", styles["Normal"]))

        doc.build(content)

        with open(tmp.name, "rb") as f:
            st.download_button("⬇ Download as PDF", f, file_name="diet_plan.pdf")