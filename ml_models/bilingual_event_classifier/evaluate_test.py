import sys

import joblib

import torch

import numpy as np

import pandas as pd

import matplotlib.pyplot as plt

import seaborn as sns

from pathlib import Path

from sklearn.metrics import (
    accuracy_score,
    f1_score,
    classification_report,
    confusion_matrix,
)

from sentence_transformers import SentenceTransformer


ROOT = Path(__file__).resolve().parent

TEST_CSV = ROOT / "data" / "splits" / "test.csv"

MODELS_DIR = ROOT / "models"

REPORTS = ROOT / "reports"


DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


# FIX 4: swapped from MiniLM -> mpnet. WHY: MiniLM is a smaller, faster but
# weaker multilingual model. Evidence ("CM Arrival" -> vehicle_breakdown at
# 81% confidence) showed it wasn't separating short domain-specific phrases
# well. mpnet is the same sentence-transformers library/API, just a larger
# backbone with stronger semantic separation -- no code changes needed
# beyond this string, only a slower first download (~1GB vs ~120MB) and
# slightly slower encode time.
EMBEDDING_MODEL = "paraphrase-multilingual-mpnet-base-v2"


def embed_test(texts: list[str]) -> np.ndarray:

    cache = MODELS_DIR / "test_embeddings.npy"

    if cache.exists():

        print(f"[evaluate] Loading cached test embeddings.")

        return np.load(cache)

    print(f"[evaluate] Embedding {len (texts ):,} test descriptions on {DEVICE } ...")

    encoder = SentenceTransformer(EMBEDDING_MODEL, device=DEVICE)

    X = encoder.encode(
        texts,
        batch_size=64,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    np.save(cache, X)

    return X


def plot_confusion(cm, class_names, title, save_path):

    fig, ax = plt.subplots(
        figsize=(max(8, len(class_names)), max(6, len(class_names) - 2))
    )

    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=class_names,
        yticklabels=class_names,
        ax=ax,
    )

    ax.set_xlabel("Predicted")

    ax.set_ylabel("True")

    ax.set_title(title)

    plt.tight_layout()

    plt.savefig(save_path, dpi=120)

    plt.close()

    print(f"  Saved confusion matrix -> {save_path }")


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

    print(f"[evaluate] Reading test CSV: {TEST_CSV }")

    if not TEST_CSV.exists():

        print("ERROR: test.csv not found. Run split_data.py first.")

        sys.exit(1)

    test_df = pd.read_csv(TEST_CSV)

    print(f"[evaluate] Loaded {len (test_df ):,} test rows")

    cause_le = joblib.load(MODELS_DIR / "cause_label_encoder.joblib")

    priority_le = joblib.load(MODELS_DIR / "priority_label_encoder.joblib")

    y_cause = cause_le.transform(test_df["event_cause"].tolist())

    y_priority = priority_le.transform(test_df["priority"].tolist())

    X_test = embed_test(build_augmented_text(test_df))  # FIX 4: station-prefixed text

    cause_clf = joblib.load(MODELS_DIR / "cause_classifier.joblib")

    priority_clf = joblib.load(MODELS_DIR / "priority_classifier.joblib")

    cause_preds = cause_clf.predict(X_test)

    priority_preds = priority_clf.predict(X_test)

    cause_acc = accuracy_score(y_cause, cause_preds)

    cause_f1 = f1_score(y_cause, cause_preds, average="macro")

    priority_acc = accuracy_score(y_priority, priority_preds)

    priority_f1 = f1_score(y_priority, priority_preds, average="macro")

    print(f"\n[evaluate] ============ FINAL TEST RESULTS ============")

    print(f"  event_cause   accuracy : {cause_acc :.4f}")

    print(f"  event_cause   macro-F1 : {cause_f1 :.4f}")

    print(f"  priority      accuracy : {priority_acc :.4f}")

    print(f"  priority      macro-F1 : {priority_f1 :.4f}")

    cause_report = classification_report(
        y_cause,
        cause_preds,
        target_names=cause_le.classes_,
        labels=range(len(cause_le.classes_)),
    )

    priority_report = classification_report(
        y_priority,
        priority_preds,
        target_names=priority_le.classes_,
        labels=range(len(priority_le.classes_)),
    )

    print("\n[evaluate] === event_cause classification report ===")

    print(cause_report)

    print("\n[evaluate] === priority classification report ===")

    print(priority_report)

    REPORTS.mkdir(parents=True, exist_ok=True)

    cm_cause = confusion_matrix(y_cause, cause_preds)

    plot_confusion(
        cm_cause,
        cause_le.classes_,
        "Confusion Matrix — event_cause (test set)",
        REPORTS / "confusion_matrix_cause.png",
    )

    cm_prio = confusion_matrix(y_priority, priority_preds)

    plot_confusion(
        cm_prio,
        priority_le.classes_,
        "Confusion Matrix — priority (test set)",
        REPORTS / "confusion_matrix_priority.png",
    )

    report_text = "\n".join(
        [
            "=== FINAL TEST SET RESULTS ===",
            f"event_cause  accuracy={cause_acc :.4f}  macro-F1={cause_f1 :.4f}",
            f"priority     accuracy={priority_acc :.4f}  macro-F1={priority_f1 :.4f}",
            "",
            "=== event_cause ===",
            cause_report,
            "",
            "=== priority ===",
            priority_report,
        ]
    )

    report_path = REPORTS / "test_report.txt"

    report_path.write_text(report_text)

    print(f"\n[evaluate] Test report saved -> {report_path }")

    print("[evaluate] Done. These are the numbers to quote to judges.")


if __name__ == "__main__":

    main()