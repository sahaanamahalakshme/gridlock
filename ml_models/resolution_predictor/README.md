# resolution_predictor — Person B's model

**What it does:** Takes structured event fields and predicts how many minutes until the event is cleared.

**Input:** `event_cause`, `corridor`, `priority`, `requires_road_closure`, `police_station`, `hour_of_day`, `day_of_week`  
**Output:** `predicted_minutes` + a rough confidence band

---

## Project structure

```
resolution_predictor/
├── data/
│   ├── raw/
│   │   └── astram_events_raw.csv      ← put the original 8173-row CSV here
│   ├── processed/
│   │   └── resolution_events_clean.csv
│   └── splits/
│       ├── train.csv
│       ├── val.csv
│       └── test.csv
├── models/                             ← created when you run the scripts
│   ├── baseline_medians.json
│   ├── preprocessor.joblib
│   ├── xgb_phase2.joblib
│   ├── xgb_phase3_best.joblib         ← use this in production
│   ├── phase3_best_params.json
│   └── test_evaluation.json
├── src/
│   ├── clean_data.py      → raw CSV → cleaned CSV
│   ├── split_data.py      → cleaned CSV → train/val/test
│   ├── train_model.py     → runs all 3 training phases
│   ├── evaluate_test.py   → one-time final test metrics
│   └── predict.py         → inference function for the API
├── requirements.txt
└── README.md
```

---

## Setup

```bash
pip install -r requirements.txt
```

---

## Run order

```bash
# 1. Put your CSV in data/raw/astram_events_raw.csv

# 2. Clean the data
python src/clean_data.py

# 3. Split into train / val / test
python src/split_data.py

# 4. Train (all 3 phases — takes a few minutes on CPU)
python src/train_model.py

# 5. Final evaluation — run ONCE when you're done tuning
python src/evaluate_test.py

# 6. Smoke-test the inference function
python src/predict.py
```

---

## Three training phases explained

| Phase | What it is | Why |
|---|---|---|
| 1 – Baseline | Median duration per event_cause | Floor to beat; judge-friendly "dumb baseline" |
| 2 – XGBoost defaults | 300 trees, no tuning | Proves the model beats baseline before touching hyperparams |
| 3 – XGBoost tuned | RandomizedSearchCV, 40 combos, 5-fold CV on train only | Best model; never looks at test.csv |

---

## What to tell judges

- **2,437 usable rows** (events with a recorded close time), all unplanned events.
- **Target:** minutes from event logged to road cleared (0–600 min range).
- **Dominant class:** ~75% vehicle breakdowns — per-cause MAE breakdown is more honest than overall MAE.
- **Why XGBoost:** 2,400 rows of mixed categorical + numeric data is exactly the regime where gradient-boosted trees outperform neural networks, and it trains in seconds, meaning you can re-run it if features change.
- The preprocessor and model are two separate `.joblib` files that must be loaded together.

---

## Connecting to Person B's FastAPI

```python
from src.predict import load_artifacts, predict

# At server startup
artifacts = load_artifacts()

# In your endpoint handler
result = predict(artifacts, {
    "event_cause":           "vehicle_breakdown",
    "corridor":              "ORR East 1",
    "priority":              "High",
    "requires_road_closure": False,
    "police_station":        "HSR Layout",
})
# → {"predicted_minutes": 54.3, "confidence_band": [24.3, 84.3], "method": "xgboost"}
```