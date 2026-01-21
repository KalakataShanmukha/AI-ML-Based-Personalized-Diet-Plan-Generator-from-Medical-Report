import streamlit as st
import pdfplumber
import pytesseract
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
import re
import json
import io
import textwrap

# ---------------- PAGE CONFIG ----------------
st.set_page_config("MyDiet_AI", "🍎", layout="wide")

# ---------------- BACKGROUND IMAGE ----------------
st.markdown("""
<style>
.stApp {
    background-image: url("https://images.unsplash.com/photo-1540189549336-e6e99c3679fe");
    background-size: cover;
    background-attachment: fixed;
}
</style>
""", unsafe_allow_html=True)

# ---------------- UNIQUE CARD CSS ----------------
st.markdown("""
<style>
.unique-card {
    position: relative;
    background: rgba(255,255,255,0.9);
    backdrop-filter: blur(6px);
    border-radius: 18px;
    padding: 18px 18px 18px 58px;
    box-shadow: 0 12px 30px rgba(0,0,0,0.15);
    margin-bottom: 26px;
}
.day-ribbon {
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 42px;
    background: linear-gradient(180deg,#27ae60,#2ecc71);
    color: white;
    writing-mode: vertical-rl;
    font-weight: 700;
    text-align: center;
    border-radius: 18px 0 0 18px;
}
.food-tag {
    font-size: 12px;
    padding: 4px 10px;
    background: #eafaf1;
    color: #27ae60;
    border-radius: 12px;
    display: inline-block;
    margin-bottom: 10px;
}
.meal { font-size: 14px; margin-top: 6px; }
.meal span { font-weight: 600; }
.alt {
    font-size: 12px;
    color: #555;
    border: 1px dashed #bbb;
    padding: 6px 10px;
    border-radius: 10px;
    margin-top: 3px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- TITLE ----------------
st.title("🍎 MyDiet_AI")
st.caption("AI-based Personalized Diet Recommendation System")
st.markdown("---")

# ---------------- TEXT EXTRACTION ----------------
def extract_text(file):
    if file.name.endswith(".pdf"):
        text = ""
        with pdfplumber.open(file) as pdf:
            for p in pdf.pages:
                text += (p.extract_text() or "") + "\n"
        return text
    elif file.name.endswith((".png",".jpg",".jpeg")):
        return pytesseract.image_to_string(Image.open(file))
    elif file.name.endswith(".txt"):
        return file.read().decode()
    return ""

# ---------------- MEDICAL NLP ----------------
def extract_medical_info(text):
    info = {"name":"","age":"","conditions":[],"restricted_foods":[]}

    name = re.search(r"(name|patient name)[:\-]?\s*([A-Za-z ]+)", text, re.I)
    age = re.search(r"(age)[:\-]?\s*(\d{1,3})", text, re.I)

    if name: info["name"] = name.group(2).strip()
    if age: info["age"] = age.group(2)

    t = text.lower()
    if "diabetes" in t:
        info["conditions"].append("Diabetes")
        info["restricted_foods"] += ["Sugar", "Sweet drinks"]
    if "cholesterol" in t:
        info["conditions"].append("High Cholesterol")
        info["restricted_foods"] += ["Fried food", "Butter"]
    if "hypertension" in t or "blood pressure" in t:
        info["conditions"].append("Hypertension")
        info["restricted_foods"] += ["Salt", "Pickles"]

    return info

# ---------------- DIET TYPE BUTTON ----------------
st.subheader("Choose Diet Type")
c1, c2 = st.columns(2)
with c1: veg = st.button("🟢 Vegetarian")
with c2: nonveg = st.button("🔴 Non-Vegetarian")

if not veg and not nonveg:
    st.stop()

diet_type = "Vegetarian" if veg else "Non-Vegetarian"

# ---------------- WEEKLY PLANS (NO REPEAT) ----------------
def weekly_plan(choice):
    if choice == "Vegetarian":
        return [
            {"day":"Mon","b":"Besan chilla","b_alt":"Veg upma","l":"Rajma rice","l_alt":"Chole rice","s":"Fruit salad","s_alt":"Sprouts","d":"Paneer bhurji","d_alt":"Veg stir fry"},
            {"day":"Tue","b":"Poha","b_alt":"Idli","l":"Curd rice","l_alt":"Veg pulao","s":"Roasted chana","s_alt":"Nuts","d":"Dal tadka","d_alt":"Veg soup"},
            {"day":"Wed","b":"Oats","b_alt":"Fruit bowl","l":"Mushroom curry","l_alt":"Veg kurma","s":"Green tea","s_alt":"Apple","d":"Palak paneer","d_alt":"Tofu curry"},
            {"day":"Thu","b":"Dosa","b_alt":"Upma","l":"Sambar rice","l_alt":"Lemon rice","s":"Buttermilk","s_alt":"Coconut water","d":"Baingan bharta","d_alt":"Veg curry"},
            {"day":"Fri","b":"Idli","b_alt":"Sandwich","l":"Veg biryani","l_alt":"Khichdi","s":"Yogurt","s_alt":"Seeds","d":"Veg korma","d_alt":"Dal soup"},
            {"day":"Sat","b":"Paratha","b_alt":"Oats dosa","l":"Paneer rice","l_alt":"Veg fried rice","s":"Makhana","s_alt":"Popcorn","d":"Veg stew","d_alt":"Curd curry"},
            {"day":"Sun","b":"Smoothie","b_alt":"Cornflakes","l":"Dal makhani","l_alt":"Chickpeas","s":"Fruit chaat","s_alt":"Dry fruits","d":"Veg soup","d_alt":"Stuffed capsicum"}
        ]
    else:
        return [
            {"day":"Mon","b":"Egg omelette","b_alt":"Boiled eggs","l":"Grilled chicken","l_alt":"Chicken curry","s":"Apple & almonds","s_alt":"Yogurt","d":"Fish curry","d_alt":"Fish soup"},
            {"day":"Tue","b":"Scrambled eggs","b_alt":"Egg sandwich","l":"Chicken biryani","l_alt":"Chicken pulao","s":"Fruit bowl","s_alt":"Nuts","d":"Grilled fish","d_alt":"Fish stew"},
            {"day":"Wed","b":"Egg bhurji","b_alt":"Egg whites","l":"Egg curry","l_alt":"Chicken curry","s":"Peanuts","s_alt":"Seeds","d":"Chicken stir fry","d_alt":"Chicken kebab"},
            {"day":"Thu","b":"Omelette toast","b_alt":"Boiled eggs","l":"Fish rice","l_alt":"Fish curry","s":"Buttermilk","s_alt":"Coconut water","d":"Chicken soup","d_alt":"Grilled chicken"},
            {"day":"Fri","b":"Egg wrap","b_alt":"Egg dosa","l":"Chicken salad","l_alt":"Chicken sandwich","s":"Yogurt","s_alt":"Dry fruits","d":"Fish tikka","d_alt":"Fish curry"},
            {"day":"Sat","b":"Boiled eggs","b_alt":"Omelette","l":"Chicken rice","l_alt":"Chicken curry","s":"Popcorn","s_alt":"Nuts","d":"Chicken roast","d_alt":"Chicken soup"},
            {"day":"Sun","b":"Egg toast","b_alt":"Egg scramble","l":"Grilled fish","l_alt":"Fish curry","s":"Fruit bowl","s_alt":"Seeds","d":"Chicken biryani","d_alt":"Chicken stew"}
        ]

plan = weekly_plan(diet_type)

# ---------------- FILE UPLOAD ----------------
file = st.file_uploader("Upload medical report")
text = extract_text(file) if file else ""
info = extract_medical_info(text)

# ---------------- SUMMARY ----------------
st.subheader("🧾 Patient Summary")
st.json(info)

# ---------------- DISPLAY UNIQUE CARDS ----------------
st.subheader("📅 Weekly Diet Plan")
cols = st.columns(2)
for i, d in enumerate(plan):
    with cols[i % 2]:
        st.markdown(f"""
        <div class="unique-card">
            <div class="day-ribbon">{d['day']}</div>
            <div class="food-tag">{diet_type}</div>
            <div class="meal">🍳 <span>Breakfast:</span> {d['b']}</div><div class="alt">Alt: {d['b_alt']}</div>
            <div class="meal">🍛 <span>Lunch:</span> {d['l']}</div><div class="alt">Alt: {d['l_alt']}</div>
            <div class="meal">🍎 <span>Snack:</span> {d['s']}</div><div class="alt">Alt: {d['s_alt']}</div>
            <div class="meal">🌙 <span>Dinner:</span> {d['d']}</div><div class="alt">Alt: {d['d_alt']}</div>
        </div>
        """, unsafe_allow_html=True)

# ---------------- DOWNLOAD ----------------
output = {
    "patient": info,
    "diet_type": diet_type,
    "weekly_plan": plan
}

st.download_button("⬇ Download JSON", json.dumps(output,indent=2), "diet_plan.json")