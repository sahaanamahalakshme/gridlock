"""
clean_data.py
=============
Reads the raw ASTRAM CSV and produces:
    data/processed/classifier_events_clean.csv

Task: Bilingual Event Classifier
Labels to predict:
    - event_cause  (multi-class: the TYPE of event)
    - priority     (binary: High / Low)

WHY we use the FULL dataset here (not 2,711 rows):
    The 2,711-row number applies to resolution-time prediction, where
    we need a known closure timestamp.  For the TEXT classifier we only
    need a description + a label — no closure time required.  That gives
    us access to ~6,000-8,000 rows depending on how many have usable
    descriptions, which is 3× more training signal.

Steps:
  1. Keep only columns the classifier needs.
  2. Drop rows where description is null or junk (< 3 real chars).
  3. Normalize event_cause casing/whitespace + merge known variants.
  4. Drop rows where priority is null.
  5. Drop rare event_cause classes (< MIN_CLASS_SIZE samples) — a class
     with 2 rows cannot be split into train/val/test meaningfully.
  6. Save cleaned CSV.

Usage:
    python src/clean_data.py
"""

import re
import sys
import pandas as pd
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT       = Path(__file__).resolve().parent          # bilingual_event_classifier/
OUTPUT_CSV = ROOT / "data" / "processed" / "classifier_events_clean.csv"


def _find_raw_csv() -> Path:
    """Auto-locate the raw ASTRAM CSV — handles any filename in data/."""
    data_dir   = ROOT / "data"
    candidates = sorted(p for p in data_dir.glob("*.csv"))
    if candidates:
        return candidates[0]
    return data_dir / "astram_events_raw.csv"   # fallback / docs reference


RAW_CSV = _find_raw_csv()

# ── Config ────────────────────────────────────────────────────────────────────
MIN_CLASS_SIZE = 10    # drop causes with fewer than this many samples
JUNK_CHAR_LEN  = 3    # descriptions with ≤ this many alphanumeric chars are junk

# ── Cause normalization ───────────────────────────────────────────────────────
# Add any case-variant merges you discover in YOUR csv here.
CAUSE_NORMALIZE = {
    "Debris":                  "debris",
    "Fog / Low Visibility":    "fog_low_visibility",
    "fog_/_low_visibility":    "fog_low_visibility",
    "VIP Movement":            "vip_movement",
    "Vip Movement":            "vip_movement",
}


def is_real_text(text: str, threshold: int = JUNK_CHAR_LEN) -> bool:
    """True if text has more than `threshold` alphanumeric or Kannada chars."""
    cleaned = re.sub(r'[^a-zA-Z0-9\u0C80-\u0CFF]', '', str(text))
    return len(cleaned) > threshold


def normalize_cause(cause: str) -> str:
    """Strip, title-map first, then lowercase + underscores."""
    cause = str(cause).strip()
    if cause in CAUSE_NORMALIZE:
        return CAUSE_NORMALIZE[cause]
    return cause.lower().replace(" ", "_").replace("/", "_")


def main():
    print(f"[clean_data] Reading: {RAW_CSV}")
    if not RAW_CSV.exists():
        print(f"ERROR: raw CSV not found at {RAW_CSV}")
        print("  -> Place your original ASTRAM CSV at data/raw/astram_events_raw.csv")
        sys.exit(1)

    df = pd.read_csv(RAW_CSV, low_memory=False)
    print(f"[clean_data] Loaded {len(df):,} rows × {df.shape[1]} columns")
    print(f"[clean_data] Columns: {df.columns.tolist()}")

    # ── Step 1: Keep only what the classifier needs ───────────────────────────
    KEEP = ["id", "description", "event_cause", "priority", "police_station", "corridor"]
    available = [c for c in KEEP if c in df.columns]
    missing   = [c for c in KEEP if c not in df.columns]
    if missing:
        print(f"[clean_data] WARNING — columns not found in CSV (will skip): {missing}")
    df = df[available].copy()

    # ── Step 2: Drop null descriptions ───────────────────────────────────────
    before = len(df)
    df = df[df["description"].notna()].copy()
    print(f"[clean_data] Dropped {before - len(df):,} rows with null description  ->  {len(df):,} remain")

    # ── Step 3: Drop junk descriptions ───────────────────────────────────────
    before = len(df)
    df = df[df["description"].apply(is_real_text)].copy()
    print(f"[clean_data] Dropped {before - len(df):,} junk descriptions             ->  {len(df):,} remain")

    # Strip extra whitespace
    df["description"] = df["description"].str.strip()

    # ── Step 4: Drop null / null-like priority ────────────────────────────────
    before = len(df)
    df = df[df["priority"].notna()].copy()
    df["priority"] = df["priority"].str.strip().str.capitalize()  # "High" or "Low"
    # Remove any unexpected priority values
    valid_priorities = {"High", "Low"}
    df = df[df["priority"].isin(valid_priorities)].copy()
    print(f"[clean_data] Dropped {before - len(df):,} rows with bad/null priority  ->  {len(df):,} remain")

    # ── Step 5: Drop rows with null event_cause ─────────────────────────────
    before = len(df)
    df = df[df["event_cause"].notna()].copy()
    if before - len(df):
        print(f"[clean_data] Dropped {before - len(df):,} rows with null event_cause  ->  {len(df):,} remain")

    # ── Step 6: Normalize event_cause ─────────────────────────────────────────
    df["event_cause"] = df["event_cause"].apply(normalize_cause)

    # ── Step 7: Drop rare classes ─────────────────────────────────────────────
    cause_counts = df["event_cause"].value_counts()
    rare_causes  = cause_counts[cause_counts < MIN_CLASS_SIZE].index.tolist()
    before = len(df)
    df = df[~df["event_cause"].isin(rare_causes)].copy()
    print(f"[clean_data] Dropped rare causes (< {MIN_CLASS_SIZE} samples): {rare_causes}")
    print(f"[clean_data] -> {len(df):,} rows remain after dropping rare classes")

    df = df.reset_index(drop=True)

    # ── Report ────────────────────────────────────────────────────────────────
    print(f"\n[clean_data] === FINAL DATASET SUMMARY ===")
    print(f"  Total rows  : {len(df):,}")
    print(f"  Unique causes: {df['event_cause'].nunique()}")
    print(f"\n  event_cause distribution:")
    print(df["event_cause"].value_counts().to_string())
    print(f"\n  priority distribution:")
    print(df["priority"].value_counts().to_string())

    # ── Save ──────────────────────────────────────────────────────────────────
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\n[clean_data] Saved -> {OUTPUT_CSV}")


if __name__ == "__main__":
    main()