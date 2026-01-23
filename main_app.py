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
# -------------------- NLP + DIET LOGIC (MILESTONE 3) --------------------
def generate_diet(text):
    diet = {
        "condition": [],
        "allowed_foods": ["vegetables", "whole grains", "fruits"],
        "restricted_foods": [],
        "diet_plan": [],
        "lifestyle_advice": []
    }

    text = text.lower()

    if "diabetes" in text:
        diet["condition"].append("Diabetes")
        diet["restricted_foods"].append("sugar")
        diet["diet_plan"].append("Follow a diabetic-friendly low sugar diet.")
        diet["lifestyle_advice"].append("Walk daily for 30 minutes.")

    if "cholesterol" in text:
        diet["condition"].append("High Cholesterol")
        diet["restricted_foods"].append("oily food")
        diet["diet_plan"].append("Increase fiber intake and avoid fried foods.")

    if "blood pressure" in text or "hypertension" in text:
        diet["condition"].append("Hypertension")
        diet["restricted_foods"].append("salt")
        diet["diet_plan"].append("Reduce sodium intake.")
        diet["lifestyle_advice"].append("Practice stress management.")

    if not diet["condition"]:
        diet["condition"].append("General Health")
        diet["diet_plan"].append("Maintain a balanced diet.")
        diet["lifestyle_advice"].append("Stay active and hydrated.")

    return {
        "condition": ", ".join(diet["condition"]),
        "allowed_foods": list(set(diet["allowed_foods"])),
        "restricted_foods": list(set(diet["restricted_foods"])),
        "diet_plan": " ".join(diet["diet_plan"]),
        "lifestyle_advice": " ".join(diet["lifestyle_advice"])
    }

def generate_meal_plan(has_diabetes, has_high_cholesterol, diet_type):
    veg = diet_type in ["Vegetarian", "Vegan"]
    dairy_ok = diet_type != "Vegan"
    def nv(nonveg_item, veg_item):
        return nonveg_item if not veg else veg_item
    def dairy(with_dairy_item, no_dairy_item):
        return with_dairy_item if dairy_ok else no_dairy_item
    def build_week(menu):
        b = menu["breakfast"][:]
        l = menu["lunch"][:]
        s = menu["snack"][:]
        d = menu["dinner"][:]
        random.shuffle(b)
        random.shuffle(l)
        random.shuffle(s)
        random.shuffle(d)
        days = []
        for i in range(7):
            days.append({
                "breakfast": b[i % len(b)],
                "lunch": l[i % len(l)],
                "snack": s[i % len(s)],
                "dinner": d[i % len(d)],
            })
        return days
    group = "both" if has_diabetes and has_high_cholesterol else ("diabetes" if has_diabetes else ("cholesterol" if has_high_cholesterol else "general"))
    dia_alt1 = {
        "breakfast": [
            dairy("Oats porridge with skim milk, green tea", "Oats porridge with soy milk, green tea"),
            "Moong dal chilla with mint chutney",
            "Ragi dosa with sambar",
            "Vegetable upma",
            "Poha with vegetables",
            dairy("Dalia with milk and nuts", "Dalia with soy milk and nuts"),
        ],
        "lunch": [
            "Whole wheat roti, dal, mixed sabzi",
            "Brown rice, rajma, salad",
            nv("Grilled chicken salad with olive oil and lemon", "Quinoa salad with legumes"),
            nv("Fish curry with brown rice", "Millet khichdi, salad"),
            dairy("Curd rice with cucumber", "Quinoa pulao, cucumber salad"),
        ],
        "snack": [
            "Sprouts chaat",
            "Roasted chana and walnuts",
            dairy("Unsweetened yogurt with chia", "Soy yogurt with chia"),
            "Apple or guava slices",
            "Carrot sticks with hummus",
        ],
        "dinner": [
            nv("Grilled fish with steamed vegetables", "Grilled tofu with steamed vegetables"),
            "Dal, roti, sautéed greens",
            dairy("Paneer bhurji with roti", "Tofu bhurji with roti"),
            "Vegetable curry with cauliflower rice",
            "Khichdi with cucumber salad",
        ],
    }
    dia_alt2 = {
        "breakfast": [
            "Besan chilla, herbal tea",
            dairy("Greek yogurt with chia and berries", "Soy yogurt with chia and berries"),
            "Idli with sambar",
            "Vegetable dalia",
            "Ragi idli with sambar",
        ],
        "lunch": [
            "Brown rice, chole, salad",
            "Whole wheat roti, dal, bhindi/leafy greens",
            nv("Tandoori chicken with salad", "Paneer tikka with salad") if dairy_ok else "Tofu tikka with salad",
            "Millet khichdi, salad",
        ],
        "snack": [
            "Roasted peanuts (small portion) and fruit",
            "Sprouted moong salad",
            dairy("Buttermilk (unsweetened)", "Coconut water"),
            "Tomato-cucumber salad",
        ],
        "dinner": [
            nv("Grilled chicken with steamed broccoli", "Stir-fry tofu with vegetables"),
            "Dal, roti, sautéed greens",
            "Vegetable soup and salad",
            "Quinoa vegetable bowl",
        ],
    }
    dia_alt3 = {
        "breakfast": [
            "Oats upma, herbal tea",
            "Ragi dosa, sambar",
            "Poha with peanuts (low oil)",
            dairy("Curd with flax seeds", "Soy yogurt with flax seeds"),
        ],
        "lunch": [
            "Brown rice, sambar, salad",
            "Roti, dal, mixed veg",
            nv("Fish tikka with salad", "Grilled tofu with salad"),
            "Quinoa pulao, salad",
        ],
        "snack": [
            "Roasted chana",
            "Apple slices, almonds",
            "Carrot sticks, hummus",
            dairy("Lassi (unsweetened, low-fat)", "Unsweetened soy milk"),
        ],
        "dinner": [
            "Khichdi with salad",
            nv("Grilled fish with vegetables", "Paneer/tofu curry with roti") if dairy_ok else "Tofu curry with roti",
            "Vegetable curry with cauliflower rice",
            "Dal, roti, sautéed greens",
        ],
    }
    chol_alt1 = {
        "breakfast": [
            "Oats upma, herbal tea",
            "Ragi idli with sambar",
            "Vegetable poha with peanuts",
            dairy("Greek yogurt with chia and berries", "Soy yogurt with chia and berries"),
            "Multigrain toast with tomato chutney",
            "Fruit bowl and soaked almonds",
        ],
        "lunch": [
            "Brown rice, chole, salad",
            "Whole wheat roti, dal, mixed sabzi",
            "Millet khichdi, salad",
            nv("Grilled fish with lemon, salad", "Grilled tofu with lemon, salad"),
            "Mixed bean salad with olive oil and lemon",
            dairy("Vegetable daliya with curd", "Vegetable daliya with cucumber salad"),
        ],
        "snack": [
            "Roasted chana",
            "Sprouts chaat",
            "Carrot and cucumber sticks with hummus",
            "Apple slices and walnuts",
            dairy("Buttermilk (low-fat, unsalted)", "Coconut water"),
        ],
        "dinner": [
            "Dal, roti, sautéed greens",
            "Vegetable soup and salad",
            nv("Grilled chicken breast with vegetables", "Stir-fry vegetables with tofu"),
            "Khichdi with salad",
            "Quinoa vegetable salad",
        ],
    }
    chol_alt2 = {
        "breakfast": [
            "Masala oats, green tea",
            "Vegetable dalia",
            "Upma with vegetables",
            dairy("Curd with chia seeds", "Soy yogurt with chia seeds"),
        ],
        "lunch": [
            "Brown rice, rajma, salad",
            "Roti, dal, bhindi/leafy greens",
            nv("Fish curry with salad", "Tofu curry with salad"),
            "Quinoa pulao, salad",
        ],
        "snack": [
            "Roasted almonds (small portion) and fruit",
            "Sprouted moong salad",
            "Tomato-cucumber salad",
            dairy("Buttermilk (low-fat)", "Coconut water"),
        ],
        "dinner": [
            "Vegetable soup and salad",
            "Dal, roti, sautéed greens",
            nv("Grilled chicken tikka with vegetables", "Grilled tofu with vegetables"),
            "Millet khichdi, salad",
        ],
    }
    chol_alt3 = {
        "breakfast": [
            "Oats porridge with nuts",
            "Ragi dosa, sambar",
            "Poha (low oil) and herbal tea",
            "Multigrain porridge with seeds",
        ],
        "lunch": [
            "Brown rice, sambar, salad",
            "Roti, chole, mixed veg",
            "Quinoa salad with lemon dressing",
            nv("Grilled fish with steamed vegetables", "Grilled tofu with steamed vegetables"),
        ],
        "snack": [
            "Roasted chana and walnuts",
            "Carrot sticks, hummus",
            "Apple or guava slices",
            dairy("Low-fat curd", "Soy yogurt"),
        ],
        "dinner": [
            "Khichdi with salad",
            "Dal, roti, sautéed greens",
            "Vegetable curry with cauliflower rice",
            "Mixed bean salad",
        ],
    }
    both_alt1 = {
        "breakfast": [
            "Besan chilla with mint chutney",
            "Oats upma, herbal tea",
            "Ragi dosa with sambar",
            "Vegetable dalia",
            "Idli with sambar",
        ],
        "lunch": [
            "Roti, dal, mixed veg (low oil)",
            "Brown rice, sambar, salad",
            "Millet khichdi, salad",
            nv("Grilled fish with steamed vegetables", "Grilled tofu with steamed vegetables"),
            "Quinoa veggie bowl",
        ],
        "snack": [
            "Sprouts salad",
            "Roasted chana",
            "Apple or guava slices",
            dairy("Unsweetened curd with chia", "Soy yogurt with chia"),
            "Tomato-cucumber salad",
        ],
        "dinner": [
            "Dal, roti, sautéed greens",
            "Vegetable curry with cauliflower rice",
            "Tofu stir-fry with vegetables",
            "Khichdi with salad",
            nv("Grilled chicken/fish with vegetables", "Grilled tofu with vegetables"),
        ],
    }
    both_alt2 = {
        "breakfast": [
            "Ragi idli, sambar",
            dairy("Greek yogurt with berries", "Soy yogurt with berries"),
            "Multigrain porridge with seeds",
            "Upma with vegetables",
        ],
        "lunch": [
            "Roti, dal, greens",
            "Brown rice, rajma, salad",
            "Millet khichdi, salad",
            nv("Fish tikka with salad", "Paneer/tofu tikka with salad") if dairy_ok else "Tofu tikka with salad",
        ],
        "snack": [
            "Roasted peanuts (small portion) and fruit",
            "Sprouted moong chaat",
            "Carrot sticks, hummus",
            dairy("Buttermilk (unsweetened)", "Coconut water"),
        ],
        "dinner": [
            "Vegetable soup and salad",
            "Dal, roti, sautéed greens",
            "Quinoa vegetable bowl",
            nv("Grilled chicken breast with vegetables", "Stir-fry tofu with vegetables"),
        ],
    }
    both_alt3 = {
        "breakfast": [
            "Oats porridge, green tea",
            "Besan chilla",
            "Vegetable dalia",
            "Poha (low oil)",
        ],
        "lunch": [
            "Brown rice, sambar, salad",
            "Roti, chole, mixed veg",
            "Quinoa salad with lemon dressing",
            nv("Grilled fish with steamed vegetables", "Grilled tofu with steamed vegetables"),
        ],
        "snack": [
            "Roasted chana",
            "Apple slices and walnuts",
            dairy("Low-fat curd with chia", "Soy yogurt with chia"),
            "Tomato-cucumber salad",
        ],
        "dinner": [
            "Khichdi with salad",
            "Dal, roti, sautéed greens",
            "Vegetable curry with cauliflower rice",
            nv("Grilled chicken/fish with vegetables", "Grilled tofu with vegetables"),
        ],
    }
    gen_alt = {
        "breakfast": [
            dairy("Oatmeal with skim milk, green tea", "Oatmeal with soy milk, green tea"),
            "Vegetable smoothie and whole grain toast",
            "Idli with sambar, herbal tea",
            "Upma with vegetables, green tea",
        ],
        "lunch": [
            nv("Grilled chicken salad with olive oil and lemon", "Quinoa salad with legumes"),
            "Dal, brown rice, mixed vegetables",
            "Chickpea salad wrap with lettuce and tomato",
        ],
        "snack": [
            "Apple slices, almonds",
            dairy("Low-fat yogurt, berries", "Berries with nuts"),
            "Carrot sticks, hummus",
            "Roasted chana, walnuts",
        ],
        "dinner": [
            nv("Steamed fish with steamed vegetables", "Grilled tofu with steamed vegetables"),
            "Vegetable curry with cauliflower rice",
            "Lentil soup with whole grain bread",
            "Whole wheat roti with dal and sautéed greens",
        ],
    }
    if group == "diabetes":
        return build_week(random.choice([dia_alt1, dia_alt2, dia_alt3]))
    if group == "cholesterol":
        return build_week(random.choice([chol_alt1, chol_alt2, chol_alt3]))
    if group == "both":
        return build_week(random.choice([both_alt1, both_alt2, both_alt3]))
    return build_week(gen_alt)

def meal_plan_text(plan):
    lines = []
    for i, day in enumerate(plan, start=1):
        lines.append(f"Day {i}:")
        lines.append(f"Breakfast: {day['breakfast']}")
        lines.append(f"Lunch: {day['lunch']}")
        lines.append(f"Snack: {day['snack']}")
        lines.append(f"Dinner: {day['dinner']}")
        lines.append("")
    return "\n".join(lines).strip()
def meal_plan_pdf(plan):
    txt = meal_plan_text(plan)
    font = ImageFont.load_default()
    width, height = 800, 1100
    margin = 40
    max_chars = 90
    try:
        tmp = Image.new("RGB", (width, height), "white")
        draw_tmp = ImageDraw.Draw(tmp)
        bbox = draw_tmp.textbbox((0, 0), "A", font=font)
        line_height = (bbox[3] - bbox[1]) + 6
    except Exception:
        tmp = Image.new("RGB", (width, height), "white")
        draw_tmp = ImageDraw.Draw(tmp)
        w, h = draw_tmp.textsize("A", font=font)
        line_height = h + 6
    lines = []
    for para in txt.split("\n"):
        wrapped = textwrap.wrap(para, width=max_chars) if para else [""]
        lines.extend(wrapped + [""])
    pages = []
    y = margin
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    for line in lines:
        if y + line_height > height - margin:
            pages.append(img)
            img = Image.new("RGB", (width, height), "white")
            draw = ImageDraw.Draw(img)
            y = margin
        draw.text((margin, y), line, fill="black", font=font)
        y += line_height
    pages.append(img)
    buf = io.BytesIO()
    pages[0].save(buf, format="PDF", save_all=True, append_images=pages[1:])
    return buf.getvalue()
def has_required_numeric_data(d):
    req = ["age", "glucose", "cholesterol", "blood_pressure", "bmi"]
    return d is not None and all(k in d and d[k] is not None for k in req)
# -------------------- USER INPUT --------------------
uploaded_file = st.file_uploader(
    "📄 Upload Medical Report",
    type=["pdf","png","jpg","jpeg","txt","csv"]
)

diet_type = st.selectbox("🥦 Select Diet Type", ["Veg","Non-Veg"])

if st.button("🍽 Generate Diet Plan") and uploaded_file:
    text = extract_text(uploaded_file)
    name, age = extract_patient_info(text)

    condition, avoid, lifestyle = generate_diet(text)

    has_diabetes = "Diabetes" in condition
    has_cholesterol = "High Cholesterol" in condition

    plan = generate_meal_plan(has_diabetes, has_cholesterol, diet_type)

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