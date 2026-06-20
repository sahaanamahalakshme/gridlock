import re

import sys

import pandas as pd

from pathlib import Path


ROOT = Path(__file__).resolve().parent

OUTPUT_CSV = ROOT / "data" / "processed" / "classifier_events_clean.csv"


def _find_raw_csv() -> Path:

    data_dir = ROOT / "data"

    candidates = sorted(p for p in data_dir.glob("*.csv"))

    if candidates:

        return candidates[0]

    return data_dir / "astram_events_raw.csv"


RAW_CSV = _find_raw_csv()


MIN_CLASS_SIZE = 25

JUNK_CHAR_LEN = 3


CAUSE_NORMALIZE = {
    "Debris": "debris",
    "Fog / Low Visibility": "fog_low_visibility",
    "fog_/_low_visibility": "fog_low_visibility",
    "VIP Movement": "vip_movement",
    "Vip Movement": "vip_movement",
    "debris": "tree_fall",
    "protest": "vip_movement",
    "road_conditions": "pot_holes",
}


POST_NORMALIZE_MERGE = {
    "debris": "tree_fall",
    "protest": "vip_movement",
    "road_conditions": "pot_holes",
}


def is_real_text(text: str, threshold: int = JUNK_CHAR_LEN) -> bool:

    cleaned = re.sub(r"[^a-zA-Z0-9\u0C80-\u0CFF]", "", str(text))

    return len(cleaned) > threshold


def normalize_cause(cause: str) -> str:

    cause = str(cause).strip()

    if cause in CAUSE_NORMALIZE:

        return CAUSE_NORMALIZE[cause]

    return cause.lower().replace(" ", "_").replace("/", "_")


def main():

    print(f"[clean_data] Reading: {RAW_CSV }")

    if not RAW_CSV.exists():

        print(f"ERROR: raw CSV not found at {RAW_CSV }")

        print("  -> Place your original ASTRAM CSV at data/raw/astram_events_raw.csv")

        sys.exit(1)

    df = pd.read_csv(RAW_CSV, low_memory=False)

    print(f"[clean_data] Loaded {len (df ):,} rows × {df .shape [1 ]} columns")

    print(f"[clean_data] Columns: {df .columns .tolist ()}")

    KEEP = [
        "id",
        "description",
        "event_cause",
        "priority",
        "police_station",
        "corridor",
    ]

    available = [c for c in KEEP if c in df.columns]

    missing = [c for c in KEEP if c not in df.columns]

    if missing:

        print(
            f"[clean_data] WARNING — columns not found in CSV (will skip): {missing }"
        )

    df = df[available].copy()

    before = len(df)

    df = df[df["description"].notna()].copy()

    print(
        f"[clean_data] Dropped {before -len (df ):,} rows with null description  ->  {len (df ):,} remain"
    )

    before = len(df)

    df = df[df["description"].apply(is_real_text)].copy()

    print(
        f"[clean_data] Dropped {before -len (df ):,} junk descriptions             ->  {len (df ):,} remain"
    )

    df["description"] = df["description"].str.strip()

    before = len(df)

    df = df[df["priority"].notna()].copy()

    df["priority"] = df["priority"].str.strip().str.capitalize()

    valid_priorities = {"High", "Low"}

    df = df[df["priority"].isin(valid_priorities)].copy()

    print(
        f"[clean_data] Dropped {before -len (df ):,} rows with bad/null priority  ->  {len (df ):,} remain"
    )

    before = len(df)

    df = df[df["event_cause"].notna()].copy()

    if before - len(df):

        print(
            f"[clean_data] Dropped {before -len (df ):,} rows with null event_cause  ->  {len (df ):,} remain"
        )

    df["event_cause"] = df["event_cause"].apply(normalize_cause)

    before_merge_classes = df["event_cause"].nunique()
    df["event_cause"] = df["event_cause"].replace(POST_NORMALIZE_MERGE)
    after_merge_classes = df["event_cause"].nunique()
    print(
        f"[clean_data] Merged thin classes: {before_merge_classes} -> {after_merge_classes} unique causes"
    )
    print(f"[clean_data] Merge map applied: {POST_NORMALIZE_MERGE}")

    cause_counts = df["event_cause"].value_counts()

    rare_causes = cause_counts[cause_counts < MIN_CLASS_SIZE].index.tolist()

    before = len(df)

    df = df[~df["event_cause"].isin(rare_causes)].copy()

    print(
        f"[clean_data] Dropped rare causes (< {MIN_CLASS_SIZE } samples): {rare_causes }"
    )

    print(f"[clean_data] -> {len (df ):,} rows remain after dropping rare classes")

    df = df.reset_index(drop=True)

    print(f"\n[clean_data] === FINAL DATASET SUMMARY ===")

    print(f"  Total rows  : {len (df ):,}")

    print(f"  Unique causes: {df ['event_cause'].nunique ()}")

    print(f"\n  event_cause distribution:")

    print(df["event_cause"].value_counts().to_string())

    print(f"\n  priority distribution:")

    print(df["priority"].value_counts().to_string())

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(OUTPUT_CSV, index=False)

    print(f"\n[clean_data] Saved -> {OUTPUT_CSV }")


if __name__ == "__main__":

    main()
