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
    # -------------------- Meal options --------------------
    # Diabetes
    diabetes_meals = {
        "Veg": {
            "Breakfast": ["Oats with berries","Vegetable Dalia","Moong dal chilla","Multigrain toast with peanut butter","Smoothie with almond milk and spinach","Besan chilla with vegetables","Poha with peas and carrots","Upma with veggies","Greek yogurt with flaxseeds","Masala oats","Whole wheat sandwich with cucumber and tomato","Quinoa porridge with nuts","Spinach and egg white omelette","Chia pudding with almond milk","Low-fat paneer toast","Avocado toast with chia seeds","Cottage cheese smoothie","Vegetable idli","Sprouts upma","Almond flour pancakes"],
            "Lunch": ["Brown rice with dal and vegetables","Grilled veggies with quinoa","Chickpea salad with olive oil dressing","Vegetable soup with chapati","Paneer stir fry with spinach and peppers","Lentil salad with cucumber and tomato","Millet khichdi with vegetables","Grilled tofu with sautéed veggies","Vegetable curry with whole wheat roti","Mixed bean salad","Zucchini noodles with tomato sauce","Vegetable stir fry with brown rice","Palak dal with millet roti","Quinoa salad with roasted veggies","Steamed broccoli with grilled paneer","Low-fat vegetable lasagna","Tomato and cucumber salad with lentils","Baked tofu with bell peppers","Cauliflower rice with veggies"],
            "Snacks": ["Nuts (almonds, walnuts)","Seeds (pumpkin, sunflower)","Sprouts salad","Greek yogurt with cinnamon","Roasted chana","Carrot sticks with hummus","Apple slices with peanut butter","Cucumber and tomato salad","Mixed berries","Protein shake with almond milk","Boiled eggs","Celery sticks with hummus","Roasted almonds with cinnamon","Low-fat paneer cubes","Vegetable sticks with guacamole","Homemade trail mix","Green smoothie with spinach","Walnut and flaxseed mix","Edamame beans","Kale chips"],
            "Dinner": ["Grilled fish with vegetables","Tofu stir fry with bell peppers","Vegetable soup","Zoodles with tomato sauce","Light lentil curry with spinach","Steamed vegetables with quinoa","Paneer tikka with salad","Stir-fried mushrooms and broccoli","Baked salmon with asparagus","Cauliflower rice with veggies","Grilled chicken with sautéed vegetables","Vegetable curry with millet roti","Low-fat vegetable stew","Baked tofu with green beans","Spinach soup with whole wheat toast","Vegetable stir fry with tofu","Masala grilled paneer with salad","Zucchini and carrot noodles","Quinoa with roasted vegetables","Vegetable khichdi"]
        },
        "Non-Veg": {
            "Breakfast": ["Egg white omelette with spinach","Oats with milk and nuts","Smoothie with protein powder","Boiled eggs with tomato","Poha with eggs","Masala oats with milk","Whole wheat toast with boiled egg","Quinoa porridge with almonds","Vegetable and egg chilla","Scrambled eggs with vegetables"],
            "Lunch": ["Grilled chicken with brown rice","Fish curry with steamed vegetables","Egg curry with chapati","Grilled salmon with quinoa","Chicken salad with olive oil","Tuna salad with veggies","Egg bhurji with roti","Baked fish with vegetables","Chicken stir fry with broccoli","Seafood soup with millet"],
            "Snacks": ["Boiled eggs","Chicken salad","Greek yogurt with nuts","Protein shake","Roasted chickpeas","Cottage cheese with fruits","Carrot sticks with hummus","Edamame beans","Mixed nuts","Celery sticks with peanut butter"],
            "Dinner": ["Grilled chicken with vegetables","Baked fish with asparagus","Egg curry with spinach","Seafood stir fry","Chicken soup with vegetables","Tuna steak with roasted veggies","Grilled salmon with zucchini noodles","Low-fat chicken curry","Vegetable and egg stir fry","Baked fish with cauliflower rice"]
        }
    }

    # Cholesterol
    cholesterol_meals = {
        "Veg": {
            "Breakfast": ["Oats with apple and cinnamon","Multigrain toast with avocado","Vegetable smoothie with flaxseeds","Poha with peas","Chia pudding with berries","Quinoa porridge with nuts","Masala oats with vegetables","Green smoothie with spinach and banana","Whole wheat vegetable upma","Soy milk smoothie with berries","Sprouted moong salad","Almond flour pancakes","Low-fat paneer toast","Vegetable idli","Spinach and tomato omelette","Cottage cheese smoothie","Avocado and chia seed toast","Fruit and nut bowl","Overnight oats with seeds","Buckwheat porridge"],
            "Lunch": ["Grilled fish or chicken with salad","Brown rice with lentils and vegetables","Quinoa salad with chickpeas","Vegetable soup with whole wheat bread","Paneer salad with olive oil","Stir-fried tofu with broccoli","Lentil soup with vegetables","Baked salmon with quinoa","Mixed vegetable curry with millet roti","Chickpea and spinach stir fry","Vegetable khichdi with flaxseeds","Grilled chicken with sautéed vegetables","Steamed broccoli with tofu","Zucchini noodles with tomato sauce","Quinoa bowl with roasted veggies","Vegetable stir fry with brown rice","Palak dal with millet roti","Baked fish with green beans","Sprout salad with olive oil"],
            "Snacks": ["Nuts (almonds, walnuts, pistachios)","Fruit bowl (apple, pear, berries)","Hummus with carrots/cucumber","Roasted chickpeas","Green smoothie with kale","Air-popped popcorn","Cucumber and tomato slices","Low-fat yogurt with seeds","Celery sticks with almond butter","Sprouts salad","Boiled eggs","Carrot and celery sticks with hummus","Mixed nuts with raisins","Vegetable sticks with guacamole","Protein smoothie with almond milk","Roasted pumpkin seeds","Kale chips","Edamame beans","Fruit and nut energy balls"],
            "Dinner": ["Grilled salmon or tofu with vegetables","Stir-fried veggies with tofu","Vegetable soup with herbs","Zoodles with tomato sauce","Steamed vegetables with brown rice","Baked chicken breast with salad","Quinoa bowl with roasted vegetables","Vegetable curry with millet roti","Paneer tikka with green salad","Lentil and spinach soup","Baked fish with asparagus","Stir-fried mushrooms and broccoli","Grilled tofu with spinach","Vegetable khichdi with flaxseeds","Low-fat vegetable stew","Masala grilled paneer with salad","Zucchini and carrot noodles","Vegetable stir fry with quinoa","Baked chicken with roasted vegetables","Grilled fish with sautéed vegetables"]
        },
        "Non-Veg": {
            "Breakfast": ["Egg omelette with vegetables","Scrambled eggs with spinach","Boiled eggs with toast","Protein smoothie with milk","Egg white omelette","Oats with milk and nuts","Masala oats with egg","Quinoa porridge with eggs","Whole wheat toast with boiled eggs","Vegetable egg chilla"],
            "Lunch": ["Grilled chicken salad","Baked fish with vegetables","Egg curry with chapati","Tuna salad with olive oil","Chicken stir fry with brown rice","Grilled salmon with quinoa","Egg bhurji with roti","Seafood soup with vegetables","Baked fish with asparagus","Low-fat chicken curry"],
            "Snacks": ["Boiled eggs","Chicken salad","Protein shake","Greek yogurt with nuts","Roasted chickpeas","Cottage cheese with fruits","Carrot sticks with hummus","Edamame beans","Mixed nuts","Celery sticks with peanut butter"],
            "Dinner": ["Grilled chicken with vegetables","Baked fish with zucchini noodles","Egg curry with spinach","Seafood stir fry","Chicken soup with vegetables","Tuna steak with roasted veggies","Grilled salmon with roasted vegetables","Low-fat chicken curry","Vegetable and egg stir fry","Baked fish with cauliflower rice"]
        }
    }

    # -------------------- General Health --------------------
    general_meals = {
        "Veg": {
            "Breakfast": ["Oats","Idli","Dosa","Poha","Upma","Toast","Smoothie"],
            "Lunch": ["Dal Rice","Chapati Curry","Khichdi","Quinoa Bowl","Paneer","Salad","Veg Biryani"],
            "Snacks": ["Fruits","Nuts","Sprouts","Yogurt","Seeds","Protein Shake","Roasted Chana"],
            "Dinner": ["Soup","Salad","Grilled Veg","Paneer","Tofu","Zoodles","Light Curry"]
        },
        "Non-Veg": {
            "Breakfast": ["Eggs","Oats with milk","Chicken Sausage","Scrambled Eggs","Protein Shake"],
            "Lunch": ["Grilled Chicken","Egg Curry with Rice","Fish Curry","Chicken Salad","Tuna Sandwich"],
            "Snacks": ["Boiled Eggs","Chicken Slices","Protein Shake","Greek Yogurt","Nuts with Cheese"],
            "Dinner": ["Grilled Chicken","Fish Curry with Veggies","Egg Stir Fry","Chicken Soup","Baked Fish"]
        }
    }

    # -------------------- Determine condition --------------------
    if "diabetes" in text:
        condition = "Diabetes"
        avoid = ["Sugar", "White rice", "Soft drinks", "Sweets", "Refined flour"]
        meals = diabetes_meals[diet_type]
    elif "cholesterol" in text:
        condition = "High Cholesterol"
        avoid = ["Fried food", "Butter", "Red meat", "Full-fat dairy", "Processed snacks"]
        meals = cholesterol_meals[diet_type]
    else:
        condition = "General Health"
        avoid = ["Junk food", "Excess sugar"]
        meals = general_meals[diet_type]

    # -------------------- Lifestyle Advice --------------------
    lifestyle = [
        "Exercise at least 30 minutes daily",
        "Drink 2–3 liters of water",
        "Sleep 7–8 hours daily",
        "Limit processed and high-fat foods"
    ]

    # -------------------- Generate 7-day plan --------------------
    days = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

    breakfast_plan = random.sample(meals["Breakfast"], min(7, len(meals["Breakfast"])))
    lunch_plan = random.sample(meals["Lunch"], min(7, len(meals["Lunch"])))
    snacks_plan = random.sample(meals["Snacks"], min(7, len(meals["Snacks"])))
    dinner_plan = random.sample(meals["Dinner"], min(7, len(meals["Dinner"])))

    df = pd.DataFrame({
        "Day": days,
        "Breakfast": breakfast_plan,
        "Lunch": lunch_plan,
        "Snacks": snacks_plan,
        "Dinner": dinner_plan
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

    elements.append(Paragraph(f"<b>Name:</b> {name}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Age:</b> {age}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Condition:</b> {condition}", styles["Normal"]))
    elements.append(Paragraph(f"<b>Diet Type:</b> {diet_type}", styles["Normal"]))
    elements.append(Paragraph("<br/>", styles["Normal"]))

    for _, row in diet_df.iterrows():
        elements.append(Paragraph(
            f"""
            <b>{row['Day']}</b><br/>
            Breakfast: {row['Breakfast']}<br>
            Lunch: {row['Lunch']}<br>
            Snacks: {row['Snacks']}<br>
            Dinner: {row['Dinner']}<br/><br/>
            """,
            styles["Normal"]
        ))

    elements.append(Paragraph("<b>Foods to Avoid</b>", styles["Heading2"]))
    elements.append(Paragraph(", ".join(avoid), styles["Normal"]))
    elements.append(Paragraph("<br/>", styles["Normal"]))

    elements.append(Paragraph("<b>Lifestyle Recommendations</b>", styles["Heading2"]))
    for l in lifestyle:
        elements.append(Paragraph(f"- {l}", styles["Normal"]))

    doc.build(elements)
    buffer.seek(0)
    return buffer

# -------------------- USER INPUT --------------------
uploaded_file = st.file_uploader("📄 Upload Medical Report", type=["pdf","png","jpg","jpeg","txt","csv"])
diet_type = st.selectbox("🥦 Select Diet Type", ["Veg","Non-Veg"])

if st.button("🍽 Generate Diet Plan") and uploaded_file:
    text = extract_text(uploaded_file)
    name, age = extract_patient_info(text)
    condition, avoid, lifestyle, diet_df = generate_diet(text, diet_type=diet_type)

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
        for col, idx in zip([col1, col2], [i, i+1]):
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

    # Lifestyle
    lifestyle_html = "".join([f"<li>{l}</li>" for l in lifestyle])
    st.markdown(f"""
    <div class="info-card">
        <div class="info-header">🏃 Lifestyle Recommendations</div>
        <ul>{lifestyle_html}</ul>
    </div>
    """, unsafe_allow_html=True)

    # ---------------- DOWNLOADS ----------------
    pdf_file = generate_diet_pdf(name, age, condition, diet_type, avoid, lifestyle, diet_df)

    st.download_button(
        "📄 Download Diet Plan PDF",
        pdf_file,
        "AI_Diet_Plan.pdf",
        mime="application/pdf"
    )

    st.download_button(
        "📥 Download Diet Plan JSON",
        json.dumps(diet_df.to_dict(), indent=4),
        "diet_plan.json"
    )