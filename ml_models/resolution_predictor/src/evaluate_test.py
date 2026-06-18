"""
evaluate_test.py
----------------
Run ONCE after all training and hyperparameter decisions are finalised.
Loads the Phase 3 tuned model and evaluates on test.csv.

Do NOT run this during development to avoid leaking test-set information
into your training decisions.  Run it only when you're truly done tuning.

Outputs a printed report and saves results to models/test_evaluation.json.

Run:
    python src/evaluate_test.py
"""

import pandas as pd
import numpy as np
import json
import os
import joblib

from sklearn.metrics import mean_absolute_error, r2_score

TEST_PATH  = os.path.join("data", "splits", "test.csv")
MODEL_PATH = os.path.join("models", "xgb_phase3_best.joblib")
PREP_PATH  = os.path.join("models", "preprocessor.joblib")
OUT_PATH   = os.path.join("models", "test_evaluation.json")

CAT_FEATURES = ["event_cause", "corridor", "priority", "police_station"]
NUM_FEATURES = ["requires_road_closure", "hour_of_day", "day_of_week", "is_peak_hour"]
ALL_FEATURES = CAT_FEATURES + NUM_FEATURES
TARGET       = "duration_min"


def main():
    print("[eval] Loading test set and model …")
    test_df      = pd.read_csv(TEST_PATH)
    model        = joblib.load(MODEL_PATH)
    preprocessor = joblib.load(PREP_PATH)

    X_test = preprocessor.transform(test_df[ALL_FEATURES])
    y_test = test_df[TARGET].values
    preds  = model.predict(X_test)

    mae    = mean_absolute_error(y_test, preds)
    r2     = r2_score(y_test, preds)
    median = np.median(np.abs(y_test - preds))   # median absolute error

    print(f"\n── Final test-set results ────────────────────────────────────────")
    print(f"  Rows evaluated : {len(test_df)}")
    print(f"  MAE            : {mae:.1f} minutes")
    print(f"  Median AE      : {median:.1f} minutes")
    print(f"  R²             : {r2:.3f}")
    print()

    # Per-cause breakdown — useful for judges
    test_df = test_df.copy()
    test_df["pred"] = preds
    test_df["abs_error"] = np.abs(y_test - preds)
    print("  Per-cause MAE:")
    per_cause = (
        test_df.groupby("event_cause")
        .agg(count=("duration_min", "count"), mae=("abs_error", "mean"))
        .round(1)
    )
    print(per_cause.to_string())

    results = {
        "n_rows":         int(len(test_df)),
        "mae_minutes":    round(float(mae), 2),
        "median_ae_min":  round(float(median), 2),
        "r2":             round(float(r2), 4),
        "per_cause_mae":  per_cause["mae"].to_dict(),
    }
    with open(OUT_PATH, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n[eval] Results saved -> {OUT_PATH}")


if __name__ == "__main__":
    main()