"""
build_baseline.py
-----------------
ONE-TIME SETUP SCRIPT — run before starting the server.

Reads the raw ASTRAM CSV, computes average events per corridor per hour-of-day
across 152 days, and writes output/baseline.json.

Run:
    cd gridlock/ml_models/temporal_baseline
    python src/build_baseline.py
"""

import pandas as pd
import numpy as np
import json, os

RAW_CSV = os.path.join("data", "astram_raw.csv")
OUT_PATH = os.path.join("output", "baseline.json")

THRESHOLDS = {
    "normal": [0.0, 1.5],
    "elevated": [1.5, 3.0],
    "spike": [3.0, 6.0],
    "severe": [6.0, 9999],
}


def main():
    df = pd.read_csv(RAW_CSV, low_memory=False)
    df["start"] = pd.to_datetime(df["start_datetime"], utc=True, errors="coerce")
    df["hour"] = df["start"].dt.hour
    n_days = int(df["start"].dt.date.nunique())
    print(f"[baseline] {len(df)} rows across {n_days} days")

    valid = df.dropna(subset=["corridor", "hour"]).copy()
    valid["hour"] = valid["hour"].astype(int)

    grouped = (
        valid.groupby(["corridor", "hour"]).size().reset_index(name="total_events")
    )
    grouped["avg_per_day"] = grouped["total_events"] / n_days
    grouped["is_peak_hour"] = False

    for corridor, grp in grouped.groupby("corridor"):
        top3 = grp.nlargest(3, "total_events")["hour"].tolist()
        grouped.loc[grp.index, "is_peak_hour"] = grp["hour"].isin(top3).values

    baseline = {}
    for _, row in grouped.iterrows():
        c = str(row["corridor"])
        h = int(row["hour"])
        baseline.setdefault(c, {})[h] = {
            "total_events": int(row["total_events"]),
            "avg_per_day": round(float(row["avg_per_day"]), 4),
            "is_peak_hour": bool(row["is_peak_hour"]),
        }

    sys_hourly = valid.groupby("hour").size().reset_index(name="count")
    system = {
        int(r["hour"]): {
            "total_events": int(r["count"]),
            "avg_per_day": round(float(r["count"]) / n_days, 4),
        }
        for _, r in sys_hourly.iterrows()
    }

    out = {
        "n_days": n_days,
        "thresholds": THRESHOLDS,
        "corridors": baseline,
        "system": system,
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(out, f, indent=2)

    print(f"[baseline] {len(baseline)} corridors written → {OUT_PATH}")
    print(f"[baseline] Mysore Road hr21: {baseline.get('Mysore Road',{}).get(21)}")
    print(
        f"[baseline] System peak hour: {max(system, key=lambda h: system[h]['avg_per_day'])}:00"
    )
    print("\n[baseline] Done. Run python src/score.py to verify.")


if __name__ == "__main__":
    main()
