import joblib
import pandas as pd

class HealthRiskAnalyzer:
    def __init__(self, model_file):
        self.model_file = model_file
        self._model = None
        self.features = (
            "age",
            "glucose",
            "cholesterol",
            "blood_pressure",
            "bmi"
        )

    def _load(self):
        if self._model is None:
            self._model = joblib.load(self.model_file)

    def analyze(self, patient_record):
        self._load()
        
        row = {f: float(patient_record.get(f, 0)) for f in self.features}
        frame = pd.DataFrame([row])
        
        pred_label = int(self._model.predict(frame)[0])
        status_map = {0: "Normal", 1: "Abnormal"}
        
        return status_map.get(pred_label, "Unknown")