import sys

import joblib

import torch

import numpy as np

import pandas as pd

from pathlib import Path

from sklearn.linear_model import LogisticRegression

from sklearn.svm import LinearSVC

from sklearn.calibration import CalibratedClassifierCV

from sklearn.metrics import (
    accuracy_score,
    f1_score,
    classification_report,
)

from sentence_transformers import SentenceTransformer
from imblearn.over_sampling import RandomOverSampler


ROOT = Path(__file__).resolve().parent

VAL_CSV = ROOT / "data" / "splits" / "val.csv"

MODELS_DIR = ROOT / "models"

REPORTS = ROOT / "reports"


DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


EMBEDDING_MODEL = "paraphrase-multilingual-mpnet-base-v2"

RANDOM_SEED = 42


C_GRID = [0.1, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0]


def embed_val(texts: list[str]) -> np.ndarray:

    cache = MODELS_DIR / "val_embeddings.npy"

    if cache.exists():

        print(f"[validate] Loading cached val embeddings from {cache }")

        return np.load(cache)

    print(f"[validate] Embedding {len (texts ):,} val descriptions on {DEVICE } ...")

    encoder = SentenceTransformer(EMBEDDING_MODEL, device=DEVICE)

    X = encoder.encode(
        texts,
        batch_size=64,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    np.save(cache, X)

    print(f"[validate] Val embeddings cached -> {cache }")

    return X


def load_train_embeddings() -> np.ndarray:

    path = MODELS_DIR / "train_embeddings.npy"

    if not path.exists():

        print("ERROR: train_embeddings.npy not found. Run train_model.py first.")

        sys.exit(1)

    return np.load(path)


def oversample(X, y, label):
    """FIX 3: same oversampling logic as train_model.py -- applied before
    EVERY model in the sweep, so the comparison between C values / SVC stays
    apples-to-apples with the imbalance-corrected training data, not the raw
    imbalanced data the original sweep used."""
    ros = RandomOverSampler(random_state=RANDOM_SEED)
    X_resampled, y_resampled = ros.fit_resample(X, y)
    print(
        f"[validate] Oversampled '{label}' for tuning: {len(y):,} -> {len(y_resampled):,} rows"
    )
    return X_resampled, y_resampled


def sweep_lr(X_train, y_train, X_val, y_val, label: str) -> tuple:
    """Grid-search C for LR. Returns (best_C, best_score, best_clf)."""

    print(f"\n[validate] Sweeping LR C values for '{label }':")

    best_c, best_score, best_clf = None, -1.0, None

    for c in C_GRID:

        clf = LogisticRegression(
            C=c,
            max_iter=1000,
            solver="lbfgs",
            class_weight="balanced",
            random_state=RANDOM_SEED,
            n_jobs=-1,
        )

        clf.fit(X_train, y_train)

        preds = clf.predict(X_val)

        score = f1_score(y_val, preds, average="macro")

        print(f"  C={c :<6}  macro-F1={score :.4f}")

        if score > best_score:

            best_score, best_c, best_clf = score, c, clf

    print(f"  -> Best C={best_c }, macro-F1={best_score :.4f}")

    return best_c, best_score, best_clf


def try_svc(X_train, y_train, X_val, y_val, label: str):

    print(f"\n[validate] Trying LinearSVC for '{label }':")

    svc = CalibratedClassifierCV(
        LinearSVC(max_iter=2000, class_weight="balanced", random_state=RANDOM_SEED),
        cv=3,
    )

    svc.fit(X_train, y_train)

    preds = svc.predict(X_val)

    score = f1_score(y_val, preds, average="macro")

    print(f"  LinearSVC macro-F1 = {score :.4f}")

    return score, svc


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

    print(f"[validate] Reading val CSV: {VAL_CSV }")

    if not VAL_CSV.exists():

        print("ERROR: val.csv not found. Run split_data.py first.")

        sys.exit(1)

    val_df = pd.read_csv(VAL_CSV)

    print(f"[validate] Loaded {len (val_df ):,} val rows")

    cause_le = joblib.load(MODELS_DIR / "cause_label_encoder.joblib")

    priority_le = joblib.load(MODELS_DIR / "priority_label_encoder.joblib")

    y_cause_val = cause_le.transform(val_df["event_cause"].tolist())

    y_priority_val = priority_le.transform(val_df["priority"].tolist())

    X_train = load_train_embeddings()

    X_val = embed_val(build_augmented_text(val_df))

    train_df = pd.read_csv(ROOT / "data" / "splits" / "train.csv")

    y_cause_train = cause_le.transform(train_df["event_cause"].tolist())

    y_priority_train = priority_le.transform(train_df["priority"].tolist())

    lines = []

    print("\n" + "=" * 60)

    print("CAUSE CLASSIFIER TUNING")

    print("=" * 60)

    default_cause_clf = joblib.load(MODELS_DIR / "cause_classifier.joblib")

    default_preds = default_cause_clf.predict(X_val)

    default_score = f1_score(y_cause_val, default_preds, average="macro")

    print(f"\n[validate] Default model (C=4.0) val macro-F1: {default_score :.4f}")

    X_train_cause_os, y_cause_train_os = oversample(
        X_train, y_cause_train, "event_cause"
    )

    best_c_cause, best_lr_score_cause, best_lr_cause = sweep_lr(
        X_train_cause_os, y_cause_train_os, X_val, y_cause_val, "event_cause"
    )

    svc_score_cause, svc_cause = try_svc(
        X_train_cause_os, y_cause_train_os, X_val, y_cause_val, "event_cause"
    )

    if svc_score_cause > best_lr_score_cause:

        best_cause_clf = svc_cause

        best_cause_score = svc_score_cause

        best_cause_name = "LinearSVC"

    else:

        best_cause_clf = best_lr_cause

        best_cause_score = best_lr_score_cause

        best_cause_name = f"LogisticRegression(C={best_c_cause })"

    print(
        f"\n[validate] Best cause model: {best_cause_name }  macro-F1={best_cause_score :.4f}"
    )

    joblib.dump(best_cause_clf, MODELS_DIR / "cause_classifier.joblib")

    print(f"  Saved -> models/cause_classifier.joblib")

    cause_report = classification_report(
        y_cause_val,
        best_cause_clf.predict(X_val),
        target_names=cause_le.classes_,
        labels=range(len(cause_le.classes_)),
    )

    print("\n[validate] Cause classifier — val set classification report:")

    print(cause_report)

    lines.append("=== CAUSE CLASSIFIER (val set) ===")

    lines.append(f"Best model: {best_cause_name }  macro-F1={best_cause_score :.4f}")

    lines.append(cause_report)

    print("\n" + "=" * 60)

    print("PRIORITY CLASSIFIER TUNING")

    print("=" * 60)

    default_prio_clf = joblib.load(MODELS_DIR / "priority_classifier.joblib")

    default_prio_preds = default_prio_clf.predict(X_val)

    default_prio_score = f1_score(y_priority_val, default_prio_preds, average="macro")

    print(f"\n[validate] Default model (C=4.0) val macro-F1: {default_prio_score :.4f}")

    X_train_prio_os, y_priority_train_os = oversample(
        X_train, y_priority_train, "priority"
    )

    best_c_prio, best_lr_score_prio, best_lr_prio = sweep_lr(
        X_train_prio_os, y_priority_train_os, X_val, y_priority_val, "priority"
    )

    svc_score_prio, svc_prio = try_svc(
        X_train_prio_os, y_priority_train_os, X_val, y_priority_val, "priority"
    )

    if svc_score_prio > best_lr_score_prio:

        best_prio_clf = svc_prio

        best_prio_score = svc_score_prio

        best_prio_name = "LinearSVC"

    else:

        best_prio_clf = best_lr_prio

        best_prio_score = best_lr_score_prio

        best_prio_name = f"LogisticRegression(C={best_c_prio })"

    print(
        f"\n[validate] Best priority model: {best_prio_name }  macro-F1={best_prio_score :.4f}"
    )

    joblib.dump(best_prio_clf, MODELS_DIR / "priority_classifier.joblib")

    print(f"  Saved -> models/priority_classifier.joblib")

    prio_report = classification_report(
        y_priority_val,
        best_prio_clf.predict(X_val),
        target_names=priority_le.classes_,
        labels=range(len(priority_le.classes_)),
    )

    print("\n[validate] Priority classifier — val set classification report:")

    print(prio_report)

    lines.append("\n=== PRIORITY CLASSIFIER (val set) ===")

    lines.append(f"Best model: {best_prio_name }  macro-F1={best_prio_score :.4f}")

    lines.append(prio_report)

    REPORTS.mkdir(parents=True, exist_ok=True)

    report_path = REPORTS / "val_report.txt"

    report_path.write_text("\n".join(lines))

    print(f"\n[validate] Report saved -> {report_path }")

    print("\n[validate] Done. Next step: python src/evaluate_test.py")


if __name__ == "__main__":

    main()
