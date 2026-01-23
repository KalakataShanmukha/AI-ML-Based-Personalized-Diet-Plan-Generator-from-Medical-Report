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
    text = ""
    numeric_data = None
    file_type = uploaded_file.name.split(".")[-1].lower()

    if file_type == "pdf":
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""

    elif file_type in ["png", "jpg", "jpeg"]:
        image = Image.open(uploaded_file)
        text = pytesseract.image_to_string(image)

    elif file_type == "txt":
        text = uploaded_file.read().decode("utf-8")

    elif file_type == "csv":
        df = pd.read_csv(uploaded_file)
        text = df["doctor_prescription"].iloc[0]
        numeric_data = df.iloc[0].to_dict()

    return text, numeric_data

