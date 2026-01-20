import streamlit as st
import pandas as pd
import pdfplumber
import pytesseract
from PIL import Image
import spacy
from fpdf import FPDF
import io

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
AI-based Personalized Diet Recommendation System
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
    diet = {
        "condition": [],
        "allowed": ["Vegetables", "Whole grains", "Fruits"],
        "restricted": [],
        "diet": [],
        "lifestyle": []
    }
    
    text = text.lower()
    
    if "diabetes" in text:
        diet["condition"].append("Diabetes")
        diet["restricted"].append("Sugar")
        diet["diet"].append("Follow a diabetic-friendly low sugar diet.")
        diet["lifestyle"].append("Walk daily for 30 minutes.")
    
    if "cholesterol" in text:
        diet["condition"].append("High Cholesterol")
        diet["restricted"].append("Oily food")
        diet["diet"].append("Increase fiber intake.")
    
    if "blood pressure" in text or "hypertension" in text:
        diet["condition"].append("Hypertension")
        diet["restricted"].append("Salt")
        diet["diet"].append("Reduce sodium intake.")
        diet["lifestyle"].append("Practice stress management.")
    
    if not diet["condition"]:
        diet["condition"].append("General Health")
        diet["diet"].append("Maintain a balanced diet.")
        diet["lifestyle"].append("Stay active.")
    
    return diet

# -------------------- 7-DAY DIET PLAN --------------------
def generate_7day_plan(diet):
    # Sample meals for demonstration
    sample_meals = {
        "Breakfast": [
            "Oatmeal with skim milk, green tea",
            "Vegetable smoothie, whole grain toast",
            "Greek yogurt with berries",
            "Egg white omelet, whole wheat toast",
            "Fruit salad with nuts",
            "Quinoa porridge with almonds",
            "Avocado toast with herbal tea"
        ],
        "Lunch": [
            "Grilled chicken salad with olive oil dressing",
            "Quinoa salad with legumes",
            "Steamed fish with vegetables",
            "Brown rice with grilled tofu",
            "Lentil soup with salad",
            "Vegetable stir-fry with rice",
            "Grilled salmon with quinoa"
        ],
        "Snack": [
            "Apple slices, almonds",
            "Low-fat yogurt, berries",
            "Carrot sticks, hummus",
            "Handful of nuts",
            "Fruit smoothie",
            "Cucumber slices with yogurt dip",
            "Roasted chickpeas"
        ],
        "Dinner": [
            "Steamed fish, steamed vegetables",
            "Grilled tofu with spinach",
            "Chicken stir-fry with vegetables",
            "Vegetable soup with whole grain bread",
            "Baked salmon with asparagus",
            "Quinoa salad with veggies",
            "Zucchini noodles with tomato sauce"
        ]
    }
    
    plan = {}
    for day in range(1, 8):
        plan[f"Day {day}"] = {
            meal: sample_meals[meal][day-1] for meal in sample_meals
        }
    
    return plan

# -------------------- PDF EXPORT --------------------
def export_pdf(plan, username="JohnDoe"):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"{username}'s 7-Day Diet Plan", ln=True, align='C')
    pdf.ln(5)
    
    pdf.set_font("Arial", '', 12)
    for day, meals in plan.items():
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, day, ln=True)
        pdf.set_font("Arial", '', 12)
        for meal, menu in meals.items():
            pdf.multi_cell(0, 8, f"{meal}: {menu}")
        pdf.ln(3)
    
    pdf_buffer = io.BytesIO()
    pdf.output(pdf_buffer)
    pdf_buffer.seek(0)
    return pdf_buffer

# -------------------- INPUT --------------------
st.subheader("📄 Upload Medical Report")
uploaded_file = st.file_uploader(
    "Upload PDF / Image / TXT / CSV",
    type=["pdf", "png", "jpg", "jpeg", "txt", "csv"]
)

manual_text = st.text_area("Or enter medical notes manually here:")

process_btn = st.button("🍽 Generate 7-Day Diet Plan")

# -------------------- OUTPUT --------------------
if process_btn:
    text = extract_text(uploaded_file) if uploaded_file else manual_text
    
    if not text.strip():
        st.warning("Please upload a file or enter medical notes!")
    else:
        diet = generate_diet(text)
        plan = generate_7day_plan(diet)
        
        # ---------- Extracted Text ----------
        st.markdown(f"""
        <div class='card'>
            <h4>📄 Extracted Text</h4>
            <p>{text[:800]}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # ---------- Health Status ----------
        st.markdown(f"""
        <div class='card'>
            <h4>🩺 Health Status</h4>
            <p>Conditions inferred: {', '.join(diet['condition'])}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # ---------- 7-Day Diet Plan ----------
        for day, meals in plan.items():
            st.markdown(f"""
            <div class='card'>
                <h4>🍽 {day}</h4>
                <b>Breakfast:</b> {meals['Breakfast']}<br>
                <b>Lunch:</b> {meals['Lunch']}<br>
                <b>Snack:</b> {meals['Snack']}<br>
                <b>Dinner:</b> {meals['Dinner']}
            </div>
            """, unsafe_allow_html=True)
        
        # ---------- Export PDF ----------
        pdf_file = export_pdf(plan)
        st.download_button(
            label="📥 Download Diet Plan PDF",
            data=pdf_file,
            file_name="JohnDoe_DietPlan.pdf",
            mime="application/pdf"
        )

# -------------------- CSS --------------------
st.markdown("""
<style>
.stApp {
    background-image: url("https://images.pexels.com/photos/5938/food-salad-healthy-lunch.jpg");
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