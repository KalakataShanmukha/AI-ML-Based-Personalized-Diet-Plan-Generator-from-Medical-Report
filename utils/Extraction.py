import pdfplumber
import pytesseract
from PIL import Image
import pandas as pd
import re


# ==================================================
# MEDICAL FEATURE EXTRACTION (LIGHTGBM COMPATIBLE)
# ==================================================
def extract_medical_info(text: str) -> dict:
    """
    Extracts numeric medical features required by ML model.
    Feature names MUST match LightGBM training features.
    """

    text_clean = " ".join(text.split())

    def find(pattern):
        match = re.search(pattern, text_clean, re.IGNORECASE)
        return float(match.group(1)) if match else 0.0

    features = {
        "age": find(r"Age[:\- ]+(\d{1,3})"),
        "glucose": find(r"(?:Glucose|Blood Sugar)[^\d]*(\d+\.?\d*)"),
        "cholesterol": find(r"Cholesterol[^\d]*(\d+\.?\d*)"),
        "blood_pressure": find(r"(?:BP|Blood Pressure)[^\d]*(\d+\.?\d*)"),
        "bmi": find(r"BMI[:\- ]*(\d+\.?\d*)"),
    }

    return features


# ==================================================
# TEXT EXTRACTION FROM FILES
# ==================================================
def extract_text(uploaded_file):
    """
    Extracts raw text and ML-ready numeric features
    from uploaded medical report.
    """

    text = ""
    file_type = uploaded_file.name.split(".")[-1].lower()

    # -------- PDF --------
    if file_type == "pdf":
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""

    # -------- IMAGE --------
    elif file_type in ["png", "jpg", "jpeg"]:
        image = Image.open(uploaded_file)
        text = pytesseract.image_to_string(image)

    # -------- TEXT --------
    elif file_type == "txt":
        text = uploaded_file.read().decode("utf-8", errors="ignore")

    # -------- CSV --------
    elif file_type == "csv":
        df = pd.read_csv(uploaded_file)
        text = df.to_string(index=False)

    else:
        raise ValueError("Unsupported file format")

    # Extract ML features from text
    numerical_data = extract_medical_info(text)

    return text, numerical_data
