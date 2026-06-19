
import sys

import joblib

import torch

import numpy as np

import pandas as pd

from pathlib import Path

from sklearn.linear_model import LogisticRegression

from sklearn.preprocessing import LabelEncoder

from sklearn.metrics import classification_report, accuracy_score

from sentence_transformers import SentenceTransformer


ROOT = Path(__file__).resolve().parent

TRAIN_CSV = ROOT / "data" / "splits" / "train.csv"

MODELS_DIR = ROOT / "models"


DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"


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


def main():

    print(f"[train] Reading: {TRAIN_CSV }")

    if not TRAIN_CSV.exists():

        print("ERROR: train.csv not found. Run split_data.py first.")

        sys.exit(1)

    df = pd.read_csv(TRAIN_CSV)

    print(f"[train] Loaded {len (df ):,} training rows")

    texts = df["description"].tolist()

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

    cause_clf = train_classifier(X_train, y_cause, "event_cause")

    priority_clf = train_classifier(X_train, y_priority, "priority")

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
