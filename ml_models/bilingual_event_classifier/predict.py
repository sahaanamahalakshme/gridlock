"""
predict.py
==========
THIS IS THE FILE Person B's FastAPI imports.

Exposes one function:
    classify(description: str) -> dict

Returns:
    {
        "event_cause":         "vehicle_breakdown",
        "cause_confidence":    0.91,
        "severity":            "High",            # same as priority, renamed for API clarity
        "severity_confidence": 0.87,
        "top3_causes": [
            {"label": "vehicle_breakdown", "confidence": 0.91},
            {"label": "accident",          "confidence": 0.06},
            {"label": "debris",            "confidence": 0.02},
        ]
    }

Usage by Person B in FastAPI:
    from ml_models.bilingual_event_classifier.predict import classify

    @app.post("/classify")
    async def classify_event(body: ClassifyRequest):
        return classify(body.description)

Models are loaded lazily on the first call to classify() — safe to import
before training has completed.  Once loaded they are cached for all
subsequent requests (no per-request overhead).

Usage for standalone testing:
    python predict.py
"""

import joblib
import torch
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT       = Path(__file__).resolve().parent          # bilingual_event_classifier/
MODELS_DIR = ROOT / "models"

EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

# ── Device ────────────────────────────────────────────────────────────────────
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# ── Lazy model cache (populated on first call to classify()) ──────────────────
_models: dict | None = None


def _load_models() -> dict:
    """Load all artefacts once; raise a clear error if training hasn't run yet."""
    global _models
    if _models is not None:
        return _models

    missing = [
        f for f in [
            "cause_classifier.joblib",
            "priority_classifier.joblib",
            "cause_label_encoder.joblib",
            "priority_label_encoder.joblib",
        ]
        if not (MODELS_DIR / f).exists()
    ]
    if missing:
        raise FileNotFoundError(
            f"[predict] Missing model files in {MODELS_DIR}/:\n  "
            + "\n  ".join(missing)
            + "\n\nRun the training pipeline first:\n"
            + "  python clean_data.py\n"
            + "  python split_data.py\n"
            + "  python train_model.py\n"
            + "  python validate_tune.py"
        )

    print(f"[predict] Loading models (device={DEVICE}) ...")
    _models = {
        "encoder":      SentenceTransformer(EMBEDDING_MODEL, device=DEVICE),
        "cause_clf":    joblib.load(MODELS_DIR / "cause_classifier.joblib"),
        "priority_clf": joblib.load(MODELS_DIR / "priority_classifier.joblib"),
        "cause_le":     joblib.load(MODELS_DIR / "cause_label_encoder.joblib"),
        "priority_le":  joblib.load(MODELS_DIR / "priority_label_encoder.joblib"),
    }
    print("[predict] Models loaded.")
    return _models


def classify(description: str) -> dict:
    """
    Classify a single event description (Kannada, English, or code-mixed).

    Args:
        description: Raw text from the event log.

    Returns:
        dict with:
            event_cause         – predicted cause label  (e.g. "vehicle_breakdown")
            cause_confidence    – probability 0-1
            severity            – "High" or "Low"  (maps to the priority column)
            severity_confidence – probability 0-1
            top3_causes         – list of {label, confidence} for the top 3 causes
    """
    if not description or not description.strip():
        return {
            "event_cause":         "unknown",
            "cause_confidence":    0.0,
            "severity":            "unknown",
            "severity_confidence": 0.0,
            "top3_causes":         [],
            "error":               "Empty description provided.",
        }

    m = _load_models()

    # Embed the input
    embedding = m["encoder"].encode(
        [description.strip()],
        convert_to_numpy=True,
        normalize_embeddings=True,
    )  # shape: (1, 384)

    # ── Cause prediction ──────────────────────────────────────────────────────
    cause_probs = m["cause_clf"].predict_proba(embedding)[0]   # (n_classes,)
    cause_idx   = int(np.argmax(cause_probs))
    cause_label = m["cause_le"].classes_[cause_idx]
    cause_conf  = float(cause_probs[cause_idx])

    # Top-3 causes
    top3_idx = np.argsort(cause_probs)[::-1][:3]
    top3 = [
        {"label": m["cause_le"].classes_[i], "confidence": round(float(cause_probs[i]), 4)}
        for i in top3_idx
    ]

    # ── Severity prediction (trained on the 'priority' column: High / Low) ────
    prio_probs = m["priority_clf"].predict_proba(embedding)[0]
    prio_idx   = int(np.argmax(prio_probs))
    severity   = m["priority_le"].classes_[prio_idx]   # "High" or "Low"
    prio_conf  = float(prio_probs[prio_idx])

    return {
        "event_cause":         cause_label,
        "cause_confidence":    round(cause_conf, 4),
        "severity":            severity,
        "severity_confidence": round(prio_conf, 4),
        "top3_causes":         top3,
    }


# ── Standalone test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    test_inputs = [
        "Vehicle breakdown on Mysore road near toll gate",
        "ವಾಹನ ಕೆಟ್ಟು ನಿಂತಿದೆ",                          # Kannada: "vehicle broke down"
        "Traffic jam due to accident near silk board",
        "Heavy rain causing waterlogging at Koramangala",
        "VIP movement from airport to Raj Bhavan",
        "Road blocked due to fallen tree after storm",
        "ರಸ್ತೆ ಅಪಘಾತ ಆಗಿದೆ, ಸಂಚಾರ ನಿಧಾನ",              # Kannada: "road accident, traffic slow"
    ]

    print(f"\n[predict] Device: {DEVICE}")
    print("\n" + "=" * 65)
    print("STANDALONE CLASSIFY TEST")
    print("=" * 65)
    for text in test_inputs:
        result = classify(text)
        print(f"\nInput    : {text}")
        print(f"  Cause    : {result['event_cause']}  ({result['cause_confidence']*100:.1f}%)")
        print(f"  Severity : {result['severity']}  ({result['severity_confidence']*100:.1f}%)")
        top3_display = [(r['label'], f"{r['confidence']*100:.1f}%") for r in result['top3_causes']]
        print(f"  Top-3    : {top3_display}")