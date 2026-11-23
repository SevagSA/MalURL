import os
import re
from pathlib import Path
import joblib

MODEL_PATH = Path(__file__).resolve().parent / "models" / "model.joblib"
_model = None

STRICTNESS = {
    "high": 0.30, # Strict, blocks at minimal suspicion
    "medium": 0.50,
    "low": 0.75,
}

def clean_url(url: str) -> str:
    """Normalize URL and strip protocol and www., matching data_loader.py"""
    if not isinstance(url, str):
        return ""
    url = url.strip().lower()
    url = re.sub(r"^[a-z]+://", "", url)
    url = re.sub(r"^www\.", "", url)
    return url.rstrip("/")

def _get_model():
    global _model
    if _model is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Model not found at {MODEL_PATH}. Run python -m ml.train first.")
    _model = joblib.load(MODEL_PATH)
    return _model

def predict_url(url: str, strictness: str | None = None) -> dict:
    """Predict if a URL is benign or malicious"""
    level = (strictness or os.getenv("STRICTNESS", "medium")).lower()
    if level not in STRICTNESS:
        raise ValueError(f"Level '{level}' not valid. Use: {list(STRICTNESS.keys())}")

    threshold = STRICTNESS[level]
    cleaned = clean_url(url)
    if not cleaned:
        return {
            "prediction": "benign", 
            "probability": 0.0,
            "strictness": level,
            "threshold": threshold,
        }

    model = _get_model()
    proba = model.predict_proba([cleaned])[0]
    classes = list(model.classes_)

    #Dataset classes: 'benign', 'defacement', 'malware', 'phishing'
    if "benign" in classes:
        benign_idx = classes.index("benign")
        malicious_prob = float(1.0 - proba[benign_idx])
    else:
        malicious_prob = float(proba[1])

    prediction = "malicious" if malicious_prob >= threshold else "benign"
    return {
        "prediction": prediction,
        "probability": round(malicious_prob, 4),
        "strictness": level,
        "threshold": threshold,
    }

if __name__ == "__main__":
    test_urls = [
        "https://www.google.com/search?q=docker",
        "http://www.paypal-login-security-update.xyz/verify",
    ]
    for url in test_urls:
        print(f"\nURL: {url}")
        for level in ("high", "medium", "low"):
            print(f"  [{level}] -> {predict_url(url, strictness=level)}")