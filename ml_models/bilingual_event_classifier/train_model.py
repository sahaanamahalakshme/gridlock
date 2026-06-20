import sys

import joblib

import torch

import numpy as np

import pandas as pd

from pathlib import Path

from sklearn.linear_model import LogisticRegression

from sklearn.preprocessing import LabelEncoder

from sklearn.metrics import classification_report, accuracy_score
from imblearn.over_sampling import RandomOverSampler  # FIX 3: oversampling
from imblearn.over_sampling import RandomOverSampler  # FIX 3: oversampling

from sentence_transformers import SentenceTransformer


ROOT = Path(__file__).resolve().parent

TRAIN_CSV = ROOT / "data" / "splits" / "train.csv"

MODELS_DIR = ROOT / "models"


DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


# FIX 4: swapped from MiniLM -> mpnet. WHY: MiniLM is a smaller, faster but
# weaker multilingual model. Evidence ("CM Arrival" -> vehicle_breakdown at
# 81% confidence) showed it wasn't separating short domain-specific phrases
# well. mpnet is the same sentence-transformers library/API, just a larger
# backbone with stronger semantic separation -- no code changes needed
# beyond this string, only a slower first download (~1GB vs ~120MB) and
# slightly slower encode time.
EMBEDDING_MODEL = "paraphrase-multilingual-mpnet-base-v2"


LR_C = 4.0

LR_MAXITER = 1000

LR_SOLVER = "lbfgs"

RANDOM_SEED = 42


def embed(
    texts: list[str], model: SentenceTransformer, batch_size: int = 64
) -> np.ndarray:
    """Embed a list of strings using the configured device. Shows a progress bar."""

    return model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )


def oversample(X, y, label):
    """
    FIX 3: Oversample minority classes BEFORE fitting the classifier.

    WHY THIS IS NEEDED ON TOP OF class_weight="balanced":
    class_weight reweights the LOSS function, but it cannot create new
    information -- a class with 30 samples is still only 30 distinct
    points in embedding space, no matter how heavily its errors are
    penalized. The confusion matrix showed several classes (vip_movement,
    debris, protest) at 0.00 recall even WITH balanced weighting, which
    means the decision boundary genuinely never carves out space for them.

    RandomOverSampler duplicates minority-class embedding vectors until
    every class matches the largest class's count. This directly forces
    the classifier to pay attention to minority classes while fitting,
    not just during loss-weighted scoring.
    """
    before_counts = pd.Series(y).value_counts().to_dict()
    ros = RandomOverSampler(random_state=RANDOM_SEED)
    X_resampled, y_resampled = ros.fit_resample(X, y)
    after_counts = pd.Series(y_resampled).value_counts().to_dict()
    print(f"\n[train] Oversampling '{label}': {len(y):,} -> {len(y_resampled):,} rows")
    print(f"  Before (min/max class count): {min(before_counts.values())} / {max(before_counts.values())}")
    print(f"  After  (min/max class count): {min(after_counts.values())} / {max(after_counts.values())}")
    return X_resampled, y_resampled


def train_classifier(X: np.ndarray, y: np.ndarray, label: str) -> LogisticRegression:

    print(f"\n[train] Training Logistic Regression for '{label }' ...")

    clf = LogisticRegression(
        C=LR_C,
        max_iter=LR_MAXITER,
        solver=LR_SOLVER,
        random_state=RANDOM_SEED,
        class_weight="balanced",
        n_jobs=-1,
    )

    clf.fit(X, y)

    train_preds = clf.predict(X)

    acc = accuracy_score(y, train_preds)

    print(
        f"  Train accuracy ({label }): {acc :.4f}  (expect this to be high — train set)"
    )

    return clf


def build_augmented_text(df):
    """
    FIX 4 (context augmentation): prepend police_station to description
    before embedding.

    WHY: short inputs like "CM Arrival" or "Debris" carry almost no signal
    on their own -- the live test showed "CM Arrival" misclassified as
    vehicle_breakdown at 81% confidence. Adding the police_station name
    (e.g. "Cubbon Park: CM Arrival") gives the embedding model genuine
    extra context to work with, since certain stations correlate strongly
    with certain event types in this data (VIP movement events cluster
    near government-area stations, water_logging near low-lying areas).

    Falls back to description alone if police_station is missing, so this
    never crashes on incomplete rows.
    """
    if "police_station" in df.columns:
        station = df["police_station"].fillna("").astype(str).str.strip()
        desc = df["description"].fillna("").astype(str).str.strip()
        combined = station.where(station == "", station + ": " + desc)
        combined = combined.where(station != "", desc)
        return combined.tolist()
    return df["description"].tolist()


def main():

    print(f"[train] Reading: {TRAIN_CSV }")

    if not TRAIN_CSV.exists():

        print("ERROR: train.csv not found. Run split_data.py first.")

        sys.exit(1)

    df = pd.read_csv(TRAIN_CSV)

    print(f"[train] Loaded {len (df ):,} training rows")

    texts = build_augmented_text(df)  # FIX 4: station-prefixed text

    cause_labels = df["event_cause"].tolist()

    priority_labels = df["priority"].tolist()

    print(f"\n[train] Loading sentence-transformer: {EMBEDDING_MODEL }")

    print(
        f"  Device : {DEVICE }  ({'RTX 4060 active 🚀'if DEVICE =='cuda'else 'CPU — no CUDA detected'})"
    )

    print("  (First run downloads ~120 MB — subsequent runs use cache)")

    encoder = SentenceTransformer(EMBEDDING_MODEL, device=DEVICE)

    print(f"\n[train] Embedding {len (texts ):,} training descriptions ...")

    X_train = embed(texts, encoder)

    print(f"  Embedding shape: {X_train .shape }")

    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    np.save(MODELS_DIR / "train_embeddings.npy", X_train)

    print(f"  Cached embeddings -> models/train_embeddings.npy")

    cause_le = LabelEncoder()

    y_cause = cause_le.fit_transform(cause_labels)

    print(f"\n[train] event_cause classes ({len (cause_le .classes_ )}):")

    for i, cls in enumerate(cause_le.classes_):

        count = np.sum(y_cause == i)

        print(f"  [{i :2d}] {cls :<35} {count :,} samples")

    priority_le = LabelEncoder()

    y_priority = priority_le.fit_transform(priority_labels)

    print(f"\n[train] priority classes: {priority_le .classes_ }")

    X_train_cause_os, y_cause_os = oversample(X_train, y_cause, "event_cause")
    cause_clf = train_classifier(X_train_cause_os, y_cause_os, "event_cause")

    X_train_prio_os, y_priority_os = oversample(X_train, y_priority, "priority")
    priority_clf = train_classifier(X_train_prio_os, y_priority_os, "priority")

    joblib.dump(cause_clf, MODELS_DIR / "cause_classifier.joblib")

    joblib.dump(priority_clf, MODELS_DIR / "priority_classifier.joblib")

    joblib.dump(cause_le, MODELS_DIR / "cause_label_encoder.joblib")

    joblib.dump(priority_le, MODELS_DIR / "priority_label_encoder.joblib")

    print(f"\n[train] Models saved to {MODELS_DIR }/")

    print("  cause_classifier.joblib")

    print("  priority_classifier.joblib")

    print("  cause_label_encoder.joblib")

    print("  priority_label_encoder.joblib")

    print(f"\n[train] === TRAIN SET CLASSIFICATION REPORT (event_cause) ===")

    cause_preds = cause_clf.predict(X_train)

    print(classification_report(y_cause, cause_preds, target_names=cause_le.classes_))

    print(f"\n[train] === TRAIN SET CLASSIFICATION REPORT (priority) ===")

    prio_preds = priority_clf.predict(X_train)

    print(
        classification_report(y_priority, prio_preds, target_names=priority_le.classes_)
    )

    print("\n[train] Done. Next step: python src/validate_tune.py")


if __name__ == "__main__":

    main()