"""
train_model.py
--------------
Trains the resolution-time regression model in three explicit phases.

Phase 1 – Baseline (median predictor per event_cause)
    No ML at all. Predict the median duration for this event_cause.
    This gives you a floor to beat and is defensible to judges
    ("here's what a rule-based system would do").

Phase 2 – XGBoost with default hyperparameters
    Categorical features encoded with OrdinalEncoder.
    Numeric features passed through.
    Trained on train.csv, evaluated on val.csv after each phase.

Phase 3 – XGBoost with light hyperparameter tuning (RandomizedSearchCV on train)
    5-fold CV inside train split.  Does NOT touch test.csv.
    Best params saved alongside the model.

Outputs (all in models/):
    baseline_medians.json          ← Phase 1 artefact
    xgb_phase2.joblib              ← Phase 2 model
    xgb_phase3_best.joblib         ← Phase 3 tuned model  (use this in production)
    preprocessor.joblib            ← fitted OrdinalEncoder (must ship with models)
    phase3_best_params.json        ← best hyperparams from Phase 3

Run:
    python src/train_model.py
"""

import pandas as pd
import numpy as np
import json
import os
import joblib

from sklearn.preprocessing import OrdinalEncoder
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import RandomizedSearchCV
from xgboost import XGBRegressor

# ── paths ─────────────────────────────────────────────────────────────────────
TRAIN_PATH = os.path.join("data", "splits", "train.csv")
VAL_PATH   = os.path.join("data", "splits", "val.csv")
MODEL_DIR  = "models"
os.makedirs(MODEL_DIR, exist_ok=True)

# ── feature lists ─────────────────────────────────────────────────────────────
CAT_FEATURES = ["event_cause", "corridor", "priority", "police_station"]
NUM_FEATURES = ["requires_road_closure", "hour_of_day", "day_of_week", "is_peak_hour"]
ALL_FEATURES = CAT_FEATURES + NUM_FEATURES
TARGET       = "duration_min"


# ── helpers ───────────────────────────────────────────────────────────────────
def load_splits():
    train = pd.read_csv(TRAIN_PATH)
    val   = pd.read_csv(VAL_PATH)
    print(f"[train] train={len(train)} rows, val={len(val)} rows")
    return train, val


def metrics(y_true, y_pred, label=""):
    mae = mean_absolute_error(y_true, y_pred)
    r2  = r2_score(y_true, y_pred)
    print(f"  [{label}]  MAE={mae:.1f} min  |  R²={r2:.3f}")
    return mae, r2


def build_preprocessor(train_df):
    """Fit OrdinalEncoder on training data only."""
    enc = OrdinalEncoder(
        handle_unknown="use_encoded_value",
        unknown_value=-1,
        encoded_missing_value=-2,
    )
    ct = ColumnTransformer(
        transformers=[
            ("cat", enc, CAT_FEATURES),
            ("num", "passthrough", NUM_FEATURES),
        ]
    )
    ct.fit(train_df[ALL_FEATURES])
    return ct


def transform(preprocessor, df):
    return preprocessor.transform(df[ALL_FEATURES])


# ── Phase 1: Baseline ─────────────────────────────────────────────────────────
def phase1_baseline(train_df, val_df):
    print("\n── Phase 1: Median-per-cause baseline ──────────────────────────")
    medians = train_df.groupby("event_cause")[TARGET].median().to_dict()
    global_median = train_df[TARGET].median()

    preds = val_df["event_cause"].map(medians).fillna(global_median)
    metrics(val_df[TARGET], preds, "Baseline val")

    out = {"medians": medians, "global_median": global_median}
    path = os.path.join(MODEL_DIR, "baseline_medians.json")
    with open(path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"  Saved -> {path}")
    return global_median


# ── Phase 2: XGBoost defaults ─────────────────────────────────────────────────
def phase2_xgb(train_df, val_df, preprocessor):
    print("\n── Phase 2: XGBoost (default hyperparams) ──────────────────────")
    X_train = transform(preprocessor, train_df)
    y_train = train_df[TARGET].values
    X_val   = transform(preprocessor, val_df)
    y_val   = val_df[TARGET].values

    model = XGBRegressor(
        n_estimators=300,
        random_state=42,
        tree_method="hist",   # fast on CPU
        verbosity=0,
    )
    model.fit(X_train, y_train)

    metrics(y_train, model.predict(X_train), "Phase 2 train")
    mae_val, _ = metrics(y_val,   model.predict(X_val),   "Phase 2 val  ")

    path = os.path.join(MODEL_DIR, "xgb_phase2.joblib")
    joblib.dump(model, path)
    print(f"  Saved -> {path}")
    return mae_val


# ── Phase 3: Tuned XGBoost ────────────────────────────────────────────────────
def phase3_tuned(train_df, val_df, preprocessor):
    print("\n── Phase 3: XGBoost with RandomizedSearchCV (5-fold on train) ──")
    X_train = transform(preprocessor, train_df)
    y_train = train_df[TARGET].values
    X_val   = transform(preprocessor, val_df)
    y_val   = val_df[TARGET].values

    param_dist = {
        "n_estimators":      [200, 400, 600, 800],
        "max_depth":         [3, 4, 5, 6, 7],
        "learning_rate":     [0.01, 0.05, 0.1, 0.2],
        "subsample":         [0.7, 0.8, 0.9, 1.0],
        "colsample_bytree":  [0.6, 0.7, 0.8, 1.0],
        "min_child_weight":  [1, 3, 5, 10],
        "gamma":             [0, 0.1, 0.3, 0.5],
    }

    base_model = XGBRegressor(
        tree_method="hist",
        random_state=42,
        verbosity=0,
    )

    search = RandomizedSearchCV(
        base_model,
        param_distributions=param_dist,
        n_iter=40,           # 40 random combos — enough for 5 days, not too slow
        cv=5,
        scoring="neg_mean_absolute_error",
        random_state=42,
        n_jobs=-1,           # use all CPU cores on Yoga Slim
        verbose=1,
    )
    search.fit(X_train, y_train)

    best = search.best_estimator_
    print(f"  Best params: {search.best_params_}")

    metrics(y_train, best.predict(X_train), "Phase 3 train")
    mae_val, _ = metrics(y_val, best.predict(X_val), "Phase 3 val  ")

    # Save model
    model_path = os.path.join(MODEL_DIR, "xgb_phase3_best.joblib")
    joblib.dump(best, model_path)
    print(f"  Saved -> {model_path}")

    # Save best params
    params_path = os.path.join(MODEL_DIR, "phase3_best_params.json")
    with open(params_path, "w") as f:
        json.dump(search.best_params_, f, indent=2)
    print(f"  Saved -> {params_path}")

    return mae_val


# ── main ──────────────────────────────────────────────────────────────────────
def main():
    train_df, val_df = load_splits()

    # Build & save preprocessor (fit on train ONLY — never on val or test)
    preprocessor = build_preprocessor(train_df)
    prep_path = os.path.join(MODEL_DIR, "preprocessor.joblib")
    joblib.dump(preprocessor, prep_path)
    print(f"[train] Preprocessor saved -> {prep_path}")

    # Run the three phases
    phase1_baseline(train_df, val_df)
    phase2_xgb(train_df, val_df, preprocessor)
    phase3_tuned(train_df, val_df, preprocessor)

    print("\n[train] All three phases done.")
    print("[train] Use xgb_phase3_best.joblib + preprocessor.joblib in production.")
    print("[train] Run src/evaluate_test.py for final one-time test metrics.")


if __name__ == "__main__":
    main()