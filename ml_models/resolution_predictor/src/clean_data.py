"""

clean_data.py

-------------

RAW CSV  →  data/processed/resolution_events_clean.csv



What this script does, step by step:

  1. Loads the raw 8173-row ASTRAM CSV.

  2. Parses datetimes and derives duration_min (clearance time in minutes).

     - Uses resolved_datetime if present, falls back to closed_datetime.

     - Only keeps rows where 0 < duration_min < 600 (avoid negatives, outlier closures).

  3. Keeps only the unplanned events (planned events belong to Person C's model).

  4. Drops rows missing any feature column we actually train on.

  5. Engineers a few lightweight features (hour_of_day, day_of_week, is_peak_hour).

  6. Writes the cleaned CSV to data/processed/.



Run:

    python src/clean_data.py

"""

import pandas as pd

import numpy as np

import os


RAW_PATH = os.path.join("data", "raw", "astram_events_raw.csv")

OUT_PATH = os.path.join("data", "processed", "resolution_events_clean.csv")


FEATURE_COLS = [
    "event_cause",
    "corridor",
    "priority",
    "requires_road_closure",
    "police_station",
    "hour_of_day",
    "day_of_week",
    "is_peak_hour",
]

TARGET_COL = "duration_min"


def load_raw(path: str) -> pd.DataFrame:

    df = pd.read_csv(path, low_memory=False)

    print(f"[clean] Loaded {len (df )} rows from {path }")

    return df


def parse_datetimes(df: pd.DataFrame) -> pd.DataFrame:

    df["start"] = pd.to_datetime(df["start_datetime"], utc=True, errors="coerce")

    df["resolved"] = pd.to_datetime(df["resolved_datetime"], utc=True, errors="coerce")

    df["closed"] = pd.to_datetime(df["closed_datetime"], utc=True, errors="coerce")

    df["end_time"] = df["resolved"].fillna(df["closed"])

    df["duration_min"] = (df["end_time"] - df["start"]).dt.total_seconds() / 60

    return df


def filter_usable(df: pd.DataFrame) -> pd.DataFrame:

    before = len(df)

    df = df[df["event_type"] == "unplanned"].copy()

    print(f"[clean] After keeping unplanned only: {len (df )} rows")

    df = df[df["duration_min"].notna()].copy()

    df = df[(df["duration_min"] > 0) & (df["duration_min"] < 600)].copy()

    print(f"[clean] After duration filter (0–600 min): {len (df )} rows")

    core_features = [
        "event_cause",
        "corridor",
        "priority",
        "requires_road_closure",
        "police_station",
    ]

    df = df.dropna(subset=core_features).copy()

    print(
        f"[clean] After dropping rows with missing core features: {len (df )} rows  (dropped {before -len (df )} total)"
    )

    return df


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:

    df["hour_of_day"] = df["start"].dt.hour

    df["day_of_week"] = df["start"].dt.dayofweek

    df["is_peak_hour"] = df["hour_of_day"].isin(range(7, 10)).astype(int) | df[
        "hour_of_day"
    ].isin(range(17, 20)).astype(int)

    df["is_peak_hour"] = df["is_peak_hour"].astype(int)

    df["requires_road_closure"] = df["requires_road_closure"].astype(int)

    return df


def save(df: pd.DataFrame, path: str) -> None:

    os.makedirs(os.path.dirname(path), exist_ok=True)

    out_cols = FEATURE_COLS + [TARGET_COL]

    df[out_cols].to_csv(path, index=False)

    print(f"[clean] Saved {len (df )} rows -> {path }")

    print(f"[clean] Columns: {out_cols }")

    print(f"\n[clean] Target (duration_min) summary:")

    print(df[TARGET_COL].describe().round(2).to_string())

    print(f"\n[clean] event_cause distribution:")

    print(df["event_cause"].value_counts().to_string())


def main():

    df = load_raw(RAW_PATH)

    df = parse_datetimes(df)

    df = filter_usable(df)

    df = engineer_features(df)

    save(df, OUT_PATH)

    print("\n[clean] Done. Run src/split_data.py next.")


if __name__ == "__main__":

    main()
