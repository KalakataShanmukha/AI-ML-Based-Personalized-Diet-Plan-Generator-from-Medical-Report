import pdfplumber
import pytesseract
from PIL import Image
import pandas as pd
import re

# --------------------------------------------------
# REGEX MEDICAL INFO EXTRACTION
# --------------------------------------------------
def extract_medical_info(text):
    results = {}
    text_clean = " ".join(text.split())

    # Name
    name_match = re.search(
        r"Patient Name[:\-]?\s*([A-Za-z]{2,20}\s+[A-Za-z]{2,20})",
        text_clean,
        re.IGNORECASE
    )
    results["name"] = name_match.group(1) if name_match else ""

    # Age
    age_match = re.search(r"Age[:\- ]+(\d{1,3})", text_clean)
    results["age"] = int(age_match.group(1)) if age_match else ""

    # Gender
    sex_match = re.search(r"(Male|Female|M|F)", text_clean, re.IGNORECASE)
    results["sex"] = sex_match.group(1) if sex_match else ""

    # Labs
    patterns = {
        "bmi": r"BMI[:\-]?\s*(\d+\.?\d*)",
        "blood_sugar": r"(Glucose|Blood Sugar)[^\d]*(\d+\.?\d*)",
        "cholesterol": r"Cholesterol[^\d]*(\d+\.?\d*)",
        "hemoglobin": r"(Hb|Hemoglobin)[^\d]*(\d+\.?\d*)"
    }

    for key, pattern in patterns.items():
        m = re.search(pattern, text_clean, re.IGNORECASE)
        results[key] = m.group(2) if m and len(m.groups()) > 1 else (m.group(1) if m else "")

    return results


# --------------------------------------------------
# MAIN EXTRACTOR 
# --------------------------------------------------
def extract_text(uploaded_file):
    ext = uploaded_file.name.split(".")[-1].lower()
    text = ""
    numeric_data = None

    if ext == "pdf":
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

    elif ext in ["png", "jpg", "jpeg"]:
        try:
            img = Image.open(uploaded_file)
            text = pytesseract.image_to_string(img)
        except Exception:
            text = "OCR not supported in this environment."

    elif ext == "txt":
        text = uploaded_file.read().decode("utf-8")

    elif ext == "csv":
        df = pd.read_csv(uploaded_file)

        # Text column (for NLP)
        if "doctor_prescription" in df.columns:
            text = df["doctor_prescription"].iloc[0]

        # Numeric columns (for ML)
        numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns
        if len(numeric_cols) > 0:
            numeric_data = df[numeric_cols].iloc[0].to_dict()

    return text.strip(), numeric_data