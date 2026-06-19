"""

predict.py

----------

The function Person B's FastAPI endpoint actually calls at inference time.



Load the model once at server startup (expensive), then call predict() per request (cheap).



Usage in FastAPI:

    from src.predict import load_artifacts, predict



    # At startup:

    artifacts = load_artifacts()



    # Per request:

    result = predict(artifacts, {

        "event_cause":          "vehicle_breakdown",

        "corridor":             "ORR East 1",

        "priority":             "High",

        "requires_road_closure": False,

        "police_station":       "HSR Layout",

        "hour_of_day":          8,      # optional — defaults to current hour

        "day_of_week":          1,      # optional — defaults to today

    })



    # result = {"predicted_minutes": 54.3, "confidence_band": [24, 84]}

"""

import os

import json

import joblib

import numpy as np

import pandas as pd

from datetime import datetime, timezone


MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")


CAT_FEATURES = ["event_cause", "corridor", "priority", "police_station"]

NUM_FEATURES = ["requires_road_closure", "hour_of_day", "day_of_week", "is_peak_hour"]

ALL_FEATURES = CAT_FEATURES + NUM_FEATURES


def load_artifacts(model_dir: str = MODEL_DIR) -> dict:
    """

    Load model + preprocessor from disk.

    Call this ONCE at server startup, not per request.

    """

    model = joblib.load(os.path.join(model_dir, "xgb_phase3_best.joblib"))

    preprocessor = joblib.load(os.path.join(model_dir, "preprocessor.joblib"))

    with open(os.path.join(model_dir, "baseline_medians.json")) as f:

        baseline = json.load(f)

    return {"model": model, "preprocessor": preprocessor, "baseline": baseline}


def predict(artifacts: dict, event: dict) -> dict:
    """

    Predict resolution time for a single event.



    Parameters

    ----------

    artifacts : dict

        Output of load_artifacts().

    event : dict

        Must have: event_cause, corridor, priority, requires_road_closure, police_station.

        Optional : hour_of_day, day_of_week (defaults to now if omitted).



    Returns

    -------

    dict with:

        predicted_minutes  : float  — point estimate

        confidence_band    : [low, high]  — ±1 std based on training residuals (rough)

        method             : "xgboost" or "baseline_fallback"

    """

    now = datetime.now(tz=timezone.utc)

    hour = event.get("hour_of_day", now.hour)

    dow = event.get("day_of_week", now.weekday())

    is_peak = int(hour in range(7, 10) or hour in range(17, 20))

    road_close = int(bool(event.get("requires_road_closure", False)))

    row = pd.DataFrame(
        [
            {
                "event_cause": event.get("event_cause", "others"),
                "corridor": event.get("corridor", "Non-corridor"),
                "priority": event.get("priority", "Low"),
                "police_station": event.get("police_station", ""),
                "requires_road_closure": road_close,
                "hour_of_day": hour,
                "day_of_week": dow,
                "is_peak_hour": is_peak,
            }
        ]
    )

    try:

        X = artifacts["preprocessor"].transform(row[ALL_FEATURES])

        pred = float(artifacts["model"].predict(X)[0])

        method = "xgboost"

    except Exception as e:

        cause = event.get("event_cause", "others")

        medians = artifacts["baseline"]["medians"]

        pred = medians.get(cause, artifacts["baseline"]["global_median"])

        method = f"baseline_fallback (reason: {e })"

    band_low = max(0.0, round(pred - 30, 1))

    band_high = round(pred + 30, 1)

    return {
        "predicted_minutes": round(pred, 1),
        "confidence_band": [band_low, band_high],
        "method": method,
    }


if __name__ == "__main__":

    print("[predict] Loading artifacts …")

    arts = load_artifacts()

    test_event = {
        "event_cause": "vehicle_breakdown",
        "corridor": "ORR East 1",
        "priority": "High",
        "requires_road_closure": False,
        "police_station": "HSR Layout",
        "hour_of_day": 8,
        "day_of_week": 1,
    }

    result = predict(arts, test_event)

    print(f"[predict] Prediction: {result }")
