"""Illustrative fraud classifier; reviewed feedback is incorporated only through retraining."""
import csv
import os
import threading
from pathlib import Path

import joblib
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

BASE = Path(__file__).resolve().parent
MODEL = None
_MODEL_LOCK = threading.RLock()
_MODEL_MTIME = None
MODEL_PATH = Path(os.environ.get("JOBGUARD_MODEL_PATH", str(BASE / "model_store" / "fraud_model.joblib")))

def read_examples(path):
    with Path(path).open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    examples = [(r["text"].strip(), int(r["fraud"])) for r in rows]
    if not examples or set(y for _, y in examples) != {0, 1}:
        raise ValueError("Training examples must contain both classes")
    return examples

def train(examples=None):
    if examples is None:
        examples = read_examples(BASE / "data" / "jobs.csv")
    model = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2))),
        ("lr", LogisticRegression(class_weight="balanced", random_state=42, max_iter=1000)),
    ])
    model.fit([text for text, _ in examples], [label for _, label in examples])
    return model

def current_model():
    global MODEL, _MODEL_MTIME
    with _MODEL_LOCK:
        mtime = MODEL_PATH.stat().st_mtime_ns if MODEL_PATH.exists() else None
        if MODEL is None or mtime != _MODEL_MTIME:
            # Only a trusted administrator can write the model artifact.
            MODEL = joblib.load(MODEL_PATH) if mtime is not None else train()
            _MODEL_MTIME = mtime
        return MODEL

def refresh_model():
    global MODEL, _MODEL_MTIME
    with _MODEL_LOCK:
        MODEL = None
        _MODEL_MTIME = None

def predict(text):
    """Combine illustrative ML score with explicit high-concern safety indicators."""
    import re
    probability = float(current_model().predict_proba([text])[0, 1])
    lower = text.lower()
    warnings = []
    payment = bool(re.search(r"\b(registration|processing|application|interview)\s+fee\b|\bpay\s+(?:an?\s+)?(?:upfront|deposit|fee)\b|\bdeposit\s+required\b|\bsend\s+money\b", lower))
    banking = bool(re.search(r"\b(bank(?:ing)?\s+(?:details|information|account)|account\s+(?:number|details))\b", lower))
    secrecy = bool(re.search(r"\b(do\s+not\s+tell\s+anyone|don't\s+tell\s+anyone|come\s+alone|isolated\s+location|keep\s+(?:this|it)\s+secret)\b", lower))
    if payment:
        warnings.append("Upfront payment")
    if banking:
        warnings.append("Banking information requested")
    if secrecy:
        warnings.append("Secrecy or unsafe meeting request")
    if "whatsapp only" in lower:
        warnings.append("WhatsApp-only contact")
    if "guaranteed income" in lower:
        warnings.append("Guaranteed income claim")
    high_concern = payment or banking or secrecy
    return {
        "label": "Potentially fraudulent" if high_concern or probability >= 0.5 else "Likely legitimate",
        "risk_percent": round(probability * 100, 1),
        "safety_level": "High concern" if high_concern else ("Review recommended" if probability >= 0.5 else "No specific warning detected"),
        "warnings": warnings,
        "model": "Trained TF-IDF + Logistic Regression with explicit safety rules",
        "disclaimer": "Educational prototype only. NOT a verified fraud decision or employer safety guarantee.",
    }

if __name__ == "__main__":
    print("Model trained:", len(train().named_steps["lr"].coef_[0]), "features")
