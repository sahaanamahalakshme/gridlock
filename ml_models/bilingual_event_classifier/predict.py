import joblib

import torch

import numpy as np

from pathlib import Path

from sentence_transformers import SentenceTransformer

from .routing_map import route_event

ROOT = Path(__file__).resolve().parent

MODELS_DIR = ROOT / "models"


EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"


DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


_models: dict | None = None


def _load_models() -> dict:

    global _models

    if _models is not None:

        return _models

    missing = [
        f
        for f in [
            "cause_classifier.joblib",
            "priority_classifier.joblib",
            "cause_label_encoder.joblib",
            "priority_label_encoder.joblib",
        ]
        if not (MODELS_DIR / f).exists()
    ]

    if missing:

        raise FileNotFoundError(
            f"[predict] Missing model files in {MODELS_DIR }/:\n  "
            + "\n  ".join(missing)
            + "\n\nRun the training pipeline first:\n"
            + "  python clean_data.py\n"
            + "  python split_data.py\n"
            + "  python train_model.py\n"
            + "  python validate_tune.py"
        )

    print(f"[predict] Loading models (device={DEVICE }) ...")

    _models = {
        "encoder": SentenceTransformer(EMBEDDING_MODEL, device=DEVICE),
        "cause_clf": joblib.load(MODELS_DIR / "cause_classifier.joblib"),
        "priority_clf": joblib.load(MODELS_DIR / "priority_classifier.joblib"),
        "cause_le": joblib.load(MODELS_DIR / "cause_label_encoder.joblib"),
        "priority_le": joblib.load(MODELS_DIR / "priority_label_encoder.joblib"),
    }

    print("[predict] Models loaded.")

    return _models


def classify(description: str) -> dict:

    if not description or not description.strip():

        return {
            "event_cause": "unknown",
            "cause_confidence": 0.0,
            "severity": "unknown",
            "severity_confidence": 0.0,
            "top3_causes": [],
            "error": "Empty description provided.",
        }

    m = _load_models()

    embedding = m["encoder"].encode(
        [description.strip()],
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    cause_probs = m["cause_clf"].predict_proba(embedding)[0]

    cause_idx = int(np.argmax(cause_probs))

    cause_label = m["cause_le"].classes_[cause_idx]

    cause_conf = float(cause_probs[cause_idx])

    top3_idx = np.argsort(cause_probs)[::-1][:3]

    top3 = [
        {
            "label": m["cause_le"].classes_[i],
            "confidence": round(float(cause_probs[i]), 4),
        }
        for i in top3_idx
    ]

    prio_probs = m["priority_clf"].predict_proba(embedding)[0]

    prio_idx = int(np.argmax(prio_probs))

    severity = m["priority_le"].classes_[prio_idx]

    prio_conf = float(prio_probs[prio_idx])

    result = {
        "event_cause": cause_label,
        "cause_confidence": round(cause_conf, 4),
        "severity": severity,
        "severity_confidence": round(prio_conf, 4),
        "top3_causes": top3,
    }
    result["routing"] = route_event(result["event_cause"])

    return result


if __name__ == "__main__":

    test_inputs = [
        "Vehicle breakdown on Mysore road near toll gate",
        "ವಾಹನ ಕೆಟ್ಟು ನಿಂತಿದೆ",
        "Traffic jam due to accident near silk board",
        "Heavy rain causing waterlogging at Koramangala",
        "VIP movement from airport to Raj Bhavan",
        "Road blocked due to fallen tree after storm",
        "ರಸ್ತೆ ಅಪಘಾತ ಆಗಿದೆ, ಸಂಚಾರ ನಿಧಾನ",
    ]

    print(f"\n[predict] Device: {DEVICE }")

    print("\n" + "=" * 65)

    print("STANDALONE CLASSIFY TEST")

    print("=" * 65)

    for text in test_inputs:

        result = classify(text)

        print(f"\nInput    : {text }")

        print(
            f"  Cause    : {result ['event_cause']}  ({result ['cause_confidence']*100 :.1f}%)"
        )

        print(
            f"  Severity : {result ['severity']}  ({result ['severity_confidence']*100 :.1f}%)"
        )

        top3_display = [
            (r["label"], f"{r ['confidence']*100 :.1f}%") for r in result["top3_causes"]
        ]

        print(f"  Top-3    : {top3_display }")
